import os
import shutil
import tempfile
import unittest
from pathlib import Path
from gemini_console import HAFileManager, GeminiHAConsole


class TestHAFileManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mgr = HAFileManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_blueprint(self):
        bp_code = "blueprint:\n  name: Test\n  domain: automation\n"
        path, old = self.mgr.save_blueprint("test_bp", bp_code)
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "test_bp.yaml")
        self.assertEqual(self.mgr.read_file("blueprints/automation/test_bp.yaml"), bp_code)

    def test_write_and_read_file(self):
        content = "test_key: test_val\n"
        path, old = self.mgr.write_file("test.yaml", content)
        self.assertTrue(path.exists())
        self.assertEqual(self.mgr.read_file("test.yaml"), content)

    def test_path_traversal_protection(self):
        with self.assertRaises(PermissionError):
            self.mgr.read_file("../../outside.txt")

    def test_list_files(self):
        self.mgr.write_file("file1.yaml", "1")
        self.mgr.write_file("dir1/file2.yaml", "2")
        files = self.mgr.list_files()
        self.assertIn("file1.yaml", files)
        self.assertIn("dir1/", files)


class TestGeminiHAConsoleConfirmation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_blueprint_confirmation_granted(self):
        console = GeminiHAConsole(
            config_dir=self.test_dir,
            confirm_fn=lambda action, target, old, new: True
        )
        res = console.execute_tool(
            "save_blueprint",
            {"name": "motion_lights", "yaml_code": "blueprint:\n  name: Motion Lights\n"}
        )
        self.assertTrue(res["success"])
        bp_file = Path(self.test_dir) / "blueprints" / "automation" / "motion_lights.yaml"
        self.assertTrue(bp_file.exists())

    def test_blueprint_confirmation_denied(self):
        console = GeminiHAConsole(
            config_dir=self.test_dir,
            confirm_fn=lambda action, target, old, new: False
        )
        res = console.execute_tool(
            "save_blueprint",
            {"name": "motion_lights", "yaml_code": "blueprint:\n  name: Motion Lights\n"}
        )
        self.assertFalse(res["success"])
        self.assertTrue(res.get("cancelled"))
        bp_file = Path(self.test_dir) / "blueprints" / "automation" / "motion_lights.yaml"
        self.assertFalse(bp_file.exists())

    def test_write_file_confirmation_denied(self):
        console = GeminiHAConsole(
            config_dir=self.test_dir,
            confirm_fn=lambda action, target, old, new: False
        )
        res = console.execute_tool(
            "write_file",
            {"file_path": "configuration.yaml", "content": "homeassistant:\n"}
        )
        self.assertFalse(res["success"])
        self.assertTrue(res.get("cancelled"))
        target_file = Path(self.test_dir) / "configuration.yaml"
        self.assertFalse(target_file.exists())


if __name__ == "__main__":
    unittest.main()
