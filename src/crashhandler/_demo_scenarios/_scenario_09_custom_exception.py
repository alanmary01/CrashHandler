import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
class GameStateCorrupted(Exception):
    def __init__(self, save_slot: int):
        super().__init__(f"save slot {save_slot} has invalid checksum")
        self.save_slot = save_slot

raise GameStateCorrupted(save_slot=3)
