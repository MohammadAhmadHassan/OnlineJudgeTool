"""Shared judging logic for executing submitted Python solutions.

This preserves the Streamlit app's current script/function judging behavior.
The module is intentionally UI-free so it can run inside a disposable worker.
"""
import ast
import contextlib
import io
import json
import sys


_UNPARSED = object()
MAX_OUTPUT_CHARS = 10000


def _clip_output(value):
    text = "" if value is None else str(value)
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n...[output truncated]"


def _build_exec_globals():
    """Create a compatibility execution context with common contest libraries."""
    exec_globals = {
        "__builtins__": __builtins__,
    }

    try:
        from textblob import TextBlob
        exec_globals["TextBlob"] = TextBlob
    except ImportError:
        pass

    try:
        import numpy as np
        exec_globals["np"] = np
        exec_globals["numpy"] = np
    except ImportError:
        pass

    try:
        import requests
        exec_globals["requests"] = requests
    except ImportError:
        pass

    try:
        import math
        exec_globals["math"] = math
    except ImportError:
        pass

    try:
        import re
        exec_globals["re"] = re
    except ImportError:
        pass

    try:
        from collections import Counter, defaultdict, deque
        exec_globals["Counter"] = Counter
        exec_globals["defaultdict"] = defaultdict
        exec_globals["deque"] = deque
    except ImportError:
        pass

    try:
        from sklearn.tree import DecisionTreeClassifier
        exec_globals["DecisionTreeClassifier"] = DecisionTreeClassifier
    except ImportError:
        class DecisionTreeClassifier:
            def __init__(self, *args, **kwargs):
                self._X = []
                self._y = []

            def fit(self, X, y):
                self._X = [list(row) for row in (X or [])]
                self._y = list(y or [])
                return self

            def predict(self, X):
                if not self._X or not self._y:
                    raise ValueError("DecisionTreeClassifier is not fitted yet.")

                predictions = []
                for row in X or []:
                    candidate = list(row)
                    best_idx = 0
                    best_distance = None
                    for i, train_row in enumerate(self._X):
                        distance = 0.0
                        for a, b in zip(candidate, train_row):
                            diff = float(a) - float(b)
                            distance += diff * diff
                        if best_distance is None or distance < best_distance:
                            best_distance = distance
                            best_idx = i
                    predictions.append(self._y[best_idx])
                return predictions

        exec_globals["DecisionTreeClassifier"] = DecisionTreeClassifier

        try:
            import types

            sklearn_module = sys.modules.get("sklearn")
            if sklearn_module is None:
                sklearn_module = types.ModuleType("sklearn")
                sklearn_module.__path__ = []
                sys.modules["sklearn"] = sklearn_module

            tree_module = types.ModuleType("sklearn.tree")
            tree_module.DecisionTreeClassifier = DecisionTreeClassifier
            sys.modules["sklearn.tree"] = tree_module
            setattr(sklearn_module, "tree", tree_module)
        except Exception:
            pass

    return exec_globals


def _build_mock_input(raw_input):
    """Return deterministic input() implementation for a test case."""
    if isinstance(raw_input, (list, tuple)):
        input_lines = [str(item) for item in raw_input]
    else:
        input_text = "" if raw_input is None else str(raw_input)
        input_lines = input_text.splitlines() if input_text else []

    input_index = [0]

    def mock_input(prompt=""):
        if input_index[0] < len(input_lines):
            value = input_lines[input_index[0]]
            input_index[0] += 1
            return value
        return ""

    return mock_input


def _extract_function_spec(input_format):
    """Parse function name from formats like: 'Function: solve(a, b)'."""
    if not input_format:
        return None, None

    text = str(input_format).strip()
    if ":" not in text:
        return None, None

    label, remainder = text.split(":", 1)
    if label.strip().lower() != "function":
        return None, None

    signature = remainder.strip()
    if not signature:
        return None, None

    if "(" in signature:
        function_name = signature.split("(", 1)[0].strip()
        args_part = signature.split("(", 1)[1].rsplit(")", 1)[0].strip()
        arg_names = [arg.strip() for arg in args_part.split(",") if arg.strip()]
        expected_param_count = len(arg_names)
    else:
        function_name = signature.split()[0].strip()
        expected_param_count = None

    if not function_name.isidentifier():
        return None, None
    return function_name, expected_param_count


def _infer_function_spec_from_code(code):
    """Infer a top-level function signature from user code when metadata is missing."""
    try:
        tree = ast.parse(code)
    except Exception:
        return None, None

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        function_name = getattr(node, "name", None)
        if not function_name or not function_name.isidentifier():
            continue

        posonly_args = list(getattr(node.args, "posonlyargs", []))
        regular_args = list(node.args.args)
        expected_param_count = len(posonly_args + regular_args)
        return function_name, expected_param_count

    return None, None


def _try_parse_value(value):
    """Try converting text into Python scalar/list/dict."""
    if isinstance(value, (int, float, bool, list, tuple, dict)):
        return value

    if value is None:
        return ""

    text = str(value).strip()
    if text == "":
        return ""

    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        return ast.literal_eval(text)
    except Exception:
        return _UNPARSED


def _parse_token(token):
    """Parse a scalar token, fallback to raw string."""
    token = token.strip()
    parsed = _try_parse_value(token)
    if parsed is _UNPARSED:
        return token
    return parsed


def _parse_function_args(raw_input, expected_param_count=None):
    """Convert test input into function args/kwargs."""
    if isinstance(raw_input, dict):
        if expected_param_count == 1 or expected_param_count is None:
            return [dict(raw_input)], {}
        return [], dict(raw_input)
    if isinstance(raw_input, (list, tuple)):
        if expected_param_count == 1:
            return [list(raw_input)], {}
        return list(raw_input), {}

    raw_text = "" if raw_input is None else str(raw_input)
    stripped = raw_text.strip()
    if stripped == "":
        return [], {}

    parsed_all = _try_parse_value(stripped)
    if parsed_all is not _UNPARSED:
        if isinstance(parsed_all, dict):
            if expected_param_count == 1 or expected_param_count is None:
                return [parsed_all], {}
            return [], parsed_all
        if isinstance(parsed_all, tuple):
            return list(parsed_all), {}
        if isinstance(parsed_all, list):
            if expected_param_count == 1:
                return [parsed_all], {}
            return list(parsed_all), {}
        return [parsed_all], {}

    lines = raw_text.splitlines()
    if len(lines) > 1:
        parsed_lines = [_parse_token(line) for line in lines]
        if expected_param_count == 1:
            return [parsed_lines], {}
        if expected_param_count and len(parsed_lines) == expected_param_count:
            return parsed_lines, {}
        if expected_param_count and len(parsed_lines) > expected_param_count:
            if expected_param_count == 2:
                return [parsed_lines[:-1], parsed_lines[-1]], {}
            if (
                expected_param_count == 3
                and isinstance(parsed_lines[0], (list, tuple, dict))
                and isinstance(parsed_lines[-1], (list, tuple, dict))
            ):
                return [parsed_lines[0], parsed_lines[1:-1], parsed_lines[-1]], {}

            overflow = len(parsed_lines) - expected_param_count + 1
            grouped_first_arg = parsed_lines[:overflow]
            return [grouped_first_arg] + parsed_lines[overflow:], {}
        return parsed_lines, {}

    line = lines[0] if lines else stripped

    if "," in line:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) > 1:
            return [_parse_token(part) for part in parts], {}

    if expected_param_count and expected_param_count > 1 and " " in line:
        parts = [part for part in line.split() if part]
        if len(parts) == expected_param_count:
            return [_parse_token(part) for part in parts], {}

    return [_parse_token(line)], {}


def _normalize_return_value(value):
    """Format function return value for display/comparison."""
    if value is None:
        return ""
    if isinstance(value, tuple):
        return "\n".join(str(item) for item in value).strip()
    if isinstance(value, list):
        return "\n".join(str(item) for item in value).strip()
    return str(value).strip()


def _run_single_test_as_script(code, test):
    stdout_capture = io.StringIO()
    exec_globals = _build_exec_globals()
    exec_globals["input"] = _build_mock_input(test.get("input", ""))

    with contextlib.redirect_stdout(stdout_capture):
        exec(code, exec_globals)

    output = _clip_output(stdout_capture.getvalue().strip())
    expected = str(test.get("output", "")).strip()
    passed = output == expected
    return output, expected, passed


def _run_single_test_as_function(code, test, function_name, expected_param_count=None):
    stdout_capture = io.StringIO()
    exec_globals = _build_exec_globals()

    exec_globals["input"] = _build_mock_input(test.get("input", ""))

    with contextlib.redirect_stdout(stdout_capture):
        exec(code, exec_globals)

    target_function = exec_globals.get(function_name)
    if not callable(target_function):
        raise NameError(f"Function '{function_name}' not found.")

    args, kwargs = _parse_function_args(test.get("input", ""), expected_param_count)
    expected = str(test.get("output", "")).strip()
    parsed_expected = _try_parse_value(expected)

    call_candidates = [(args, kwargs)]
    if expected_param_count == 1 and not kwargs and len(args) == 1 and not isinstance(args[0], (list, tuple)):
        call_candidates.append(([[args[0]]], {}))

    first_exception = None
    first_result = None

    for candidate_args, candidate_kwargs in call_candidates:
        try:
            call_stdout_capture = io.StringIO()
            with contextlib.redirect_stdout(call_stdout_capture):
                result = target_function(*candidate_args, **candidate_kwargs)

            printed_output = _clip_output(call_stdout_capture.getvalue().strip())
            if result is None:
                output = printed_output
            else:
                output = _clip_output(_normalize_return_value(result))
                if not output and printed_output:
                    output = printed_output

            passed = output == expected
            if not passed and result is not None:
                if parsed_expected is not _UNPARSED and result == parsed_expected:
                    passed = True

            if first_result is None or (not first_result[0] and output):
                first_result = (output, expected, passed)

            if passed:
                return output, expected, passed
        except Exception as call_error:
            if first_exception is None:
                first_exception = call_error

    if first_result is not None:
        return first_result
    if first_exception is not None:
        raise first_exception
    raise RuntimeError("Unable to evaluate function call.")


def run_code_with_tests(code, test_cases, input_format=None):
    """Execute competitor code against test cases, supporting script and function styles."""
    results = []
    function_name, expected_param_count = _extract_function_spec(input_format)
    inferred_function_name, inferred_param_count = (None, None)
    if not function_name:
        inferred_function_name, inferred_param_count = _infer_function_spec_from_code(code)

    for i, test in enumerate(test_cases):
        try:
            if function_name:
                function_attempt = None
                function_exception = None

                try:
                    function_attempt = _run_single_test_as_function(
                        code=code,
                        test=test,
                        function_name=function_name,
                        expected_param_count=expected_param_count,
                    )
                except Exception as function_error:
                    function_exception = function_error

                script_attempt = None
                script_exception = None
                try:
                    script_attempt = _run_single_test_as_script(code, test)
                except Exception as script_error:
                    script_exception = script_error

                if function_attempt and function_attempt[2]:
                    output, expected, passed = function_attempt
                elif script_attempt and script_attempt[2]:
                    output, expected, passed = script_attempt
                elif function_attempt:
                    output, expected, passed = function_attempt
                elif function_exception is not None:
                    raise function_exception
                elif script_attempt:
                    output, expected, passed = script_attempt
                elif script_exception is not None:
                    raise script_exception
                else:
                    raise RuntimeError("Unable to evaluate test case.")
            else:
                output, expected, passed = _run_single_test_as_script(code, test)

                if (
                    not passed
                    and not output
                    and str(expected).strip() != ""
                    and inferred_function_name
                ):
                    try:
                        function_output, function_expected, function_passed = _run_single_test_as_function(
                            code=code,
                            test=test,
                            function_name=inferred_function_name,
                            expected_param_count=inferred_param_count,
                        )
                        if function_passed or function_output:
                            output, expected, passed = function_output, function_expected, function_passed
                    except Exception:
                        pass

            results.append({
                "test_num": i + 1,
                "passed": passed,
                "input": str(test.get("input", "")),
                "expected": str(expected),
                "output": _clip_output(output),
                "error": None,
            })

        except Exception as exc:
            results.append({
                "test_num": i + 1,
                "passed": False,
                "input": str(test.get("input", "")),
                "expected": str(test.get("output", "")),
                "output": f"Error: {str(exc)}",
                "error": str(exc),
            })

    return results
