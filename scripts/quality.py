"""Repository YAML syntax, formatting and Conventional Commit checks."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".venv", ".ruff_cache", "__pycache__", "build"}


def files():
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not IGNORED.intersection(path.relative_to(ROOT).parts)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["lint", "format", "commit-msg"])
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args()
    if args.command == "commit-msg":
        if args.path is None:
            parser.error("commit-msg requires a message file")
        subject = args.path.read_text(encoding="utf-8").splitlines()[0]
        if not re.fullmatch(r"[a-z]+(?:\([^()\n]+\))?!?: .+", subject):
            print("FAIL: expected Conventional Commit: type(scope): description", file=sys.stderr)
            return 1
        print("PASS: Conventional Commit")
        return 0
    errors = []
    paths = files()
    for path in paths:
        if path.suffix not in {".yml", ".yaml"}:
            continue
        try:
            list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        except (yaml.YAMLError, UnicodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    markdown = [str(path.relative_to(ROOT)) for path in paths if path.suffix == ".md"]
    mode = "fix" if args.command == "format" else "scan"
    result = subprocess.run(
        ["pymarkdown", "--config", str(ROOT / ".pymarkdown.json"), mode, *markdown], cwd=ROOT
    )
    if errors:
        print("\n".join(errors), file=sys.stderr)
    if result.returncode or errors:
        return 1
    print(f"PASS: Markdown and YAML {args.command}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
