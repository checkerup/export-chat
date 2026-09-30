"""JEV-gate #2 for export-chat: all-harness audit. PASS if verdict >= 0.9.

Portable: discovers sessions dynamically (no hardcoded IDs, paths, or
user-specific content). Place next to export_chat.py (or set
EXPORT_CHAT_SKILL to its path) and run.
"""
import os, re, subprocess, sys, tempfile

SKILL = os.environ.get("EXPORT_CHAT_SKILL") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "export_chat.py")
TMP = os.path.join(tempfile.gettempdir(), "jev_gate_harnesses")
os.makedirs(TMP, exist_ok=True)

def run(*args):
    p = subprocess.run([sys.executable, SKILL, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    return p

def first_session(harness):
    r = run("--list", "--harness", harness)
    lines = [l for l in (r.stdout or "").splitlines() if "|" in l]
    return r, (lines[0].split()[0] if lines else None)

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

# Cursor: list + full export of a session with real bodies
r, sid = first_session("cursor")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
has_cursor = bool(m and int(m.group(1)) > 0 and sid)
check("cursor list finds sessions" if has_cursor else "cursor absent (graceful)",
      has_cursor or (r.returncode in (0, 1)))
if has_cursor:
    out = os.path.join(TMP, "jev_cursor.md")
    r2 = run("-s", sid, "--harness", "cursor", "-o", out)
    t = open(out, encoding="utf-8", errors="replace").read() if os.path.isfile(out) else ""
    n_u = len(re.findall(r"\| USER \|", t))
    n_a = len(re.findall(r"\| ASSISTANT \|", t))
    if n_u + n_a > 0:
        check("cursor export real bodies", r2.returncode == 0 and n_u > 0 and n_a > 0,
              f"user={n_u} assist={n_a}")
    else:
        # first session empty is legitimate; scan up to ALL composers
        r3 = run("--list", "--list-all", "--harness", "cursor")
        lines = [l for l in (r3.stdout or "").splitlines() if "|" in l]
        okany, detail = False, "no non-empty composer found"
        for l in lines[:60]:
            s2 = l.split()[0]
            o2 = os.path.join(TMP, "jev_cursor2.md")
            rr = run("-s", s2, "--harness", "cursor", "-o", o2)
            if rr.returncode != 0:
                continue
            t2 = open(o2, encoding="utf-8", errors="replace").read() if os.path.isfile(o2) else ""
            n2u = len(re.findall(r"\| USER \|", t2))
            n2a = len(re.findall(r"\| ASSISTANT \|", t2))
            if n2u > 0 and n2a > 0:
                okany, detail = True, f"sid={s2[:8]} user={n2u} assist={n2a}"
                break
        check("cursor export real bodies", okany, detail)

# Continue
r, sid = first_session("continue")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
if m and int(m.group(1)) > 0 and sid:
    out = os.path.join(TMP, "jev_continue.md")
    r2 = run("-s", sid, "--harness", "continue", "-o", out)
    t = open(out, encoding="utf-8", errors="replace").read() if os.path.isfile(out) else ""
    n_u = len(re.findall(r"\| USER \|", t))
    check("continue export has messages", r2.returncode == 0 and n_u > 0, f"user={n_u}")
else:
    check("continue absent (graceful)", True)

# Trae: sessions + metadata export
r, sid = first_session("trae")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
if m and int(m.group(1)) > 0 and sid:
    out = os.path.join(TMP, "jev_trae.md")
    r2 = run("-s", sid, "--harness", "trae", "-o", out)
    t = open(out, encoding="utf-8", errors="replace").read() if os.path.isfile(out) else ""
    check("trae metadata export honest", r2.returncode == 0 and "IndexedDB" in t)
else:
    check("trae absent (graceful)", True)

# Windsurf: graceful result either way (index may legitimately be empty)
r, sid = first_session("windsurf")
m = re.search(r"(\d+) session\(s\) found", r.stdout or "")
check("windsurf graceful", r.returncode == 0 and m is not None, (m.group(0) if m else "no match"))

# Undetected harness: graceful
r = run("--list", "--harness", "zed")
check("undetected harness graceful", r.returncode != 0 and "not detected" in ((r.stdout or "") + (r.stderr or "")).lower())

# Version + compiles
import py_compile
try:
    py_compile.compile(SKILL, doraise=True)
    ok = True
except Exception:
    ok = False
src = open(SKILL, encoding="utf-8").read()
check("compiles + version 2.2.0", ok and 'VERSION = "2.2.0"' in src)

passed = sum(1 for _, c, _ in results if c)
verdict = passed / len(results)
print(f"\nJEV VERDICT (harnesses): {verdict:.2f} ({passed}/{len(results)}) -> {'PASS' if verdict >= 0.9 else 'FAIL'}")
sys.exit(0 if verdict >= 0.9 else 1)
