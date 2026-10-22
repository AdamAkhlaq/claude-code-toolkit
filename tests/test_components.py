"""Structural checks over the plugin's skills, agents, hooks and docs.

Skill prose is not tested. What is tested is the set of rules every component
must keep whatever its prose says: invocation flags, cross references, tool
allowlists, and the component tables in README.md and PHILOSOPHY.md.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
AGENTS = REPO / "agents"
HOOKS = REPO / "hooks"

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def split(path):
    """(frontmatter dict, body) for a Markdown file with a flat YAML header."""
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"{path.relative_to(REPO)}: no frontmatter")
    data = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip():
            data[key.strip()] = value.strip().strip("\"'")
    return data, match.group(2)


def skills():
    return {p.parent.name: split(p) for p in sorted(SKILLS.glob("*/SKILL.md"))}


def agents():
    return {p.stem: split(p) for p in sorted(AGENTS.glob("*.md"))}


def readme_table(heading_word):
    """Rows of the first README table whose header starts with `| heading_word`."""
    rows = []
    in_table = False
    for line in (REPO / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {heading_word}"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not set(cells[0]) <= set("- "):
                rows.append(cells)
        elif in_table:
            break
    return rows


class SkillRules(unittest.TestCase):
    def test_frontmatter_names_and_descriptions(self):
        for name, (meta, _) in skills().items():
            self.assertEqual(meta.get("name"), name, f"skills/{name}: name must match the folder")
            self.assertTrue(meta.get("description"), f"skills/{name}: description is required")

    def test_invocation_matches_readme(self):
        listed = {row[0].strip("`"): row for row in readme_table("Skill")}
        for name, (meta, _) in skills().items():
            self.assertIn(name, listed, f"skills/{name} is missing from the README skill table")
            invocation = listed[name][1]
            flag = meta.get("disable-model-invocation", "false").lower()
            if invocation == "user":
                self.assertEqual(flag, "true", f"skills/{name}: user-invoked skills carry disable-model-invocation: true")
            else:
                self.assertEqual(invocation, "model", f"README: skill {name} invocation must be user or model")
                self.assertEqual(flag, "false", f"skills/{name}: model-invoked skills must stay model-invocable")
        for name, row in listed.items():
            if "planned" not in row[2]:
                self.assertIn(name, sorted(skills()), f"README lists {name} as shipped but skills/{name}/SKILL.md is missing")

    def test_no_component_calls_a_user_invoked_skill(self):
        all_skills = skills()
        user_invoked = {n for n, (m, _) in all_skills.items() if m.get("disable-model-invocation", "").lower() == "true"}
        model_invoked = set(all_skills) - user_invoked
        agent_names = set(agents())
        sources = {f"skills/{n}": body for n, (_, body) in all_skills.items()}
        sources.update({f"agents/{n}": body for n, (_, body) in agents().items()})
        for source, body in sources.items():
            for ref in re.findall(r"(?<![/\w-])toolkit:([a-z-]+)", body):
                self.assertNotIn(ref, user_invoked, f"{source} calls user-invoked skill toolkit:{ref}; only /toolkit:{ref} hand-offs are allowed")
                self.assertIn(ref, model_invoked | agent_names, f"{source} references toolkit:{ref}, which does not exist")
            for ref in re.findall(r"/toolkit:([a-z-]+)", body):
                self.assertNotIn(ref, model_invoked, f"{source} tells the user to type /toolkit:{ref}, a model-invoked skill")

    def test_user_invoked_skills_never_push(self):
        for name, (meta, body) in skills().items():
            commits = re.search(r"(?i)commit only when|git merge", body)
            if meta.get("disable-model-invocation", "").lower() == "true" and commits:
                self.assertRegex(body, r"[Nn]ever push", f"skills/{name}: a skill that commits must say it never pushes")


class AgentRules(unittest.TestCase):
    def test_agents_have_names_descriptions_and_tool_allowlists(self):
        for name, (meta, _) in agents().items():
            self.assertEqual(meta.get("name"), name, f"agents/{name}: name must match the file")
            self.assertTrue(meta.get("description"), f"agents/{name}: description is required")
            tools = [t.strip() for t in meta.get("tools", "").split(",") if t.strip()]
            self.assertTrue(tools, f"agents/{name}: tools allowlist is required")
            self.assertNotIn("*", tools, f"agents/{name}: an allowlist names tools, it does not grant all of them")

    def test_readers_cannot_write(self):
        for name in ("researcher", "reviewer"):
            meta, _ = agents()[name]
            for tool in ("Edit", "Write", "NotebookEdit", "Agent"):
                self.assertNotIn(tool, meta["tools"], f"agents/{name}: must not carry {tool}")

    def test_readme_names_every_agent(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for name in agents():
            self.assertIn(f"`{name}`", readme, f"README does not mention agent {name}")


class HookRules(unittest.TestCase):
    def test_every_hook_script_is_registered_and_documented(self):
        config = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
        registered = set()
        for entries in config["hooks"].values():
            for entry in entries:
                for hook in entry["hooks"]:
                    match = re.search(r"hooks/scripts/([a-z_]+)\.py", hook["command"])
                    self.assertIsNotNone(match, hook["command"])
                    self.assertIn('"${CLAUDE_PLUGIN_ROOT}', hook["command"], "plugin root must be quoted")
                    registered.add(match.group(1))
        scripts = {p.stem for p in (HOOKS / "scripts").glob("*.py") if not p.stem.startswith("_")}
        self.assertEqual(registered, scripts)
        documented = {row[0].strip("`").replace("-", "_") for row in readme_table("Hook")}
        self.assertEqual(documented, scripts, "README hook table must list every hook script")


class PhilosophyRules(unittest.TestCase):
    def enforcers(self):
        text = (REPO / "PHILOSOPHY.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("| ") and not line.startswith("| Principle") and not set(line) <= set("|- "):
                yield line.strip("|").split("|")[-1]

    def test_every_link_resolves(self):
        for cell in self.enforcers():
            for target in re.findall(r"\]\(\./([^)]+)\)", cell):
                self.assertTrue((REPO / target).exists(), f"PHILOSOPHY.md links to missing {target}")

    def test_shipped_components_are_linked_not_just_named(self):
        shipped = {f"skills/{n}/SKILL.md": n for n in skills()}
        shipped.update({f"agents/{n}.md": n for n in agents()})
        shipped.update({f"hooks/scripts/{p.stem}.py": p.stem.replace("_", "-") for p in (HOOKS / "scripts").glob("*.py") if not p.stem.startswith("_")})
        for cell in self.enforcers():
            linked = set(re.findall(r"\[`([^`]+)`\]\(\./", cell))
            bare = set(re.findall(r"(?<!\[)`([^`]+)`(?!\])", cell))
            for path, name in shipped.items():
                if name in bare and name not in linked:
                    self.fail(f"PHILOSOPHY.md names `{name}` without linking ./{path}")


if __name__ == "__main__":
    unittest.main()
