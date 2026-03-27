import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
import sys
def good_hook(): print("[hook] good_hook ran fine", file=sys.stderr)
def bad_hook():  raise Exception("hook itself exploded")

crash_handler.register_cleanup_hook(bad_hook)
crash_handler.register_cleanup_hook(good_hook)

raise RuntimeError("game crash with a broken cleanup hook registered")
