"""Fixture trees exercise the checker's public behaviour."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.skills_tree import check_tree

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


if __name__ == "__main__":
    unittest.main()
