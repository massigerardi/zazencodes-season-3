---
name: factory
description: Run the software factory. Use when the user types /factory <feature>, /factory from-gsd <phase>, /factory next, /factory approve <job-id>, or /factory rework <job-id> <note>. The session that runs it becomes the orchestrator of the spec → build → review → approve loop.
---

# Factory

You are the orchestrator for one job. You run the loop below, spawn every agent,
and are the only writer of your job's `job.json`. You never write code, specs,
reviews or decisions yourself. Agents do the work and each writes one file; you
move the job along and keep `job.json` current.

## The loop

```
feature → spec-writer → builder → [security, ux, ui, code] → WAIT FOR ALL
                           ▲                                      │
                           └──── any CHANGES: resume builder ◄────┤
                                                                  ▼ all PASS
                                     merge to main ◄─ APPROVE ─ approver ─ ESCALATE → needs-human
```

| Step         | Agent (`subagent_type`) | Writes                                      |
| ------------ | ----------------------- | ------------------------------------------- |
| spec         | `spec-writer`           | `spec.md`                                   |
| build        | `builder`               | `build.md` + commits on `factory/<job-id>`  |
| review       | `reviewer-security`     | `round-N/review-security.md`                |
|              | `reviewer-ux`           | `round-N/review-ux.md`                      |
|              | `reviewer-ui`           | `round-N/review-ui.md`                      |
|              | `reviewer-code`         | `round-N/review-code.md`                    |
| approve      | `approver`              | `decision.md`                               |

`MAX_RESUMES = 2`: after round 1 the builder can be resumed at most twice, so a
run has at most 3 review rounds. To change the factory, edit this file and the
agent files in `.claude/agents/`.

Every agent reads `AGENTS.md` (or `CLAUDE.md`) for the repo's setup, dev server,
validation commands and conventions. Nothing repo-specific lives in these files.

## Planning comes from GSD

GSD (`@opengsd/gsd-core`) owns the plan, in `.planning/`
on `main`: `PROJECT.md`, `REQUIREMENTS.md` (checkbox requirements with IDs like
`AUTH-03`) and `ROADMAP.md` (phases, each listing its requirement IDs, what it
depends on and its success criteria). The factory builds it, one requirement per
job.

- `/factory from-gsd <phase>` queues a phase's requirements in the backlog, one
  line each, with `(after ...)` for the requirements they wait on.
- A requirement is **done** when it is ticked in `.planning/REQUIREMENTS.md`.
  `/factory next` skips items whose `(after ...)` requirements aren't done.
- **Merge** ticks the job's requirement and commits that one file. That is the
  only change the factory ever makes to `.planning/`. Job branches never touch it.
- `factory/bin/gsd` does all the parsing and ticking. Never edit
  `REQUIREMENTS.md` or parse `ROADMAP.md` yourself.

Items without a requirement ID still work: they are plain features, as before.

## Parallel jobs

Every job runs in its own git worktree on its own branch, so several jobs can run
at once, one per Claude session. To run three features, open three sessions in
this repo and start `/factory` in each. Your session orchestrates only the job it
started or was handed.

- Your session stays in the main checkout. Agents work in the job's worktree.
  The main checkout is the user's, and it may be dirty or on another branch.
  Only **Merge** touches it.
- Job state lives in `factory/jobs/<job-id>/` in the main checkout, never in a
  worktree. Each job has its own `job.json`, so sessions never write the same
  file.
- Each job gets its own dev server ports and agent-browser sessions (see
  **Prompts**), so reviewers of different jobs never see each other's pages.

## Files

`<repo>` is the main checkout (`git rev-parse --show-toplevel` from your
session) and `<name>` is its folder name. `factory/jobs/` is gitignored runtime
state that never lands in a commit.

```
<repo>/.planning/                              GSD's plan, committed on main (GSD writes it)
<repo>/factory/bin/gsd                         the GSD bridge: backlog, next, tick
<repo>/factory/backlog.md                      queue for /factory next
<repo>/factory/jobs/<job-id>/job.json          the job's state (you write it, the dashboard reads it)
<repo>/factory/jobs/<job-id>/spec.md
<repo>/factory/jobs/<job-id>/build.md
<repo>/factory/jobs/<job-id>/rework-<k>.md     written by you, from /factory rework
<repo>/factory/jobs/<job-id>/round-<N>/review-{security,ux,ui,code}.md
<repo>/factory/jobs/<job-id>/decision.md
<repo>/../<name>-factory/<job-id>/             the job's worktree, on factory/<job-id>
```

### job.json

```json
{ "id": "003-password-reset", "feature": "AUTH-03: User can reset a forgotten password via an emailed link",
  "requirement": "AUTH-03",
  "branch": "factory/003-password-reset",
  "worktree": "/Users/you/code/my-app-factory/003-password-reset",
  "stage": "review", "round": 2,
  "reviews": { "security": "CHANGES", "ux": "PASS", "ui": "pending", "code": "PASS" } }
```

- `stage` is one of `spec`, `build`, `review`, `approve`, `merged`,
  `needs-human`. Worktree setup counts as `spec`.
- `round` is the current review round (0 until the first round starts).
- `reviews` holds the current round only. Each value is `pending`, `PASS` or
  `CHANGES`. Earlier rounds live in their `round-<N>/` folders, which the
  dashboard reads directly.
- `requirement` is the GSD requirement ID when the feature starts with one
  (`AUTH-03: ...`), otherwise `null`.
- Rewrite the whole file on every change. `worktree` is always an absolute path.

### Prompts

Every agent prompt starts with the job's absolute paths:
`Job folder: <repo>/factory/jobs/<job-id>/. Worktree: <worktree>. Branch: factory/<job-id>.`
Below, `<paths>` stands for that sentence.

Agents that open pages also get a port. With `n` the job number (`003` → 3),
the builder gets `5100 + 10n`, `reviewer-ux` gets `5101 + 10n` and `reviewer-ui`
gets `5102 + 10n`, appended as ` Port: <port>.`

## /factory <feature>

1. **Create the job.** If the feature starts with a requirement ID and a colon
   (`AUTH-03: ...`), that is the job's requirement. Check that it is committed:
   `git show main:.planning/REQUIREMENTS.md | grep -F '**<ID>**'` must print a
   line. If it doesn't, stop and tell the user to commit `.planning/` on `main`
   (agents only see what `main` has). Then `mkdir -p factory/jobs`, and pick the next 3-digit number
   after the highest numbered folder in `factory/jobs/` (`001` if there are
   none) and a 2–4 word kebab-case slug of the feature: `004-blog-reading-time`.
   Claim it with `mkdir factory/jobs/<job-id>` (no `-p`). If that fails because
   another session took the number, pick the next number and try again.
   The worktree path is `$(cd .. && pwd)/$(basename "$PWD")-factory/<job-id>`,
   run from `<repo>`. Write `job.json` with that `worktree`, the `requirement`
   (or `null`), `stage: "spec"`, `round: 0` and all reviews `pending`.
2. **Worktree.** Create the branch and its worktree from `main`:
   ```bash
   git worktree add -b factory/<job-id> <worktree> main
   ```
   Then, in the worktree, run the setup AGENTS.md gives for a fresh checkout
   (installing dependencies, for example). If any of it fails, stop and tell
   the user.
3. **Spec.** Spawn `spec-writer` with the prompt
   `<paths> Feature: <feature, verbatim>`, followed by ` Requirement: <ID>.`
   when the job has one.
   Wait for it to finish, then check that `spec.md` exists.
4. **Build.** Set `stage: "build"`. Spawn `builder` **with the name
   `builder-<job-id>`** and the prompt `<paths> Build round 1. Port: <port>.`
   Wait for it to finish, then go to **Build check**.

### Build check

Read the first line of `build.md`.

- `STATUS: READY`: start the next review round.
- `STATUS: BLOCKED`: go to **Needs human**.

### Review round N

1. Set `stage: "review"`, `round: N` and all four reviews to `pending`. Create
   `factory/jobs/<job-id>/round-<N>/`.
2. Spawn all four reviewers **in one message**, so they run in parallel. Each
   gets the prompt `<paths> Review round N.`, plus its port for `reviewer-ux`
   and `reviewer-ui`.
3. **WAIT FOR ALL.** Each time a reviewer finishes, read the first line of its
   file (`VERDICT: PASS` or `VERDICT: CHANGES`) and write that verdict to
   `job.json` straight away, so the dashboard chips fill in as they land. The
   round is done only when all four `review-*.md` files exist in `round-<N>/`.
   Never resume the builder mid-round. If a reviewer finishes without writing
   its file, or writes a first line that isn't a verdict, stop and tell the user.
4. Decide:
   - **All PASS**: go to **Approve**.
   - **Any CHANGES, resumes left**: set `stage: "build"`, then resume the same
     builder with `SendMessage` to `builder-<job-id>`:
     `Round N reviews are in factory/jobs/<job-id>/round-<N>/. Address every review with VERDICT: CHANGES, commit, and update build.md for round N+1.`
     Wait for it to finish, then go to **Build check**.
   - **Any CHANGES, no resumes left**: write `decision.md` yourself, reading
     `ESCALATE`, then a blank line, then
     `Review rounds exhausted. Outstanding CHANGES in round-<N>/ from: <reviewers>.`
     Go to **Needs human**.

### Approve

Set `stage: "approve"`. Spawn `approver` with the prompt `<paths> Final round: N.`
When it finishes, read the first line of `decision.md`:

- `APPROVE`: go to **Merge**.
- `ESCALATE`: go to **Needs human**.

### Merge

The merge happens in the main checkout, so it must be clean and on `main`:
`git status --porcelain -- . ':!factory/backlog.md'` prints nothing and
`git branch --show-current` prints `main`. `factory/backlog.md` is exempt: every
`/factory next` edits it, and job branches never touch it, so a dirty backlog
cannot conflict with the merge. If not, set `stage: "needs-human"` and tell the
user the job is approved but the main checkout is busy; they run
`/factory approve <job-id>` once it is clean. Otherwise:

1. Merge:
   ```bash
   git merge --no-ff factory/<job-id> -m "Merge factory/<job-id>"
   ```
   If it fails, run `git merge --abort` (when a merge is in progress), set
   `stage: "needs-human"` and tell the user why. Stop.
2. If the job has a requirement, tick it:
   ```bash
   factory/bin/gsd tick <ID>
   git commit -m "Mark <ID> complete" -- .planning/REQUIREMENTS.md
   ```
   Pass on whatever `tick` prints. When it says a phase is complete, tell the
   user that every requirement of that phase is merged. If `tick` fails, the job
   is still merged: tell the user to tick `<ID>` by hand.
3. Clean up:
   ```bash
   git worktree remove <worktree>
   git branch -d factory/<job-id>
   ```
   If removing the worktree fails, the job is still merged: tell the user what
   `git worktree remove` printed.

Set `stage: "merged"`. Never push.

### Needs human

Set `stage: "needs-human"`. The branch and its worktree stay for the human to
inspect. Tell the user which job is waiting, give the worktree path, and quote
`decision.md` (or the BLOCKED reason from `build.md`).

## /factory from-gsd <phase>

Queue a ROADMAP phase in `factory/backlog.md`.

1. Preview it: `factory/bin/gsd backlog <phase> --dry-run`. It prints one line
   per unticked requirement of the phase, already waiting on the unticked
   requirements of the phases this one depends on. If it fails, pass its message
   on and stop. No `.planning/`: the user runs `/gsd-new-project` first. A phase
   GSD has started executing: the user finishes it with `/gsd-execute-phase`;
   add `--force` to both runs only when the user explicitly asks for it.
   If it warns that GSD has planned the phase, keep going: the spec-writer
   reuses those plans. Pass the warning on in step 3.
2. Requirements of one phase run in parallel by default. Read them, with the
   phase's goal and success criteria in `.planning/ROADMAP.md`, and look for one
   that can't be built until another in the same phase is merged (password reset
   needs sign-up to exist). Add only clear cases, each as
   `--after <ID>=<ID>[,<ID>...]`.
3. Queue it: `factory/bin/gsd backlog <phase> [--after ...]`. Tell the user what
   was queued, which items can start now, any warning it printed, and that
   `.planning/` (plans included) must be committed on `main` before jobs start.
   Then stop: queuing doesn't start a job.

## /factory next

1. Run `factory/bin/gsd next`.
   - Exit 0: it prints `{"line", "feature", "requirement"}` for the first item
     that is ready.
   - Exit 3: every unchecked item waits on unmerged requirements. Pass on what
     it printed and stop.
   - Exit 4: nothing is left. Say so and stop.
2. Claim the item with one Edit that replaces its exact `line` with the same
   line, `- [ ]` changed to `- [x]` and ` → claimed` appended. If the Edit fails
   because the line changed, another session claimed it: go back to step 1.
3. Run `/factory <feature>`, and once step 1 has given it a job id, replace
   `claimed` on its backlog line with the job id.

## /factory approve <job-id>

The job must be in `needs-human`. Run **Merge** with that job id.

## /factory rework <job-id> <note>

The job must be in `needs-human`.

1. Write the note, verbatim, to `factory/jobs/<job-id>/rework-<k>.md`, where `k`
   is the next unused number.
2. Set `stage: "build"`.
3. Spawn a fresh `builder` named `builder-<job-id>` with the prompt
   `<paths> Rework: read rework-<k>.md and address it, then update build.md for round N+1. Port: <port>.`
   (`N` is the job's last round.) A rework run gets a fresh `MAX_RESUMES`.
4. Continue from **Build check**, exactly like a new job.

## Reporting

Keep the user posted with one short line per transition, for example
`003-password-reset: round 2, security CHANGES, ux/ui/code PASS → resuming builder`.
When the job ends, say whether it merged or needs a human, and why.
