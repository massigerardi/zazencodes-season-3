# Software Factory + GSD

GSD plans the project, the factory builds it. GSD turns your idea into
requirements and a roadmap of phases. The factory takes each requirement as a
job: it writes a spec, builds it on its own branch, reviews it from four
angles, and merges it to `main` or hands it to you. After each merge it ticks
the requirement off in GSD's plan.

It runs entirely on your machine: no GitHub, no PRs, nothing is pushed.

```
/gsd-new-project ──► .planning/ (PROJECT, REQUIREMENTS, ROADMAP)
                         │
/factory from-gsd 1 ─────┘──► factory/backlog.md   one line per requirement, with (after ...)
                                    │
/factory next ──► first item whose dependencies are ticked
                                    │
      spec-writer → builder → [security, ux, ui, code] → approver ─ ESCALATE → needs-human
            ▲          ▲                │ any CHANGES       │ APPROVE
            │          └────────────────┘                   ▼
     reads the requirement,                  merge to main, tick the requirement
     its phase and PROJECT.md                in REQUIREMENTS.md, commit it
```

Based on [Software Factory for Claude Code (v1)](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code).
The review loop is the same; what's new is that the work comes from GSD.

## What's in here

```
.claude/                      the Claude Code skill and agents, ready to copy
.opencode/                    the OpenCode command, agents and permissions, ready to copy
install.sh                    copies the factory into a project
factory/
  bin/gsd                     the GSD bridge: backlog, next, tick, plans (python3, stdlib only)
  bin/dashboard               start, stop or check the dashboard server
  backlog.md                  the queue
  dashboard.html              the board; cards show their requirement ID
examples/planning/            a small GSD plan, to see the shape (also the test fixture)
tests/test_gsd.py             tests for factory/bin/gsd
```

## Install in a project

Works the same for a new or an existing project. You need Claude Code, `git`
and `python3`. No GitHub account is needed: everything stays local. To use
OpenCode instead, see [OpenCode](#opencode).

### 1. Install GSD

```bash
npx -y @opengsd/gsd-core@latest --claude --local    # this project only
```

### 2. Copy the factory in

On a clean `main` in your project, run the install script from this folder:

```bash
cd /path/to/software-factory-gsd
./install.sh /path/to/your/project
```

It copies `factory/` (bin/, backlog.md, dashboard.html), the orchestrator skill
to `.claude/skills/factory/` and the seven agents (spec-writer, builder, four
reviewers, approver) to `.claude/agents/`, and adds `/factory/jobs/` to
`.gitignore`. No model runs and nothing is generated or committed.

Run it again to update an installed project's scripts and dashboard. It keeps
the project's `factory/backlog.md`.

- **Base branch:** the files say `main`. If you integrate on another branch (for
  example `development`), replace it in `.claude/` after installing.
- **Clashes:** it stops without copying anything if the project has its own
  `factory` skill, or agents with the same names (`builder.md`, `approver.md`
  and so on), that differ from these.

### 3. Prepare the project

- **`AGENTS.md` (or `CLAUDE.md`)** must say how to set up a fresh checkout,
  start the dev server on a given port, and run the tests, build and lint. Every
  agent reads it; nothing else in the factory is specific to your project.
- **Tailor the reviewers.** Ask Claude to adjust the four reviewers and the
  approver's escalate list to your stack: framework, security hot spots, what
  should always go to a human.
- **`agent-browser`**: install the
  [`agent-browser`](https://github.com/vercel-labs/agent-browser) CLI if the
  project has pages to look at. The builder and the UX and UI reviewers use it.
- **Commit** all of it on `main`.

### 4. Get a GSD plan

- **New to GSD:** run `/gsd-new-project` and stop once the roadmap exists (no
  need to plan phases). On an existing codebase, accept its offer to map the
  code first: features that already exist become "Validated" in `PROJECT.md`,
  and only new work becomes `- [ ] **ID**` requirements, so the factory never
  rebuilds what's there. `/gsd-onboard` is the guided alternative, and also
  pulls in existing specs, ADRs and PRDs.
- **Already on GSD:** keep your `.planning/` and add the next batch of work with
  `/gsd-new-milestone`. Requirements GSD has already built are ticked, so the
  factory skips them. See [Phases GSD has already planned](#phases-gsd-has-already-planned).

Then make sure `.planning/` is committed on `main` (GSD does it by default):

```bash
git add .planning && git commit -m "Add the GSD plan"
```

## Use it

```
/factory from-gsd 1              queue phase 1's requirements
/factory next                    build the next ready one; open more sessions to run several at once
```

Other commands, unchanged from v1:

```
/factory <feature>               build a one-off feature (no requirement ID needed)
/factory approve <job-id>        merge a needs-human job (also ticks its requirement)
/factory rework <job-id> <note>  send a needs-human job back to the builder
```

## OpenCode

The factory also runs on [OpenCode](https://opencode.ai), with every agent on
the free **Big Pickle** model (`opencode/big-pickle`). It was built for OpenCode
1.19.3; other versions may name tools and settings differently, so check
`opencode --version`. Background and sources:
[`opencode-variant.md`](opencode-variant.md).

### Install

```bash
npx -y @opengsd/gsd-core@latest --opencode --local   # in your project
cd /path/to/software-factory-gsd
./install.sh --opencode /path/to/your/project
```

The script copies `factory/` and these ready-made files into your project. No
model runs and nothing is generated:

```
.opencode/commands/factory.md    the orchestrator (/factory)
.opencode/agents/                spec-writer, builder, four reviewers, approver
.opencode/opencode.json          allows the job worktrees, hides the Claude Code skill
```

It stops without copying anything if the project has its own file with one of
those command or agent names. If the project already has
`.opencode/opencode.json`, the script prints the entries to add to it.

Then follow steps 3 and 4 above and commit `.opencode/` with the rest. The
commands are the same: `/factory from-gsd 1`, `/factory next` and so on.

- **Base branch:** the files say `main`. If you integrate on another branch,
  replace it in `.opencode/` after installing.
- **Both tools:** a project can have `.claude/` and `.opencode/` and run the
  factory from either, one tool per job. The two sets are maintained separately,
  so make a change to the factory in both.

### What's different

- **Big Pickle can't view images.** The UX and UI reviewers judge pages from the
  accessibility snapshot, element boxes and computed styles, and say in their
  review that nobody looked. Check visual changes yourself, or give
  `reviewer-ux` and `reviewer-ui` a `model:` that accepts images.
- **Your code goes to a free preview model.** The
  [OpenCode Zen docs](https://opencode.ai/docs/zen/) say data collected during
  Big Pickle's free period may be used to improve the model. Don't use it on
  code you can't share. To switch, change `model:` in `.opencode/`.
- **Dashboard chips fill in together.** The orchestrator gets the reviewers'
  results back from its `task` calls, then writes the verdicts. The stage
  captions on the board still say `opus`.
- **Resuming the builder** uses its task id, saved as `builder_task` in
  `job.json`.
- **Edit limits are enforced.** Reviewers, spec-writer and approver can only use
  the edit tools under `factory/jobs/`; the builder also in worktrees, never in
  `.planning/`. These limits don't cover shell commands.

### The free usage limit

Big Pickle has a free usage limit, and one small job can be enough to reach it
when other use has counted toward it. A job that hits it may stall without a
word: the screen stops at the last step and the process stays alive. The error,
`Free usage limit reached`, shows up in the log:

```bash
grep "Free usage limit" ~/.local/share/opencode/log/opencode.log | tail -3
```

So don't leave jobs unattended and assume they finish.

### Recover a stalled job

1. Stop the stalled OpenCode process, and wait until the limit has reset (the
   commands below need a model too), or change `model:` in `.opencode/`.
2. Look at how far it got: `stage` in `factory/jobs/<job-id>/job.json`, the
   files beside it, and `git log --oneline main`.
3. Pick the matching case. `/factory approve` and `/factory rework` only accept
   a `needs-human` job, so set `"stage": "needs-human"` in `job.json` first.

| The job stalled | What to do |
|---|---|
| Before `spec.md` was complete | Start over (below). |
| With a spec, before the approver wrote `APPROVE` | `/factory rework <job-id> Finish the build from spec.md and any review findings.` It goes through review and approval again. |
| After `decision.md` says `APPROVE`, with no merge on `main` | `/factory approve <job-id>` |
| After `Merge factory/<job-id>` is on `main` | Don't approve again. Finish by hand: `factory/bin/gsd tick <ID>` (if the job has a requirement), commit `.planning/REQUIREMENTS.md`, `git worktree remove <worktree>`, `git branch -d factory/<job-id>`, and set `"stage": "merged"`. |

`/factory approve` merges without reviewing anything, so use it only when
`decision.md` says `APPROVE` or you have checked the branch yourself.

To start over, run `git worktree remove --force <worktree>` and
`git branch -D factory/<job-id>` (both discard the job's work; skip whichever
doesn't exist), delete `factory/jobs/<job-id>/`, and in `factory/backlog.md`
change the item back to `- [ ]` and remove its `→` note.

## How requirements flow

GSD writes requirements as checkbox lines with IDs, and phases that list them:

```markdown
<!-- .planning/REQUIREMENTS.md -->
- [ ] **AUTH-01**: User can sign up and sign in with email and password
- [ ] **AUTH-02**: User can reset a forgotten password via an emailed link

<!-- .planning/ROADMAP.md -->
### Phase 2: Shelf
**Depends on**: Phase 1
**Requirements**: LINK-01, LINK-02, LINK-03
**Success Criteria** (what must be TRUE):
  1. Pasting a URL adds it to the top of the shelf
```

`/factory from-gsd <phase>` adds one backlog line per unticked requirement.
Requirements in a later phase wait for the earlier phase's requirements. The
orchestrator adds a same-phase dependency only when one clearly needs another,
like password reset needing sign-up:

```markdown
- [ ] AUTH-01: User can sign up and sign in with email and password [phase 1]
- [ ] AUTH-02: User can reset a forgotten password via an emailed link [phase 1] (after AUTH-01)
- [ ] LINK-01: User can save a link by pasting its URL [phase 2] (after AUTH-01, AUTH-02, AUTH-03)
```

A requirement is done when it is ticked in `REQUIREMENTS.md`, so `/factory next`
skips items that are still waiting. You can edit `(after ...)` by hand, and add
plain items without an ID: they work as they did in v1.

The spec-writer turns the requirement into `spec.md`. The requirement line
becomes the first acceptance criterion, the phase's matching success criteria
become the rest, and the phase's other requirements go under Out of scope, since
each is its own job. `PROJECT.md` supplies the constraints.

To settle a phase's gray areas first, run `/gsd-discuss-phase <phase>` before
`/factory from-gsd <phase>`. It only asks you questions and commits the
answers to `.planning/phases/<NN>-*/<NN>-CONTEXT.md`: no code, no plans. The
spec-writer reads that file and treats its decisions as fixed. Skip `--auto`
and `--chain`, which carry on into planning and execution.

When a job merges, the orchestrator runs `factory/bin/gsd tick <ID>`. That ticks
the checkbox, marks the requirement's row in the Traceability table `Complete`,
and commits `.planning/REQUIREMENTS.md`. When that finishes a phase, it says so.
Job branches never touch `.planning/`: the builder is told not to, the code
reviewer blocks it, and the approver checks it.

## Phases GSD has already planned

If `/gsd-plan-phase` ran before you installed the factory, the phase has
`*-PLAN.md` files in `.planning/phases/`. What to do depends on how far GSD got.

### Check where the phase is

```bash
factory/bin/gsd backlog <phase> --dry-run    # warns if planned, refuses if executed
ls .planning/phases/<NN>-*/                  # PLAN.md without SUMMARY.md = not run yet
```

`/gsd-progress` shows the same thing from GSD's side.

| The phase is | `/factory from-gsd <phase>` | Suggested |
|---|---|---|
| Not planned | Queues it | Let the factory build it. |
| Planned, not executed | Warns, then queues it | Pick one system for the whole phase (see below). |
| Partly executed | Refuses | Finish it with GSD, then queue the next phase. |
| Fully executed | Refuses | Nothing to do: queue the next phase. |

### Planned, not executed: pick one system

**Let GSD finish it** (`/gsd-execute-phase <phase>`, then
`/factory from-gsd <next phase>`) when:

- you reviewed the plans and they are recent, so the planning isn't wasted;
- the plans are tightly coupled (several waves touching the same files), which
  GSD runs as one unit but the factory would split into separate branches;
- the plans contain checkpoints that need you, which GSD asks you about as it goes.

You also keep GSD's own end-of-phase check: `/gsd-verify-work` works, because
GSD's executor writes the `SUMMARY.md` files it reads. The next phase's items wait
on this phase's ticks, so the factory starts on them as soon as GSD is done.

**Give it to the factory** (`/factory from-gsd <phase>`, and never run
`/gsd-execute-phase` on it) when:

- you want every requirement to go through the four reviewers and the approver
  before it reaches `main`;
- you want to build several requirements of the phase in parallel;
- the code has moved since the plans were written.

The spec-writer reuses the plans as a head start (`factory/bin/gsd plans <ID>`
finds them) and checks them against the current code. The cost: `/gsd-progress`
keeps showing the phase as planned with 0 plans done, since the factory writes no
`SUMMARY.md`. That's cosmetic; `REQUIREMENTS.md` shows the real progress.

**Not both.** Running `/gsd-execute-phase` on a phase the factory is building
makes both systems build the same requirements.

### Partly executed: finish it with GSD

1. `/gsd-execute-phase <phase>` resumes the plans that haven't run.
2. `factory/bin/gsd backlog <phase> --dry-run` should now print nothing to
   queue: GSD ticks each requirement once every plan that lists it has run.
3. `/factory from-gsd <next phase>`.

Don't split one phase between the two systems. A requirement shared by a plan
that ran and one that didn't is still unticked, so the factory would rebuild work
that is half done.

If a requirement is still unticked after GSD has run every plan, GSD missed
something. Either close the gap in GSD (`/gsd-verify-work <phase>` records it,
then `/gsd-plan-phase <phase> --gaps` plans the fix), or hand the leftovers to
the factory with
`factory/bin/gsd backlog <phase> --force`. The spec-writer sees the executed
plans and specs only what is still missing.

### The rule

Whatever GSD has planned is finished by one system, as a whole phase. The only
handoff between GSD and the factory is the ticks in `REQUIREMENTS.md`, so you can
switch systems at any phase boundary.

## Things to know

- **One system per phase.** Don't run `/gsd-execute-phase` on a phase the
  factory is building, or both will build the same requirements. Planning a
  phase with GSD first is fine: the factory reuses the plans. So is discussing
  it with `/gsd-discuss-phase`: the spec-writer follows its decisions.
- **GSD's own end-of-phase checks don't work here.** `/gsd-verify-work` reads
  the `SUMMARY.md` files that GSD's executor writes, and the factory doesn't
  write them. Each job is checked by its reviewers and the approver instead.
- **Requirements need checkboxes.** `factory/bin/gsd` reads `- [ ] **ID**: ...`
  lines. GSD's v2 (deferred) requirements have no checkbox, so they're never queued.
- **`.planning/` must be committed.** With GSD's `commit_docs: false`,
  `.planning/` is gitignored, job worktrees can't see it, and the factory
  refuses to start the job. Keep the default `commit_docs: true`.
- **One requirement is one job.** Split a requirement that is too big for one
  branch ("User can manage their account") in `REQUIREMENTS.md` and
  `ROADMAP.md` before running `from-gsd`.
- **Merges need a clean `main`.** If you're editing in the same checkout, an
  approved job waits in needs-human until you run `/factory approve <job-id>`.

## Dashboard

```bash
factory/bin/dashboard start          # serves factory/ on 127.0.0.1:8000, in the background
factory/bin/dashboard start 8100     # another port
factory/bin/dashboard status         # exit 3 when not running
factory/bin/dashboard stop
```

The page and its browser tab are titled with the project's folder name.
`start` prints the URL to open, <http://localhost:8000/dashboard.html> by
default. The board polls `factory/jobs/` and updates as jobs move. Its first
column, Backlog, lists the unchecked items of `factory/backlog.md` in queue
order as dashed cards, with any `(after ...)` as written. The server's
pid and log go to `factory/jobs/.dashboard.pid` and `.dashboard.log`, which are
gitignored; the log is overwritten on each start.

## Tests

```bash
python3 -m unittest discover tests
```
