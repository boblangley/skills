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
        "AGENTS metadata skip",
        'skill.name in {"README.md", "AGENTS.md"}',
        'skill.name in {"README.md"}',
        "BuildTests.test_top_level_agents_metadata_is_ignored",
    ),
    (
        "README metadata skip",
        'skill.name in {"README.md", "AGENTS.md"}',
        'skill.name in {"AGENTS.md"}',
        "BuildTests.test_top_level_readme_metadata_is_ignored",
    ),
    (
        "generation parent guard",
        "candidate.parent == output.parent",
        "True",
        "BuildTests.test_deletion_guard_refuses_generation_in_another_parent",
    ),
    (
        "generation name guard",
        're.fullmatch(re.escape(f".{output.name}.build-") + r"[a-zA-Z0-9_-]+", candidate.name)',
        "True",
        "BuildTests.test_deletion_guard_refuses_generation_with_wrong_name",
    ),
    (
        "generation marker read guard",
        "except (OSError, ValueError):\n        return False",
        "except (OSError, ValueError):\n        return True",
        "BuildTests.test_deletion_guard_refuses_generation_without_marker",
    ),
    (
        "generation owner guard",
        'metadata.get("output") == str(output)',
        "True",
        "BuildTests.test_deletion_guard_refuses_generation_with_foreign_owner",
    ),
    (
        "stale build cleanup",
        "        cleanup_stale_builds(output, previous)",
        "        pass  # MUTANT: do not reclaim interrupted builds",
        "BuildTests.test_stale_owned_builds_are_cleaned_without_removing_foreign_data",
    ),
    (
        "generation read permissions",
        "            stage.chmod(0o755)",
        "            pass  # MUTANT: leave mkdtemp's private permissions",
        "BuildTests.test_published_generation_is_readable_by_other_users",
    ),
    (
        "HTML block links",
        'if token.type == "html_block":',
        "if False:",
        "CheckTests.test_html_block_only_broken_links_are_reported",
    ),
    (
        "HTML inline links",
        'elif child.type == "html_inline":',
        "elif False:",
        "CheckTests.test_html_inline_only_broken_links_are_reported",
    ),
    (
        "HTML id anchors",
        'if key == "id" or (tag == "a" and key == "name"):',
        'if tag == "a" and key == "name":',
        "CheckTests.test_html_id_and_name_anchors_are_fragment_targets",
    ),
    (
        "HTML name anchors",
        'if key == "id" or (tag == "a" and key == "name"):',
        'if key == "id":',
        "CheckTests.test_html_id_and_name_anchors_are_fragment_targets",
    ),
    (
        "base symlink refusal",
        "                    if source.is_symlink():",
        "                    if False:",
        "BuildTests.test_base_symlink_is_refused",
    ),
    (
        "identical non-Markdown collision refusal",
        'if target.exists() and source.suffix.lower() != ".md":',
        'if target.exists() and source.suffix.lower() != ".md" '
        "and source.read_bytes() != target.read_bytes():",
        "BuildTests.test_identical_non_markdown_collision_is_refused",
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
