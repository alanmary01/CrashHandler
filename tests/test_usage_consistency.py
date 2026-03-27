"""Static analysis check: all application entry points must call setup_crash_handler()."""

from __future__ import annotations

import ast
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

ENTRY_POINTS = [
    WORKSPACE_ROOT / "OpenWorld" / "src" / "openworld" / "game.py",
    WORKSPACE_ROOT / "TerrainSculpting" / "terrain_sculpting.py",
    WORKSPACE_ROOT / "Assets" / "src" / "assets" / "base_editor.py",
    WORKSPACE_ROOT / "WorldGeneration" / "tools" / "terrain_viewer.py",
]


def _calls_setup_crash_handler(source: str) -> bool:
    """Returns True if the source contains a call to setup_crash_handler()."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "setup_crash_handler":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "setup_crash_handler":
                return True
    return False


class TestCrashHandlerUsageConsistency:
    def test_all_entry_points_exist(self):
        for path in ENTRY_POINTS:
            assert path.exists(), f"Entry point not found: {path}"

    def test_openworld_game_calls_setup(self):
        path = WORKSPACE_ROOT / "OpenWorld" / "src" / "openworld" / "game.py"
        assert _calls_setup_crash_handler(path.read_text(encoding="utf-8")), (
            f"setup_crash_handler() not called in {path.name}"
        )

    def test_terrain_sculpting_calls_setup(self):
        path = WORKSPACE_ROOT / "TerrainSculpting" / "terrain_sculpting.py"
        assert _calls_setup_crash_handler(path.read_text(encoding="utf-8")), (
            f"setup_crash_handler() not called in {path.name}"
        )

    def test_base_editor_calls_setup(self):
        path = WORKSPACE_ROOT / "Assets" / "src" / "assets" / "base_editor.py"
        assert _calls_setup_crash_handler(path.read_text(encoding="utf-8")), (
            f"setup_crash_handler() not called in {path.name}"
        )

    def test_terrain_viewer_calls_setup(self):
        path = WORKSPACE_ROOT / "WorldGeneration" / "tools" / "terrain_viewer.py"
        assert _calls_setup_crash_handler(path.read_text(encoding="utf-8")), (
            f"setup_crash_handler() not called in {path.name}"
        )
