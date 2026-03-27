import sys, os, time, subprocess
from pathlib import Path

# Always use the project root/logs
# Note: scenario scripts are in src/crashhandler/_demo_scenarios/ (3 levels deep)
_ROOT_DIR = Path(__file__).resolve().parents[3]
LOG_DIR   = _ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

time.sleep(1.1)   # ensure timestamp differs from any prior scenario
before = set(LOG_DIR.glob("crash_*.html"))

subprocess.run(
    [sys.executable, "-c",
     "import sys, os; sys.path.insert(0, os.path.join(os.getcwd(), 'src')); "
     "from crashhandler import crash_handler; crash_handler.setup_crash_handler(); "
     "raise TypeError('html report test')"],
    capture_output=True, text=True,
    cwd=str(_ROOT_DIR),
)

time.sleep(0.3)
after  = set(LOG_DIR.glob("crash_*.html"))
new    = after - before

if not new:
    print("DEMO_FAIL: no HTML report was created")
    sys.exit(1)

html = sorted(new)[-1].read_text(encoding="utf-8")
checks = {
    "severity badge": 'class="badge"' in html,
    "environment table": "<table>" in html,
    "traceback block": "<pre>" in html,
    "dark background": "#1e1e2e" in html,
    "crash title": "Crash Report" in html,
}

failures = [name for name, ok in checks.items() if not ok]
if failures:
    print(f"DEMO_FAIL: HTML report missing: {failures}")
    sys.exit(1)

print(f"[check] HTML report structure verified ({len(checks)} checks).", file=sys.stderr)
for name, ok in checks.items():
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name}", file=sys.stderr)
