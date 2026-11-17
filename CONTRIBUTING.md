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

The caller supplies the base, output and overlays. The build discovers no workspace or project paths.

### Calling the build

Before calling it:

- Install Task, uv and Python 3.11 or later in the caller's environment.
- Update the skills clone to a commit containing this `Taskfile.yml`, `scripts/skills_tree.py`, `pyproject.toml` and `uv.lock`. The checkout passed to `task --dir` supplies the builder; an older checkout without these files cannot build. In the example below, that checkout is also the input `--base` tree. A different `--base` changes the input, not the builder version.
- Keep the builder checkout writable. Every call runs `uv sync --frozen` there before building. It maintains `.venv/` in that checkout and installs the locked development group (Ruff and PyMarkdown) as well as the build dependencies. `.venv/` is ignored, so the clone remains clean for `git status --porcelain` and fast-forward updates.
- Provide network access on the first build and after `uv.lock` changes whenever a locked package is missing from the uv cache. Prewarm with `task --dir /absolute/path/to/base tools` while online for later offline runs. An offline first build with an empty cache fails before producing output; dependencies are not bundled with the clone.
- Choose a writable, dedicated output parent outside every input tree. All overlay folders must exist; omit missing optional overlays in the caller. An empty overlay folder is valid.

```sh
task --dir /absolute/path/to/base build -- \
  --base /absolute/path/to/base \
  --output /absolute/path/to/generated/skills \
  --overlay /absolute/path/to/workspace-overlay \
  --project /absolute/path/to/project /absolute/path/to/project/skills
```

`--overlay FOLDER` and `--project PATH FOLDER` may each repeat; they are applied in argument order after the base. For workspace-then-project precedence, pass the workspace overlay first. `PATH` is the absolute project path used as the heading, and may contain spaces when quoted. All filesystem arguments are relative to the Taskfile directory unless absolute, so callers should pass absolute paths.

### Overlay content

Overlay folders mirror the base: `<skill>/SKILL.md`, `<skill>/references/...`, and other files within the skill. Top-level dotfiles, `README.md` and `AGENTS.md` are metadata and are ignored. Every other top-level overlay entry must be a skill folder. A new skill supplies its own `SKILL.md`.

- An existing Markdown file is appended with a blank-line separator, including files introduced by an earlier overlay. An appended `SKILL.md` contains body text, without YAML front matter, so the base description stays intact.
- A new file or skill is added. A collision on a non-Markdown file fails, even when the bytes are identical. New non-Markdown files retain their permissions.
- Every project Markdown contribution begins with `## Project: PATH`. For a new file with YAML front matter, the heading follows the front matter so a new skill's description remains readable.

All included base and overlay content is subject to the [tree check](#checking-a-skills-tree): a source symlink within a skill fails the build, and an overlay support file that no Markdown file in that skill links to is an orphan and fails the build. Fix the source links/content before retrying.

### Output lifecycle

OUTPUT must be **absent before the first build; afterwards it is the managed symlink** reused by every later build. The parent directory is created if missing. Reserve that parent for this output: with `/absolute/path/to/generated/skills` it holds `.skills.lock`, `.skills.build-*` generation directories, and temporary `.skills.build-*.link` symlinks. Each generation carries `.skills-build.json` naming its absolute output owner. Keep the parent and output name stable so those ownership records stay valid.

The output path must be separate from every input tree. Inputs within this output's `.skills.build-*` generation directories are refused before cleanup, because those directories are managed build state. An existing ordinary directory or unmanaged symlink is refused. In particular, today's `~/.claude/skills` directory of links cannot be OUTPUT: choose a new generated path, successfully build it, then migrate the agent links to point through that path while preserving any existing installation data. Consumers should keep links pointed through OUTPUT rather than resolving its generation directory.

A build holds the sibling lock, stages and checks the merged tree, then switches the output symlink atomically. Merge or validation failure exits nonzero, prints the failing paths to stderr, removes the failed stage and leaves the previous output intact. Success prints `PASS: built skills tree ...` only after publication and removes the previous generation. A published generation's root has mode 0755. Failure to remove an obsolete generation is reported as a warning after publication.

### Recovery

- A missing generation behind OUTPUT is rebuilt automatically when the link names a sibling `.skills.build-*` for that output. The dangling output link is replaced only after a new tree passes validation. An unrelated dangling link is refused.
- After an interrupted process, rerun the same build command. While holding the lock, it removes owned stale generations, leftover `.skills.build-*.link` symlinks and empty unmarked staging directories, keeping the current generation. Nonempty directories without a valid ownership marker and foreign/symlinked generation directories are preserved.
- If an output is refused because it is an ordinary directory, has a corrupt/mismatched ownership marker, or points elsewhere, choose a fresh generated path and migrate consumer links only after it builds successfully. To restore the original output path instead, stop all builders, retain the whole dedicated output parent as a backup, then rerun the original command to recreate it. Inspect preserved unmarked leftovers before removing them; they may contain data the builder does not own.

Leave the lock file in place while any builder may run: removing it can give concurrent processes different locks. Builders and consumers should run as users with access to the output parent and source files.

The command requires POSIX symlinks and file locks (Linux/macOS). This repository provides the merge/check operation; workspace discovery, the `skills sync` command and links for Claude Code, Codex and Pi belong to the caller.
