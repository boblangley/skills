"""Exercise the published Task interface from outside the repository."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.skills_tree import skill_folders

ROOT = Path(__file__).resolve().parents[1]


class TaskInterfaceTests(unittest.TestCase):
    def test_build_and_check_accept_spaces_from_another_directory(self):
        with tempfile.TemporaryDirectory(prefix="skills-task-") as temp:
            root = Path(temp)
            base = root / "base tree"
            overlay = root / "overlay tree"
            output = root / "generated tree"
            for tree, body in [(base, "# Base\n"), (overlay, "Project instructions\n")]:
                (tree / "alpha").mkdir(parents=True)
                (tree / "alpha/SKILL.md").write_text(body, encoding="utf-8")
            build = subprocess.run(
                [
                    "task",
                    "--dir",
                    str(ROOT),
                    "build",
                    "--",
                    "--base",
                    str(base),
                    "--output",
                    str(output),
                    "--project",
                    "/workspace/project with spaces",
                    str(overlay),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, build.returncode, build.stdout + build.stderr)
            self.assertIn(
                "## Project: /workspace/project with spaces\n\nProject instructions",
                (output / "alpha/SKILL.md").read_text(),
            )
            check = subprocess.run(
                ["task", "--dir", str(ROOT), "skills:check", f"TREE={output}"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertIn("PASS: skills tree", check.stdout)

    def test_builds_the_repository_skills_without_copying_repository_tooling(self):
        with tempfile.TemporaryDirectory(prefix="skills-repo-build-") as temp:
            output = Path(temp) / "skills"
            result = subprocess.run(
                [
                    "task",
                    "--dir",
                    str(ROOT),
                    "build",
                    "--",
                    "--base",
                    str(ROOT),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(
                {skill.name for skill in skill_folders(ROOT)},
                {path.name for path in output.iterdir() if path.is_dir()},
            )
            for excluded in ["scripts", "tests", "Taskfile.yml", ".venv"]:
                self.assertFalse((output / excluded).exists(), excluded)
