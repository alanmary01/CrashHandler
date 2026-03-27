# CrashHandler

A centralised exception-handling subsystem for Python / Ursina Engine projects **in active development**.

       Instead of hiding errors with try-except, CrashHandler intentionally lets crashes propagate — then captures every diagnostic detail before the process exits. The goal is to surface bugs faster, not suppress them.

---

## Why?

| Standard approach | CrashHandler approach |
|-------------------|-----------------------|
| `try / except` everywhere | One hook, zero boilerplate |
| Errors silently swallowed | Every crash is logged in full |
| Plain traceback in terminal | Coloured terminal output |
| Nothing saved to disk | JSON log written automatically |
| Thread crashes die silently | Worker threads captured too |

---

## Features

- **Single setup call** — `setup_crash_handler()` and you're done
- **Severity classification** — FATAL / ERROR / INTERRUPT
- **Environment snapshot** — Python version, OS, argv, active thread, timestamp
- **JSON crash log** — machine-readable, timestamped, in `logs/`
- **Thread safety** — patches `threading.excepthook` to catch worker-thread crashes
- **Cleanup hooks** — register callbacks that run before exit (e.g. autosave)
- **Ursina integration** — calls `application.quit()` if Ursina is running; degrades gracefully if not

---

## Prerequisites

- Python 3.14+
- [Ursina Engine](https://www.ursinaengine.org/)

---

## Installation

```powershell
# Using uv (recommended)
uv sync

# Using pip
pip install ursina
```

---

## Quick Start

```python
# main.py
from crashhandler.crash_handler import (
    setup_crash_handler,
    register_cleanup_hook,
)

# 1. Activate — do this before anything else
setup_crash_handler()

# 2. (Optional) Register cleanup hooks
register_cleanup_hook(save_world_state)

# 3. Run your app normally — no try-except needed
from ursina import Ursina
app = Ursina()
app.run()
```

When an unhandled exception occurs:

1. A structured **terminal message** is printed (colour-coded by severity).
2. A **JSON log** is written to `logs/crash_<timestamp>.json`.
3. All registered **cleanup hooks** are called.
4. Ursina is shut down cleanly, then `sys.exit(1)` is called.

---

## API

### `setup_crash_handler() -> None`
Registers the global exception hook and thread safety patch. Call once at startup.

### `register_cleanup_hook(fn: Callable[[], None]) -> None`
Register a zero-argument callable to be invoked on crash before exit.

```python
register_cleanup_hook(my_autosave_fn)
```

---

## Log Output

```
logs/
  crash_2025-06-14_13-42-01.json   ← structured data
```

---

## Project Structure

```
main.py              ← entry point for the demo suite
src/
  crashhandler/
    crash_handler.py ← the entire subsystem (single file)
    demo_suite.py    ← feature demonstration runner
    _demo_scenarios/ ← isolated scripts for the demo suite
logs/                ← auto-created; crash reports land here
docs/
  ARCHITECTURE.md    ← system design and component map
  ROADMAP.md         ← planned features
```

---

## Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for planned features including an in-engine log viewer, local variable capture, and screenshot-on-crash.

---

## License

MIT — see [LICENSE](LICENSE).
