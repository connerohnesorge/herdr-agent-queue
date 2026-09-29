import json
import os
import readline
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("HERDR_PLUGIN_STATE_DIR", tempfile.mkdtemp())
import agent_queue  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class Frontmatter(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_plain_fields(self):
        path = write(self.dir / "SKILL.md", '---\nname: Herdr\ndescription: "Control herdr"\n---\nbody\n')
        self.assertEqual(agent_queue.frontmatter(path), ("Herdr", "Control herdr"))

    def test_folded_description(self):
        path = write(self.dir / "SKILL.md", "---\nname: lazy\ndescription: >\n  Forces the\n  laziest fix.\n---\n")
        self.assertEqual(agent_queue.frontmatter(path), ("lazy", "Forces the laziest fix."))

    def test_no_frontmatter(self):
        path = write(self.dir / "cmd.md", "Just a prompt\n")
        self.assertEqual(agent_queue.frontmatter(path), (None, ""))


class ClaudeSkills(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.claude = self.home / ".claude"
        patcher = mock.patch.object(Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_all_sources(self):
        write(self.claude / "skills/Herdr/SKILL.md", "---\nname: Herdr\ndescription: user skill\n---\n")
        write(self.claude / "skills/nameless/SKILL.md", "no frontmatter\n")
        write(self.claude / "commands/spectr/apply.md", "---\ndescription: nested command\n---\n")
        project = self.home / "src/app"
        write(project / ".claude/skills/deploy/SKILL.md", "---\nname: deploy\ndescription: project skill\n---\n")
        on, off = self.home / "plugins/on", self.home / "plugins/off"
        write(on / "skills/review/SKILL.md", "---\nname: review\ndescription: plugin skill\n---\n")
        write(off / "skills/hidden/SKILL.md", "---\nname: hidden\n---\n")
        write(self.claude / "settings.json", json.dumps({"enabledPlugins": {"tail@mkt": True, "off@mkt": False}}))
        write(self.claude / "plugins/installed_plugins.json", json.dumps({"plugins": {
            "tail@mkt": [{"installPath": str(on)}],
            "off@mkt": [{"installPath": str(off)}],
        }}))

        skills = agent_queue.claude_skills(project)

        self.assertEqual(skills, {
            "/Herdr": "user skill",
            "/nameless": "",
            "/spectr:apply": "nested command",
            "/deploy": "project skill",
            "/tail:review": "plugin skill",
        })

    def test_empty_home(self):
        self.assertEqual(agent_queue.claude_skills(self.home), {})


class Completion(unittest.TestCase):
    def test_completes_only_slash_words(self):
        agent_queue.enable_skill_completion({"/Herdr": "", "/herd-cats": "", "/Other": ""})
        complete = readline.get_completer()

        def matches(text):
            found = []
            while (match := complete(text, len(found))) is not None:
                found.append(match)
            return found

        self.assertEqual(matches("/her"), ["/Herdr", "/herd-cats"])
        self.assertEqual(matches("/x"), [])
        self.assertEqual(matches("her"), [])


class Deliver(unittest.TestCase):
    def setUp(self):
        agent_queue.STATE = Path(tempfile.mkdtemp())
        self.info = {"pane_id": "w1:p1", "terminal_id": "term_1", "agent": "claude", "agent_status": "done"}
        self.calls = []
        patchers = [
            mock.patch.object(agent_queue, "pane", side_effect=lambda _: self.info),
            mock.patch.object(agent_queue, "herdr", side_effect=lambda *a: self.calls.append(a) or ""),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

    def prompts(self):
        return [c[3] for c in self.calls if c[:2] == ("agent", "prompt")]

    def test_holds_while_working(self):
        self.info["agent_status"] = "working"
        agent_queue.add("w1:p1", "first")
        self.assertEqual(self.prompts(), [])
        self.assertEqual(agent_queue.load(self.info), ["first"])
        self.assertIn(("pane", "report-metadata", "w1:p1", "--source", "conner.agent-queue",
                       "--token", "queued=1 queued"), self.calls)

    def test_submits_one_per_finished_turn(self):
        self.info["agent_status"] = "working"
        agent_queue.add("w1:p1", "first")
        agent_queue.add("w1:p1", "second")
        self.info["agent_status"] = "done"
        agent_queue.deliver("w1:p1")
        self.assertEqual(self.prompts(), ["first"])
        self.assertEqual(agent_queue.load(self.info), ["second"])
        self.info["agent_status"] = "idle"
        agent_queue.deliver("w1:p1")
        self.assertEqual(self.prompts(), ["first", "second"])
        self.assertEqual(agent_queue.load(self.info), [])

    def test_never_submits_while_blocked(self):
        self.info["agent_status"] = "working"
        agent_queue.add("w1:p1", "first")
        self.info["agent_status"] = "blocked"
        agent_queue.deliver("w1:p1")
        self.assertEqual(self.prompts(), [])

    def test_failed_submit_keeps_prompt(self):
        self.info["agent_status"] = "working"
        agent_queue.add("w1:p1", "first")
        self.info["agent_status"] = "done"
        agent_queue.herdr.side_effect = RuntimeError("herdr agent: stalled")
        with self.assertRaises(RuntimeError):
            agent_queue.deliver("w1:p1")
        self.assertEqual(agent_queue.load(self.info), ["first"])

    def test_event_ignores_working_status(self):
        with mock.patch.object(agent_queue, "deliver") as deliver, \
             mock.patch.dict(os.environ, {"HERDR_PLUGIN_EVENT_JSON": json.dumps(
                 {"data": {"pane_id": "w1:p1", "agent_status": "working"}})}):
            agent_queue.event()
        deliver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
