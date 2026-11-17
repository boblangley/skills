"""Prove the link, orphan, overlay and publication guards with targeted mutations."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = [
    (
        "broken-link reporting",
        "                    errors.append(label)\n",
        "                    pass  # MUTANT: ignore a missing target\n",
        "CheckTests.test_names_every_broken_link_and_orphan",
    ),
    (
        "orphan reporting",
        "for path in sorted(files - referenced):",
        "for path in []:",
        "CheckTests.test_names_every_broken_link_and_orphan",
    ),
    (
        "Markdown append order",
        'target.read_text(encoding="utf-8").rstrip("\\n") + "\\n\\n" + text',
        'text + "\\n\\n" + target.read_text(encoding="utf-8")',
        "BuildTests.test_appends_in_argument_order_adds_files_skills_and_project_headings",
    ),
    (
        "non-Markdown collision refusal",
        'if target.exists() and source.suffix.lower() != ".md":',
        "if False:",
        "BuildTests.test_non_markdown_collisions_are_refused",
    ),
    (
        "description protection",
        'if target.exists() and source.name == "SKILL.md" and text.startswith("---\\n"):',
        "if False:",
        "BuildTests.test_appended_skill_front_matter_is_refused",
    ),
    (
        "validation before publication",
        "errors = check_tree(stage)\n            if errors:",
        "errors = check_tree(stage)\n            if False:",
        "BuildTests.test_validation_failures_preserve_previous_output",
    ),
]


def run(root, test=None):
    command = [sys.executable, "-m", "unittest"]
    command += ["test_skills_tree." + test] if test else ["discover", "-s", "tests"]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root), str(root / "tests")]))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=60)


def main():
    baseline = run(ROOT)
    if baseline.returncode:
        print("FAIL: unmodified test suite did not pass", file=sys.stderr)
        print(baseline.stdout + baseline.stderr, file=sys.stderr)
        return 1
    source = (ROOT / "scripts/skills_tree.py").read_text(encoding="utf-8")
    caught = 0
    for name, original, replacement, test in MUTATIONS:
        if source.count(original) != 1:
            print(f"FAIL: mutation {name!r} no longer matches exactly once", file=sys.stderr)
            return 1
        with tempfile.TemporaryDirectory(prefix="skills-mutation-") as temp:
            root = Path(temp)
            shutil.copytree(
                ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__")
            )
            shutil.copytree(
                ROOT / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__")
            )
            (root / "scripts/skills_tree.py").write_text(
                source.replace(original, replacement), encoding="utf-8"
            )
            result = run(root, test)
        assertions = re.findall(r"^FAIL: (.+)$", result.stderr, re.MULTILINE)
        if not result.returncode or not assertions or "ERROR:" in result.stderr:
            print(f"FAIL: mutation {name!r} survived or had no assertion failure", file=sys.stderr)
            print(result.stdout + result.stderr, file=sys.stderr)
            return 1
        caught += 1
        print(f"CAUGHT: {name}: {'; '.join(assertions)}")
    if caught != len(MUTATIONS) or caught == 0:
        return 1
    print(f"PASS: {caught}/{len(MUTATIONS)} mutations caught by named assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
