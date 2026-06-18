# export-chat

opencode skill that exports the full conversation from the current (or any) session to a Markdown file.

## What It Does

Reads opencode's SQLite database (`~/.local/share/opencode/opencode.db`) and reconstructs the complete chat history — including user messages, assistant responses, and tool calls — into a structured Markdown file.

## Installation

This skill is designed for [opencode](https://opencode.ai). Place it in your skills directory:

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
- "export chat"

The agent will invoke the skill and save the Markdown file to the current project directory.

### Command Line

The script works standalone:

```bash
# Export the current session (auto-detected from project directory)
python export_chat.py --directory /path/to/project

# Export a specific session by ID
python export_chat.py --session-id ses_abc123def

# Custom output path
python export_chat.py -d /path/to/project -o /tmp/my_chat.md

# List recent sessions
python export_chat.py --list --directory /path/to/project

# List all sessions
python export_chat.py --list-all

# Export text only (no tool calls)
python export_chat.py --directory /path/to/project --no-tools

# Custom database path
python export_chat.py --db /path/to/opencode.db --list
```

## Script Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--session-id` | `-s` | Export a specific session by ID |
| `--output` | `-o` | Custom output file path |
| `--directory` | `-d` | Project directory to find the session |
| `--list` | `-l` | List 20 most recent sessions |
| `--list-all` | | List all sessions |
| `--no-tools` | | Exclude tool calls from export |
| `--db` | | Custom path to opencode.db |

## Output Format

The exported Markdown file looks like:

```markdown
# Chat Export: My Session Title
- Session ID: `ses_13548c35fffe...`
- Directory: `/home/user/my-project`
- Exported: 2026-06-17 19:00:00
- Total messages: 42

---
## #1 | USER | 2026-06-17 18:00:00

Hello, I need help with my project.

---
## #2 | ASSISTANT | 2026-06-17 18:00:05

I'll look into that for you.

[TOOL: read_file (result)]
Args:
{"filePath": "/home/user/my-project/src/main.py"}
Result:
<file contents...>

---
## #3 | USER | 2026-06-17 18:01:00

Great, now fix the bug on line 42.
```

## How It Works

1. Locates the opencode SQLite database (auto-detected at `~/.local/share/opencode/opencode.db`)
2. Queries the `session` table to find the session matching the current project directory
3. Iterates through all `message` rows for that session, ordered by creation time
4. For each message, extracts all `part` rows (text content, tool invocations, results)
5. Assembles everything into a structured Markdown document
6. Writes the file to the specified output path

## Database Schema

The script reads from these tables in `opencode.db`:

| Table | Purpose |
|-------|---------|
| `session` | Session metadata (id, title, directory, timestamps) |
| `message` | Top-level messages (user/assistant turns) |
| `part` | Individual parts within a message (text blocks, tool calls, tool results) |

## Smart Truncation

To keep exported files manageable:

- Tool call arguments are truncated at 800 characters
- Tool call results are truncated at 2000 characters
- Use `--no-tools` for a clean conversation-only export

## Requirements

- Python 3.6+ (no external dependencies — only stdlib)
- Access to opencode's database file (read-only, does not modify the database)

## Platform Support

| Platform | Database Location |
|----------|-------------------|
| Linux / WSL | `~/.local/share/opencode/opencode.db` |
| macOS | `~/.local/share/opencode/opencode.db` |
| Windows | `%USERPROFILE%\.local\share\opencode\opencode.db` |

If the database is in a non-standard location, use `--db /path/to/opencode.db`.

## Troubleshooting

**"opencode.db not found"**
- Check that opencode is installed and has been run at least once
- Use `--db` to specify the path manually
- On Windows, check `%LOCALAPPDATA%\opencode\opencode.db`

**"No session found"**
- Make sure you're pointing to the correct project directory with `--directory`
- Use `--list` to see available sessions
- You may need to specify the session ID directly with `--session-id`

**Empty export**
- The session may have been archived/compacted, moving messages out of `message`/`part` tables
- Try `--list-all` to find sessions with data

## License

MIT
