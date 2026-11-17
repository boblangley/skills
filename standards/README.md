# standards

The rules our work is held to. The agent doing the work follows them, and the agent reviewing it checks them, so both read the same text instead of keeping their own copies. The skill is not a process: `executing` and `review` say how to do and check the work. A repository's own `AGENTS.md` and docs win over these standards for that repository.

| File | What it is for |
|---|---|
| [SKILL.md](SKILL.md) | Which standard covers the work, and what to do when one is missing |
| [references/documentation.md](references/documentation.md) | How design documents are worded |
| [references/user-documentation.md](references/user-documentation.md) | Documentation for users and developers: audience and page kind, generated reference, published links and reproducible interface captures |
| [references/instructions.md](references/instructions.md) | How skills, `AGENTS.md` files and briefs to delegates are written |
| [references/interface.md](references/interface.md) | How an interface a person uses is built: usability, accessibility, states, layout, colour, type, motion, copy, platforms and terminal tools |
| [references/stack.md](references/stack.md) | What websites and web applications are built with, and the template a site starts from |
| [references/repository.md](references/repository.md) | What every repository holds: its README, `AGENTS.md`, `CONTRIBUTING.md`, license, automation with Task and Lefthook, configuration and layout, and how a fork is treated |
| [assets/repository/](assets/repository/) | Templates for those files |
| [references/workspace.md](references/workspace.md) | How the workspace environment is configured, and fitted to one workspace's needs |

## Sources

The standards are written in our own words. These works shaped them; nothing is copied from them. Each link is to the commit we read.

| Source | License | What we drew on |
|---|---|---|
| [dembrandt/dembrandt-skills](https://github.com/dembrandt/dembrandt-skills/tree/8f78f13f74a2356326d0c3c21bc63e5624e6a457/skills) | MIT | Interface: most of the concrete rules. Feedback and loading, states, overlays, forms and errors, status colours, information architecture and navigation, layout, density and alignment, tables, type scale, colour palettes and themes, elevation, responsive paradigms, accessibility thresholds and web performance. |
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/writing-for-agents): `writing-for-agents` | MIT | Instructions: the description as the pointer that decides when material is read, one trigger per case, what every case needs in `SKILL.md` and the rest behind pointers, a topic kept together, criteria that are checkable and exhaustive, saying what to do rather than what not to, leaving to the environment what it says, and cutting sentences that change nothing. |
| [obra/superpowers](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7/skills): `writing-skills`, `subagent-driven-development` | MIT | Instructions: fitting the form of a rule to the failure, exceptions as their own conditions, no workflow in a description; and for briefs, one task with no history, files named rather than pasted, a fixed shape for what comes back, when to stop, and no delegating onward. |
| [anthropics/skills](https://github.com/anthropics/skills/tree/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator): `skill-creator` | Apache-2.0 | Instructions: reasons rather than capitals, `SKILL.md` under 500 lines, and scripts for code agents keep rewriting. |
| [Anthropic's skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Published guide | Instructions: a default rather than a menu, and references one level deep. |
| [cursor/plugins](https://github.com/cursor/plugins/tree/3dbd22ff12742fb28c9700b9760baa29ed41dc13/pstack/skills/principle-encode-lessons-in-structure): `pstack`'s `principle-encode-lessons-in-structure` | MIT | Instructions: a correction given twice becomes a check. |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/a90602e9f6fed600d6d9b18cf78275d66cac7a6c/skill) | Apache-2.0 | Interface: the defaults of generated interfaces to avoid, familiarity on work surfaces, iOS and Android conventions, copy and localisation, hardening against extreme content, and checking the rendered result. |
| [emilkowalski/skills](https://github.com/emilkowalski/skills/tree/5206a950b715e0cabe7043ea0b2304332b91494e/skills/animate) | MIT | Interface: motion. Its purpose, duration and easing, no animation on frequent actions, and interruption. |
| [Leonxlnx/cook](https://github.com/Leonxlnx/cook/tree/b23cac6fd9439dfddcab61b14808e7bf72549b46) | MIT | Interface, proving it: shots at fixed framing rendered beside their references, a score for each dimension, critics who see only the shots and the rubric, and every number marked as measured or judged. |
| [benjitaylor/skills](https://github.com/benjitaylor/skills/tree/299140fafd08df55a9c234e610c3f64af3f45531/stageshow): `stageshow` | MIT | Interface, proving it: a handover that says what was not checked. |
| [Diátaxis](https://github.com/evildmp/diataxis-documentation-framework/tree/957c09ca40b4a1edc23874f713e01937d50d54d5/source), by Daniele Procida | CC-BY-SA-4.0 | User documentation: the four kinds of page and the reader each serves; a tutorial as a lesson on one reliable path with visible results and little explanation; how-to guides titled by their goal; reference that describes and follows the structure of the machinery; explanation bounded by its subject. |
| [wyrd-company/deck](https://github.com/wyrd-company/deck/tree/2ed4796f22c8bac154239b0e5134ab3b5d75d002/docs): `user/`, `AGENTS.md`, `demo/` | Apache-2.0 | User documentation: published pages link into design documents and examples in design folders, the failures the standard prevents; interface recordings are reproduced from committed scripts and inputs. |
| [wyrd-company/t3code-client](https://github.com/wyrd-company/t3code-client/tree/1fd2f4da1964bd41b6b6155a819fb1bac6f6822c): `Taskfile.yml`, `packages/t3code-lib/Taskfile.yml`, `packages/t3code-lib/scripts/reference.mjs`, `docs/user/t3c/library-*.md`, `docs/specifications/cli-surface.json`, `packages/t3code-cli/scripts/build.mjs` | MIT | User documentation: public library reference generated from exported signatures and source doc comments; missing JSDoc rejected for functions and class members; generated output compared by a check included in the repository's checks. The native CLI specification is copied into the build as the command surface. |
| [google-labs-code/design.md](https://github.com/google-labs-code/design.md) | Apache-2.0 | Interface: the `DESIGN.md` linter as one of the checks. |

The documentation standard comes from our earlier `authoring-specifications` skill, the repository standard from our earlier drafts of it and the files in our repositories, the workspace standard from our own workspace repositories, and the stack from our own templates and choices. None has an outside source.
