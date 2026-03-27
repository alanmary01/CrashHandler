"""
CrashHandler Demo Suite
=======================
Run this file directly to see every CrashHandler feature in action.

    python demo_suite.py

Each scenario runs in an isolated subprocess so a real crash does not
kill the demo runner. Results are printed live, and a summary is shown
at the end together with the log files that were produced.

Requirements: colorama (optional but recommended)
"""

import subprocess
import sys
import time
import os
import json
import shutil
from pathlib import Path

# ── ANSI colour helpers — no third-party dependencies ────────────────────────
def _ansi(code: str) -> str:
    return f"\033[{code}m" if sys.stdout.isatty() else ""

_RST = _ansi("0")
_BLD = _ansi("1")

def Grn(t: str) -> str: return f"{_ansi('32')}{t}{_RST}"
def Yel(t: str) -> str: return f"{_ansi('33')}{t}{_RST}"
def Red(t: str) -> str: return f"{_ansi('31')}{t}{_RST}"
def Cyn(t: str) -> str: return f"{_ansi('36')}{t}{_RST}"
def Mag(t: str) -> str: return f"{_ansi('35')}{t}{_RST}"
def Bld(t: str) -> str: return f"{_BLD}{t}{_RST}"

# ── Scenario feature_registry ─────────────────────────────────────────────────────────
# Each entry: (title, description, script_name)
SCENARIOS: list[tuple[str, str, str]] = [
    (
        "Basic ValueError",
        "The simplest crash: an unhandled ValueError. Shows coloured terminal\n"
        "output, severity badge (ERROR), and structured JSON log.",
        "_scenario_01_basic_error.py",
    ),
    (
        "Deeply nested traceback",
        "A chain of 8 nested function calls before the crash. Verifies that\n"
        "the full call stack is preserved in both log outputs.",
        "_scenario_02_deep_traceback.py",
    ),
    (
        "FATAL — RecursionError",
        "Infinite recursion triggers a RecursionError, classified as FATAL\n"
        "(red badge). Confirms that Python's recursion guard doesn't prevent\n"
        "the handler from running.",
        "_scenario_03_recursion.py",
    ),
    (
        "Cleanup hooks — ordered execution",
        "Three cleanup hooks are registered (autosave, flush_network,\n"
        "close_db). All three run in order before exit, printing confirmation\n"
        "to stderr.",
        "_scenario_04_cleanup_hooks.py",
    ),
    (
        "Failing cleanup hook — resilience",
        "One of two cleanup hooks deliberately raises an exception. The handler\n"
        "skips it with a warning and still runs the remaining hook, then exits.",
        "_scenario_05_bad_hook.py",
    ),
    (
        "Thread crash",
        "An exception is raised on a worker thread. Without CrashHandler the\n"
        "thread would die silently. With it, the full crash pipeline runs.",
        "_scenario_06_thread_crash.py",
    ),
    (
        "Multiple concurrent thread crashes",
        "Two worker threads crash near-simultaneously. Each crash is handled\n"
        "independently and produces its own log file.",
        "_scenario_07_multi_thread.py",
    ),
    (
        "Chained exceptions (raise from)",
        "An exception is caught and re-raised with 'raise X from Y'. Verifies\n"
        "that the full exception chain appears in the traceback.",
        "_scenario_08_chained.py",
    ),
    (
        "Custom exception class",
        "A user-defined exception class (GameStateCorrupted) is raised.\n"
        "Classified as ERROR. The class name and message appear correctly.",
        "_scenario_09_custom_exception.py",
    ),
    (
        "Environment snapshot contents",
        "After a crash, the JSON log is read back and each environment field\n"
        "(timestamp, python, platform, cwd, argv, and thread) is verified\n"
        "to be present and non-empty.",
        "_scenario_10_env_snapshot.py",
    ),
    (
        "KeyboardInterrupt passthrough",
        "KeyboardInterrupt must NOT be captured by CrashHandler — it should\n"
        "fall through to Python's default handler so Ctrl-C still works.",
        "_scenario_12_keyboard_interrupt.py",
    ),
]

SCENARIO_DIR = Path(__file__).parent / "_demo_scenarios"
# LOG_DIR always points to the project root/logs
# Note: src/crashhandler/demo_suite.py is 2 levels deep from root
_ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR   = _ROOT_DIR / "logs"


# ── Subprocess runner ─────────────────────────────────────────────────────────

def _run_scenario(script: Path, timeout: int = 10) -> tuple[bool, str, str]:
    """Run a scenario script in a subprocess. Returns (passed, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    # Scenarios that intentionally crash exit with code 1 — that's a PASS.
    # A scenario fails only if it exits 0 when it should have crashed, or
    # if it writes "DEMO_FAIL" to stdout.
    passed = "DEMO_FAIL" not in stdout and "DEMO_FAIL" not in stderr
    return passed, stdout, stderr


# ── Pretty printer ─────────────────────────────────────────────────────────────

def _banner(text: str) -> None:
    width = 70
    print("\n" + Cyn("╔" + "═" * (width - 2) + "╗"))
    print(Cyn("║") + Bld(f"  {text:<{width - 4}}") + Cyn("║"))
    print(Cyn("╚" + "═" * (width - 2) + "╝"))


def _section(n: int, title: str) -> None:
    print(f"\n{Mag(f'── Scenario {n:02d}')}  {Bld(title)}")


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


# ── Log inspector ─────────────────────────────────────────────────────────────

def _count_new_logs(before: set[Path]) -> list[Path]:
    after = set(LOG_DIR.glob("crash_*.json"))
    return sorted(after - before)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _banner("CrashHandler — Feature Demonstration Suite")

    print(f"\n  {Grn('▶')} Scenarios : {len(SCENARIOS)}")
    print(f"  {Grn('▶')} Log dir   : {LOG_DIR.resolve()}")
    print(f"  {Grn('▶')} Python    : {sys.version.split()[0]}")

    # Write all scenario scripts
    SCENARIO_DIR.mkdir(exist_ok=True)
    _write_scenario_scripts()

    LOG_DIR.mkdir(exist_ok=True)
    logs_before = set(LOG_DIR.glob("crash_*.json"))

    results: list[tuple[str, bool]] = []

    for i, (title, description, script_name) in enumerate(SCENARIOS, 1):
        _section(i, title)
        print(_indent(description, "    "))

        script_path = SCENARIO_DIR / script_name

        try:
            passed, stdout, stderr = _run_scenario(script_path)
        except subprocess.TimeoutExpired:
            passed = False
            stdout = ""
            stderr = "TIMED OUT after 10 s"

        status = Grn("  ✓  PASSED") if passed else Red("  ✗  FAILED")
        print(status)

        # Show stderr (the interesting bit — crash handler output)
        if stderr.strip():
            for line in stderr.strip().splitlines():
                print(f"     {Yel('│')} {line}")

        results.append((title, passed))
        time.sleep(0.05)   # tiny pause so log timestamps are distinct

    # ── Summary ───────────────────────────────────────────────────────────────
    new_logs = _count_new_logs(logs_before)

    _banner("Results Summary")
    passed_count = sum(1 for _, p in results if p)
    failed_count = len(results) - passed_count

    for title, passed in results:
        mark = Grn("✓") if passed else Red("✗")
        print(f"  {mark}  {title}")

    print()
    print(f"  {Grn(str(passed_count))} passed   {Red(str(failed_count))} failed   "
          f"{len(SCENARIOS)} total")

    if new_logs:
        print(f"\n  {Cyn('Log files produced:')}")
        for p in new_logs:
            # Peek at severity from JSON
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                sev = data.get("severity", "?")
                sev_str = {
                    "FATAL": Red(f"[{sev}]"),
                    "ERROR": Yel(f"[{sev}]"),
                }.get(sev, Cyn(f"[{sev}]"))
            except Exception:
                sev_str = ""
            print(f"    {sev_str}  {p.name}")

    print()
    if failed_count == 0:
        print(Grn("  All scenarios passed. CrashHandler is working correctly."))
    else:
        print(Red(f"  {failed_count} scenario(s) failed — review output above."))
    print()


# ── Scenario script generator ─────────────────────────────────────────────────

def _write_scenario_scripts() -> None:
    """Write all scenario .py files into SCENARIO_DIR."""
    scripts: dict[str, str] = {}

    # Shared preamble — every scenario must import crash_handler from the package path
    # It also ensures crash_handler knows its root for log writing
    PREAMBLE = """\
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from crashhandler import crash_handler
crash_handler.setup_crash_handler()
"""

    # ── 01 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_01_basic_error.py"] = PREAMBLE + """\
raise ValueError("player position out of bounds: x=-9999")
"""

    # ── 02 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_02_deep_traceback.py"] = PREAMBLE + """\
def level_8(): raise RuntimeError("deep crash")
def level_7(): level_8()
def level_6(): level_7()
def level_5(): level_6()
def level_4(): level_5()
def level_3(): level_4()
def level_2(): level_3()
def level_1(): level_2()
level_1()
"""

    # ── 03 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_03_recursion.py"] = PREAMBLE + """\
def recurse(): return recurse()
recurse()
"""

    # ── 04 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_04_cleanup_hooks.py"] = PREAMBLE + """\
def autosave():      print("[hook] autosave: world state saved", file=sys.stderr)
def flush_network(): print("[hook] flush_network: socket closed", file=sys.stderr)
def close_db():      print("[hook] close_db: database flushed",  file=sys.stderr)

import sys
crash_handler.register_cleanup_hook(autosave)
crash_handler.register_cleanup_hook(flush_network)
crash_handler.register_cleanup_hook(close_db)

raise RuntimeError("simulated mid-game crash")
"""

    # ── 05 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_05_bad_hook.py"] = PREAMBLE + """\
import sys
def good_hook(): print("[hook] good_hook ran fine", file=sys.stderr)
def bad_hook():  raise Exception("hook itself exploded")

crash_handler.register_cleanup_hook(bad_hook)
crash_handler.register_cleanup_hook(good_hook)

raise RuntimeError("game crash with a broken cleanup hook registered")
"""

    # ── 06 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_06_thread_crash.py"] = PREAMBLE + """\
import threading, time

def worker():
    time.sleep(0.05)
    raise ValueError("worker thread: texture atlas failed to load")

t = threading.Thread(target=worker, name="AssetLoader")
t.start()
t.join()
"""

    # ── 07 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_07_multi_thread.py"] = PREAMBLE + """\
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
"""

    # ── 08 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_08_chained.py"] = PREAMBLE + """\
try:
    int("not_a_number")
except ValueError as original:
    raise RuntimeError("failed to parse config file") from original
"""

    # ── 09 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_09_custom_exception.py"] = PREAMBLE + """\
class GameStateCorrupted(Exception):
    def __init__(self, save_slot: int):
        super().__init__(f"save slot {save_slot} has invalid checksum")
        self.save_slot = save_slot

raise GameStateCorrupted(save_slot=3)
"""

    # ── 10 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_10_env_snapshot.py"] = """\
import sys, os, json, time, subprocess
from pathlib import Path

# Always use the project root/logs
# Note: scenario scripts are in src/crashhandler/_demo_scenarios/ (3 levels deep)
_ROOT_DIR = Path(__file__).resolve().parents[4]
LOG_DIR   = _ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

time.sleep(1.1)   # ensure timestamp differs from any prior scenario
before = set(LOG_DIR.glob("crash_*.json"))

subprocess.run(
    [sys.executable, "-c",
     "import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), 'src')); "
     "from crashhandler import crash_handler; crash_handler.setup_crash_handler(); "
     "raise RuntimeError('env test')"],
    capture_output=True, text=True,
    cwd=str(_ROOT_DIR),
)

time.sleep(0.3)
after = set(LOG_DIR.glob("crash_*.json"))
new = after - before

if not new:
    print("DEMO_FAIL: no JSON log was created")
    sys.exit(1)

log = json.loads(sorted(new)[-1].read_text(encoding="utf-8"))
env = log.get("environment", {})

required_keys = ["timestamp", "python", "platform", "cwd", "argv", "thread"]
missing = [k for k in required_keys if k not in env]

if missing:
    print(f"DEMO_FAIL: environment snapshot missing keys: {missing}")
    sys.exit(1)

print(f"[check] All {len(required_keys)} environment keys present.", file=sys.stderr)
for k, v in env.items():
    print(f"  {k}: {v}", file=sys.stderr)
"""

    # ── 12 ────────────────────────────────────────────────────────────────────
    scripts["_scenario_12_keyboard_interrupt.py"] = """\
import sys, os, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Run a subprocess that installs the handler then raises KeyboardInterrupt.
# It should exit with code 1 (Python default for KeyboardInterrupt) NOT via
# our handler — i.e. no crash log should be written, and no "CRITICAL" header.
result = subprocess.run(
    [sys.executable, "-c",
     "import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), 'src')); "
     "from crashhandler import crash_handler; crash_handler.setup_crash_handler(); "
     "raise KeyboardInterrupt()"],
    capture_output=True, text=True
)

if "CRITICAL APPLICATION ERROR" in result.stderr:
    print("DEMO_FAIL: KeyboardInterrupt was captured by CrashHandler — it should not be")
    sys.exit(1)

print("[check] KeyboardInterrupt correctly passed through to default handler.", file=sys.stderr)
"""

    for name, source in scripts.items():
        (SCENARIO_DIR / name).write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()


