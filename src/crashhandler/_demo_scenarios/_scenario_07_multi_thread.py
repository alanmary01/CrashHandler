import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
import threading, time

def worker_a():
    time.sleep(0.02)
    raise RuntimeError("Thread-A: physics engine NaN detected")

def worker_b():
    time.sleep(0.04)
    raise RuntimeError("Thread-B: audio buffer underrun")

threads = [
    threading.Thread(target=worker_a, name="PhysicsThread"),
    threading.Thread(target=worker_b, name="AudioThread"),
]
for t in threads: t.start()
for t in threads: t.join()
