"""Standalone smoke tests for the StokerCloud API client.

Run with:
    python standalone_api_test.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parent
    test_file = repo_root / "tests" / "test_stokercloud_api.py"

    print("[1/1] Running standalone API unit tests...")
    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=str(repo_root),
        check=False,
    )
    if result.returncode != 0:
        print("[FAIL] Standalone API tests failed")
        return result.returncode

    print("[OK] Standalone API tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
