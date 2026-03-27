"""
CrashHandler — Centralised exception handling and diagnostic logging for Ursina projects.

Features:
  - Global exception hook (replaces sys.excepthook)
  - Severity classification (FATAL / ERROR / INTERRUPT)
  - Structured JSON crash logs with full environment snapshot
  - Human-readable terminal output with colour (raw ANSI — no dependencies)
  - Thread-safe: catches exceptions raised on non-main threads
  - Configurable callbacks so subsystems can register cleanup hooks
"""

import sys
import os
import json
import threading
import traceback
import platform
import datetime
from pathlib import Path
from typing import Any, Callable

# ── ANSI colour codes — no third-party dependencies ──────────────────────────
# Enabled on all modern terminals (Windows 10+, macOS, Linux).
# Disabled automatically when output is not a TTY (e.g. redirected to a file).
def _ansi(code: str) -> str:
    return f"\033[{code}m" if sys.stderr.isatty() else ""

_RESET  = _ansi("0")
_RED    = _ansi("31")
_YELLOW = _ansi("33")
_GREEN  = _ansi("32")
_CYAN   = _ansi("36")

def _c(colour: str, text: str) -> str:
    return f"{colour}{text}{_RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# LOG_DIR points to the workspace root /logs directory.
# Path depth from CrashHandler/src/crashhandler/crash_handler.py:
#   parents[0] = CrashHandler/src/crashhandler/
#   parents[1] = CrashHandler/src/
#   parents[2] = CrashHandler/
#   parents[3] = workspace root
_ROOT_DIR = Path(__file__).resolve().parents[3]
LOG_DIR   = _ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

_TIMESTAMP_FMT = "%Y-%m-%d_%H-%M-%S"
_CLEANUP_HOOKS: list[Callable[[], None]] = []
_LOCK = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def setup_crash_handler() -> None:
    """Register the global exception hook and a thread-safety wrapper."""
    sys.excepthook = _handle_exception
    _patch_threading()
    _print_info("CrashHandler active — all unhandled exceptions will be captured.")


def register_cleanup_hook(fn: Callable[[], None]) -> None:
    """Register a zero-argument callable that runs before the app exits on crash.

    Example::

        crash_handler.register_cleanup_hook(save_world_state)
    """
    with _LOCK:
        _CLEANUP_HOOKS.append(fn)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _classify(exc_type: type[BaseException]) -> str:
    """Return a severity label for the exception type."""
    if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
        return "INTERRUPT"
    if issubclass(exc_type, (MemoryError, RecursionError, SystemError)):
        return "FATAL"
    if issubclass(exc_type, Exception):
        return "ERROR"
    return "FATAL"


def _collect_environment() -> dict:
    """Snapshot runtime environment for the crash report."""
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "thread": threading.current_thread().name,
    }


def _format_traceback(exc_type, exc_value, exc_tb) -> str:
    """Format a traceback into a single string."""
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def _write_json_log(severity: str, tb_str: str, env: dict) -> Path:
    """Write a structured JSON crash log to LOG_DIR."""
    ts = datetime.datetime.now().strftime(_TIMESTAMP_FMT)
    path = LOG_DIR / f"crash_{ts}.json"
    payload = {
        "severity": severity,
        "environment": env,
        "traceback": tb_str,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _run_cleanup_hooks() -> None:
    """Execute all registered cleanup hooks, skipping any that raise."""
    with _LOCK:
        hooks = list(_CLEANUP_HOOKS)
    for fn in hooks:
        try:
            fn()
        except Exception:  # noqa: BLE001
            print(
                _c(_YELLOW, f"[CrashHandler] Cleanup hook {fn.__name__!r} raised an error — skipping."),
                file=sys.stderr
            )


def _handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: Any,
) -> None:
    """Global exception handler — logs, reports, cleans up, then exits."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    severity   = _classify(exc_type)
    tb_str     = _format_traceback(exc_type, exc_value, exc_traceback)
    env        = _collect_environment()

    severity_labels = {"FATAL": _RED, "ERROR": _YELLOW, "INTERRUPT": _CYAN}
    sev_colour      = severity_labels.get(severity, _RED)

    # ── Terminal output ───────────────────────────────────────────────────────
    print(_c(sev_colour, f"\n{'═' * 60}"), file=sys.stderr)
    print(_c(sev_colour, f"  {severity}: UNHANDLED EXCEPTION"), file=sys.stderr)
    print(_c(sev_colour, f"{'═' * 60}"), file=sys.stderr)
    print(tb_str, file=sys.stderr)

    # ── Persist logs ──────────────────────────────────────────────────────────
    json_path = _write_json_log(severity, tb_str, env)

    print(_c(_CYAN, f"[CrashHandler] JSON log    → {json_path}"), file=sys.stderr)

    # ── Cleanup hooks ─────────────────────────────────────────────────────────
    _run_cleanup_hooks()

    # ── Shutdown ──────────────────────────────────────────────────────────────
    # If Ursina is present, tell it to quit gracefully.
    try:
        from ursina import application
        if application and hasattr(application, "quit"):
            application.quit()
    except (ImportError, Exception):  # noqa: BLE001
        pass

    sys.exit(1)


def _patch_threading() -> None:
    """Redirect unhandled exceptions on worker threads through our handler."""
    def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
        if args.exc_type is SystemExit:
            return
        _handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thread_excepthook


def _print_info(msg: str) -> None:
    """Print an informational message to stdout."""
    print(_c(_GREEN, f"[CrashHandler] {msg}"))
