import importlib.machinery
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "bin" / "toolkit-graph"


def load_tool():
    loader = importlib.machinery.SourceFileLoader("toolkit_graph", str(SCRIPT))
    spec = importlib.util.spec_from_loader("toolkit_graph", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


graph = load_tool()


def ticket(ticket_id, title, blocked_by=(), files=("src/a.ts",), status="todo", extra=""):
    deps = ", ".join(blocked_by)
    paths = ", ".join(files)
    return (
        "---\n"
        f"id: {ticket_id}\n"
        f"title: {title}\n"
        f"blocked_by: [{deps}]\n"
        f"files: [{paths}]\n"
        f'proves: "{title} works"\n'
        f"status: {status}\n"
        f"{extra}"
        "---\n\n## Context\n"
    )


class ChangeFixture:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.change = self.root / "docs" / "changes" / "0003-sample"
        (self.change / "tickets").mkdir(parents=True)
        (self.change / "intent.md").write_text("---\nid: 0003\n---\n")

    def add(self, filename, body):
        (self.change / "tickets" / filename).write_text(body)

    def cleanup(self):
        self.tmp.cleanup()


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = graph.main(argv)
    return code, out.getvalue(), err.getvalue()


class FrontmatterTests(unittest.TestCase):
    def test_scalars_flow_and_block_lists(self):
        data = graph.parse_frontmatter(
            "---\nid: T1\ntitle: \"Quoted: title\"\nblocked_by: [T2, 'T3']\nfiles:\n  - src/a.ts\n  - src/b.ts\nserial: true\ncount: 4\nempty:\n---\nbody\n"
        )
        self.assertEqual(data["id"], "T1")
        self.assertEqual(data["title"], "Quoted: title")
        self.assertEqual(data["blocked_by"], ["T2", "T3"])
        self.assertEqual(data["files"], ["src/a.ts", "src/b.ts"])
        self.assertIs(data["serial"], True)
        self.assertEqual(data["count"], 4)
        self.assertIsNone(data["empty"])

    def test_missing_and_unterminated_frontmatter(self):
        with self.assertRaises(graph.GraphError):
            graph.parse_frontmatter("no frontmatter\n")
        with self.assertRaises(graph.GraphError):
            graph.parse_frontmatter("---\nid: T1\n")


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.fx = ChangeFixture()
        self.addCleanup(self.fx.cleanup)

    def test_valid_graph_passes(self):
        self.fx.add("T1-middleware.md", ticket("T1", "Middleware", files=["src/mw.ts"]))
        self.fx.add("T2-config.md", ticket("T2", "Config", files=["src/config.ts"]))
        self.fx.add("T3-router.md", ticket("T3", "Router", blocked_by=["T1", "T2"], files=["src/router.ts"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "0003"])
        self.assertEqual(code, 0, out)
        self.assertIn("ok (3 tickets)", out)

    def test_cycle_is_reported(self):
        self.fx.add("T1-a.md", ticket("T1", "A", blocked_by=["T2"], files=["a"]))
        self.fx.add("T2-b.md", ticket("T2", "B", blocked_by=["T1"], files=["b"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "sample"])
        self.assertEqual(code, 1)
        self.assertIn("dependency cycle", out)

    def test_unknown_dependency_and_self_dependency(self):
        self.fx.add("T1-a.md", ticket("T1", "A", blocked_by=["T9"], files=["a"]))
        self.fx.add("T2-b.md", ticket("T2", "B", blocked_by=["T2"], files=["b"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "0003"])
        self.assertEqual(code, 1)
        self.assertIn("unknown ticket T9", out)
        self.assertIn("blocked by itself", out)

    def test_parallel_tickets_sharing_a_file_fail(self):
        self.fx.add("T1-a.md", ticket("T1", "A", files=["src/shared.ts"]))
        self.fx.add("T2-b.md", ticket("T2", "B", files=["src/shared.ts", "src/other.ts"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "0003"])
        self.assertEqual(code, 1)
        self.assertIn("T1 and T2 can run in parallel but both touch src/shared.ts", out)

    def test_ordered_tickets_may_share_a_file(self):
        self.fx.add("T1-a.md", ticket("T1", "A", files=["src/shared.ts"]))
        self.fx.add("T2-b.md", ticket("T2", "B", blocked_by=["T1"], files=["src/shared.ts"]))
        self.fx.add("T3-c.md", ticket("T3", "C", blocked_by=["T2"], files=["src/shared.ts"]))
        code, _, _ = run(["--root", str(self.fx.root), "validate", "0003"])
        self.assertEqual(code, 0)

    def test_field_and_naming_errors(self):
        self.fx.add("T1-a.md", "---\nid: T1\ntitle: A\nblocked_by: []\nfiles: []\nproves: \"\"\nstatus: weird\n---\n")
        self.fx.add("wrong-name.md", ticket("T2", "B", files=["b"]))
        self.fx.add("T3-dup.md", ticket("T2", "Dup", files=["c"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "0003"])
        self.assertEqual(code, 1)
        self.assertIn("missing 'proves'", out)
        self.assertIn("status 'weird' is not one of", out)
        self.assertIn("'files' must list at least one path", out)
        self.assertIn("wrong-name.md: file name must start with its id", out)
        self.assertIn("duplicate id T2", out)

    def test_json_output(self):
        self.fx.add("T1-a.md", ticket("T1", "A", files=["a"]))
        code, out, _ = run(["--root", str(self.fx.root), "validate", "0003", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"errors": []', out)


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.fx = ChangeFixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.add("T1-a.md", ticket("T1", "A", files=["a"], status="done"))
        self.fx.add("T2-b.md", ticket("T2", "B", files=["b"], status="todo"))
        self.fx.add("T3-c.md", ticket("T3", "C", blocked_by=["T1", "T2"], files=["c"]))
        self.fx.add("T4-d.md", ticket("T4", "D", blocked_by=["T1"], files=["d"], status="reopened", extra="serial: true\n"))

    def test_frontier_lists_unblocked_not_done_tickets(self):
        code, out, _ = run(["--root", str(self.fx.root), "frontier", "0003"])
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual([line.split()[0] for line in lines], ["T2", "T4"])
        self.assertIn("[serial, reopened]", lines[1])
        self.assertNotIn("T3", out)

    def test_frontier_json(self):
        code, out, _ = run(["--root", str(self.fx.root), "frontier", "0003", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"id": "T2"', out)

    def test_frontier_refuses_invalid_graph(self):
        self.fx.add("T5-e.md", ticket("T5", "E", blocked_by=["T99"], files=["e"]))
        code, _, err = run(["--root", str(self.fx.root), "frontier", "0003"])
        self.assertEqual(code, 1)
        self.assertIn("graph is invalid", err)

    def test_empty_frontier_message(self):
        self.fx.add("T2-b.md", ticket("T2", "B", files=["b"], status="in-progress"))
        self.fx.add("T4-d.md", ticket("T4", "D", blocked_by=["T1"], files=["d"], status="in-progress"))
        code, out, _ = run(["--root", str(self.fx.root), "frontier", "0003"])
        self.assertEqual(code, 0)
        self.assertIn("frontier is empty; waiting on T2, T3, T4", out)
        for name in ("T2-b.md", "T3-c.md", "T4-d.md"):
            (self.fx.change / "tickets" / name).unlink()
        code, out, _ = run(["--root", str(self.fx.root), "frontier", "0003"])
        self.assertEqual(code, 0)
        self.assertIn("every ticket is done", out)

    def test_status_and_render(self):
        code, out, _ = run(["--root", str(self.fx.root), "status", "0003"])
        self.assertEqual(code, 0)
        self.assertIn("2 todo, 1 done, 1 reopened", out)
        self.assertIn("T3  todo", out)
        code, out, _ = run(["--root", str(self.fx.root), "render", "0003"])
        self.assertEqual(code, 0)
        self.assertIn("graph TD", out)
        self.assertIn("T1 --> T3", out)
        self.assertIn(':::done', out)


class NewTests(unittest.TestCase):
    def test_allocates_0001_in_an_empty_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run(["--root", tmp, "new", "first-change"])
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), "docs/changes/0001-first-change")
            self.assertTrue((Path(tmp) / "docs/changes/0001-first-change/tickets").is_dir())

    def test_allocates_after_the_highest_existing_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("0001-a", "0007-b", "not-a-change"):
                (Path(tmp) / "docs/changes" / name).mkdir(parents=True)
            code, out, _ = run(["--root", tmp, "new", "c", "--dry-run"])
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), "docs/changes/0008-c")
            self.assertFalse((Path(tmp) / "docs/changes/0008-c").exists())

    def test_rejects_bad_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run(["--root", tmp, "new", "Bad Slug"])
            self.assertEqual(code, 1)
            self.assertIn("slug", err)


class ResolveTests(unittest.TestCase):
    def test_resolves_by_id_slug_name_and_path(self):
        fx = ChangeFixture()
        self.addCleanup(fx.cleanup)
        for ref in ("3", "0003", "sample", "0003-sample", str(fx.change)):
            self.assertEqual(graph.resolve_change(fx.root, ref), fx.change)
        with self.assertRaises(graph.GraphError):
            graph.resolve_change(fx.root, "missing")


if __name__ == "__main__":
    unittest.main()
