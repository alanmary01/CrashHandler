import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
def level_8(): raise RuntimeError("deep crash")
def level_7(): level_8()
def level_6(): level_7()
def level_5(): level_6()
def level_4(): level_5()
def level_3(): level_4()
def level_2(): level_3()
def level_1(): level_2()
level_1()
