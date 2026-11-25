# An OpenCode variant of the factory

Can the same factory run on [OpenCode](https://opencode.ai) instead of Claude
Code? Yes. Most of the factory doesn't depend on Claude Code, and the parts that
do have OpenCode equivalents. The variant would be an OpenCode version of
`BUILD_PROMPT.md` that generates OpenCode files, not a second copy of the
factory.

## Works unchanged

- **`factory/bin/gsd`, `factory/bin/dashboard`, `dashboard.html`,
  `backlog.md`, the tests.** They're plain Python and bash.
- **The job model:** `factory/jobs/<id>/`, `job.json`, one worktree and branch
  per job, the ports, the merge-and-tick steps. These are just git and files.
- **GSD itself.** `@opengsd/gsd-core`'s installer lists OpenCode as a target.
  A non-interactive `--opencode` flag isn't confirmed, so run
  `npx @opengsd/gsd-core@latest` and pick OpenCode. The GSD command names in
  the README may differ there.
- **`agent-browser`**, since it's a separate command-line tool.
- **The skill, mostly.** OpenCode reads `.claude/skills/<name>/SKILL.md` as
  well as `.opencode/skills/`, so the orchestrator text loads. It still needs
  the edits below.

## Needs changing

| Claude Code | OpenCode |
|---|---|
| `.claude/agents/*.md` with `tools: Read, Grep, …` and `model: opus` | `.opencode/agents/*.md` with `mode: subagent`, a `permissions:` list (for example, the reviewers can't edit) and `model: anthropic/claude-opus-5-5`. Any provider works, so a reviewer could run on a different model family. |
| Spawn by `subagent_type` | The `subagent` tool, with the agent ID, a description and a prompt |
| Builder named `builder-<job-id>`, resumed with `SendMessage` | The first call returns a `sessionID`. Store it in `job.json` (say `builder_session`) and pass it back to resume. This also lets you resume after the orchestrator session restarts. |
| "Spawn all four reviewers in one message" | Subagents run in the background and return straight away. The orchestrator waits for each `<subagent>` notice and fills in `job.json` as each one lands, as it does now. |
| "The shell returns to the main checkout, so start every command with `cd <worktree> &&`" | The `shell` tool takes a `workdir`. Tell agents to set it to the worktree instead. |
| `/factory …` runs the skill | Add `.opencode/commands/factory.md` whose body loads the `factory` skill with `$ARGUMENTS`. Leave `subagent: false` so the command runs in your session, which must be the orchestrator: subagents can't launch subagents by default. |
| `claude "$(cat BUILD_PROMPT.md)"` in `install.sh` | `opencode run "$(cat OPENCODE_BUILD_PROMPT.md)"` |

## Risks

- **OpenCode versions differ.** The current docs describe the newer format:
  `agents/` folder, `subagent` tool, `permissions` list, `steps`. Older
  versions use `agent/`, a `task` tool, and `permission`/`tools` maps.
  Generate for the version you actually run (`opencode --version`).
- **Reviewers might run one after another on older versions.** One OpenCode
  GitHub issue says several Task calls in one message ran one at a time.
  Results would still be correct, only slower.
- **Not confirmed that the current docs say OpenCode reads `AGENTS.md`.** Older
  versions did, but the factory relies on it, so check it on yours.

## Suggested shape

- Add `OPENCODE_BUILD_PROMPT.md`, written as a list of changes on top of
  `BUILD_PROMPT.md`'s output (the table above).
- Give `install.sh` a `--opencode` flag.
- Add a README section.
- Generate both `.claude/` and `.opencode/` from the same source, so a project
  can run the factory from either tool.

Open choices before building it: which OpenCode version to target, and which
models to use for the orchestrator, builder and reviewers.

## Sources

- [OpenCode docs: Agents](https://opencode.ai/docs/agents.md)
- [OpenCode docs: Commands](https://opencode.ai/docs/commands.md)
- [OpenCode docs: Tools](https://opencode.ai/docs/tools.md)
- [OpenCode docs: Skills](https://opencode.ai/docs/skills)
- [OpenCode issue on sequential subtasks](https://github.com/anomalyco/opencode/issues/14195)
- [OpenCode issue on resuming subagents](https://github.com/anomalyco/opencode/issues/6584)
- [gsd-core README](https://raw.githubusercontent.com/open-gsd/gsd-core/HEAD/README.md)
- [gsd-core install guide](https://deepwiki.com/open-gsd/gsd-core/1.1-getting-started-and-installation)
