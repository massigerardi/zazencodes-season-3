"""End-to-end tests for factory/bin/gsd against examples/planning/.

Run from the repo root: python3 -m unittest discover tests
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "factory/bin/gsd"


class GsdBridge(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        shutil.copytree(REPO / "examples/planning", self.dir / ".planning")
        (self.dir / "factory").mkdir()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def gsd(self, *args, ok=(0,)):
        res = subprocess.run(["python3", str(SCRIPT), *args], cwd=self.dir,
                             capture_output=True, text=True)
        self.assertIn(res.returncode, ok, res.stdout + res.stderr)
        return res

    def backlog(self):
        return (self.dir / "factory/backlog.md").read_text()

    def reqs(self):
        return (self.dir / ".planning/REQUIREMENTS.md").read_text()

    def claim(self, line, job_id):
        path = self.dir / "factory/backlog.md"
        done = "- [x] " + line[len("- [ ] "):] + " → " + job_id
        path.write_text(path.read_text().replace(line, done))

    def test_queue_phase_one_with_same_phase_dependency(self):
        out = self.gsd("backlog", "1", "--after", "AUTH-02=AUTH-01").stdout
        self.assertEqual(out.splitlines(), [
            "- [ ] AUTH-01: User can sign up and sign in with email and password [phase 1]",
            "- [ ] AUTH-02: User can reset a forgotten password via an emailed link [phase 1] (after AUTH-01)",
            "- [ ] AUTH-03: User stays signed in across browser refreshes [phase 1]",
        ])
        self.assertTrue(self.backlog().startswith("# Backlog"))
        self.assertIn("(after AUTH-01)", self.backlog())

    def test_dry_run_writes_nothing(self):
        self.gsd("backlog", "1", "--dry-run")
        self.assertFalse((self.dir / "factory/backlog.md").exists())

    def test_later_phase_waits_on_earlier_phase(self):
        self.gsd("backlog", "02")
        self.assertIn("LINK-01: User can save a link by pasting its URL [phase 2] "
                      "(after AUTH-01, AUTH-02, AUTH-03)", self.backlog())

    def test_requeue_skips_queued_and_ticked(self):
        self.gsd("backlog", "1")
        self.gsd("tick", "AUTH-03")
        res = self.gsd("backlog", "1")
        self.assertEqual(res.stdout, "")
        self.assertIn("AUTH-01 (already queued)", res.stderr)
        self.assertIn("AUTH-03 (ticked)", res.stderr)

    def test_next_respects_dependencies_and_claims(self):
        self.gsd("backlog", "1", "--after", "AUTH-02=AUTH-01", "--after", "AUTH-03=AUTH-01")
        self.gsd("backlog", "2")
        first = json.loads(self.gsd("next").stdout)
        self.assertEqual(first["requirement"], "AUTH-01")
        self.assertEqual(first["feature"],
                         "AUTH-01: User can sign up and sign in with email and password")
        self.claim(first["line"], "001-sign-up")

        res = self.gsd("next", ok=(3,))
        self.assertIn("waiting on: AUTH-01", res.stdout)

        self.gsd("tick", "AUTH-01")
        second = json.loads(self.gsd("next").stdout)
        self.assertEqual(second["requirement"], "AUTH-02")

    def test_next_empty_backlog(self):
        self.assertEqual(self.gsd("next", ok=(4,)).returncode, 4)

    def test_plain_items_still_work(self):
        (self.dir / "factory/backlog.md").write_text("# Backlog\n\n- [ ] Fix the footer link\n")
        item = json.loads(self.gsd("next").stdout)
        self.assertEqual(item, {"line": "- [ ] Fix the footer link",
                                "feature": "Fix the footer link", "requirement": None})

    def test_tick_updates_checkbox_and_traceability_and_reports_phase(self):
        self.gsd("tick", "AUTH-01")
        self.gsd("tick", "AUTH-02")
        out = self.gsd("tick", "AUTH-03").stdout
        self.assertIn("Phase 1 (Accounts) complete: all 3 requirements ticked.", out)
        text = self.reqs()
        self.assertIn("- [x] **AUTH-02**: User can reset", text)
        self.assertIn("| AUTH-02 | Phase 1 | Complete |", text)
        self.assertIn("- [ ] **LINK-01**", text)
        self.assertIn("| LINK-01 | Phase 2 | Pending |", text)

    def test_tick_twice_is_harmless(self):
        self.gsd("tick", "LINK-02")
        self.assertIn("already ticked", self.gsd("tick", "LINK-02").stdout)

    def plan(self, name, requirements, executed=False):
        d = self.dir / ".planning/phases" / name.split("/")[0]
        d.mkdir(parents=True, exist_ok=True)
        plan = d / name.split("/")[1]
        plan.write_text(f"---\nphase: 01-accounts\nplan: 01\n{requirements}\nwave: 1\n---\n\n<objective>x</objective>\n")
        if executed:
            plan.with_name(plan.name.replace("PLAN", "SUMMARY")).write_text("done\n")

    def test_planned_phase_warns_and_queues(self):
        self.plan("01-accounts/01-01-PLAN.md", "requirements: [AUTH-01, AUTH-03]")
        res = self.gsd("backlog", "1")
        self.assertIn("GSD has planned phase 1 (1 plans in .planning/phases/01-accounts)", res.stderr)
        self.assertIn("AUTH-01", self.backlog())

    def test_executed_phase_refuses_without_force(self):
        self.plan("01-accounts/01-01-PLAN.md", "requirements: [AUTH-01]", executed=True)
        self.plan("01-accounts/01-02-PLAN.md", "requirements: [AUTH-02]")
        res = self.gsd("backlog", "1", ok=(1,))
        self.assertIn("partly executed by GSD (1 of 2 plans", res.stderr)
        self.assertFalse((self.dir / "factory/backlog.md").exists())
        res = self.gsd("backlog", "1", "--force")
        self.assertIn("--force: queuing phase 1", res.stderr)
        self.assertIn("AUTH-02", self.backlog())

    def test_other_phase_plans_do_not_count(self):
        self.plan("02-shelf/02-01-PLAN.md", "requirements: [LINK-01]", executed=True)
        res = self.gsd("backlog", "1")
        self.assertNotIn("Warning", res.stderr)

    def test_plans_lists_matching_plans_in_both_frontmatter_forms(self):
        self.plan("01-accounts/01-01-PLAN.md", "requirements: [AUTH-01, AUTH-02]  # from ROADMAP")
        self.plan("01-accounts/01-02-PLAN.md", "requirements:\n  - AUTH-02\n  - AUTH-03", executed=True)
        self.plan("01-accounts/01-03-PLAN.md", "requirements: [AUTH-03]")
        self.assertEqual(self.gsd("plans", "AUTH-02").stdout.splitlines(), [
            ".planning/phases/01-accounts/01-01-PLAN.md",
            ".planning/phases/01-accounts/01-02-PLAN.md (executed)",
        ])
        self.assertEqual(self.gsd("plans", "LINK-01").stdout, "")

    def test_errors(self):
        self.assertIn("no **Requirements** line", self.gsd("backlog", "9", ok=(1,)).stderr)
        self.assertIn("not a requirement of phase 1",
                      self.gsd("backlog", "1", "--after", "LINK-01=AUTH-01", ok=(1,)).stderr)
        self.assertIn("not a checkbox requirement",
                      self.gsd("tick", "SHARE-01", ok=(1,)).stderr)
        (self.dir / ".planning/ROADMAP.md").unlink()
        self.assertIn("Run /gsd-new-project", self.gsd("backlog", "1", ok=(1,)).stderr)


if __name__ == "__main__":
    unittest.main()
