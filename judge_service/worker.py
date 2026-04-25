"""Disposable worker process used by the judge API.

The API process starts this script for each submission and kills it on timeout.
Keeping user code in this child process protects the API server from hangs.
"""
import json
import os
import sys

from runner import run_code_with_tests


def _apply_linux_limits():
    """Apply best-effort CPU and memory limits on Linux hosts."""
    try:
        import resource
    except ImportError:
        return

    try:
        memory_mb = int(os.environ.get("MAX_WORKER_MEMORY_MB", "512"))
        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    except Exception:
        pass

    try:
        cpu_seconds = int(os.environ.get("MAX_WORKER_CPU_SECONDS", "8"))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    except Exception:
        pass


def main():
    _apply_linux_limits()

    payload = json.loads(sys.stdin.read() or "{}")
    results = run_code_with_tests(
        code=str(payload.get("code", "")),
        test_cases=payload.get("test_cases", []) or [],
        input_format=payload.get("input_format"),
    )
    sys.stdout.write(json.dumps({"results": results}, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
