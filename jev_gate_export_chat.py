"""JEV-gate for export-chat: 10 binary checks, verdict = passed/10. PASS if >= 0.9.

Portable: picks a live session dynamically (no hardcoded IDs or user paths).
Place next to export_chat.py (or set EXPORT_CHAT_SKILL to its path) and run.
"""
import os, re, subprocess, sys, tempfile, json

SKILL = os.environ.get("EXPORT_CHAT_SKILL") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "export_chat.py")
ZERO_DB = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "opencode", "opencode.db")
REAL_DB = os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "opencode.db")
TMP = os.path.join(tempfile.gettempdir(), "jev_gate_opencode")
os.makedirs(TMP, exist_ok=True)

def run(*args):
    p = subprocess.run([sys.executable, SKILL, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    return p

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

# Pick a live session dynamically: newest with actual messages
r = run("--list", "--list-all", "--harness", "opencode")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
lines = [l for l in (r.stdout or "").splitlines() if "|" in l]
SID = lines[0].split()[0] if lines else ""
check("list finds sessions", bool(SID) and m and int(m.group(1)) > 0,
      (m.group(0) if m else "none"))

# 2. full export of live session
out = os.path.join(TMP, "jev_full.md")
r = run("-s", SID, "-o", out)
check("export exit 0 + non-empty file", r.returncode == 0 and os.path.isfile(out) and os.path.getsize(out) > 1000,
      f"size={os.path.getsize(out) if os.path.isfile(out) else '-'}")

# 3-4. content checks
t = open(out, encoding="utf-8").read() if os.path.isfile(out) else ""
tool_pat = r"(?m)^\[TOOL:"
n_tools = len(re.findall(tool_pat, t))
check("TOOL blocks present (type=tool parser)", n_tools > 0, f"count={n_tools}")
check("user text present", len(re.findall(r"\| USER \|", t)) > 0)

# 5. --db pointing at a 0-byte placeholder falls back to the real DB
r = run("--db", ZERO_DB, "--list", "--harness", "opencode")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
check("0-byte --db falls back to real DB", m and int(m.group(1)) > 0, (m.group(0) if m else "no match"))

# 6. --db explicit real path
out6 = os.path.join(TMP, "jev_db.md")
r = run("--db", REAL_DB, "-s", SID, "-o", out6)
check("explicit --db works", r.returncode == 0 and os.path.isfile(out6) and os.path.getsize(out6) > 1000)

# 7. --no-tools
out7 = os.path.join(TMP, "jev_notools.md")
r = run("-s", SID, "--no-tools", "-o", out7)
t7 = open(out7, encoding="utf-8", errors="replace").read() if os.path.isfile(out7) else ""
# Rendered tool blocks start at line beginning; inline mentions in message
# bodies (docs quoting "[TOOL: ...]") must not count.
n7 = len(re.findall(tool_pat, t7))
check("no-tools excludes TOOL blocks", r.returncode == 0 and n7 == 0, f"line-blocks={n7}")

# 8. bogus session -> clean fail
r = run("-s", "ses_DOESNOTEXIST123", "-o", os.path.join(TMP, "jev_bogus.md"))
check("bogus session clean error+exit!=0", r.returncode != 0 and "not found" in ((r.stderr or "") + (r.stdout or "")).lower())

# 9. directory filter (workspace of the picked session)
mdir = re.search(r"\|\s+([^|]+?)\s+\|\s+\[opencode\]", lines[0]).group(1) if lines else None
if mdir:
    r = run("--list", "--harness", "opencode", "--directory", mdir)
    m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
    check("directory filter works", m and int(m.group(1)) > 0, (m.group(0) if m else "no match"))
else:
    check("directory filter works", False, "no dir parsed")

# 10. compiles + version
import py_compile
try:
    py_compile.compile(SKILL, doraise=True)
    ok = True
except Exception:
    ok = False
ver = 'VERSION = "2.2.0"' in open(SKILL, encoding="utf-8").read()
check("compiles + version 2.2.0", ok and ver)

passed = sum(1 for _, c, _ in results if c)
verdict = passed / len(results)
print(f"\nJEV VERDICT: {verdict:.2f} ({passed}/{len(results)}) -> {'PASS' if verdict >= 0.9 else 'FAIL'}")
sys.exit(0 if verdict >= 0.9 else 1)
