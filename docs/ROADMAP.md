# CrashHandler Roadmap

---

## Phase 1: Core Crash Pipeline ✅

- [x] `sys.excepthook` registration
- [x] Severity classification (FATAL / ERROR / INTERRUPT)
- [x] Coloured terminal output (raw ANSI — no third-party dependencies)
- [x] Environment snapshot at crash time
- [x] JSON structured log (`logs/crash_<ts>.json`)
- [x] HTML diagnostic report (`logs/crash_<ts>.html`)
- [x] Thread safety via `threading.excepthook`
- [x] Cleanup hook registry (`register_cleanup_hook`)
- [x] Graceful Ursina shutdown (`application.quit`)
- [x] Integration test: automated crash-and-recover test suite (`demo_suite.py`)

---

## Phase 2: Log Viewer ⏸ Deferred

Deferred — `CrashHandler` is currently under general stability only (no new features) per studio
portfolio constraints. Phase 2 requires a track allocation before work can begin.

- [ ] In-engine overlay: press `F9` to open the last crash report as a panel inside the running app
- [ ] Standalone HTML log viewer (`tools/log_viewer.html`) — drag-and-drop any crash JSON to inspect it
- [ ] Log list sorted by recency; filter by severity

---

## Phase 3: Smart Context Capture 🔜

- [ ] Capture local variables from each frame in the traceback (opt-in, privacy-safe)
- [ ] Record the last N lines of `stdout`/`stderr` before the crash (ring buffer)
- [ ] Snapshot Ursina scene state: entity count, active camera, current scene name
- [ ] Screenshot-on-crash: save a `.png` of the last rendered frame alongside the log

---

## Phase 4: Warning & Soft-Error Tracking 🔜

- [ ] `crash_handler.warn(msg)` — logs a recoverable warning without crashing
- [ ] `crash_handler.caught(exc)` — manually report a caught exception for visibility
- [ ] Aggregate warning count in HTML report header
- [ ] Optional in-engine HUD badge showing warning count

---

## Phase 5: Developer Experience Polish 🔜

- [ ] External publishing: package for installation outside the workspace via `pyproject.toml` / `uv`
      (internal workspace installation is already in place)
- [ ] Auto-open HTML report in the default browser after a crash (opt-in flag)
- [ ] Discord / desktop notification webhook on crash (opt-in)
- [ ] `crash_handler.simulate_crash()` — intentionally trigger a test crash to verify the pipeline

---

## Future Ideas 💡

- Cross-session crash analytics: compare recurrence of exception types across multiple runs
- Plugin architecture so third-party Ursina subsystems can self-register context providers
