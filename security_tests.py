"""Run the automatic security suite required by the assignment, without LLM calls."""
from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    raise SystemExit(subprocess.call([
        sys.executable, "-m", "pytest", "entrega_4/tests/test_guardrails.py",
        "entrega_4/tests/test_api.py", "-q",
    ], cwd=root))
