"""
Entry point for the CrashHandler project.

This script serves as the main entry point to run the demonstration suite,
which showcases the various features and capabilities of CrashHandler.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from crashhandler import demo_suite


def main() -> None:
    demo_suite.main()


if __name__ == "__main__":
    main()
