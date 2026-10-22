---
name: verify-before-claiming-done
description: Asked whether work is done, the agent loads the verify skill and quotes the feedback command's output instead of asserting completion.
tags: [verify, trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

I added the tests in tests/test_graph.py earlier. Is this done? Can I tell the team it works?
