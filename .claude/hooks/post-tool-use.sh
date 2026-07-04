#!/usr/bin/env bash
#
# ARCHETYPE: COPY-AND-TWEAK — works as-is, but the formatter `case` is yours to edit.
#
# PostToolUse hook for Edit|Write. Runs AFTER Claude edits a file. We read the
# tool call JSON on stdin, pull .tool_input.file_path, and run the matching
# formatter over just that file. Stay SILENT on success; on failure print to
# stderr and exit 1 so the problem surfaces.
#
# Requires `jq`. Registered under hooks.PostToolUse (matcher "Edit|Write") in
# .claude/settings.json — this script does nothing unless that registration exists.

set -euo pipefail

input="$(cat)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"

# Nothing to format (no path, or file no longer exists) — done.
[ -z "$file_path" ] && exit 0
[ -f "$file_path" ] || exit 0

# ── PERSONALISE: map file types to your formatter of choice ───────────────────
# Add branches for your stack (gofmt, black, rustfmt, …). The default handles the
# web-ish types via prettier. Unmatched types fall through and are left untouched.
case "$file_path" in
  *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.scss|*.md)
    npx --no-install prettier --write "$file_path"
    ;;
  *)
    exit 0
    ;;
esac
# ──────────────────────────────────────────────────────────────────────────────

exit 0
