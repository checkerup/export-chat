[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![Русский](https://img.shields.io/badge/lang-Русский-red.svg)](README.ru.md) [![中文](https://img.shields.io/badge/lang-中文-green.svg)](README.zh.md)

# export-chat

Universal chat history export tool for **20+ AI coding harnesses/IDEs**. Reads conversations directly from each tool's local storage (SQLite, JSON, JSONL, Markdown, YAML) and exports them to a structured Markdown file.

## Supported Harnesses

| # | Harness | Format | Status |
|---|---------|--------|--------|
| 1 | Claude Code | JSONL | вњ… Full |
| 2 | Cursor | SQLite (state.vscdb) | вњ… Full |
| 3 | GitHub Copilot Chat | SQLite (VS Code) | вљ пёЏ Partial |
| 4 | Windsurf | SQLite (state.vscdb) | вљ пёЏ Partial |
| 5 | Continue | JSON | вњ… Full |
| 6 | Cline | JSON (per-task) | вњ… Full |
| 7 | Aider | Markdown | вњ… Full |
| 8 | Codex CLI | JSONL | вњ… Full |
| 9 | Opencode | SQLite (opencode.db) | вњ… Full |
| 10 | Zed AI | SQLite | вљ пёЏ Undocumented |
| 11 | Trae | SQLite (state.vscdb) | вљ пёЏ Partial |
| 12 | JetBrains AI Assistant | XML | вљ пёЏ Undocumented |
| 13 | Cody (Sourcegraph) | JSON | вњ… Full |
| 14 | Amazon Q Developer | SQLite (VS Code) | вљ пёЏ Partial |
| 15 | Gemini Code Assist | SQLite (VS Code) | вљ пёЏ Partial |
| 16 | Tabnine | SQLite (VS Code) | вљ пёЏ Partial |
| 17 | Warp | SQLite + JSON | вљ пёЏ Partial |
| 18 | Kilo Code | JSON (per-task) | вњ… Full |
| 19 | Roo Code | JSON (per-task) | вњ… Full |
| 20 | Goose | YAML | вњ… Full |

## Installation

Place the skill files in your opencode skills directory:

```
~/.config/opencode/skills/export-chat/SKILL.md
~/.config/opencode/skills/export-chat/export_chat.py
```

Or for a project-specific install:

```
.opencode/skills/export-chat/SKILL.md
.opencode/skills/export-chat/export_chat.py
```

After installing, **restart opencode** for the skill to be loaded.

## Usage

### Inside opencode

Simply ask the agent to export the chat:

- "export this conversation"
- "save our chat to a file"
- "dump the chat history"
- "export chat from Cursor"
- "export my Continue session"

The agent will invoke the skill and save the Markdown file to the current project directory.

### Command Line

```bash
# List detected harnesses on this machine
python export_chat.py --list-harnesses

# List recent sessions across ALL detected harnesses
python export_chat.py --list

# List all sessions
python export_chat.py --list-all

# List sessions from a specific harness only
python export_chat.py --list --harness cursor
python export_chat.py --list --harness opencode
python export_chat.py --list --harness continue

# Export a specific session (auto-detects which harness has it)
python export_chat.py -s "ses_abc123"

# Export with a specific harness
python export_chat.py -s "665f8904-..." --harness continue -o /tmp/chat.md

# Export text only (no tool calls)
python export_chat.py -s "ses_abc123" --no-tools

# Filter by project directory
python export_chat.py --list -d /path/to/project

# Custom database path (legacy, opencode only)
python export_chat.py --db /path/to/opencode.db --list
```

## Script Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--session-id` | `-s` | Specific session ID to export |
| `--output` | `-o` | Custom output file path |
| `--directory` | `-d` | Project directory to filter sessions |
| `--list` | `-l` | List 20 most recent sessions across all harnesses |
| `--list-all` | | List all sessions |
| `--list-harnesses` | | Show all 20 harnesses and detection status |
| `--harness` | | Filter to a specific harness (e.g. `opencode`, `cursor`) |
| `--no-tools` | | Exclude tool calls from export |
| `--db` | | Custom database path (legacy, opencode only) |

## Output Format

```markdown
# Chat Export: My Session Title
- Harness: `opencode`
- Directory: `/home/user/my-project`
- Exported: 2026-08-18 15:45:00
- Total messages: 42

---
## #1 | USER | 2026-08-18 18:00:00

Hello, I need help with my project.

---
## #2 | ASSISTANT | 2026-08-18 18:00:05

I'll look into that for you.

[TOOL: read_file]
Args:
{"filePath": "/home/user/my-project/src/main.py"}
Result:
<file contents...>
```

## How It Works

1. **Auto-detect**: On startup, the tool checks all 20 known storage locations for each harness.
2. **List**: Queries each detected harness's storage and aggregates sessions.
3. **Export**: For a given session ID, finds which harness owns it, reads messages and tool calls, renders to Markdown.

## Smart Truncation

- Tool call arguments are truncated at 800 characters
- Tool call results are truncated at 2000 characters
- Use `--no-tools` for a clean conversation-only export

## Requirements

- Python 3.6+ (no external dependencies вЂ” only stdlib)
- Read-only access to harness databases (does not modify anything)

## Platform Support

| Platform | Database Location |
|----------|-------------------|
| Linux / WSL | `~/.local/share/opencode/opencode.db` |
| macOS | `~/.local/share/opencode/opencode.db` |
| Windows | `%USERPROFILE%\.local\share\opencode\opencode.db` |

## Troubleshooting

**"opencode.db not found"**
- Check that opencode is installed and has been run at least once
- Use `--db` to specify the path manually

**"UnicodeEncodeError: 'charmap' codec can't encode character..." (Windows)**
- v1.1+ fixes this automatically by forcing UTF-8 on stdout/stderr
- On older versions, set `PYTHONUTF8=1` before running the script

**"No session found"**
- Use `--list-harnesses` to see which harnesses are detected
- Use `--list` to see all sessions across harnesses
- You may need to specify the session ID directly with `--session-id`

## Changelog

### v2.0.0 вЂ” 2026-08-18

**Major rewrite: universal multi-harness support**

- **20 harnesses supported**: Claude Code, Cursor, GitHub Copilot Chat, Windsurf, Continue, Cline, Aider, Codex CLI, Opencode, Zed AI, Trae, JetBrains AI Assistant, Cody, Amazon Q Developer, Gemini Code Assist, Tabnine, Warp, Kilo Code, Roo Code, Goose
- **Adapter architecture**: each harness has its own adapter with `detect()`, `list_sessions()`, `export_session()` methods
- **Cross-harness search**: `--list` scans all detected harnesses and aggregates sessions
- **Harness filter**: `--harness <name>` filters to a specific tool
- **Auto-detection**: storage locations auto-detected per platform (Windows/Linux/macOS)
- **Full backward compatibility**: v1.x commands still work (`--db`, `--directory`, etc.)

### v1.1 вЂ” 2026-08-18

**Fixed:**
- Windows Unicode crash: `export_chat.py` crashed with `UnicodeEncodeError: 'charmap' codec can't encode character` when printing session titles containing non-ASCII characters (Cyrillic, emoji, currency symbols like в‚Ѕ) on Windows, where the default console code page is cp1251 or cp437. The script now calls `sys.stdout.reconfigure(encoding="utf-8")` at startup when the default encoding is not UTF-8.

### v1.0 вЂ” Initial release

- Opencode-only export from SQLite database

## License

MIT