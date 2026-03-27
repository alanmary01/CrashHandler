import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
try:
    int("not_a_number")
except ValueError as original:
    raise RuntimeError("failed to parse config file") from original
