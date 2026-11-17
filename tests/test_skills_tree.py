"""Fixture trees exercise the checker's public behaviour."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.skills_tree import build_tree, check_tree

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skills_tree.py"


class TreeFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, text=""):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
        )


class CheckTests(TreeFixture):
    def test_names_every_broken_link_and_orphan(self):
        self.write("alpha/SKILL.md", "[a](missing.md)\n![b](missing.png)\n")
        self.write("alpha/README.md")
        self.write("alpha/references/unused.md")
        self.write("alpha/assets/unused.json")
        errors = check_tree(self.root)
        self.assertEqual(4, len(errors), errors)
        self.assertTrue(any("alpha/SKILL.md:1" in e and "missing.md" in e for e in errors))
        self.assertTrue(any("alpha/SKILL.md:2" in e and "missing.png" in e for e in errors))
        self.assertTrue(any("alpha/references/unused.md: orphan" in e for e in errors))
        self.assertTrue(any("alpha/assets/unused.json: orphan" in e for e in errors))
        result = self.run_cli("check", self.root)
        self.assertEqual(1, result.returncode)
        for error in errors:
            self.assertIn(error, result.stderr)
        self.assertNotIn("PASS", result.stdout)

    def test_inline_reference_image_html_and_encoded_links(self):
        self.write(
            "alpha/SKILL.md",
            '[guide](references/guide.md "Title")\n[asset][data]\n'
            "\n[data]: <assets/data file.json>\n"
            "![image](assets/image.png)\n"
            '<a href="references/guide.md#hello-world">guide</a>\n'
            '<img src="assets/image.png">\n',
        )
        self.write(
            "alpha/references/guide.md", "# Hello world\n[Data](../assets/data%20file.json)\n"
        )
        self.write("alpha/assets/data file.json", "{}")
        self.write("alpha/assets/image.png", "image")
        self.assertEqual([], check_tree(self.root))

    def test_code_comments_environment_paths_and_remote_links_are_ignored(self):
        self.write(
            "alpha/SKILL.md",
            "`[code](missing-inline.md)`\n\n```md\n[code](missing-block.md)\n```\n"
            "\n<!-- [comment](missing-comment.md) -->\n"
            "[remote](https://example.com/a) [mail](mailto:a@example.com)\n"
            "[home](~/models.yml) [absolute](/skills/alpha/SKILL.md)\n",
        )
        self.assertEqual([], check_tree(self.root))

    def test_cross_skill_links_do_not_rescue_local_orphans(self):
        self.write("alpha/SKILL.md", "[other](../beta/unused.md)\n")
        self.write("beta/SKILL.md")
        self.write("beta/unused.md", "[self](unused.md)\n")
        self.assertEqual(
            ["beta/unused.md: orphan file (no Markdown link in beta)"], check_tree(self.root)
        )

    def test_directories_do_not_rescue_orphans(self):
        self.write("alpha/SKILL.md", "[assets](assets/)\n")
        self.write("alpha/assets/unlisted.txt")
        self.assertIn("orphan file", check_tree(self.root)[0])

    def test_fragments_and_duplicate_headings(self):
        self.write(
            "alpha/SKILL.md", "[ok](#hello) [ok](#hello-1) [bad](#absent)\n# Hello\n# Hello\n"
        )
        errors = check_tree(self.root)
        self.assertEqual(1, len(errors), errors)
        self.assertIn("#absent (missing anchor)", errors[0])

    def test_empty_tree_fails(self):
        self.assertIn("no skills found", check_tree(self.root)[0])
        self.assertEqual(1, self.run_cli("check", self.root).returncode)

    def test_symlink_fails(self):
        self.write("alpha/SKILL.md", "[link](link.md)\n")
        target = self.write("outside.md")
        (self.root / "alpha/link.md").symlink_to(target)
        self.assertTrue(any("symlinks" in error for error in check_tree(self.root)))

    def test_only_asset_template_slots_are_exempt(self):
        self.write("alpha/SKILL.md", "[template](assets/template.md) [bad]({path})\n")
        self.write("alpha/assets/template.md", "[slot]({path})\n")
        errors = check_tree(self.root)
        self.assertEqual(1, len(errors), errors)
        self.assertIn("broken relative link %7Bpath%7D", errors[0])


class BuildTests(TreeFixture):
    def setUp(self):
        super().setUp()
        self.base = self.root / "base"
        self.output = self.root / "output"
        self.write(
            "base/alpha/SKILL.md",
            "---\nname: alpha\ndescription: base description\n---\n\n# Base\n",
        )
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

    def build(self, *flags):
        return self.run_cli("build", "--base", self.base, "--output", self.output, *flags)

    def assert_success(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_appends_in_argument_order_adds_files_skills_and_project_headings(self):
        self.write("workspace/alpha/SKILL.md", "Workspace instructions\n[guide](guide.md)\n")
        self.write("workspace/alpha/guide.md", "Workspace guide\n")
        self.write("project/alpha/SKILL.md", "Project instructions\n[script](run.sh)\n")
        self.write("project/alpha/guide.md", "Project guide\n")
        self.write("project/alpha/run.sh", "#!/bin/sh\necho test\n").chmod(0o755)
        self.write(
            "project/beta/SKILL.md", "---\nname: beta\ndescription: new skill\n---\n\nNew skill\n"
        )
        self.write("project/beta/README.md", "New readme\n")
        before = {path: path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        result = self.build(
            "--overlay",
            self.workspace,
            "--project",
            "/workspace/project with spaces",
            self.root / "project",
        )
        self.assert_success(result)
        merged = (self.output / "alpha/SKILL.md").read_text()
        self.assertTrue(merged.startswith("---\nname: alpha\ndescription: base description\n---"))
        self.assertLess(
            merged.index("Workspace instructions"), merged.index("Project instructions")
        )
        self.assertIn("## Project: /workspace/project with spaces\n\nProject instructions", merged)
        self.assertEqual(
            "Workspace guide\n\n## Project: /workspace/project with spaces\n\nProject guide\n",
            (self.output / "alpha/guide.md").read_text(),
        )
        new_skill = (self.output / "beta/SKILL.md").read_text()
        self.assertTrue(new_skill.startswith("---\nname: beta\ndescription: new skill\n---\n"))
        self.assertIn("## Project: /workspace/project with spaces\n\nNew skill", new_skill)
        self.assertIn(
            "## Project: /workspace/project with spaces",
            (self.output / "beta/README.md").read_text(),
        )
        self.assertEqual(0o755, (self.output / "alpha/run.sh").stat().st_mode & 0o777)
        self.assertEqual(
            before, {path: path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        )
        self.assertEqual([], check_tree(self.output))

    def test_top_level_agents_metadata_is_ignored(self):
        self.write("workspace/AGENTS.md", "Folder instructions\n[not skill content](absent.md)\n")
        self.assert_success(self.build("--project", "/workspace/project", self.workspace))
        self.assertFalse((self.output / "AGENTS.md").exists())

    def test_top_level_readme_metadata_is_ignored(self):
        self.write("workspace/README.md", "Folder documentation\n[not skill content](absent.md)\n")
        self.assert_success(self.build("--overlay", self.workspace))
        self.assertFalse((self.output / "README.md").exists())

    def test_other_top_level_file_is_refused(self):
        self.write("workspace/notes.txt", "Not overlay metadata\n")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("notes.txt: expected a skill folder", result.stderr)
        self.assertFalse(self.output.exists())

    def test_project_and_workspace_arguments_keep_their_order(self):
        self.write("workspace/alpha/SKILL.md", "last\n")
        self.write("project/alpha/SKILL.md", "first\n")
        self.assert_success(
            self.build("--project", "/project", self.root / "project", "--overlay", self.workspace)
        )
        text = (self.output / "alpha/SKILL.md").read_text()
        self.assertLess(text.index("first"), text.index("last"))

    def test_validation_failures_preserve_previous_output(self):
        self.assert_success(self.build())
        previous = self.output.readlink()
        content = (self.output / "alpha/SKILL.md").read_bytes()
        for path, text, message in [
            ("alpha/SKILL.md", "[broken](absent.md)\n", "broken relative link absent.md"),
            ("alpha/orphan.txt", "orphan", "alpha/orphan.txt: orphan file"),
        ]:
            with self.subTest(path=path):
                added = self.write("workspace/" + path, text)
                result = self.build("--overlay", self.workspace)
                self.assertEqual(1, result.returncode)
                self.assertIn(message, result.stderr)
                self.assertNotIn("PASS", result.stdout)
                self.assertEqual(previous, self.output.readlink())
                self.assertEqual(content, (self.output / "alpha/SKILL.md").read_bytes())
                self.assertEqual(1, len(list(self.root.glob(".output.build-*"))))
                added.unlink()

    def test_non_markdown_collisions_are_refused(self):
        self.write("base/alpha/SKILL.md", "[data](data.json)\n")
        self.write("base/alpha/data.json", "{}")
        self.write("workspace/alpha/data.json", "[]")
        self.assert_success(self.build())
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("refusing append to non-Markdown file", result.stderr)
        self.assertEqual("{}", (self.output / "alpha/data.json").read_text())

    def test_appended_skill_front_matter_is_refused(self):
        self.write("workspace/alpha/SKILL.md", "---\ndescription: replacement\n---\n")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("must not contain front matter", result.stderr)
        self.assertFalse(self.output.exists())

    def test_successful_rebuild_switches_symlink_and_removes_previous_generation(self):
        self.assert_success(self.build())
        previous = self.output.resolve()
        self.write("workspace/alpha/SKILL.md", "new text\n")
        self.assert_success(self.build("--overlay", self.workspace))
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(previous.exists())
        self.assertIn("new text", (self.output / "alpha/SKILL.md").read_text())
        self.assertEqual(1, len(list(self.root.glob(".output.build-*"))))

    def test_publication_error_preserves_previous_output_and_cleans_stage(self):
        self.assert_success(self.build())
        previous = self.output.readlink()
        content = (self.output / "alpha/SKILL.md").read_bytes()
        with patch("scripts.skills_tree.os.replace", side_effect=OSError("publication failed")):
            with self.assertRaisesRegex(OSError, "publication failed"):
                build_tree(self.base, [], self.output)
        self.assertEqual(previous, self.output.readlink())
        self.assertEqual(content, (self.output / "alpha/SKILL.md").read_bytes())
        self.assertEqual(1, len(list(self.root.glob(".output.build-*"))))

    def test_concurrent_builds_leave_one_complete_generation(self):
        self.write("workspace/alpha/SKILL.md", "workspace\n")
        command = [
            sys.executable,
            str(SCRIPT),
            "build",
            "--base",
            str(self.base),
            "--output",
            str(self.output),
            "--overlay",
            str(self.workspace),
        ]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        for process in [first, second]:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(0, process.returncode, stderr)
            self.assertIn("PASS:", stdout)
        self.assertEqual([], check_tree(self.output))
        self.assertIn("workspace", (self.output / "alpha/SKILL.md").read_text())
        self.assertEqual(1, len(list(self.root.glob(".output.build-*"))))

    def test_invalid_inputs_and_unmanaged_outputs_are_preserved(self):
        result = self.build("--overlay", self.root / "absent")
        self.assertEqual(1, result.returncode)
        self.assertFalse(self.output.exists())
        self.output.mkdir()
        keep = self.write("output/keep.txt", "keep")
        result = self.build()
        self.assertEqual(1, result.returncode)
        self.assertIn("output must be absent", result.stderr)
        self.assertEqual("keep", keep.read_text())
        keep.unlink()
        self.output.rmdir()
        self.output.symlink_to(self.base, target_is_directory=True)
        result = self.build()
        self.assertEqual(1, result.returncode)
        self.assertIn("unmanaged symlink", result.stderr)
        self.assertEqual(self.base, self.output.resolve())

    def generation(self, name=".output.build-fixture", parent=None, owner=None):
        target = (parent or self.root) / name
        target.mkdir(parents=True)
        (target / "keep.txt").write_text("preserve this target", encoding="utf-8")
        (target / ".skills-build.json").write_text(
            json.dumps({"output": str(owner or self.output)}), encoding="utf-8"
        )
        return target

    def assert_unmanaged_target_survives(self, target):
        self.output.symlink_to(target, target_is_directory=True)
        result = self.build()
        self.assertEqual(1, result.returncode)
        self.assertIn("refusing to replace an unmanaged symlink", result.stderr)
        self.assertEqual(target, self.output.readlink())
        self.assertEqual(target.resolve(), self.output.resolve())
        self.assertEqual("preserve this target", (target / "keep.txt").read_text())

    def test_deletion_guard_refuses_generation_without_marker(self):
        target = self.generation()
        (target / ".skills-build.json").unlink()
        self.assert_unmanaged_target_survives(target)

    def test_deletion_guard_refuses_generation_with_foreign_owner(self):
        target = self.generation(owner=self.root / "another-output")
        self.assert_unmanaged_target_survives(target)

    def test_deletion_guard_refuses_generation_in_another_parent(self):
        target = self.generation(parent=self.root / "elsewhere")
        self.assert_unmanaged_target_survives(target)

    def test_deletion_guard_refuses_generation_with_wrong_name(self):
        target = self.generation(name="unrelated-directory")
        self.assert_unmanaged_target_survives(target)

    def test_deletion_guard_refuses_generation_symlink(self):
        target = self.generation(name="unrelated-directory")
        alias = self.root / ".output.build-alias"
        alias.symlink_to(target, target_is_directory=True)
        self.assert_unmanaged_target_survives(alias)

    def test_deletion_guard_refuses_invalid_marker(self):
        for metadata in ["[]", "not JSON"]:
            with self.subTest(metadata=metadata):
                target = self.generation()
                (target / ".skills-build.json").write_text(metadata, encoding="utf-8")
                self.assert_unmanaged_target_survives(target)
                self.output.unlink()
                shutil.rmtree(target)

    def test_dangling_managed_output_is_rebuilt(self):
        self.assert_success(self.build())
        previous = self.output.readlink()
        shutil.rmtree(self.output.resolve())
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(self.output.exists())
        self.assert_success(self.build())
        self.assertNotEqual(previous, self.output.readlink())
        self.assertEqual([], check_tree(self.output))

    def test_dangling_unmanaged_output_is_refused(self):
        for target in [self.root / "missing", self.root / "other/.output.build-missing"]:
            with self.subTest(target=target):
                self.output.symlink_to(target, target_is_directory=True)
                result = self.build()
                self.assertEqual(1, result.returncode)
                self.assertIn("refusing to replace an unmanaged symlink", result.stderr)
                self.assertEqual(target, self.output.readlink())
                self.output.unlink()

    def test_failed_rebuild_preserves_dangling_managed_output(self):
        target = Path(".output.build-missing")
        self.output.symlink_to(target, target_is_directory=True)
        self.write("workspace/alpha/SKILL.md", "[bad](missing.md)\n")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("broken relative link", result.stderr)
        self.assertEqual(target, self.output.readlink())
        self.assertEqual([], list(self.root.glob(".output.build-*")))

    def test_stale_owned_builds_are_cleaned_without_removing_foreign_data(self):
        self.assert_success(self.build())
        current = self.output.resolve()
        stale = self.generation(name=".output.build-stale")
        stale_link = self.root / ".output.build-stale.link"
        stale_link.symlink_to(stale.name, target_is_directory=True)
        dangling_link = self.root / ".output.build-dangling.link"
        dangling_link.symlink_to(".output.build-missing", target_is_directory=True)
        unmarked = self.generation(name=".output.build-unmarked")
        (unmarked / ".skills-build.json").unlink()
        foreign = self.generation(name=".output.build-foreign", owner=self.root / "another-output")
        outside = self.generation(name="outside")
        alias = self.root / ".output.build-alias"
        alias.symlink_to(outside, target_is_directory=True)
        empty = self.root / ".output.build-empty"
        empty.mkdir()
        self.write("workspace/alpha/SKILL.md", "[bad](missing.md)\n")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertFalse(stale.exists())
        self.assertFalse(stale_link.is_symlink())
        self.assertFalse(dangling_link.is_symlink())
        self.assertFalse(empty.exists())
        self.assertEqual(current, self.output.resolve())
        for target in [unmarked, foreign, outside, alias]:
            self.assertEqual("preserve this target", (target / "keep.txt").read_text())

    def test_killed_builds_are_reclaimed_on_next_run(self):
        self.assert_success(self.build())
        for phase in ["copy", "publish"]:
            with self.subTest(phase=phase):
                previous = self.output.resolve()
                fault = """
import os
import signal
import sys
from pathlib import Path
from scripts import skills_tree as tree

def kill(*args, **kwargs):
    if sys.argv[3] == "copy":
        original_copy(*args, **kwargs)
    os.kill(os.getpid(), signal.SIGKILL)

original_copy = tree.shutil.copytree
if sys.argv[3] == "copy":
    tree.shutil.copytree = kill
else:
    tree.os.replace = kill
tree.build_tree(Path(sys.argv[1]), [], Path(sys.argv[2]))
"""
                result = subprocess.run(
                    [sys.executable, "-c", fault, str(self.base), str(self.output), phase],
                    cwd=SCRIPT.parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(-9, result.returncode, result.stderr)
                self.assertEqual(previous, self.output.resolve())
                stale = [p for p in self.root.glob(".output.build-*") if p != previous]
                self.assertTrue(stale)
                if phase == "publish":
                    self.assertTrue(any(p.is_symlink() for p in stale))
                self.assert_success(self.build())
                self.assertTrue(all(not p.exists() and not p.is_symlink() for p in stale))
                self.assertEqual(1, len(list(self.root.glob(".output.build-*"))))

    def test_published_generation_is_readable_by_other_users(self):
        self.assert_success(self.build())
        self.assertEqual(0o755, self.output.stat().st_mode & 0o777)

    def test_output_cannot_overlap_inputs(self):
        result = self.run_cli("build", "--base", self.base, "--output", self.base / "output")
        self.assertEqual(1, result.returncode)
        self.assertIn("separate from every input", result.stderr)
        result = self.run_cli("build", "--base", self.base, "--output", self.root)
        self.assertEqual(1, result.returncode)
        self.assertIn("separate from every input", result.stderr)

    def test_new_skill_requires_entry_point_and_rejects_symlinks(self):
        added = self.write("workspace/beta/guide.md")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("new skill must include SKILL.md", result.stderr)
        added.unlink()
        added.symlink_to(self.base / "alpha/SKILL.md")
        result = self.build("--overlay", self.workspace)
        self.assertEqual(1, result.returncode)
        self.assertIn("symlinks are not supported", result.stderr)

    def test_empty_base_fails_without_publishing(self):
        (self.base / "alpha/SKILL.md").unlink()
        result = self.build()
        self.assertEqual(1, result.returncode)
        self.assertIn("no skills found", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
