import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
def autosave():      print("[hook] autosave: world state saved", file=sys.stderr)
def flush_network(): print("[hook] flush_network: socket closed", file=sys.stderr)
def close_db():      print("[hook] close_db: database flushed",  file=sys.stderr)

import sys
crash_handler.register_cleanup_hook(autosave)
crash_handler.register_cleanup_hook(flush_network)
crash_handler.register_cleanup_hook(close_db)

raise RuntimeError("simulated mid-game crash")
