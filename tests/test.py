import json, os, subprocess, sys, tempfile
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "session_cost.py"); ok = True
def run(*a): p = subprocess.run([sys.executable, S, *a], capture_output=True, text=True); return p.returncode, p.stdout
def expect(n, c, v=True):
    global ok; ok &= bool(c); print(("ok   " if c else "FAIL ") + n + ("" if c else f" -> {v}"))
root = tempfile.mkdtemp(); proj = os.path.join(root, "proj"); os.makedirs(proj)
def msg(i, model, cr, cw, out, kw="MYGAME"):
    return json.dumps({"type": "assistant", "requestId": f"r{i}", "message": {"id": f"m{i}", "model": model, "content": kw,
            "usage": {"input_tokens": 10, "output_tokens": out, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw}}})
lines = [msg(i, "claude-opus-x", 100_000, 10_000, 500) for i in range(30)]
lines += [lines[0]] * 5                                         # duplicated chunks must be counted once
sid = os.path.join(proj, "sess1"); open(sid + ".jsonl", "w").write("\n".join(lines) + "\n")
os.makedirs(os.path.join(sid, "subagents"))
open(os.path.join(sid, "subagents", "agent-1.jsonl"), "w").write("\n".join(msg(100 + i, "claude-haiku-x", 20_000, 1_000, 200, "") for i in range(10)) + "\n")
code, out = run("MYGAME", "--root", root)
expect("measures and exits 0", code == 0, out)
expect("main calls de-duplicated (30, not 35)", "30 calls" in out, out)
expect("sub-agent logs are included", "sub-agents: 1 logs, 10 calls" in out, out)
expect("both TTL assumptions printed", "5-min cache TTL" in out and "1-hour TTL" in out, out)
c2, o2 = run("NOSUCHKEYWORD", "--root", root); expect("no matching session => unmeasured (3)", c2 == 3, o2)
c3, o3 = run("MYGAME", "--root", os.path.join(root, "nope")); expect("missing root => unmeasured (3)", c3 == 3, o3)
bp = os.path.join(root, "bad-prices.json"); open(bp, "w").write("[1, 2]")
c4, o4 = run("MYGAME", "--root", root, "--prices", bp); expect("malformed --prices file is exit 2, not a traceback", c4 == 2 and "Traceback" not in o4, o4)
c5, o5 = run("MYGAME", "--root", root, "--prices", os.path.join(root, "missing.json")); expect("missing --prices file is exit 2", c5 == 2, o5)
expect("small amounts show cents (not $0)", "$0.0" in out or "$0.1" in out or "$0.2" in out, out)
sys.exit(0 if ok else 1)
