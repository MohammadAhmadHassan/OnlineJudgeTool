"""
Competitor Interface - Streamlit Version
Solve programming problems and submit solutions
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
import os
import io
import contextlib
import time
import importlib
import html
import ast

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager
from firebase_config import FirebaseConfig

# Check if running in single-dashboard mode and hide sidebar navigation
DASHBOARD_MODE = os.environ.get('DASHBOARD_MODE', None)
if DASHBOARD_MODE is None:
    try:
        DASHBOARD_MODE = st.secrets.get('DASHBOARD_MODE', 'all')
    except:
        DASHBOARD_MODE = 'all'

# Hide sidebar navigation if in competitor-only mode
if DASHBOARD_MODE and DASHBOARD_MODE.lower() == 'competitor':
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Competitor Interface",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .problem-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .problem-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    .problem-solved {
        border-color: #27ae60;
        background: #d4edda;
    }
    .problem-failed {
        border-color: #e74c3c;
        background: #f8d7da;
    }
    .test-result {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        border-left: 4px solid;
    }
    .test-passed {
        background: #d4edda;
        border-color: #27ae60;
    }
    .test-failed {
        background: #f8d7da;
        border-color: #e74c3c;
    }
    .code-output {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }
    .stat-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-warning { background: #fff3cd; color: #856404; }
    .badge-info { background: #d1ecf1; color: #0c5460; }
    .badge-danger { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize data manager
@st.cache_resource
def get_data_manager(config_fingerprint=""):
    return create_data_manager()


def get_firebase_config_fingerprint():
    """Build a cache key that changes when firebase credential source changes."""
    FirebaseConfig.load_credentials()
    source = str(FirebaseConfig.get_last_source() or "none")
    error = str(FirebaseConfig.get_last_error() or "")
    mtime_token = "0"

    if source and source != "none" and os.path.exists(source):
        try:
            mtime_token = str(os.path.getmtime(source))
        except Exception:
            pass

    return f"{source}|{mtime_token}|{error}"


data_manager = get_data_manager(get_firebase_config_fingerprint())

# Retry once if credentials look configured but cached manager is still JSON.
if (
    data_manager.get_backend_type() == "json"
    and FirebaseConfig.is_configured()
    and not st.session_state.get("_firebase_reconnect_retry_done", False)
):
    st.session_state["_firebase_reconnect_retry_done"] = True
    get_data_manager.clear()
    data_manager = get_data_manager(get_firebase_config_fingerprint())

BACKEND_TYPE = data_manager.get_backend_type()
BACKEND_DEBUG = (
    data_manager.get_backend_debug_info()
    if hasattr(data_manager, "get_backend_debug_info")
    else {}
)

# Live rejection notifications refresh every 10 seconds.
NOTIFICATION_REFRESH_SECONDS = 10
FINAL_COMPETITION_TITLE = "FinalCompetition"
FINAL_COMPETITION_TITLE_ALIASES = ["FinalCompetion"]
FINAL_COMPETITION_WEEK = 19

LEVEL_LABEL_TO_VALUE = {
    "Junior Level": 1,
    "Senior Level": 2,
}

TEST_CASE_KEYS = [
    "test_cases",
    "testCases",
    "tests",
    "cases",
    "public_tests",
    "test_cases_display_safe",
]


def get_level_label(level_value):
    """Return display label for numeric level."""
    for label, value in LEVEL_LABEL_TO_VALUE.items():
        if value == level_value:
            return label
    return "Junior Level"

# Initialize session state
if 'competitor_name' not in st.session_state:
    st.session_state.competitor_name = None
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = None
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'test_results' not in st.session_state:
    st.session_state.test_results = None
if 'user_week' not in st.session_state:
    st.session_state.user_week = FINAL_COMPETITION_WEEK
if 'user_level' not in st.session_state:
    st.session_state.user_level = LEVEL_LABEL_TO_VALUE["Junior Level"]

# Cached problems loader
@st.cache_data(ttl=3600)  # Cache problems for 1 hour (they never change)
def get_cached_problems(week=None, level=None):
    """Get problems with Streamlit caching"""
    return data_manager.get_problems(week=week, level=level)


def _extract_level_from_collection_name(collection_name):
    """Extract numeric level from collection names like level1_session13."""
    name = str(collection_name or "").strip()
    lower_name = name.lower()

    if not lower_name.startswith("level") or "_" not in name:
        return None

    underscore_index = name.find("_")
    level_part = name[5:underscore_index]
    if level_part.isdigit():
        return int(level_part)
    return None


def _strip_level_prefix(collection_name):
    """Return collection without level prefix (level1_session13 -> session13)."""
    name = str(collection_name or "").strip()
    parsed_level = _extract_level_from_collection_name(name)
    if parsed_level is None:
        return name
    return name[name.find("_") + 1:]


def _is_session_collection_name(collection_name):
    """Check whether the collection key is a session key like session13."""
    key = _strip_level_prefix(collection_name).strip().lower()
    return key.startswith("session") and key[7:].isdigit()


def _get_session_sort_key(collection_name):
    """Session-aware sort key so session2 comes before session10."""
    key = _strip_level_prefix(collection_name).strip().lower()
    if key.startswith("session") and key[7:].isdigit():
        return int(key[7:])
    return 10**9


def _add_problem_to_map(problem_map, problem, level=None):
    """Normalize and insert a problem while keeping ids unique."""
    next_auto_id = max(problem_map.keys(), default=0) + 1
    normalized = normalize_problem_schema(
        problem,
        fallback_level=level,
        fallback_problem_id=next_auto_id
    )
    if not normalized:
        return

    if level is not None and str(normalized.get("level", "")) != str(level):
        return

    problem_id = normalized.get("id")
    if not isinstance(problem_id, int):
        problem_id = next_auto_id
        normalized["id"] = problem_id

    while problem_id in problem_map:
        problem_id += 1
        normalized["id"] = problem_id

    problem_map[problem_id] = normalized


def _extract_problem_entries(payload):
    """Return a normalized list of problem dicts from mixed payload shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        # Common shape: {"problems": [...]} or {"problems": {...}}.
        if "problems" in payload:
            return _extract_problem_entries(payload.get("problems"))

        # Direct problem map shape: {"1": {...}, "2": {...}}
        entries = []
        for value in payload.values():
            if isinstance(value, dict):
                entries.append(value)
        return entries

    return []


def normalize_problem_schema(problem, fallback_level=None, fallback_problem_id=None):
    """Normalize uploaded problem payloads into the schema expected by competitor UI."""
    if not isinstance(problem, dict):
        return None

    normalized = dict(problem)

    # Normalize title/description fields for alternate authoring formats.
    if not normalized.get("title"):
        normalized["title"] = "Untitled Problem"

    if not normalized.get("description"):
        story = str(normalized.get("story", "")).strip()
        task = str(normalized.get("task", "")).strip()
        composed = "\n\n".join([part for part in [story, task] if part])
        normalized["description"] = composed if composed else "No description available"

    # Normalize level field.
    if "level" not in normalized and fallback_level is not None:
        normalized["level"] = fallback_level

    # Normalize test cases from multiple possible key names.
    raw_test_cases = None
    for key in TEST_CASE_KEYS:
        candidate = normalized.get(key)
        if isinstance(candidate, list):
            raw_test_cases = candidate
            break

    cleaned_test_cases = []
    if isinstance(raw_test_cases, list):
        for test in raw_test_cases:
            if isinstance(test, dict):
                test_input = test.get("input", test.get("in", test.get("stdin", "")))
                test_output = test.get("output", test.get("out", test.get("expected", "")))
                cleaned_test_cases.append({
                    "input": str(test_input),
                    "output": str(test_output),
                })
            elif isinstance(test, (list, tuple)) and len(test) >= 2:
                cleaned_test_cases.append({
                    "input": str(test[0]),
                    "output": str(test[1]),
                })

    normalized["test_cases"] = cleaned_test_cases

    # Ensure numeric id exists.
    problem_id = normalized.get("id")
    if not isinstance(problem_id, int):
        if isinstance(problem_id, str) and problem_id.isdigit():
            problem_id = int(problem_id)
            normalized["id"] = problem_id
        elif fallback_problem_id is not None:
            normalized["id"] = int(fallback_problem_id)

    return normalized


@st.cache_data(ttl=3600)  # Cache named competition problems for 1 hour
def get_cached_competition_problems(competition_title, level=None):
    """Get problems for a named competition (e.g., FinalCompetion)."""
    if not competition_title:
        return {}

    # Firebase-specific fast path: read direct collection docs like:
    # level1_FinalCompetion / level2_FinalCompetion / FinalCompetion
    if data_manager.is_firebase():
        backend = getattr(data_manager, 'backend', None)
        if backend is not None and hasattr(backend, 'problems_ref'):
            doc_names_to_try = []
            if level is not None:
                doc_names_to_try.append(f"level{level}_{competition_title}")
            # Also probe known level prefixes to tolerate upload-level mismatch.
            for level_probe in [1, 2, 3, 4, 5]:
                candidate_name = f"level{level_probe}_{competition_title}"
                if candidate_name not in doc_names_to_try:
                    doc_names_to_try.append(candidate_name)
            doc_names_to_try.append(competition_title)

            for doc_name in doc_names_to_try:
                doc = backend.problems_ref.document(doc_name).get()
                if not doc.exists:
                    continue

                data = doc.to_dict() or {}
                problems_list = data.get('problems', [])
                problems = {}
                auto_problem_id = 1

                for problem in problems_list:
                    normalized = normalize_problem_schema(
                        problem,
                        fallback_level=level,
                        fallback_problem_id=auto_problem_id
                    )
                    if not normalized:
                        continue

                    problem_id = normalized.get('id')
                    if not isinstance(problem_id, int):
                        problem_id = auto_problem_id
                        normalized['id'] = problem_id

                    auto_problem_id += 1

                    if level is None or str(normalized.get('level', '')) == str(level):
                        problems[problem_id] = normalized

                if problems:
                    return problems

            # Secondary path: read from all-problems nested docs if present.
            for doc_name in ['Level1_AllProblems', 'all_problems', 'problems']:
                doc = backend.problems_ref.document(doc_name).get()
                if not doc.exists:
                    continue

                data = doc.to_dict() or {}
                sessions_data = data.get('sessions', {})
                if competition_title not in sessions_data:
                    continue

                session_data = sessions_data.get(competition_title, {})
                problems_list = session_data.get('problems', [])
                problems = {}
                auto_problem_id = 1

                for problem in problems_list:
                    normalized = normalize_problem_schema(
                        problem,
                        fallback_level=level,
                        fallback_problem_id=auto_problem_id
                    )
                    if not normalized:
                        continue

                    problem_id = normalized.get('id')
                    if not isinstance(problem_id, int):
                        problem_id = auto_problem_id
                        normalized['id'] = problem_id

                    auto_problem_id += 1

                    if level is None or str(normalized.get('level', '')) == str(level):
                        problems[problem_id] = normalized

                if problems:
                    return problems

    return {}


@st.cache_data(ttl=3600)  # Cache non-final session problems for 1 hour
def get_cached_non_final_level_problems(level=None):
    """Load all session* problems for the selected level, excluding final collections."""
    problems = {}
    requested_level = None
    if level is not None:
        try:
            requested_level = int(level)
        except (TypeError, ValueError):
            requested_level = None

    if data_manager.is_firebase():
        backend = getattr(data_manager, 'backend', None)
        if backend is not None and hasattr(backend, 'problems_ref'):
            # Primary path: level/session documents (e.g., level1_session13).
            session_docs = {}
            for doc in backend.problems_ref.stream():
                doc_name = str(getattr(doc, "id", "")).strip()
                if not _is_session_collection_name(doc_name):
                    continue

                doc_level = _extract_level_from_collection_name(doc_name)
                if requested_level is not None and doc_level is not None and doc_level != requested_level:
                    continue

                session_key = _strip_level_prefix(doc_name).strip().lower()
                candidates = session_docs.setdefault(session_key, [])
                candidates.append((doc_level, doc))

            for session_key in sorted(session_docs.keys(), key=_get_session_sort_key):
                candidates = session_docs.get(session_key, [])
                if not candidates:
                    continue

                chosen_doc = None
                if requested_level is not None:
                    for candidate_level, candidate_doc in candidates:
                        if candidate_level == requested_level:
                            chosen_doc = candidate_doc
                            break

                if chosen_doc is None:
                    for candidate_level, candidate_doc in candidates:
                        if candidate_level is None:
                            chosen_doc = candidate_doc
                            break

                if chosen_doc is None:
                    chosen_doc = candidates[0][1]

                doc_data = chosen_doc.to_dict() or {}
                problems_list = _extract_problem_entries(doc_data)

                for problem in problems_list:
                    _add_problem_to_map(problems, problem, level=requested_level)

            if problems:
                return problems

            # Secondary path: all-problems style docs that keep session keys.
            for doc_name in ['Level1_AllProblems', 'Level1_AllProblems_Fixed', 'all_problems', 'problems']:
                doc = backend.problems_ref.document(doc_name).get()
                if not doc.exists:
                    continue

                doc_data = doc.to_dict() or {}
                sessions_data = doc_data.get("sessions")
                if isinstance(sessions_data, dict):
                    source_sessions = sessions_data
                else:
                    source_sessions = doc_data

                if not isinstance(source_sessions, dict):
                    continue

                for session_key in sorted(source_sessions.keys(), key=_get_session_sort_key):
                    if not _is_session_collection_name(session_key):
                        continue

                    session_value = source_sessions.get(session_key)
                    problems_list = _extract_problem_entries(session_value)

                    for problem in problems_list:
                        _add_problem_to_map(problems, problem, level=requested_level)

                if problems:
                    return problems

    # Generic fallback (non-Firebase backends).
    fallback_problems = get_cached_problems(week=None, level=requested_level)
    for _, problem in fallback_problems.items():
        _add_problem_to_map(problems, problem, level=requested_level)
    return problems


# Function to load problems
def load_problems(week=None, level=None, competition_title=None):
    """Load all non-final competition problems for the selected level."""
    try:
        # We intentionally load session* collections only to exclude final competition sets.
        problems = get_cached_non_final_level_problems(level=level)

        # If cache is stale/empty, retry once after clearing problem caches.
        if not problems:
            try:
                get_cached_non_final_level_problems.clear()
                get_cached_problems.clear()
            except Exception:
                pass
            problems = get_cached_non_final_level_problems(level=level)

        # Optional fallback to preserve old call behavior when a specific week is provided.
        if not problems and week is not None:
            problems = get_cached_problems(week=week, level=level)
        
        # Normalize payload and add default starter code.
        normalized_problems = {}
        auto_problem_id = 1
        for problem_id, problem in problems.items():
            fallback_problem_id = problem_id
            if not isinstance(fallback_problem_id, int):
                if str(fallback_problem_id).isdigit():
                    fallback_problem_id = int(fallback_problem_id)
                else:
                    fallback_problem_id = auto_problem_id

            normalized = normalize_problem_schema(
                problem,
                fallback_level=level,
                fallback_problem_id=fallback_problem_id
            )
            if not normalized:
                continue

            normalized_id = normalized.get("id", auto_problem_id)
            if 'starter_code' not in normalized:
                normalized['starter_code'] = '''# Read input using input()
# Compute your answer
# Print output using print()
'''
            normalized_problems[normalized_id] = normalized
            auto_problem_id += 1

        return normalized_problems
    except Exception as e:
        st.error(f"Error loading problems from Firebase: {e}")
        return {}

_UNPARSED = object()


def _build_exec_globals():
    """Create a safe-ish execution context with common libraries."""
    exec_globals = {
        '__builtins__': __builtins__,
    }

    try:
        from textblob import TextBlob
        exec_globals['TextBlob'] = TextBlob
    except ImportError:
        pass

    try:
        import numpy as np
        exec_globals['np'] = np
        exec_globals['numpy'] = np
    except ImportError:
        pass

    try:
        import requests
        exec_globals['requests'] = requests
    except ImportError:
        pass

    try:
        import math
        exec_globals['math'] = math
    except ImportError:
        pass

    try:
        import re
        exec_globals['re'] = re
    except ImportError:
        pass

    try:
        from collections import Counter, defaultdict, deque
        exec_globals['Counter'] = Counter
        exec_globals['defaultdict'] = defaultdict
        exec_globals['deque'] = deque
    except ImportError:
        pass

    return exec_globals


def _build_mock_input(raw_input):
    """Return deterministic input() implementation for a test case."""
    if isinstance(raw_input, (list, tuple)):
        input_lines = [str(item) for item in raw_input]
    else:
        input_text = '' if raw_input is None else str(raw_input)
        input_lines = input_text.splitlines() if input_text else []

    input_index = [0]

    def mock_input(prompt=''):
        if input_index[0] < len(input_lines):
            value = input_lines[input_index[0]]
            input_index[0] += 1
            return value
        return ''

    return mock_input


def _extract_function_spec(input_format):
    """Parse function name from formats like: 'Function: solve(a, b)'."""
    if not input_format:
        return None, None

    text = str(input_format).strip()
    if ':' not in text:
        return None, None

    label, remainder = text.split(':', 1)
    if label.strip().lower() != 'function':
        return None, None

    signature = remainder.strip()
    if not signature:
        return None, None

    if '(' in signature:
        function_name = signature.split('(', 1)[0].strip()
        args_part = signature.split('(', 1)[1].rsplit(')', 1)[0].strip()
        arg_names = [arg.strip() for arg in args_part.split(',') if arg.strip()]
        expected_param_count = len(arg_names)
    else:
        function_name = signature.split()[0].strip()
        expected_param_count = None

    if not function_name.isidentifier():
        return None, None
    return function_name, expected_param_count


def _try_parse_value(value):
    """Try converting text into Python scalar/list/dict; return _UNPARSED if not possible."""
    if isinstance(value, (int, float, bool, list, tuple, dict)):
        return value

    if value is None:
        return ''

    text = str(value).strip()
    if text == '':
        return ''

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
        return [], dict(raw_input)
    if isinstance(raw_input, (list, tuple)):
        return list(raw_input), {}

    raw_text = '' if raw_input is None else str(raw_input)
    stripped = raw_text.strip()
    if stripped == '':
        return [], {}

    parsed_all = _try_parse_value(stripped)
    if parsed_all is not _UNPARSED:
        if isinstance(parsed_all, dict):
            return [], parsed_all
        if isinstance(parsed_all, tuple):
            return list(parsed_all), {}
        if isinstance(parsed_all, list):
            # If exactly one parameter is expected, treat a list literal as one argument.
            if expected_param_count == 1:
                return [parsed_all], {}
            return list(parsed_all), {}
        return [parsed_all], {}

    lines = raw_text.splitlines()
    if len(lines) > 1:
        return [_parse_token(line) for line in lines], {}

    line = lines[0] if lines else stripped

    if ',' in line:
        parts = [part.strip() for part in line.split(',')]
        if len(parts) > 1:
            return [_parse_token(part) for part in parts], {}

    if expected_param_count and expected_param_count > 1 and ' ' in line:
        parts = [part for part in line.split() if part]
        if len(parts) == expected_param_count:
            return [_parse_token(part) for part in parts], {}

    return [_parse_token(line)], {}


def _normalize_return_value(value):
    """Format function return value for display/comparison."""
    if value is None:
        return ''
    if isinstance(value, tuple):
        return '\n'.join(str(item) for item in value).strip()
    if isinstance(value, list):
        return '\n'.join(str(item) for item in value).strip()
    return str(value).strip()


def _run_single_test_as_script(code, test):
    stdout_capture = io.StringIO()
    exec_globals = _build_exec_globals()
    exec_globals['input'] = _build_mock_input(test.get('input', ''))

    with contextlib.redirect_stdout(stdout_capture):
        exec(code, exec_globals)

    output = stdout_capture.getvalue().strip()
    expected = str(test.get('output', '')).strip()
    passed = output == expected
    return output, expected, passed


def _run_single_test_as_function(code, test, function_name, expected_param_count=None):
    stdout_capture = io.StringIO()
    exec_globals = _build_exec_globals()

    # Keep input() available in case the user mixes function + script style.
    exec_globals['input'] = _build_mock_input(test.get('input', ''))

    with contextlib.redirect_stdout(stdout_capture):
        exec(code, exec_globals)

    target_function = exec_globals.get(function_name)
    if not callable(target_function):
        raise NameError(f"Function '{function_name}' not found.")

    args, kwargs = _parse_function_args(test.get('input', ''), expected_param_count)

    call_stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(call_stdout_capture):
        result = target_function(*args, **kwargs)

    printed_output = call_stdout_capture.getvalue().strip()
    expected = str(test.get('output', '')).strip()

    if result is None:
        output = printed_output
    else:
        output = _normalize_return_value(result)
        if not output and printed_output:
            output = printed_output

    passed = output == expected

    if not passed and result is not None:
        parsed_expected = _try_parse_value(expected)
        if parsed_expected is not _UNPARSED and result == parsed_expected:
            passed = True

    return output, expected, passed


# Function to run code with test cases
def run_code_with_tests(code, test_cases, input_format=None):
    """Execute competitor code against test cases, supporting script and function styles."""
    results = []
    function_name, expected_param_count = _extract_function_spec(input_format)

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
                        expected_param_count=expected_param_count
                    )
                except Exception as function_error:
                    function_exception = function_error

                script_attempt = None
                script_exception = None
                try:
                    script_attempt = _run_single_test_as_script(code, test)
                except Exception as script_error:
                    script_exception = script_error

                # Accept whichever mode passes first. This supports mixed authoring styles.
                if function_attempt and function_attempt[2]:
                    output, expected, passed = function_attempt
                elif script_attempt and script_attempt[2]:
                    output, expected, passed = script_attempt
                elif function_attempt:
                    output, expected, passed = function_attempt
                elif script_attempt:
                    output, expected, passed = script_attempt
                elif function_exception is not None:
                    raise function_exception
                elif script_exception is not None:
                    raise script_exception
                else:
                    raise RuntimeError("Unable to evaluate test case.")
            else:
                output, expected, passed = _run_single_test_as_script(code, test)

            results.append({
                'test_num': i + 1,
                'passed': passed,
                'input': str(test.get('input', '')),
                'expected': str(expected),
                'output': output,
                'error': None
            })

        except Exception as e:
            results.append({
                'test_num': i + 1,
                'passed': False,
                'input': str(test.get('input', '')),
                'expected': str(test.get('output', '')),
                'output': f"Error: {str(e)}",
                'error': str(e)
            })

    return results


def get_judge_status_badge(judge_approval, has_submission):
    """Return HTML badge representing current judge review status."""
    if not has_submission:
        return None

    if judge_approval == 'approved':
        return '<span class="stat-badge badge-success">👨‍⚖️ Approved</span>'
    if judge_approval == 'rejected':
        return '<span class="stat-badge badge-danger">👨‍⚖️ Rejected</span>'
    return '<span class="stat-badge badge-warning">👨‍⚖️ Pending Review</span>'


def get_streamlit_autorefresh_fn():
    """Dynamically load streamlit-autorefresh if installed."""
    try:
        module = importlib.import_module("streamlit_autorefresh")
        return getattr(module, "st_autorefresh", None)
    except Exception:
        return None


def get_cached_competitor_data(competitor_name):
    """Get competitor data with session-level cache to reduce duplicate reads."""
    cache_key = 'competitor_data_cache'
    now = time.time()
    ttl_seconds = NOTIFICATION_REFRESH_SECONDS

    cache = st.session_state.get(cache_key)
    if isinstance(cache, dict):
        if cache.get('name') == competitor_name and (now - float(cache.get('fetched_at', 0))) < ttl_seconds:
            return cache.get('data') or {}

    fresh_data = data_manager.get_competitor_data(competitor_name) or {}
    st.session_state[cache_key] = {
        'name': competitor_name,
        'fetched_at': now,
        'data': fresh_data,
    }
    return fresh_data


def invalidate_cached_competitor_data():
    """Force a fresh competitor-data read on next access."""
    st.session_state.pop('competitor_data_cache', None)


def get_rejection_notifications(comp_data):
    """Extract judge rejection notices (problem number + name only)."""
    notifications = comp_data.get('notifications', []) if isinstance(comp_data, dict) else []
    rejected = []
    for notice in notifications:
        if not isinstance(notice, dict):
            continue
        if notice.get('status') != 'rejected':
            continue
        problem_id = notice.get('problem_id')
        problem_name = notice.get('problem_name')
        if problem_id is None:
            continue
        if not problem_name:
            problem_name = f"Problem {problem_id}"
        rejected.append({
            'problem_id': problem_id,
            'problem_name': problem_name
        })
    return rejected


def get_notification_identity(notice):
    """Create a stable id for deduplicating live notification toasts."""
    return f"{notice.get('status', 'rejected')}::{notice.get('problem_id')}::{notice.get('created_at', '')}"

# Header
st.markdown("# 👨‍💻 Competitor Interface")

# Registration/Login Section
if st.session_state.competitor_name is None:
    with st.sidebar:
        st.markdown("### Competitor")
        st.caption("Register/login from the main panel to activate your dashboard.")
        st.caption(f"Backend: `{BACKEND_TYPE}`")
        if BACKEND_TYPE == "json":
            st.warning("Firebase is not active. This view is using local JSON storage.")
            reason = str(BACKEND_DEBUG.get("firebase_init_error") or "").strip()
            if reason:
                st.caption(f"Firebase error: {reason}")
            source = str(BACKEND_DEBUG.get("firebase_credentials_source") or "").strip()
            if source:
                st.caption(f"Credentials source: {source}")

    st.markdown("## Registration")
    st.markdown("Enter your name and choose your competition level to start.")
    st.caption(
        "Problems are loaded from all session collections for your level "
        "(for example: session1, session13, ...), excluding final competition collections."
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        name_input = st.text_input("Your Name", placeholder="Enter your full name")
        level_label = st.selectbox(
            "Competition Level",
            options=list(LEVEL_LABEL_TO_VALUE.keys()),
            index=0,
            help="Junior Level = level 1, Senior Level = level 2"
        )
        selected_level = LEVEL_LABEL_TO_VALUE[level_label]

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Start Competition", type="primary", use_container_width=True):
            if name_input and name_input.strip():
                competitor_name = name_input.strip()
                data_manager.register_competitor(
                    competitor_name,
                    week=FINAL_COMPETITION_WEEK,
                    level=selected_level
                )
                st.session_state.competitor_name = competitor_name
                st.session_state.user_week = FINAL_COMPETITION_WEEK
                st.session_state.user_level = selected_level
                st.success(f"Welcome, {competitor_name}!")
                st.rerun()
            else:
                st.error("Please enter your name")

else:
    # Competitor is logged in
    competitor_name = st.session_state.competitor_name

    st_autorefresh_fn = get_streamlit_autorefresh_fn()
    if st_autorefresh_fn is not None:
        st_autorefresh_fn(
            interval=NOTIFICATION_REFRESH_SECONDS * 1000,
            key="competitor_live_notification_refresh",
        )
    else:
        st.caption(
            "Live auto-refresh helper is unavailable in this runtime. "
            "Use 'Check notifications now' for instant updates."
        )
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {competitor_name}")
        st.caption(f"Backend: `{BACKEND_TYPE}`")
        if BACKEND_TYPE == "json":
            st.warning("Firebase is not active. Firestore problems will not appear.")
            reason = str(BACKEND_DEBUG.get("firebase_init_error") or "").strip()
            if reason:
                st.caption(f"Firebase error: {reason}")
            source = str(BACKEND_DEBUG.get("firebase_credentials_source") or "").strip()
            if source:
                st.caption(f"Credentials source: {source}")

        st.markdown("### 🔔 Live Alerts")
        st.caption("Live rejection checks run automatically every 10 seconds.")
        if st.button("Check notifications now", use_container_width=True):
            invalidate_cached_competitor_data()
            st.rerun()
        st.markdown("---")
        
        # Get competitor stats
        comp_data = get_cached_competitor_data(competitor_name)
        selected_level = st.session_state.get('user_level')
        if selected_level is None and isinstance(comp_data, dict):
            selected_level = comp_data.get('level')
        try:
            selected_level = int(selected_level)
        except (TypeError, ValueError):
            selected_level = LEVEL_LABEL_TO_VALUE["Junior Level"]
        if selected_level not in LEVEL_LABEL_TO_VALUE.values():
            selected_level = LEVEL_LABEL_TO_VALUE["Junior Level"]

        st.session_state.user_level = selected_level
        st.session_state.user_week = FINAL_COMPETITION_WEEK

        st.caption(f"Level: {get_level_label(selected_level)} (L{selected_level})")
        st.caption(
            "Question source: all level sessions (excluding final competition collections)"
        )
        problems_data = comp_data.get('problems', {})
        
        solved_count = sum(
            1 for p in problems_data.values() 
            if p.get('best_result', {}).get('all_passed', False)
        )
        total_submissions = sum(
            len(p.get('submissions', [])) for p in problems_data.values()
        )
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">{solved_count}</div>
            <div>Problems Solved</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Total Submissions:** {total_submissions}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.competitor_name = None
            st.session_state.current_problem = None
            st.session_state.code = ""
            st.session_state.user_week = FINAL_COMPETITION_WEEK
            st.session_state.user_level = LEVEL_LABEL_TO_VALUE["Junior Level"]
            invalidate_cached_competitor_data()
            st.rerun()

    rejection_notifications = get_rejection_notifications(comp_data)
    if rejection_notifications:
        if 'seen_rejection_notification_ids' not in st.session_state:
            st.session_state.seen_rejection_notification_ids = set()

        new_notices = []
        for notice in rejection_notifications:
            notice_id = get_notification_identity(notice)
            if notice_id not in st.session_state.seen_rejection_notification_ids:
                new_notices.append(notice)

        if new_notices:
            for notice in new_notices[-3:]:
                problem_id_text = html.escape(str(notice['problem_id']))
                problem_name_text = html.escape(str(notice['problem_name']))
                st.toast(f"Problem rejected: Problem {problem_id_text}: {problem_name_text}")

        for notice in rejection_notifications:
            st.session_state.seen_rejection_notification_ids.add(get_notification_identity(notice))

        st.markdown("### 🔔 Judge Notifications")
        for notice in reversed(rejection_notifications[-5:]):
            problem_id_text = html.escape(str(notice['problem_id']))
            problem_name_text = html.escape(str(notice['problem_name']))
            st.error(
                f"Problem rejected: Your submission for Problem {problem_id_text}: {problem_name_text} was rejected by the judge."
            )

    # Main content
    # Load all non-final session problems for the user's level.
    user_level = st.session_state.get('user_level', LEVEL_LABEL_TO_VALUE["Junior Level"])
    problems = load_problems(
        level=user_level
    )

    if not problems:
        st.warning(
            f"No non-final session problems found for "
            f"{get_level_label(user_level)} (L{user_level})."
        )
        st.info(
            "If your uploaded file is level 2, choose Senior Level and make sure "
            "you uploaded level 2 session collections in Admin."
        )
        st.session_state.current_problem = None
        st.stop()
    
    if st.session_state.current_problem is None:
        # Problem selection view
        st.markdown("## 📚 Available Problems")
        st.markdown("Select a problem to start solving!")
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_option = st.radio(
                "Filter:",
                ["All Problems", "Not Attempted", "In Progress", "Solved"],
                horizontal=True
            )
        
    # Display problems
        for problem_id, problem in sorted(problems.items()):
            # Convert problem_id to string for Firebase lookup
            problem_id_str = str(problem_id)
            problem_data = problems_data.get(problem_id_str, {})
            best_result = problem_data.get('best_result', {})
            submissions = problem_data.get('submissions', [])
            judge_approval = problem_data.get('judge_approval')
            
            # Apply filter
            if filter_option == "Not Attempted" and submissions:
                continue
            if filter_option == "In Progress" and (not submissions or best_result.get('all_passed')):
                continue
            if filter_option == "Solved" and not best_result.get('all_passed'):
                continue
            
            # Determine card style
            card_class = "problem-card"
            if best_result.get('all_passed'):
                card_class += " problem-solved"
                status_badge = '<span class="stat-badge badge-success">✓ Solved</span>'
            elif submissions:
                card_class += " problem-failed"
                status_badge = '<span class="stat-badge badge-warning">⚠ In Progress</span>'
            else:
                status_badge = '<span class="stat-badge badge-info">○ Not Attempted</span>'
            
            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### Problem {problem_id}: {problem['title']}")
                    st.markdown(status_badge, unsafe_allow_html=True)
                    if submissions:
                        st.markdown(
                            f'<span class="stat-badge badge-info">Attempts: {len(submissions)}</span>',
                            unsafe_allow_html=True
                        )
                    judge_badge = get_judge_status_badge(judge_approval, bool(submissions))
                    if judge_badge:
                        st.markdown(judge_badge, unsafe_allow_html=True)
                    st.markdown(f"**Difficulty:** {problem.get('difficulty', 'Medium')}")
                    st.markdown(f"**Description:** {problem.get('description', 'No description')}")
                
                with col2:
                    if st.button("Solve", key=f"solve_{problem_id}", type="primary", use_container_width=True):
                        st.session_state.current_problem = problem_id
                        # Load last submitted code if exists
                        if submissions:
                            st.session_state.code = submissions[-1].get('code', '')
                        else:
                            st.session_state.code = problem.get('starter_code', '')
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Problem solving view
        problem_id = st.session_state.current_problem
        problem = problems.get(problem_id, {})
        
        # Get all problem IDs sorted
        all_problem_ids = sorted(problems.keys())
        current_index = all_problem_ids.index(problem_id) if problem_id in all_problem_ids else 0
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
        
        with nav_col1:
            if st.button("← Back to Problems", use_container_width=True):
                st.session_state.current_problem = None
                st.session_state.test_results = None
                st.rerun()
        
        with nav_col2:
            # Previous button
            if current_index > 0:
                prev_problem_id = all_problem_ids[current_index - 1]
                if st.button(f"← Previous (Problem {prev_problem_id})", use_container_width=True):
                    st.session_state.current_problem = prev_problem_id
                    # Load code for previous problem
                    prev_problem_data = problems_data.get(prev_problem_id, {})
                    prev_submissions = prev_problem_data.get('submissions', [])
                    if prev_submissions:
                        st.session_state.code = prev_submissions[-1].get('code', '')
                    else:
                        st.session_state.code = problems[prev_problem_id].get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        with nav_col4:
            # Next button
            if current_index < len(all_problem_ids) - 1:
                next_problem_id = all_problem_ids[current_index + 1]
                if st.button(f"Next (Problem {next_problem_id}) →", use_container_width=True):
                    st.session_state.current_problem = next_problem_id
                    # Load code for next problem
                    next_problem_data = problems_data.get(next_problem_id, {})
                    next_submissions = next_problem_data.get('submissions', [])
                    if next_submissions:
                        st.session_state.code = next_submissions[-1].get('code', '')
                    else:
                        st.session_state.code = problems[next_problem_id].get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        st.markdown(f"## Problem {problem_id}: {problem.get('title', 'Unknown')}")
        
        # Problem description
        with st.expander("📖 Problem Description", expanded=True):
            st.markdown(f"**Difficulty:** {problem.get('difficulty', 'Medium')}")
            st.markdown(problem.get('description', 'No description available'))
            
            # Show examples
            if 'examples' in problem:
                st.markdown("**Examples:**")
                for i, example in enumerate(problem['examples'], 1):
                    st.code(f"Input: {example.get('input', '')}\nOutput: {example.get('output', '')}")

            # Show test cases when provided in uploaded problems.
            test_cases_for_display = problem.get('test_cases', [])
            if test_cases_for_display:
                st.markdown("**Test Cases:**")
                for i, test in enumerate(test_cases_for_display, 1):
                    case_input = test.get('input', '') if isinstance(test, dict) else ''
                    case_output = test.get('output', '') if isinstance(test, dict) else ''
                    st.code(
                        f"Case {i}\nInput:\n{case_input}\n\nExpected Output:\n{case_output}"
                    )
        
        # Code editor and testing
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("### 💻 Your Solution")
            
            # Code editor
            code = st.text_area(
                "Write your code here:",
                value=st.session_state.code,
                height=400,
                key="code_editor",
                help="Supports both script solutions (input/print) and function-based solutions"
            )
            st.session_state.code = code
            
            # Action buttons
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("▶️ Run Tests", type="primary", use_container_width=True):
                    if code.strip():
                        test_cases = problem.get('test_cases', [])
                        with st.spinner("Running tests..."):
                            results = run_code_with_tests(
                                code,
                                test_cases,
                                input_format=problem.get('input_format')
                            )
                            st.session_state.test_results = results
                            st.rerun()
                    else:
                        st.error("Please write some code first!")
            
            with btn_col2:
                if st.button("📤 Submit Solution", type="secondary", use_container_width=True):
                    if code.strip():
                        test_cases = problem.get('test_cases', [])
                        with st.spinner("Running tests..."):
                            results = run_code_with_tests(
                                code,
                                test_cases,
                                input_format=problem.get('input_format')
                            )
                            
                            # Check if all passed
                            all_passed = all(r['passed'] for r in results)
                            
                            # Submit to data manager
                            data_manager.submit_solution(
                                competitor_name,
                                problem_id,
                                code,
                                results,
                                all_passed,
                                problem_name=problem.get('title', f'Problem {problem_id}')
                            )
                            invalidate_cached_competitor_data()
                            
                            st.session_state.test_results = results
                            
                            if all_passed:
                                st.success("🎉 All tests passed! Solution submitted successfully!")
                            else:
                                st.warning("⚠️ Some tests failed. Keep trying!")
                            
                            st.rerun()
                    else:
                        st.error("Please write some code first!")
            
            with btn_col3:
                if st.button("🔄 Reset Code", use_container_width=True):
                    st.session_state.code = problem.get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        with col2:
            st.markdown("### 🧪 Test Results")
            
            if st.session_state.test_results:
                results = st.session_state.test_results
                
                # Summary
                passed_count = sum(1 for r in results if r['passed'])
                total_count = len(results)
                
                if passed_count == total_count:
                    st.success(f"✅ All {total_count} tests passed!")
                else:
                    st.warning(f"⚠️ {passed_count}/{total_count} tests passed")
                
                # Individual test results
                for result in results:
                    test_class = "test-passed" if result['passed'] else "test-failed"
                    icon = "✅" if result['passed'] else "❌"
                    
                    with st.expander(f"{icon} Test {result['test_num']} - {'Passed' if result['passed'] else 'Failed'}", expanded=not result['passed']):
                        st.markdown(f"**Input:** `{result['input']}`")
                        st.markdown(f"**Expected:** `{result['expected']}`")
                        st.markdown(f"**Your Output:** `{result['output']}`")
                        
                        if result['error']:
                            st.error(f"Error: {result['error']}")
            else:
                st.info("Click 'Run Tests' to see results here")
            
            # Submission history
            st.markdown("### 📜 Your Submissions")
            # Convert problem_id to string for Firebase lookup
            problem_id_str = str(problem_id)
            problem_data = problems_data.get(problem_id_str, {})
            submissions = problem_data.get('submissions', [])
            judge_approval = problem_data.get('judge_approval')

            if submissions:
                judge_badge = get_judge_status_badge(judge_approval, True)
                if judge_badge:
                    st.markdown(judge_badge, unsafe_allow_html=True)
            
            # Debug info
            # if not submissions:
            #     with st.expander("🔍 Debug - Why no submissions?", expanded=False):
            #         st.write(f"Looking for problem_id: `{problem_id}` (type: {type(problem_id).__name__})")
            #         st.write(f"Looking for problem_id_str: `{problem_id_str}`")
            #         st.write(f"Available problems in database: `{list(fresh_problems_data.keys())}`")
            #         st.write(f"Problem data found: `{bool(problem_data)}`")
            #         if problem_data:
            #             st.write(f"Submissions in problem data: `{problem_data.get('submissions', 'NO SUBMISSIONS KEY')}`")
            
            if submissions:
                for i, sub in enumerate(reversed(submissions[-5:]), 1):  # Show last 5
                    passed = sub.get('all_passed', False)
                    icon = "✅" if passed else "❌"
                    # Try both field names for backwards compatibility
                    passed_tests = sub.get('passed_tests', sub.get('tests_passed', 0))
                    total_tests = sub.get('total_tests', 0)
                    timestamp = sub.get('submitted_at', sub.get('timestamp', 'Unknown time'))
                    tests = f"{passed_tests}/{total_tests}"
                    
                    st.markdown(f"{icon} **Attempt {len(submissions) - i + 1}** - {tests} tests - {timestamp}")
            else:
                st.info("No submissions yet")

# Footer
st.markdown("---")
st.caption("💡 Tip: Test your code before submitting to ensure all test cases pass!")
