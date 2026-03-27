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
