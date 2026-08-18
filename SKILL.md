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

The skill uses a Python script (`export_chat.py`) that reads directly from opencode's SQLite database at `~/.local/share/opencode/opencode.db`. It queries the `session`, `message`, and `part` tables to reconstruct the full conversation.

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
- The database path is auto-detected on Linux (`~/.local/share/opencode/opencode.db`) and Windows (`%LOCALAPPDATA%\opencode\opencode.db` or `~\.local\share\opencode\opencode.db`).
- Tool call arguments and results are truncated to prevent excessively large files (800 chars for args, 2000 for results).
- The `--no-tools` flag produces a cleaner, conversation-only export without tool calls.
- The script is pure Python 3 with no external dependencies — only the standard library (`sqlite3`, `json`, `os`, `argparse`, `datetime`).
