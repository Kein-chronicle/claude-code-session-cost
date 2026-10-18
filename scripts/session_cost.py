#!/usr/bin/env python3
"""session_cost: measure what a piece of Claude Code work actually cost, from the raw session logs.
Counts main sessions AND sub-agent logs (<session-id>/subagents/*.jsonl), de-duplicates repeated message chunks,
and prints cost under both cache-write TTL assumptions. Never blocks: it is a meter, not a gate (exit 0).
usage: session_cost.py KEYWORD [--root ~/.claude/projects] [--min-hits 20] [--prices prices.json]
exit 0 measured | 2 bad --prices file | 3 could not measure (never a cost of zero)
exit 0 measured | 2 bad input | 3 could not measure (no logs / no session mentions KEYWORD)"""
import argparse, collections, glob, json, os, sys

# USD per million tokens [input, output]. ASSUMED defaults - override with --prices; prices change.
DEFAULT_PRICES = {"opus": [5, 25], "sonnet": [3, 15], "haiku": [1, 5]}
CACHE_READ = 0.1                      # x input price
CACHE_WRITE = {"5m": 1.25, "1h": 2.0}  # x input price, by TTL

def family(model, prices):
    m = (model or "").lower()
    for k in prices:
        if k in m: return k
    return "sonnet" if "sonnet" in prices else next(iter(prices))

def read(path):
    for line in open(path, encoding="utf-8", errors="ignore"):
        try: yield json.loads(line)
        except Exception: continue

def mentions(path, kw):
    n = 0
    for line in open(path, encoding="utf-8", errors="ignore"): n += line.count(kw)
    return n

def tally(paths, prices):
    seen, agg = set(), collections.defaultdict(lambda: collections.Counter())
    for p in paths:
        for o in read(p):
            m = o.get("message") or {}; u = m.get("usage")
            if not u or o.get("type") != "assistant": continue
            key = (m.get("id"), o.get("requestId"))
            if key != (None, None) and key in seen: continue          # chunks of one response repeat the same usage
            seen.add(key)
            f = family(m.get("model"), prices); a = agg[f]
            a["calls"] += 1; a["in"] += u.get("input_tokens", 0); a["out"] += u.get("output_tokens", 0)
            a["cr"] += u.get("cache_read_input_tokens", 0); a["cw"] += u.get("cache_creation_input_tokens", 0)
            a["ctx"] += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return agg

def cost(agg, prices, ttl):
    total = 0.0; parts = collections.Counter()
    for f, a in agg.items():
        pin, pout = prices[f]
        parts["cache_read"] += a["cr"] / 1e6 * pin * CACHE_READ
        parts["cache_write"] += a["cw"] / 1e6 * pin * CACHE_WRITE[ttl]
        parts["input"] += a["in"] / 1e6 * pin; parts["output"] += a["out"] / 1e6 * pout
    return sum(parts.values()), parts

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("keyword"); ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--min-hits", type=int, default=20); ap.add_argument("--prices")
    a = ap.parse_args()
    prices = DEFAULT_PRICES
    if a.prices:
        try:
            prices = json.load(open(a.prices))
            assert isinstance(prices, dict) and prices and all(isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v) for v in prices.values())
        except (OSError, ValueError, AssertionError) as e:
            print(f"bad prices file {a.prices}: expected {{\"family\": [input_usd_per_Mtok, output_usd_per_Mtok]}} ({type(e).__name__})"); return 2
    if not os.path.isdir(a.root): print(f"UNMEASURED: {a.root} not found"); return 3
    mains = [f for f in glob.glob(os.path.join(a.root, "*", "*.jsonl")) if mentions(f, a.keyword) >= a.min_hits]
    if not mains: print(f"UNMEASURED: no session mentions '{a.keyword}' >= {a.min_hits} times"); return 3
    subs = [s for f in mains for s in glob.glob(f[:-6] + "/subagents/*.jsonl")]       # sub-agent logs live beside the session
    for label, paths in (("main sessions", mains), ("sub-agents", subs)):
        agg = tally(paths, prices); calls = sum(x["calls"] for x in agg.values())
        if not calls: print(f"{label}: 0 calls"); continue
        ctx = sum(x["ctx"] for x in agg.values()) / calls
        lo, parts = cost(agg, prices, "5m"); hi, _ = cost(agg, prices, "1h")
        tot = sum(parts.values()) or 1
        print(f"{label}: {len(paths)} logs, {calls} calls, avg context {ctx/1000:.0f}k tokens")
        money = lambda v: f"${v:,.2f}" if v < 10 else f"${v:,.0f}"
        print(f"  cost {money(lo)} (5-min cache TTL) .. {money(hi)} (1-hour TTL)   [prices ASSUMED, see --prices]")
        print("  share: " + ", ".join(f"{k} {v/tot:.0%}" for k, v in parts.most_common()))
    print("\nReading it: cost ~ context size x number of turns; output is usually ~10%. Cheap = small context, not 'delegation' per se.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
