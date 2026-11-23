Generate the GSD software factory's skill and agents in this repo. Start from the
v1 factory and make the changes below, nothing else. Keep v1's wording, structure
and contracts wherever a change doesn't touch them.

## Inputs

- v1's `.claude/` (the `factory` skill and 7 agents). Copy it into this repo's
  root from `src/software-factory-claude-code/.claude/` in
  https://github.com/zazencodes/zazencodes-season-3, or from a local checkout of
  that repo.
- `factory/bin/gsd`, already in this repo (copied from software-factory-gsd). Run
  `factory/bin/gsd --help` and read its source: it is the only thing that parses
  `.planning/` or edits `REQUIREMENTS.md`.
- The base branch is `main`. If this repo integrates on another branch (for
  example `development`), use that branch everywhere v1 says `main`: worktree
  creation, `git log`/`git diff` ranges, `git merge-tree`, merges, and the
  approver's description.

## What changes

GSD (`@opengsd/gsd-core`) owns the plan in `.planning/` on the base branch:
`PROJECT.md`, `REQUIREMENTS.md` (checkbox lines like `- [ ] **AUTH-03**: ...`)
and `ROADMAP.md` (phases with `**Requirements**`, `**Depends on**` and
`**Success Criteria**`). The factory builds one requirement per job. A
requirement is done when it is ticked in `REQUIREMENTS.md`. Merge ticks it and
commits that one file; that is the only change the factory makes to
`.planning/`. Job branches never touch it. Plain backlog items without an ID
keep working as in v1.

### `.claude/skills/factory/SKILL.md`

1. Description: add `/factory from-gsd <phase>` to the list of commands.
2. Add a section "Planning comes from GSD" after the part about AGENTS.md,
   explaining the paragraph above, that `/factory from-gsd <phase>` queues a
   phase's requirements one line each with `(after ...)`, that `/factory next`
   skips items whose `(after ...)` requirements aren't ticked, and that
   `factory/bin/gsd` does all parsing and ticking: never edit `REQUIREMENTS.md`
   or parse `ROADMAP.md` by hand.
3. Files list: add `<repo>/.planning/` (GSD's plan, committed on the base
   branch) and `<repo>/factory/bin/gsd` (the GSD bridge).
4. `job.json`: add `"requirement": "AUTH-03"`. It is the requirement ID when the
   feature starts with one (`AUTH-03: ...`), otherwise `null`. Use a GSD-style
   example such as `003-password-reset`.
5. `/factory <feature>`, step 1: if the feature starts with `<ID>:`, check that
   `git show <base>:.planning/REQUIREMENTS.md | grep -F '**<ID>**'` prints a
   line; if not, stop and tell the user to commit `.planning/` on the base branch
   (agents only see what it has). Write `requirement` into `job.json`.
6. Spec step: append ` Requirement: <ID>.` to the spec-writer's prompt when the
   job has one.
7. Merge becomes three steps:
   1. `git merge --no-ff factory/<job-id> -m "Merge factory/<job-id>"`; on
      failure `git merge --abort`, set `needs-human`, tell the user, stop.
   2. If the job has a requirement:
      `factory/bin/gsd tick <ID>` then
      `git commit -m "Mark <ID> complete" -- .planning/REQUIREMENTS.md`. Pass on
      what `tick` prints, and say so when it reports a phase complete. If `tick`
      fails, the job is still merged: tell the user to tick it by hand.
   3. `git worktree remove` and `git branch -d`, as in v1.
   Then `stage: "merged"`. Never push.
8. New command `/factory from-gsd <phase>`:
   1. Preview with `factory/bin/gsd backlog <phase> --dry-run`. On failure pass
      the message on and stop (no `.planning/` → the user runs
      `/gsd-new-project`; a phase GSD started executing → the user finishes it
      with `/gsd-execute-phase`; add `--force` only when the user explicitly
      asks). A warning that GSD planned the phase is fine: the spec-writer reuses
      the plans; pass it on.
   2. Same-phase requirements run in parallel by default. Read them with the
      phase's goal and success criteria and add `--after <ID>=<ID>[,<ID>...]`
      only for clear cases (password reset needs sign-up). Also follow any note
      in the phase about what to queue first.
   3. Run `factory/bin/gsd backlog <phase> [--after ...]`, report what was
      queued, what can start now, any warning, and that `.planning/` must be
      committed before jobs start. Then stop.
9. `/factory next`: run `factory/bin/gsd next`. Exit 0 prints
   `{"line", "feature", "requirement"}`; exit 3 means everything waits on
   unmerged requirements (pass it on, stop); exit 4 means the backlog is empty.
   Claim with one Edit replacing the exact `line` with `- [x] ... → claimed`; if
   the Edit fails, go back to `gsd next`. Then run `/factory <feature>` and
   replace `claimed` with the job id.

### `.claude/agents/spec-writer.md`

1. The prompt may name `Requirement: <ID>`.
2. Reading list, before the code: for a requirement, read `.planning/PROJECT.md`,
   the requirement's line and the Out of Scope table in `REQUIREMENTS.md`, and
   the phase in `ROADMAP.md` whose `**Requirements**` line lists the ID. If the
   phase has `.planning/phases/<NN>-*/<NN>-CONTEXT.md` (from
   `/gsd-discuss-phase`), read it: its `<decisions>` are locked choices and its
   canonical refs are docs to read. Then run
   `cd <worktree> && factory/bin/gsd plans <ID>` and read each plan it lists.
3. Spec header: `> Requirement: <ID> (Phase <N>: <phase name>)` under the
   Feature line, only for a requirement.
4. New section "GSD requirements":
   - The requirement line is what must be true; the first acceptance criterion
     checks it directly.
   - The phase's success criteria this requirement is responsible for become
     acceptance criteria; leave out those of the phase's other requirements.
   - Out of scope names the phase's other requirements a builder might drift
     into, and matching rows of the Out of Scope table.
   - Follow `PROJECT.md`'s constraints and CONTEXT.md's decisions; never turn a
     locked decision into an Assumption or a different choice.
   - Never require changes to `.planning/`.
   - When `gsd plans` lists plans, use them as a head start, not the spec: take
     the files, `read_first` refs, actions, `verify` commands and criteria that
     serve this requirement; check each against the code (the code wins); for a
     plan marked `(executed)`, describe its work in Context and spec only what
     is missing; turn `checkpoint:decision` tasks into Assumptions and drop
     `checkpoint:human-verify`; ignore instructions about commits, SUMMARY.md and
     STATE.md; cite the plans used in Context.

### Other agents

- `builder.md`: never edit anything under `.planning/`; the orchestrator ticks
  the requirement after the merge.
- `reviewer-code.md`: under Commits, any change under `.planning/` is CHANGES.
- `approver.md`: APPROVE also requires that, when the spec names a GSD
  requirement, its line in `.planning/REQUIREMENTS.md` is true of the branch
  (APPROVE ticks it), and that the branch changes nothing under `.planning/`.
- The reviewers for security, UX and UI are unchanged.

## Then

Summarize what you changed in each file and stop. Don't commit, and don't tailor
the reviewers yet: that is a separate step.
