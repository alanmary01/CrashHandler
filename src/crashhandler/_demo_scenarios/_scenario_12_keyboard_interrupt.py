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
