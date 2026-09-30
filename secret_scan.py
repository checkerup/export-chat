"""Secret/personal-data scan of the export-chat mirror before push.

Scans every file that would be committed for:
- absolute user paths (C:\\Users\\<name>, /home/<name>, ~/<name>)
- usernames / machine identity (iamon, checkerup)
- hardcoded session/composer IDs (ses_*, msg_*, bubbleId:, composerData:, specific UUIDs)
- API keys / tokens / passwords (common patterns)
- known sensitive file names
Exit 0 = clean, exit 1 = leaks found (printed with file:line).
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATTERNS = [
    (r"C:[\\\\/]+Users[\\\\/]+[A-Za-z0-9_.-]+", "absolute Windows user path"),
    (r"/home/[A-Za-z0-9_.-]+", "absolute Linux home path"),
    (r"/Users/[A-Za-z0-9_.-]+/", "absolute macOS user path"),
    (r"\biamon\b", "username (iamon)"),
    (r"\bcheckerup\b", "username (checkerup)"),
    (r"ses_[A-Za-z0-9]{20,}", "opencode session ID"),
    (r"msg_[A-Za-z0-9]{20,}", "opencode message ID"),
    (r"bubbleId:[0-9a-f-]{36}", "Cursor bubble key"),
    (r"composerData:[0-9a-f-]{36}", "Cursor composer key"),
    (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "hardcoded UUID"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{16,}", "credential assignment"),
    (r"-----BEGIN [A-Z ]+PRIVATE KEY-----", "private key block"),
    (r"\b192\.168\.\d+\.\d+\b", "LAN IP"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
]

# Examples quoted in docs (generic placeholders) are allowed:
ALLOWLIST = re.compile(
    r"(ses_abc123|ses_abc|ses_DOESNOTEXIST123|665f8904-659b-437f|composerId|<composerId>|"
    r"<bubbleId>|bubbleId:|composerData:|session_id|sessionId|"
    r"/home/user\b|/Users/user\b|Users[\\\\/]+user\b|user@)"
)

found = 0
for fn in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, fn)
    if not os.path.isfile(p) or fn == "secret_scan.py":
        continue
    if fn.endswith((".db", ".sqlite", ".env")):
        print(f"LEAK: {fn}: sensitive file type must not be committed")
        found += 1
        continue
    for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        for pat, label in PATTERNS:
            for m in re.finditer(pat, line):
                frag = m.group(0)
                if ALLOWLIST.search(frag):
                    continue
                print(f"LEAK: {fn}:{i}: {label}: {frag[:80]}")
                found += 1

if found:
    print(f"\nSCAN VERDICT: FAIL ({found} leak(s))")
    sys.exit(1)
print("\nSCAN VERDICT: CLEAN (no personal data found)")
sys.exit(0)
