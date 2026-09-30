---
name: export-chat
description: >
  Universal chat history export tool for 20+ AI coding harnesses/IDEs. Auto-detects and reads
  conversations from Claude Code, Cursor, Opencode, Continue, Cline, Windsurf, Trae, Aider,
  Codex CLI, Goose, Kilo Code, Roo Code, Cody, Warp, Copilot Chat, Zed, JetBrains AI, Amazon Q,
  Gemini, Tabnine — from SQLite/JSON/JSONL/Markdown/YAML storage. Exports to structured Markdown.
  Use when asked to "export chat", "save conversation", "dump chat history", "export this
  conversation", "save our chat", or when the user wants a record of the discussion across any
  AI tool.
---

# Export Chat

Universal chat history export tool for 20+ AI coding harnesses/IDEs. Auto-detects each tool's
local storage and exports conversations to structured Markdown.

## When to Use

- User asks to "export chat", "save conversation", "dump chat history"
- User wants to save the current discussion for documentation
- User asks "save our chat" or "export this conversation"
- User asks to export from a specific harness (Cursor, Continue, Claude Code, etc.)
- User wants to list sessions across multiple AI tools
- Proactively suggest when a long or important conversation is nearing completion

## How It Works

The skill uses a Python script (`export_chat.py`, v2.2.0) that reads directly from each harness's local storage. It queries the underlying store (SQLite tables, JSON/JSONL files, etc.) to reconstruct the full conversation.

## Support levels (v2.2.0, live-audited 2026-09-30)

- **Verified live** (session list + full export with real bodies tested): Opencode (ranked DB detection, new `tool`/`reasoning`/`patch`/`file` part types), Cursor (bubble storage: `bubbleId:<composerId>:<bubbleId>`, titles from `composerData.name`), Continue (JSON history), Trae (session list + metadata; bodies live in IndexedDB, not SQLite), Windsurf (index-based, empty on test machine → correctly 0 sessions).
- **Code-complete** (documented format implemented, no live data on test machine): Claude Code, Cline/Kilo/Roo, Aider, Codex CLI, Cody, Warp, Goose.
- **Best-effort with honest fallback** (undocumented/private formats return what they find instead of failing silently): Copilot Chat, Zed, JetBrains AI, Amazon Q, Gemini, Tabnine.

Database auto-detection (v2.1.0): candidates are ranked by validity, not by order — files <4KB, non-SQLite files and DBs without a `session` table are skipped. This guards against the 0-byte placeholder at `%LOCALAPPDATA%\opencode\opencode.db` shadowing the real database (`~/.local/share/opencode/opencode.db`, ~1.4GB). Override with `--db <path>` or `OPENCODE_DB` env var.

Part-type coverage (v2.1.0, current opencode format): `text` → message body; `tool` (`state.{input,output,status}`) → `[TOOL: name]` blocks; `reasoning` → `[TOOL: reasoning]`; `patch`/`file` → one-line summary; `step-start`/`step-finish`/`compaction`/unknown → skipped (envelope, no content). Legacy `tool_use`/`tool_result` blobs still render.

## Steps

1. **Determine the project directory** — this is the current working directory of the opencode session (the directory the user launched opencode from).

2. **Run the export script** — use the Bash tool to execute:

```bash
python "<skill_dir>/export_chat.py" --directory "<project_dir>" --output "<project_dir>/chat_export_<timestamp>.md"
```

Where:
- `<skill_dir>` = the directory where this SKILL.md lives (typically `~/.config/opencode/skills/export-chat/`)
- `<project_dir>` = the current working directory of the session
- `<timestamp>` = current date in `YYYYMMDD` format

3. **Report the result** — tell the user where the file was saved, how many messages were exported, and the file size.

## Script Reference

The `export_chat.py` script supports these flags:

| Flag | Short | Description |
|------|-------|-------------|
| `--session-id` | `-s` | Export a specific session by ID |
| `--output` | `-o` | Custom output file path |
| `--directory` | `-d` | Project directory to find the session |
| `--list` | `-l` | List recent sessions |
| `--list-all` | | List all sessions |
| `--no-tools` | | Exclude tool calls from export |
| `--db` | | Custom path to opencode.db |

## Examples

### Export current session to project directory
```bash
python "~/.config/opencode/skills/export-chat/export_chat.py" --directory "/path/to/project"
```

### Export with custom output path
```bash
python "~/.config/opencode/skills/export-chat/export_chat.py" -s "ses_abc123" -o "/tmp/chat.md"
```

### List sessions for a project
```bash
python "~/.config/opencode/skills/export-chat/export_chat.py" --list --directory "/path/to/project"
```

### Export without tool calls (text only)
```bash
python "~/.config/opencode/skills/export-chat/export_chat.py" --directory "/path/to/project" --no-tools
```

## Output Format

The exported Markdown file has this structure:

```markdown
# Chat Export: <Session Title>
- Session ID: `<session_id>`
- Directory: `<project_directory>`
- Exported: <YYYY-MM-DD HH:MM:SS>
- Total messages: <N>

---
## #1 | USER | 2026-06-17 18:00:00

Hello, I need help with...

---
## #2 | ASSISTANT | 2026-06-17 18:00:05

Sure, let me help you...

[TOOL: read_file]
Args:
{...}
Result:
...
```

## Notes

- The script reads the SQLite database directly — it does not rely on opencode's runtime API.
- The database path is auto-detected and ranked by validity (size + SQLite magic + `session` table); use `--db <path>` or `OPENCODE_DB` env var to force a specific database.
- Tool call arguments and results are truncated to prevent excessively large files (800 chars for args, 2000 for results).
- The `--no-tools` flag produces a cleaner, conversation-only export without tool calls.
- The script is pure Python 3 with no external dependencies — only the standard library (`sqlite3`, `json`, `os`, `argparse`, `datetime`).
