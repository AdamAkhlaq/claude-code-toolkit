---
type: regex
pattern: "/toolkit:setup"
match: contains
---

PASS if the final message tells the user to run /toolkit:setup, because the repo has no .claude/toolkit.json yet. FAIL if it sends them to /toolkit:intent or anywhere else first.
