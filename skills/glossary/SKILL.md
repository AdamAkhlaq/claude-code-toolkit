---
name: glossary
description: Keep the project's vocabulary consistent through GLOSSARY.md at the repo root. Use when you are about to name a new concept, module, flag, state or artifact, when the conversation or the code uses two words for one thing, when a term in an intent, spec, plan or ticket is not in the glossary, or when a user asks what a word means in this project. Also use when writing or reviewing any artifact under docs/changes/.
---

# Glossary

One term, one definition, in `GLOSSARY.md` at the repo root, then used everywhere: code, artifacts, conversation. The glossary is the project's own language, written in its own words.

## When a term is needed

1. **Read `GLOSSARY.md` first.** If the concept is already there under another name, use that name. Do not introduce a synonym.
2. **Look in the code.** If the codebase already calls the thing something, that is the term, even if a better word exists. Record it. Renaming is a change of its own.
3. **Coin only when nothing exists.** Pick a word that a newcomer could guess the meaning of, that is not already used for something else in the project, and that reads naturally as an identifier in the project's language.
4. **Challenge weak terms.** `Handler`, `manager`, `helper`, `util`, `data`, `info`, `item`, `process` and `thing` name nothing. When one of these appears in a draft, ask what the thing actually is and name that.
5. **Write the entry.** One line: the term in bold, then a definition in one or two sentences in the project's words, with the distinction from the nearest neighbouring term when there is one. Add `Not:` and the rejected synonyms when the conversation produced them, so nobody reintroduces them.

## When a term changes

A term is never redefined in passing. If a meaning has to change, the entry is edited and a line beneath it records the old meaning and the date, so older artifacts still read correctly.

## When reviewing an artifact

Before an intent, spec, plan or ticket is presented at a gate, read it against the glossary:

- Every glossary term it uses is used with the glossary meaning.
- Every concept it introduces is either a glossary term or gets an entry in the same commit.
- No two words are used for one thing within the artifact.

List the terms added or changed when presenting the artifact, so the user reviews the vocabulary with the work.

## Rules

- Entries are alphabetical within their section when the glossary has sections, otherwise in the order coined. Follow the file's existing order.
- Definitions use other glossary terms where they can, and nothing undefined.
- Never delete an entry a committed artifact still uses. Mark it `Deprecated:` with its replacement.
- If the repo has no `GLOSSARY.md`, say so and suggest `/toolkit:setup`, which seeds one from the code. Do not create it here.
