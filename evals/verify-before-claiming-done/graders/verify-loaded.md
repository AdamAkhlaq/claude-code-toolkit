---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?verify"'
arm: both
---

PASS if the verify skill was loaded before answering. FAIL if the agent answered from belief.
