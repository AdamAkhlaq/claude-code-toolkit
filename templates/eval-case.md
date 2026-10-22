# Eval case template

A case is a directory under `evals/`. Copy the two files below into `evals/<case-name>/`, replace every `<PLACEHOLDER>`, and keep only the graders you need.

## `prompt.md`

```markdown
---
name: <CASE_NAME>
description: <WHAT_CLASS_OF_MISTAKE_THIS_CATCHES>
tags: [<TAGS>]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

<THE PROMPT, IN A USER'S WORDS, WITH NO HINT AT THE RIGHT ANSWER>
```

## `graders/<check>.md`

One grader per file. Pick the types that fit.

A pattern in the last message:

```markdown
---
type: regex
pattern: "<PATTERN>"
match: contains
---

PASS if the final message <WHAT IT MUST SAY>. FAIL if <WHAT A WRONG ANSWER LOOKS LIKE>.
```

A skill or tool that must be used (`arm: both` makes it count in the score):

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?<SKILL_NAME>"'
arm: both
---

PASS if the <SKILL_NAME> skill was loaded. FAIL if the agent answered without it.
```

A skill or tool that must not be used:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?<SKILL_NAME>"'
min: 0
max: 0
arm: both
---

PASS if <SKILL_NAME> stayed quiet for this prompt. FAIL if it loaded.
```

One tool before another:

```markdown
---
type: tool_order
before: Bash
after: Edit
---

PASS if the tests ran before any edit. FAIL if an edit came first.
```

A file the run must create:

```markdown
---
type: file_exists
path: <PATH>
exists: true
---

PASS if <PATH> was created. FAIL otherwise.
```

A judge, only when nothing deterministic fits:

```markdown
---
type: llm
---

PASS if <WHAT A CORRECT RESPONSE CONTAINS>.
FAIL if <WHAT A WRONG OR MISSING RESPONSE LOOKS LIKE>.
```
