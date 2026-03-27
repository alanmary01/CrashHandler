"""Unit tests for core CrashHandler logic."""

from __future__ import annotations

import pytest
from crashhandler.crash_handler import (
    _classify,
    _collect_environment,
    _CLEANUP_HOOKS,
    _run_cleanup_hooks,
    register_cleanup_hook,
)


@pytest.fixture(autouse=True)
def clear_cleanup_hooks():
    """Reset the global cleanup hook list before and after each test."""
    _CLEANUP_HOOKS.clear()
    yield
    _CLEANUP_HOOKS.clear()


# ── _classify ─────────────────────────────────────────────────────────────────

class TestClassify:
    def test_system_exit_is_interrupt(self):
        assert _classify(SystemExit) == "INTERRUPT"

    def test_keyboard_interrupt_is_interrupt(self):
        assert _classify(KeyboardInterrupt) == "INTERRUPT"

    def test_memory_error_is_fatal(self):
        assert _classify(MemoryError) == "FATAL"

    def test_recursion_error_is_fatal(self):
        assert _classify(RecursionError) == "FATAL"

    def test_system_error_is_fatal(self):
        assert _classify(SystemError) == "FATAL"

    def test_value_error_is_error(self):
        assert _classify(ValueError) == "ERROR"

    def test_runtime_error_is_error(self):
        assert _classify(RuntimeError) == "ERROR"

    def test_generic_exception_is_error(self):
        assert _classify(Exception) == "ERROR"

    def test_custom_exception_is_error(self):
        class MyAppError(Exception):
            pass
        assert _classify(MyAppError) == "ERROR"

    def test_custom_fatal_subclass(self):
        class CriticalError(MemoryError):
            pass
        assert _classify(CriticalError) == "FATAL"


# ── _collect_environment ──────────────────────────────────────────────────────

class TestCollectEnvironment:
    def test_returns_all_required_keys(self):
        env = _collect_environment()
        required = {"timestamp", "python", "platform", "cwd", "argv", "thread"}
        assert required.issubset(env.keys())

    def test_timestamp_is_string(self):
        env = _collect_environment()
        assert isinstance(env["timestamp"], str)
        assert len(env["timestamp"]) > 0

    def test_argv_is_list(self):
        env = _collect_environment()
        assert isinstance(env["argv"], list)

    def test_thread_is_string(self):
        env = _collect_environment()
        assert isinstance(env["thread"], str)


# ── register_cleanup_hook / _run_cleanup_hooks ────────────────────────────────

class TestCleanupHooks:
    def test_hook_is_registered(self):
        called = []
        register_cleanup_hook(lambda: called.append(1))
        assert len(_CLEANUP_HOOKS) == 1

    def test_hook_is_called_on_run(self):
        called = []
        register_cleanup_hook(lambda: called.append(1))
        _run_cleanup_hooks()
        assert called == [1]

    def test_multiple_hooks_called_in_order(self):
        order = []
        register_cleanup_hook(lambda: order.append("first"))
        register_cleanup_hook(lambda: order.append("second"))
        _run_cleanup_hooks()
        assert order == ["first", "second"]

    def test_failing_hook_does_not_prevent_others(self):
        called = []

        def bad_hook():
            raise RuntimeError("oops")

        def good_hook():
            called.append("good")

        register_cleanup_hook(bad_hook)
        register_cleanup_hook(good_hook)
        _run_cleanup_hooks()
        assert "good" in called

    def test_no_hooks_runs_cleanly(self):
        _run_cleanup_hooks()  # should not raise
