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
.claude/
  skills/factory/SKILL.md     the orchestrator, plus /factory from-gsd
  agents/                     spec-writer, builder, 4 reviewers, approver
factory/
  bin/gsd                     the GSD bridge: backlog, next, tick (python3, stdlib only)
  backlog.md                  the queue
  dashboard.html              the board; cards show their requirement ID
examples/planning/            a small GSD plan, to see the shape (also the test fixture)
tests/test_gsd.py             tests for factory/bin/gsd
```

## Setup

1. Install GSD in Claude Code, for example for this project only:
   `npx -y @opengsd/gsd-core@latest --claude --local`.
2. Copy `.claude/` and `factory/` into your repo root, and add `/factory/jobs/`
   to your `.gitignore`.
3. Make sure your `AGENTS.md` (or `CLAUDE.md`) says how to set up a fresh
   checkout, start the dev server on a given port, and run your tests, build and
   lint. The agents read everything repo-specific from there.
4. Install the [`agent-browser`](https://github.com/vercel-labs/agent-browser)
   CLI if your project has pages to look at.

## Use it

```
/gsd-new-project                 GSD asks about your project, writes .planning/
                                 (stop once the roadmap exists, no need to plan phases)
git commit .planning             agents only see what main has (GSD usually commits it itself)
/factory from-gsd 1              queue phase 1's requirements
/factory next                    build the next ready one; open more sessions to run several at once
```

Other commands, unchanged from v1:

```
/factory <feature>               build a one-off feature (no requirement ID needed)
/factory approve <job-id>        merge a needs-human job (also ticks its requirement)
/factory rework <job-id> <note>  send a needs-human job back to the builder
```

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

When a job merges, the orchestrator runs `factory/bin/gsd tick <ID>`. That ticks
the checkbox, marks the requirement's row in the Traceability table `Complete`,
and commits `.planning/REQUIREMENTS.md`. When that finishes a phase, it says so.
Job branches never touch `.planning/`: the builder is told not to, the code
reviewer blocks it, and the approver checks it.

## Things to know

- **Use GSD up to the roadmap only.** Don't also run `/gsd-plan-phase` or
  `/gsd-execute-phase` on a phase the factory is building, or two systems will
  build the same requirements.
- **GSD's own end-of-phase checks don't work here.** `/gsd-verify-work` reads
  the `SUMMARY.md` files that GSD's executor writes, and the factory doesn't
  write them. Each job is checked by its reviewers and the approver instead.
- **Requirements need checkboxes.** `factory/bin/gsd` reads `- [ ] **ID**: ...`
  lines. GSD's v2 (deferred) requirements have no checkbox, so they're never queued.

## Dashboard

```bash
cd factory && python3 -m http.server
```

Open <http://localhost:8000/dashboard.html>.

## Tests

```bash
python3 -m unittest discover tests
```
