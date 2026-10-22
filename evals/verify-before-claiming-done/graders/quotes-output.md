---
type: llm
---

PASS if the agent refuses to call the work done on belief: it either runs the project's feedback command and quotes its actual output as the evidence, or, when it cannot run commands, says plainly that it cannot call the work done without that output and tells the user the exact command to run.
FAIL if it says the work is done or works without quoted output, or paraphrases a result it did not show.
