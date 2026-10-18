---
name: claude-session-cost
description: Measure what a Claude Code project or work cycle really cost from the raw session logs - main sessions plus sub-agent logs, de-duplicated, with cache-read/write/output breakdown and both cache-TTL assumptions - and understand why long sessions are expensive. Use when a cycle's token/usage bill is a surprise, when comparing delegation vs staying in one session, or when setting a budget and an early-warning meter (not a blocker).
---

# claude-session-cost

A meter, not a gate: it exits 0 when it measured, 2 for a bad `--prices` file and 3 when it could not measure. Surface the number loudly and let a human decide.

```bash
python3 scripts/session_cost.py MY-PROJECT-SLUG --root ~/.claude/projects --min-hits 20
python3 tests/test.py
```
Associates sessions by how many times the keyword appears (a real project: thousands; unrelated sessions: 0-1).

## What measurements like these tend to show

Observations from the author's own long agent runs (one large production cycle of several thousand calls). Treat them as hypotheses to check on your data, not as benchmarks.

- **Cost is roughly context size x turns.** In that cycle cache reads were about two thirds of the cost, cache writes about a fifth and output only about a tenth.
- Sub-agents can make more calls than the main session and still cost far less, because their context is small. **Cheap is not "delegation" per se - it is a small context.**
- A long main context is usually filled by file reads. Large images read repeatedly are the classic culprit.
- **Sub-agent logs live in `<session-id>/subagents/agent-*.jsonl`**, not in the main log. Ignoring them hides part of the bill.
- Do not count base64 characters as tokens: an early "images are 95 % of the cost" claim came from exactly that. Session length (cost grows roughly with its square) was the dominant term.
- Repeated streamed chunks of one response carry identical `usage`; dedupe by (message id, request id) or you double count.
- State the price table and the cache-TTL assumption (it moves the total by about +-10 %); this tool prints both.
- Practical levers: do not re-read big images (use one downscaled view), keep the orchestrator's context small, give workers narrow prompts, split long loops at natural checkpoints, and cap review re-rounds (a round limit is a cost rule).
- On a flat-rate plan, measure the quota share too, not just dollars.
