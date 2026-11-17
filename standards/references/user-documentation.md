# User documentation

Read this when writing or reviewing documentation for the people who use what we build: a product, an application, a command line, an API or a library. The README is the front door to it, and is in the [repository standard](repository.md#readmemd). Text inside the interface, such as `--help`, empty states and error messages, is in the [interface standard](interface.md). Design documents, written for whoever builds the thing, are in [documentation](documentation.md).

A reader opens the documentation with one need: to learn, to get a task done, to look up a fact, or to understand. Each page meets one of them, and the documentation as a whole meets all four.

## Four kinds of page

| Kind | Its reader | It holds | Folder |
|---|---|---|---|
| Tutorial | A newcomer learning by doing | A lesson that leads the reader to build something that works | `docs/tutorials/` |
| How-to guide | A user with a task to finish | The steps that reach one goal | `docs/how-to/` |
| Reference | A user looking up a fact while working | A complete description of the machinery: every command, option, field, endpoint and error | `docs/reference/` |
| Explanation | A user stepping back to understand | Why it works the way it does, and how its parts fit together | `docs/explanation/` |

- **A page is one kind.** When a tutorial needs a reason, it says it in a sentence and links to the explanation. When a how-to guide needs the full list of options, it links to the reference.
- **`docs/README.md` is the index.** It lists the pages under the four kinds, and the README links to it.
- **Each folder holds only its kind.** Design documents share `docs/` in the folders [designing](../../designing/references/documents.md#which-document) gives, and stay out of these four.

## Tutorials

- **The reader succeeds.** Every step works as written in a clean environment, and shows a result the reader can see. Walk it in one before review, as you do the README's quickstart.
- **It opens with what the reader will build,** and closes with what they built and where to go next.
- **One path.** No options, alternatives or branches the lesson does not need.
- **Doing, not explaining.** Each step says what to do and what to notice in the result. A reason gets one sentence and a link to the explanation.
- **The voice of a teacher beside the learner:** "we" and "now", with the expected output after each step.

## How-to guides

- **The title is the goal,** as the reader would search for it: "Rotate an API key", "Deploy behind a proxy".
- **It starts where the reader is.** It assumes they know the product, and lists only the prerequisites that are not obvious.
- **The steps are actions in order,** each with its command, input or control. It branches only where readers' situations really differ, and says which branch applies to whom.
- **It ends when the goal is reached,** with how to check that it was.

## Reference

- **Generated from the source of truth.** The API reference comes from the specification, such as OpenAPI or JSON Schema. The command-line reference comes from the command's definition, the same source as its `--help`. The configuration reference comes from its schema, and a library's from its doc comments. Hand-written prose goes around what is generated, never in place of it.
- **The check catches drift.** A task regenerates the reference, and `check` fails when the committed reference differs from what it generates.
- **Its structure follows the product's:** a page for each command, endpoint, resource or module, in the same order and with the same names.
- **Complete and plain.** Every entry gives its name, type, default, the values it accepts, the errors it raises, and an example. It describes; it does not instruct or recommend.
- **The version that added an entry** is marked on the entry when the product has users on more than one version.

## Explanation

- **It answers why.** The concepts, the model the user works with, the reasons for the design, and the trade-offs that reach the user.
- **It is written for the user,** in the product's terms. A design document is written for the builder. Explanation links to a decision record only when the reader gains from the whole trade-off.
- **It is bounded by its topic.** A page explains one subject, titled as that subject: "How sync resolves conflicts".

## Writing

- **The glossary's words.** Use each term from `docs/terms/` with its one meaning, and the same name the interface shows.
- **Address the reader** in the present tense and the active voice: "Run `task check`", not "the user should run `task check`". A tutorial says "we", as above.
- **Describe the current version.** No "new", "now" or "previously" in the prose. The release history is in `CHANGELOG.md`.
- **Commands and code in fenced blocks,** with a language tag. A block the reader copies holds only what they type, with no prompt; its output follows in a block of its own.
- **Placeholders are visible:** `<api-key>`, with a sentence saying what goes there.
- **Examples hold.** Every command, request and snippet runs or validates as written, against the version the documentation describes.
- **Screenshots and recordings are regenerated** by a script committed beside them, as the README's demo is. Nothing the reader needs is only in an image: each image has alternative text, and a step shown in a screenshot is also written out.
- **Headings in order,** one top-level heading per page, and links between pages relative, so they work wherever the documentation is read. `check` finds broken links.

## Keeping it true

- **A change ships with its documentation.** A pull request that changes what a user sees or does updates the pages it affects, and review checks it.
- **The documentation lives with what it describes:** a component's in its repository, and pages spanning several components in the product repository, as [designing](../../designing/references/documents.md#where-it-goes) places design documents.
- **What renders it is chosen for each product.** The source is the pages in `docs/`, whatever publishes them.
