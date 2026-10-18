#!/usr/bin/env bash
cd "$(dirname "$0")/.."
run() { printf '$ %s\n' "$*"; "$@"; printf '[exit %s]\n\n' "$?"; }
echo "# Cost of every session whose log mentions MYGAME (synthetic logs; your real root is ~/.claude/projects)"
run python3 scripts/session_cost.py MYGAME --root examples/fake-projects
echo "# A keyword that matches nothing is 'unmeasured' (exit 3), not 'free'"
run python3 scripts/session_cost.py NOSUCHKEYWORD --root examples/fake-projects
