---
description: Scaffold or rewrite a project README from the Standard Readme template.
argument-hint: [project name or path]
disable-model-invocation: true
---

Create or rewrite a README for: **$ARGUMENTS** (defaults to the current repo if no
argument is given).

Follow the `docs:readme` skill for the Standard Readme structure, section order,
and the quality rubric. The blank template is at `skills/readme/templates/readme.md`.

Steps:

1. **Apply the `readme` skill** to load the canonical structure and rubric.
2. **Inspect the project:** infer the name, purpose, install steps, and a minimal
   usage example from the code, package manifests, and entry points. If a README
   already exists, treat it as input to improve, not overwrite blindly — preserve
   anything still accurate.
3. **Draft the README:** fill the template in the spec's section order. Ensure the
   first screen answers what/why/how, and that Install and Usage are runnable.
   Keep deep material out — link to `docs/` (Diátaxis) instead of bloating it.
4. **Write the file** to `README.md` at the project root (or the given path). If
   overwriting an existing README, show the user a diff/summary of what changed
   before finalising.
5. **Print the path** and flag anything you couldn't verify (e.g. install steps
   you inferred but didn't run).
