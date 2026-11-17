# Contributing to skills

## Reporting an issue

[Open an issue](https://github.com/wyrd-company/skills/issues/new) with the skill or command involved, what you expected, and a small example that reproduces the problem. Propose changes to shared behaviour there before changing the skills.

## Setting up

Use the workspace devcontainer, which provides Python 3.11 or later, [uv](https://docs.astral.sh/uv/) and [Task](https://taskfile.dev/). Task installs the exact Python dependencies recorded in `uv.lock` into `.venv/`:

```sh
task tools
```

## Making a change

Run `task hooks:install` once in a working checkout to enable the repository's Lefthook hooks.

Work on a branch in a worktree; keep the shared checkout clean so it can update by fast-forward. Write Conventional Commits and stage explicit paths. Open a pull request describing the resulting behaviour, the issue it serves, and the checks you ran. Skills follow the [instructions standard](standards/references/instructions.md); independent review follows [review](review/SKILL.md).

## Checking a change

```sh
task check
```

This runs Python lint and formatting checks, Markdown lint, YAML syntax checks, the repository's skills tree check, fixture tests and targeted mutation checks. Markdown lint follows the existing long-line prose and template style: MD009, MD013, MD022, MD036 and MD041 are disabled in `.pymarkdown.json`; `git diff --check` still rejects newly introduced trailing whitespace. The mutation report names the assertion that catches each deliberately broken guard.

To run one part:

```sh
task lint
task test
task test -- -k validation_failures
task test:mutations
task format
```

`task format` rewrites Python and Markdown where their configured rules support a fix. YAML is checked for syntax and kept in its authored layout. Review the diff after formatting.

## Checking a skills tree

```sh
task skills:check
task skills:check TREE=/absolute/path/to/skills
```

A tree contains immediate skill folders with `SKILL.md`. Repository tooling and root files are excluded. In each skill, `SKILL.md` and `README.md` are entry points. Every other file must have a direct link from another Markdown file in the same skill; a directory link, self-link, or link from a different skill does not count. Links from README tables count.

The check names every broken relative link (including Markdown heading fragments) and orphan file. It reads inline links, reference links, images and HTML `href`/`src`, ignoring code and comments. Relative links must stay within the tree. URLs, absolute paths and `~/` paths refer to external resources and are not checked. `{slot}` destinations in `assets/` templates are checked after their user fills them in. Source symlinks are refused.

## Building overlays: the interface for skills sync

The caller supplies the base, output and overlays. The build discovers no workspace or project paths:

```sh
task --dir /absolute/path/to/base build -- \
  --base /absolute/path/to/base \
  --output /absolute/path/to/generated/skills \
  --overlay /absolute/path/to/workspace-overlay \
  --project /absolute/path/to/project /absolute/path/to/project/skills
```

`--overlay FOLDER` and `--project PATH FOLDER` may each repeat; they are applied in argument order after the base. For workspace-then-project precedence, pass the workspace overlay first. `PATH` is the absolute project path used as the heading, and may contain spaces when quoted. All source folders must exist; omit missing optional overlays in the caller. An empty overlay folder is valid. All filesystem arguments are relative to the Taskfile directory unless absolute, so callers should pass absolute paths.

Overlay folders mirror the base: `<skill>/SKILL.md`, `<skill>/references/...`, and other files within the skill. Top-level dotfiles and `README.md` are metadata and are ignored. Every other top-level overlay entry must be a skill folder. A new skill supplies its own `SKILL.md`.

- An existing Markdown file is appended with a blank-line separator, including files introduced by an earlier overlay. An appended `SKILL.md` contains body text, without YAML front matter, so the base description stays intact.
- A new file or skill is added. A collision on a non-Markdown file fails, even when the bytes are identical. New non-Markdown files retain their permissions.
- Every project Markdown contribution begins with `## Project: PATH`. For a new file with YAML front matter, the heading follows the front matter so a new skill's description remains readable.

The output path must be separate from every input tree and must initially be absent. On success it is a **managed symlink** to a sibling directory named `.skills.build-*` (using the output basename). Consumers should keep links pointed through the output path, rather than resolving its generation directory. The sibling `.skills.lock` serializes builds; `.skills-build.json` inside a generation identifies its owner. These files are managed build state.

The build checks the staged merged tree before switching the symlink atomically. A merge or validation failure exits nonzero, prints the failing paths to stderr, removes the failed staging directory, and leaves the previous output intact. Success prints `PASS: built skills tree ...` only after publication and removes the previous generation. An existing ordinary directory or unmanaged symlink is refused. A failure to remove an obsolete generation is reported as a warning after publication.

The command works on Linux and macOS (POSIX symlinks and file locks). This repository provides the merge/check operation; workspace discovery, the `skills sync` command and links for Claude Code, Codex and Pi belong to the caller.
