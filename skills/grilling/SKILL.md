---
name: grilling
description: Ask the user the questions a piece of work cannot proceed without, in one numbered round with a recommended answer for each. Use when an intent, spec or plan has gaps only a human can fill, when a decision is needed before building, when requirements are ambiguous, or whenever you are about to ask the user more than one question. Not for facts you can look up yourself.
---

# Grilling

A round of questions that moves the work forward. The agent finds facts. The human makes decisions. A question is only asked when looking cannot answer it.

## Before asking

1. **Look first.** Search the code, the docs, `GLOSSARY.md`, `docs/changes/`, `docs/adr/`, git history and, when the subject is external, the web. Anything found this way is stated as a finding with its source, not asked.
2. **Sort what is left.** Each remaining question is one of:
   - `Fact`: something that exists somewhere you cannot reach, such as production behaviour, a stakeholder's constraint, or an undocumented convention. Ask who knows, or ask the user to look.
   - `Decision`: a choice between workable options where the user's preference is what matters. Ask the user.
     A question that is neither is not asked. It is answered by you, and the answer is written down as an assumption.
3. **Drop the cheap ones.** If a wrong answer is cheap to reverse later, take the recommended answer silently and note the assumption in the artifact's Open questions. Save the user's attention for one-way doors and for anything that changes what gets built.

## The round

Ask every remaining question in one message, as a numbered list. For each:

- One sentence stating the question, tagged `Fact:` or `Decision:`.
- The options, when there are a few. Two to four, each a short phrase.
- `Recommended:` the answer you would take and the reason in a clause. Every question has a recommendation; a question without one means you have not thought about it enough to ask it.
- What changes depending on the answer, in a clause, when it is not obvious.

Keep a round to seven questions or fewer. Put the one that most changes the shape of the work first. Tell the user they can answer by number (`1 yes, 2 the second option, 3 see below`) and that `recommended` accepts every recommendation at once.

Do not pad the round with questions whose answer you already know, and do not re-ask something already answered in the conversation, the input, or an artifact.

## After the round

- Apply the answers. Where the user's answer differs from the recommendation, follow the user without re-arguing.
- Record every question and its answer in the artifact being produced, under Open questions, as `Resolved:` lines. An unanswered question stays as `Open:` with its owner named.
- If the answers raise new questions, run at most one more round. After two rounds, stop asking: write what is still unknown as open questions in the artifact and move on. The gate is where the user reviews what remains open.
- If an answer introduces a term the project has not used before, see the `toolkit:glossary` skill before writing it into an artifact.

## Not grilling

- A single yes or no on an action you are about to take. Just ask it.
- Confirming a choice the user already made.
- Asking the user to pick between options you have not examined.
