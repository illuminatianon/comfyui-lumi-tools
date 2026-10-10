"""Behavioral tests for wildcard cache validation and multiple roots."""

import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "nodes" / "wildcards.py"


def load_wildcards():
    # Import the utility without importing nodes/__init__.py (which requires ComfyUI).
    spec = importlib.util.spec_from_file_location("lumi_test_wildcards", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WildcardCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.module = load_wildcards()
        self.clock = [100.0]
        clock_patch = patch.object(self.module.time, "monotonic", side_effect=lambda: self.clock[0])
        clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.module._CACHE_VALIDATION_INTERVAL = 30

    def test_hit_skips_all_filesystem_and_configuration_work_until_expiration(self):
        (self.root / "color.txt").write_text("red\n")
        with (
            patch.object(self.module, "get_wildcard_paths", return_value=[self.root]) as paths,
            patch.object(self.module.os, "walk", wraps=os.walk) as walk,
        ):
            manager = self.module.get_wildcard_manager()
            self.assertEqual(self.module.process_wildcards("__color__", 123), "red")
            self.assertIn("__color__", self.module.get_wildcard_list())
            self.assertIs(self.module.get_wildcard_manager(), manager)
            self.assertEqual(paths.call_count, 1)
            self.assertEqual(walk.call_count, 2)  # One scan plus manager initialization.

            self.clock[0] += 30
            self.assertIs(self.module.get_wildcard_manager(), manager)
            self.assertEqual(paths.call_count, 2)
            self.assertEqual(walk.call_count, 3)
            self.assertIs(self.module.get_wildcard_manager(), manager)
            self.assertEqual(walk.call_count, 3)

    def test_file_changes_and_nested_directory_changes_reload_after_interval(self):
        color = self.root / "color.txt"
        color.write_text("red\n")
        with patch.object(self.module, "get_wildcard_paths", return_value=[self.root]):
            manager = self.module.get_wildcard_manager()
            color.write_text("blue\n")
            self.assertIs(self.module.get_wildcard_manager(), manager)
            self.clock[0] += 30
            updated = self.module.get_wildcard_manager()
            self.assertIsNot(updated, manager)
            self.assertEqual(self.module.process_wildcards("__color__", 42), "blue")

            nested = self.root / "nested"
            nested.mkdir()
            (nested / "animal.txt").write_text("cat\n")
            self.clock[0] += 30
            added = self.module.get_wildcard_manager()
            self.assertIsNot(added, updated)
            self.assertIn("__nested/animal__", self.module.get_wildcard_list())

            (nested / "animal.txt").rename(nested / "pet.txt")
            self.clock[0] += 30
            renamed = self.module.get_wildcard_manager()
            self.assertIsNot(renamed, added)
            self.assertIn("__nested/pet__", self.module.get_wildcard_list())

            (nested / "pet.txt").unlink()
            self.clock[0] += 30
            removed = self.module.get_wildcard_manager()
            self.assertIsNot(removed, renamed)
            self.assertNotIn("__nested/pet__", self.module.get_wildcard_list())

    def test_same_size_edit_with_unchanged_directory_mtime_is_detected(self):
        color = self.root / "color.txt"
        color.write_text("red\n")
        with patch.object(self.module, "get_wildcard_paths", return_value=[self.root]):
            manager = self.module.get_wildcard_manager()
            directory_mtime = self.root.stat().st_mtime_ns
            old_mtime = color.stat().st_mtime_ns
            color.write_text("tan\n")
            os.utime(color, ns=(old_mtime + 1_000_000_000, old_mtime + 1_000_000_000))
            os.utime(self.root, ns=(directory_mtime, directory_mtime))
            self.clock[0] += 30
            self.assertIsNot(self.module.get_wildcard_manager(), manager)
            self.assertEqual(self.module.process_wildcards("__color__", 7), "tan")

    def test_seeded_processing_remains_repeatable(self):
        (self.root / "color.txt").write_text("red\nblue\ngreen\n")
        with patch.object(self.module, "get_wildcard_paths", return_value=[self.root]):
            first = self.module.process_wildcards("__color__ __color__", 12345)
            self.assertEqual(self.module.process_wildcards("__color__ __color__", 12345), first)

    def test_interval_is_configurable_at_import(self):
        with patch.dict(os.environ, {"LUMI_WILDCARDS_CACHE_INTERVAL": "5.5"}):
            self.assertEqual(load_wildcards()._CACHE_VALIDATION_INTERVAL, 5.5)

    def test_multiple_roots_and_configuration_change(self):
        first = self.root / "env"
        second = self.root / "yaml"
        first.mkdir()
        second.mkdir()
        (first / "color.txt").write_text("red\n")
        (second / "animal.txt").write_text("cat\n")
        folder_paths = types.SimpleNamespace(
            base_path=str(self.root),
            get_folder_paths=lambda name: [str(second)],
            folder_names_and_paths={"wildcards": ([str(second)], {".txt"})},
        )
        with (
            patch.dict(sys.modules, {"folder_paths": folder_paths}),
            patch.dict(os.environ, {"LUMI_WILDCARDS_PATH": str(first)}),
        ):
            self.assertEqual(self.module.get_wildcard_paths()[:2], [first, second])
            manager = self.module.get_wildcard_manager()
            self.assertEqual(self.module.process_wildcards("__color__ __animal__", 23), "red cat")
            self.assertIn("__animal__", self.module.get_wildcard_list())
            folder_paths.get_folder_paths = lambda name: [str(first)]
            self.clock[0] += 30
            self.assertIsNot(self.module.get_wildcard_manager(), manager)
            self.assertNotIn("__animal__", self.module.get_wildcard_list())


if __name__ == "__main__":
    unittest.main()
