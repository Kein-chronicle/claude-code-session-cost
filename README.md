# claude-code-session-cost

**Estimate what a Claude Code project cost from its session logs, sub-agents included, with both cache-TTL price assumptions shown.**

[![test](https://github.com/Kein-chronicle/claude-code-session-cost/actions/workflows/test.yml/badge.svg)](https://github.com/Kein-chronicle/claude-code-session-cost/actions/workflows/test.yml) ![license](https://img.shields.io/badge/license-MIT-blue.svg) ![dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

## Why

Cost is roughly context size times number of turns; output is usually a small share. The useful question is "what did this project cost", and the sub-agent logs live in a separate folder next to the session.

## Install

**As a Claude Code skill** (Claude uses it when the task matches the skill description):

```sh
git clone https://github.com/Kein-chronicle/claude-code-session-cost.git ~/.claude/skills/claude-session-cost
```

For a single project, clone into `<project>/.claude/skills/claude-session-cost` instead, then start a new Claude Code session.

**As plain scripts:**

```sh
git clone https://github.com/Kein-chronicle/claude-code-session-cost.git
cd claude-code-session-cost
```

**Requires:** Python 3.10+.

## Quick start

Run it on synthetic logs:

```console
$ bash examples/demo.sh
# Cost of every session whose log mentions MYGAME (synthetic logs; your real root is ~/.claude/projects)
$ python3 scripts/session_cost.py MYGAME --root examples/fake-projects
main sessions: 1 logs, 30 calls, avg context 110k tokens
  cost $3.75 (5-min cache TTL) .. $4.88 (1-hour TTL)   [prices ASSUMED, see --prices]
  share: cache_write 50%, cache_read 40%, output 10%, input 0%
sub-agents: 1 logs, 10 calls, avg context 21k tokens
  cost $0.04 (5-min cache TTL) .. $0.05 (1-hour TTL)   [prices ASSUMED, see --prices]
  share: cache_read 47%, cache_write 29%, output 23%, input 0%

Reading it: cost ~ context size x number of turns; output is usually ~10%. Cheap = small context, not 'delegation' per se.
[exit 0]

# A keyword that matches nothing is 'unmeasured' (exit 3), not 'free'
$ python3 scripts/session_cost.py NOSUCHKEYWORD --root examples/fake-projects
UNMEASURED: no session mentions 'NOSUCHKEYWORD' >= 20 times
[exit 3]
```

The output above is real: it is produced by the files in `examples/`.

## Use it on your own files

```sh
python3 scripts/session_cost.py "my-project-keyword" --root ~/.claude/projects --prices my-prices.json
```

Sample inputs for every file format are in `examples/` and `tests/`; the details are in [SKILL.md](SKILL.md).

## What it checks

- Finds sessions whose log mentions a keyword at least `--min-hits` times. Exit `0` measured, `2` bad `--prices` file, `3` could not measure.
- De-duplicates repeated streamed chunks by message id and counts sub-agent logs separately.
- Prints a range: a 5-minute cache-TTL price and a 1-hour one. Prices are assumptions you can override with `--prices`.
- No match or no root: exit `3` (unmeasured), never a cost of zero.

## Limits

- Estimates from local logs; your invoice is the authority.
- Built-in prices are placeholders and will go stale.

## Related projects

These solve neighbouring problems; use them when they fit better.

- **ccusage**: the established usage reporter by day and session; this answers per-project/keyword totals

## More from the same collection

Small, tested tools that grew out of running AI agents and game/app pipelines for months:

- [**claude-code-memory-lint**](https://github.com/Kein-chronicle/claude-code-memory-lint): Lint a Claude Code memory folder: orphan files, missing files, oversized index lines, and the index lines that are silently cut at load.
- [**claude-code-launchd-loops**](https://github.com/Kein-chronicle/claude-code-launchd-loops): Generate a macOS launchd job that runs Claude Code headless on a schedule, from one command.
- [**pidfile-process-watchdog**](https://github.com/Kein-chronicle/pidfile-process-watchdog): A small process watchdog with an honest state machine: pid and working-directory identity, restart grace, flap warnings, and giving up.

## Development

```sh
python3 tests/test.py
```

The tests include inputs that are supposed to be rejected, so a green run also shows the checks can fail. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

If this saved you a debugging session, a star helps other people find it. Bug reports and failing test cases are even better.

<sub>Keywords: claude-code, claude-skills, agent-skills, cost-tracking, tokens, llm-cost, observability</sub>
