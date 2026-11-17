"""Check skill-local links and support-file references in a skills tree."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

MARKDOWN = MarkdownIt("commonmark")
ENTRY_POINTS = {"SKILL.md", "README.md"}


@dataclass(frozen=True)
class Link:
    target: str
    line: int


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[Link] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value is None:
                continue
            if key in {"href", "src"}:
                self.links.append(Link(value, self.getpos()[0]))
            if key == "id" or (tag == "a" and key == "name"):
                self.anchors.add(value)


def markdown_info(text: str) -> tuple[list[Link], set[str]]:
    """Use Markdown tokens so code examples and comments are not links."""
    links: list[Link] = []
    anchors: set[str] = set()
    slugs: Counter[str] = Counter()
    tokens = MARKDOWN.parse(text)
    for index, token in enumerate(tokens):
        line = token.map[0] + 1 if token.map else 1
        if token.type == "heading_open":
            inline = tokens[index + 1]
            title = "".join(
                child.content
                for child in inline.children or []
                if child.type in {"text", "code_inline", "image"}
            )
            slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
            suffix = f"-{slugs[slug]}" if slugs[slug] else ""
            slugs[slug] += 1
            anchors.add(slug + suffix)
        if token.type == "html_block":
            parser = HTMLLinks()
            parser.feed(token.content)
            links.extend(Link(link.target, line + link.line - 1) for link in parser.links)
            anchors.update(parser.anchors)
        for child in token.children or []:
            if child.type in {"softbreak", "hardbreak"}:
                line += 1
            elif child.type == "link_open":
                links.append(Link(child.attrGet("href") or "", line))
            elif child.type == "image":
                links.append(Link(child.attrGet("src") or "", line))
            elif child.type == "html_inline":
                parser = HTMLLinks()
                parser.feed(child.content)
                links.extend(Link(link.target, line) for link in parser.links)
                anchors.update(parser.anchors)
    return links, anchors


def skill_folders(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if not path.name.startswith(".") and path.is_dir() and (path / "SKILL.md").is_file()
    )


def check_tree(root: Path) -> list[str]:
    root = root.resolve(strict=True)
    errors: list[str] = []
    skills = skill_folders(root)
    if not skills:
        return [f"{root}: no skills found (expected <skill>/SKILL.md)"]
    for skill in skills:
        if skill.is_symlink():
            errors.append(f"{skill.name}: symlinked skill folder is not supported")
            continue
        files: set[Path] = set()
        for path in sorted(skill.rglob("*")):
            if path.is_symlink():
                errors.append(f"{path.relative_to(root)}: symlinks are not supported")
            elif path.is_file():
                files.add(path)
        referenced: set[Path] = set()
        for path in sorted(files):
            if path.suffix.lower() != ".md":
                continue
            try:
                links, _ = markdown_info(path.read_text(encoding="utf-8"))
            except UnicodeError as exc:
                errors.append(f"{path.relative_to(root)}: invalid Markdown encoding: {exc}")
                continue
            for link in links:
                try:
                    url = urlsplit(link.target)
                except ValueError:
                    errors.append(
                        f"{path.relative_to(root)}:{link.line}: invalid link {link.target}"
                    )
                    continue
                # Absolute/home paths refer to the installed environment, not the skills tree.
                if url.scheme or url.netloc or url.path.startswith(("/", "~/")):
                    continue
                relative = unquote(url.path)
                # Repository templates deliberately carry slots filled by their eventual user.
                if "assets" in path.relative_to(skill).parts and re.search(r"\{.+?\}", relative):
                    continue
                target = (path.parent / relative).resolve() if relative else path
                label = f"{path.relative_to(root)}:{link.line}: broken relative link {link.target}"
                if not target.exists():
                    errors.append(label)
                    continue
                if target.is_file() and target.is_relative_to(skill) and target != path:
                    referenced.add(target)
                if url.fragment and target.is_file() and target.suffix.lower() == ".md":
                    try:
                        _, anchors = markdown_info(target.read_text(encoding="utf-8"))
                    except UnicodeError:
                        continue  # Reported when scanning the target.
                    if unquote(url.fragment) not in anchors:
                        errors.append(label + " (missing anchor)")
        for path in sorted(files - referenced):
            if path.parent == skill and path.name in ENTRY_POINTS:
                continue
            errors.append(
                f"{path.relative_to(root)}: orphan file (no Markdown link in {skill.name})"
            )
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check relative links and orphan files")
    check.add_argument("tree", type=Path)
    args = parser.parse_args(argv)
    try:
        errors = check_tree(args.tree)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"PASS: skills tree {args.tree}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
