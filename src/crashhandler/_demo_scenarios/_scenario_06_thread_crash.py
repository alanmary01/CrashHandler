import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
import threading, time

def worker():
    time.sleep(0.05)
    raise ValueError("worker thread: texture atlas failed to load")

t = threading.Thread(target=worker, name="AssetLoader")
t.start()
t.join()
