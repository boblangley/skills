# Documents

Read this when the work is prose: documentation, a design, a specification, or instructions written for agents. Prose fails differently from code. It compiles whatever it says, so nothing stops it being wrong, unclear or out of step with the system it describes, and its reader acts on it anyway.

## Read in this order

1. **The contract,** and the standard the document is judged against: its soft claims, a template, a style guide, the pattern of its neighbours.
2. **The document whole,** before any line-level reading. Then write a paraphrase in a few sentences: what it proposes or instructs, and how it says the existing system works. If you cannot write one for a section, that section is a finding. Compare the paraphrase with the task's intent: a wrong paraphrase is a finding too.
3. **What it describes:** the code, the other documents, the skills it refers to.

## What to look for

- **Truth:** each claim about the system matches the system. Read the code or run the command; do not trust the document's own word. A claim about tested behaviour matches its test.
- **Completeness for its reader:** each term is defined or linked, and nothing assumes a prerequisite the reader does not have. Read from where its reader starts, not from where you start.
- **One source:** each contract has one authoritative definition. Other documents link to it or to its generated reference instead of copying it. Published user pages use the generated reference. Two copies of a rule will disagree.
- **Calibration:** each claim is as strong as its evidence. Each caveat names the decision it affects, or it goes.
- **Economy:** cut what the reader does not need. A sentence that changes nothing is a cost every reader pays.
- **Structure:** it follows the template or standard it is held to, and its headings let a reader find the part they need.

## Designs and specifications

A design is reviewed before anything is built on it, when a miss costs least to fix. It is held to the [documentation standard](../../standards/references/documentation.md) as well as to what follows.

- **Its questions are answered.** Check it against its template or the issue: every question it must settle is settled.
- **Check the specification layout** against [designing](../../designing/references/documents.md#specification-definitions), then run the definition's native validator from its module root and confirm that the invalid fixtures produce their asserted errors.
- **Its assumptions are justified.** A claim about behaviour, performance or a constraint that the design rests on has evidence, or is marked as an assumption to test.
- **Its failure modes are named:** what happens on error, under load, at the limits, and with an attacker.
- **It can be built.** An implementer can start without making a design decision of their own: a storage choice, an interface, an error strategy. Each one left open is a finding.
- **Its trade-offs are real.** Where it accepts a compromise as unavoidable, ask whether it is. A finding here proposes the alternative and says what the alternative costs.
- **An interface design names its states and its visual language.** Every state of every view is designed, and a `DESIGN.md` passes `npx @google/design.md lint` with no errors and no contrast warnings ([interface](../../designing/references/interface.md)).

## User documentation

Documentation for users is held to the [user documentation standard](../../standards/references/user-documentation.md), and checked as follows.

- **Walk it as its reader.** Follow a tutorial or a how-to guide in a clean environment, exactly as written. Each step that fails, or that needs knowledge the page does not give, is a finding.
- **Each page has an audience and kind.** Navigation groups Users and Developers, then the four page kinds. The main reader determines where a shared topic lives, with a link from the other audience. A tutorial that lists options, or a how-to guide that stops to explain, is a finding.
- **The reference matches the product.** It is generated from raw specification definitions or public source signatures and doc comments, and covers every public entry affected by the change. Run the drift check; change an input without regenerating and confirm that it fails, then restore the input. Missing and obsolete generated pages are drift too.
- **Published links keep the reader in user documentation and public surfaces.** Inspect the rendered links, including full source-host URLs: any link into a design document is a finding. Page links, fragments, images and downloadable examples resolve in the published output.
- **The interface is shown.** Pages about an interface embed screenshots; pages describing a workflow also embed an animated recording. Run the committed capture scripts affected by the change and compare the output with the page. Instructions and expected results remain readable without the media.
- **Check examples** against their definitions and verify that readers can reach them as the [user documentation standard](../../standards/references/user-documentation.md#published-links) requires.
- **The change brought its pages.** Compare the diff with the documentation: behaviour a user sees or does that changed without its pages changing is a finding.

## Instructions for agents

Skills, briefs, `AGENTS.md` files and templates are followed literally, by readers who cannot ask the author what was meant. A wrong rule repeats in every piece of work that follows it. They are held to the [instructions standard](../../standards/references/instructions.md), and checked as follows.

- **Walk it as its reader.** Take a realistic task and follow the instructions step by step. Find where an agent would stop because nothing says what to do next, guess, or loop.
- **Every rule is reachable.** The description says when the instructions apply, and the agent would actually load them then. A reference says when to read it.
- **No contradiction with other instructions.** Search the other skills and `AGENTS.md` files for the same subject. Two instructions that disagree are a finding, even when this one is right.
- **Each rule earns its place.** Ask what goes wrong without it. A rule that covers a case that never happens costs every reader.
