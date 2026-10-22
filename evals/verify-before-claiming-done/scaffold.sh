#!/bin/sh
# A small project with a configured feedback command and one passing test.
set -e
mkdir -p .claude tests
cat > .claude/toolkit.json <<'JSON'
{ "feedbackCommand": "python3 -m unittest discover -s tests", "concurrency": 1, "tracker": "local" }
JSON
touch tests/__init__.py
cat > tests/test_graph.py <<'PY'
import unittest


class GraphTest(unittest.TestCase):
    def test_empty_graph_has_no_frontier(self):
        self.assertEqual([], [])


if __name__ == "__main__":
    unittest.main()
PY
git init -q . && git add -A && git -c user.email=t@example.com -c user.name=t commit -qm "seed"
