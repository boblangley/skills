"""Check skill-local links and support-file references in a skills tree."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import sys
import tempfile
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
                if not target.is_relative_to(root):
                    errors.append(label + " (outside skills tree)")
                    continue
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


@dataclass(frozen=True)
class Overlay:
    folder: Path
    project: str | None = None


class OrderedOverlay(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        overlays = list(getattr(namespace, self.dest, None) or [])
        if option_string == "--project":
            project, folder = values
            if not Path(project).is_absolute() or "\n" in project or "\r" in project:
                raise argparse.ArgumentError(self, "project path must be absolute and on one line")
            overlays.append(Overlay(Path(folder), project))
        else:
            overlays.append(Overlay(Path(values)))
        setattr(namespace, self.dest, overlays)


def project_text(text: str, project: str) -> str:
    heading = f"## Project: {project}\n\n"
    if text.startswith("---\n"):
        # Keep a new skill's YAML description at the beginning of SKILL.md.
        match = re.search(r"^---[ \t]*$", text[4:], re.MULTILINE)
        if match:
            end = 4 + match.end()
            return text[:end] + "\n\n" + heading + text[end:].lstrip("\n")
    return heading + text


def merge_overlay(stage: Path, overlay: Overlay) -> None:
    for skill in sorted(overlay.folder.iterdir()):
        if skill.name.startswith(".") or skill.name in {"README.md", "AGENTS.md"}:
            continue
        if skill.is_symlink() or not skill.is_dir():
            raise ValueError(f"{skill}: expected a skill folder, not a symlink or file")
        for source in sorted(skill.rglob("*")):
            if source.is_symlink():
                raise ValueError(f"{source}: symlinks are not supported")
            target = stage / source.relative_to(overlay.folder)
            if source.is_dir():
                if target.exists() and not target.is_dir():
                    raise ValueError(f"{source}: directory conflicts with a file")
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not source.is_file():
                raise ValueError(f"{source}: expected a regular file")
            if target.is_dir():
                raise ValueError(f"{source}: file conflicts with a directory")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and source.suffix.lower() != ".md":
                raise ValueError(f"{source}: refusing append to non-Markdown file")
            if source.suffix.lower() == ".md":
                text = source.read_text(encoding="utf-8")
                if target.exists() and source.name == "SKILL.md" and text.startswith("---\n"):
                    raise ValueError(f"{source}: appended SKILL.md must not contain front matter")
                if overlay.project:
                    text = project_text(text, overlay.project)
                if target.exists():
                    text = target.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + text
                target.write_text(text, encoding="utf-8")
            else:
                shutil.copy2(source, target)
        if not (stage / skill.name / "SKILL.md").is_file():
            raise ValueError(f"{skill}: a new skill must include SKILL.md")


def previous_build(output: Path) -> Path | None:
    if not output.is_symlink():
        if output.exists():
            raise ValueError(f"{output}: output must be absent or a symlink managed by this build")
        return None
    previous = output.resolve(strict=True)
    marker = previous / ".skills-build.json"
    if (
        previous.parent != output.parent
        or not previous.name.startswith(f".{output.name}.build-")
        or not marker.is_file()
        or json.loads(marker.read_text(encoding="utf-8")).get("output") != str(output)
    ):
        raise ValueError(f"{output}: refusing to replace an unmanaged symlink")
    return previous


def build_tree(base: Path, overlays: list[Overlay], output: Path) -> None:
    base = base.resolve(strict=True)
    overlays = [Overlay(item.folder.resolve(strict=True), item.project) for item in overlays]
    # Resolve the parent, but preserve the leaf: it is the published symlink.
    output = output.parent.resolve() / output.name
    for source in [base, *(item.folder for item in overlays)]:
        if not source.is_dir():
            raise ValueError(f"{source}: expected a directory")
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError(f"{output}: output must be separate from every input tree")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Serialize publishers. Keep the lock file so all processes lock the same inode.
    with (output.parent / f".{output.name}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = previous_build(output)
        stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.build-", dir=output.parent))
        link = stage.with_name(stage.name + ".link")
        published = False
        try:
            for skill in skill_folders(base):
                for source in [skill, *skill.rglob("*")]:
                    if source.is_symlink():
                        raise ValueError(f"{source}: symlinks are not supported")
                shutil.copytree(skill, stage / skill.name)
            for overlay in overlays:
                merge_overlay(stage, overlay)
            errors = check_tree(stage)
            if errors:
                raise ValueError("built tree failed validation:\n" + "\n".join(errors))
            marker = {"output": str(output)}
            (stage / ".skills-build.json").write_text(json.dumps(marker) + "\n", encoding="utf-8")
            link.symlink_to(stage.name, target_is_directory=True)
            os.replace(link, output)
            published = True
        finally:
            link.unlink(missing_ok=True)
            if not published:
                shutil.rmtree(stage)
        if previous:
            try:
                shutil.rmtree(previous)
            except OSError as exc:
                print(
                    f"Warning: published build; could not remove {previous}: {exc}", file=sys.stderr
                )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check relative links and orphan files")
    check.add_argument("tree", type=Path)
    build = commands.add_parser("build", help="Merge ordered overlays and publish a checked tree")
    build.add_argument("--base", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--overlay", dest="overlays", action=OrderedOverlay, metavar="FOLDER")
    build.add_argument(
        "--project", dest="overlays", action=OrderedOverlay, nargs=2, metavar=("PATH", "FOLDER")
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            build_tree(args.base, args.overlays or [], args.output)
            print(f"PASS: built skills tree {args.output}")
            return 0
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
