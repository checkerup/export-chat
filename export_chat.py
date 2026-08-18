#!/usr/bin/env python3
"""Export opencode chat history from SQLite database to Markdown."""

import sqlite3
import json
import sys
import os
import argparse
from datetime import datetime

# Force UTF-8 on stdout/stderr so non-ASCII (e.g. Cyrillic, emoji) doesn't crash
# the script on Windows where the default console code page is often cp1251/cp437.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DB_PATH_CANDIDATES = [
    os.path.expanduser("~/.local/share/opencode/opencode.db"),
]

WORKSPACE_DIR = os.environ.get("OPENCODE_WORKSPACE_DIR", "")


def find_db():
    for p in DB_PATH_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def get_session_id(conn, directory=None, latest=False, session_id=None):
    c = conn.cursor()
    if session_id:
        c.execute("SELECT id FROM session WHERE id = ?", (session_id,))
        row = c.fetchone()
        if row:
            return row[0]
        print(f"Session {session_id} not found.", file=sys.stderr)
        return None

    if directory:
        c.execute(
            "SELECT id, time_updated FROM session WHERE directory = ? ORDER BY time_updated DESC LIMIT 1",
            (directory,),
        )
    else:
        c.execute("SELECT id, time_updated FROM session ORDER BY time_updated DESC LIMIT 1")

    row = c.fetchone()
    if row:
        return row[0]
    return None


def format_role(role):
    mapping = {"user": "USER", "assistant": "ASSISTANT", "system": "SYSTEM"}
    return mapping.get(role, role.upper())


def extract_text_from_part(part_data):
    ptype = part_data.get("type", "unknown")

    if ptype == "text":
        text = part_data.get("text", "").strip()
        return ("text", text) if text else None

    if ptype in ("tool", "tool-invocation"):
        tool_obj = part_data.get("toolInvocation", part_data.get("tool", {}))
        if isinstance(tool_obj, dict):
            tname = tool_obj.get("toolName", "unknown")
            tstate = tool_obj.get("state", "")
            targs = tool_obj.get("args", {})
            tresult = tool_obj.get("result", None)

            label = f"[TOOL: {tname}"
            if tstate:
                label += f" ({tstate})"
            label += "]"

            parts = [label]
            if targs and isinstance(targs, dict) and targs:
                args_str = json.dumps(targs, ensure_ascii=False, indent=2)
                if len(args_str) > 800:
                    args_str = args_str[:800] + "\n... (truncated)"
                parts.append(f"Args:\n{args_str}")

            if tresult is not None:
                result_str = str(tresult)
                if len(result_str) > 2000:
                    result_str = result_str[:2000] + "\n... (truncated)"
                parts.append(f"Result:\n{result_str}")

            return ("tool", "\n".join(parts))

    if ptype in ("step-start", "step-finish"):
        return None

    return None


def export_session(conn, session_id, output_path, include_tools=True):
    c = conn.cursor()

    c.execute("SELECT title, directory FROM session WHERE id = ?", (session_id,))
    row = c.fetchone()
    title = row[0] if row else "Unknown"
    directory = row[1] if row else "Unknown"

    c.execute(
        "SELECT id, data, time_created FROM message WHERE session_id = ? ORDER BY time_created",
        (session_id,),
    )
    messages = c.fetchall()

    if not messages:
        print(f"No messages found for session {session_id}", file=sys.stderr)
        return 0

    lines = []
    lines.append(f"# Chat Export: {title}")
    lines.append(f"- Session ID: `{session_id}`")
    lines.append(f"- Directory: `{directory}`")
    lines.append(f"- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Total messages: {len(messages)}")
    lines.append("")

    msg_num = 0

    for m in messages:
        msg_id = m[0]
        data = json.loads(m[1]) if m[1] else {}
        role = data.get("role", "unknown")
        ts = datetime.fromtimestamp(m[2] / 1000).strftime("%Y-%m-%d %H:%M:%S") if m[2] else "N/A"

        c.execute(
            "SELECT id, data, time_created FROM part WHERE message_id = ? ORDER BY time_created",
            (msg_id,),
        )
        parts = c.fetchall()

        text_parts = []
        tool_parts = []

        for p in parts:
            pdata = json.loads(p[1]) if p[1] else {}
            result = extract_text_from_part(pdata)
            if result:
                rtype, rtext = result
                if rtype == "text":
                    text_parts.append(rtext)
                elif rtype == "tool":
                    tool_parts.append(rtext)

        if not text_parts and (not tool_parts or not include_tools):
            continue

        msg_num += 1
        role_label = format_role(role)

        lines.append("---")
        lines.append(f"## #{msg_num} | {role_label} | {ts}")
        lines.append("")

        if text_parts:
            lines.append("\n\n".join(text_parts))
            lines.append("")

        if tool_parts and include_tools:
            for tp in tool_parts:
                lines.append(tp)
                lines.append("")

    output = "\n".join(lines)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    return msg_num


def list_sessions(conn, directory=None, limit=20):
    c = conn.cursor()
    if directory:
        c.execute(
            "SELECT id, title, directory, time_updated FROM session WHERE directory = ? ORDER BY time_updated DESC LIMIT ?",
            (directory, limit),
        )
    else:
        c.execute(
            "SELECT id, title, directory, time_updated FROM session ORDER BY time_updated DESC LIMIT ?",
            (limit,),
        )

    rows = c.fetchall()
    for r in rows:
        ts = datetime.fromtimestamp(r[3] / 1000).strftime("%Y-%m-%d %H:%M") if r[3] else "N/A"
        print(f"  {r[0]}  |  {ts}  |  {r[1]}  |  {r[2]}")

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Export opencode chat history")
    parser.add_argument("--session-id", "-s", help="Specific session ID to export")
    parser.add_argument("--output", "-o", help="Output file path (default: <project_dir>/chat_export_<session>.md)")
    parser.add_argument("--directory", "-d", help="Project directory to find session for")
    parser.add_argument("--list", "-l", action="store_true", help="List recent sessions")
    parser.add_argument("--list-all", action="store_true", help="List all sessions")
    parser.add_argument("--no-tools", action="store_true", help="Exclude tool calls from export")
    parser.add_argument("--db", help="Path to opencode.db (auto-detected if omitted)")

    args = parser.parse_args()

    db_path = args.db or find_db()
    if not db_path:
        print("Error: opencode.db not found. Use --db to specify path.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)

    if args.list or args.list_all:
        directory = args.directory or WORKSPACE_DIR or None
        limit = 9999 if args.list_all else 20
        count = list_sessions(conn, directory=directory, limit=limit)
        print(f"\n{count} session(s) found.")
        conn.close()
        return

    directory = args.directory or WORKSPACE_DIR or None
    session_id = get_session_id(conn, directory=directory, session_id=args.session_id)

    if not session_id:
        print("Error: No session found. Use --list to see available sessions.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    if args.output:
        output_path = args.output
    elif directory and os.path.isdir(directory):
        output_path = os.path.join(directory, f"chat_export_{session_id[:16]}.md")
    else:
        output_path = os.path.join(os.getcwd(), f"chat_export_{session_id[:16]}.md")

    count = export_session(conn, session_id, output_path, include_tools=not args.no_tools)

    size = os.path.getsize(output_path) if count > 0 else 0
    print(f"Exported {count} messages to {output_path} ({size:,} bytes)")

    conn.close()


if __name__ == "__main__":
    main()
