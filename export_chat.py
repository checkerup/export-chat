#!/usr/bin/env python3
"""
Universal Chat Export Tool — exports chat history from 20+ AI coding harnesses/IDEs.

Supports: Claude Code, Cursor, GitHub Copilot Chat, Windsurf, Continue, Cline,
Aider, Codex CLI, Opencode, Zed AI, Trae, JetBrains AI Assistant, Cody,
Amazon Q Developer, Gemini Code Assist, Tabnine, Warp, Kilo Code, Roo Code, Goose.

Each adapter auto-detects its storage location and format (SQLite/JSON/JSONL/Markdown/YAML).
"""

import sqlite3
import json
import sys
import os
import argparse
import glob
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod

# Force UTF-8 on stdout/stderr so non-ASCII (Cyrillic, emoji, etc.) doesn't crash
# on Windows where the default console code page is often cp1251/cp437.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Version
VERSION = "2.2.0"

# Helpers ----------------------------------------------------------------------

def _home(*parts):
    """Join paths under the user home directory."""
    return os.path.join(os.path.expanduser("~"), *parts)

def _appdata(*parts):
    """Join paths under %APPDATA% (Windows) or ~/.config (Linux/macOS)."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", _home("AppData", "Roaming")), *parts)
    return os.path.join(os.path.expanduser("~"), ".config", *parts)

def _localappdata(*parts):
    """Join paths under %LOCALAPPDATA% (Windows) or ~/.local/share (Linux/macOS)."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", _home("AppData", "Local")), *parts)
    return os.path.join(os.path.expanduser("~"), ".local", "share", *parts)


# SessionInfo — lightweight session descriptor --------------------------------

class SessionInfo:
    """Describes a single chat session found by an adapter."""
    def __init__(self, session_id, title, directory, timestamp, harness, extra=None):
        self.session_id = session_id
        self.title = title or "Untitled"
        self.directory = directory or ""
        self.timestamp = timestamp  # epoch ms or 0
        self.harness = harness
        self.extra = extra or {}

    def display(self):
        ts = datetime.fromtimestamp(self.timestamp / 1000).strftime("%Y-%m-%d %H:%M") if self.timestamp else "N/A"
        return f"  {self.session_id}  |  {ts}  |  {self.title}  |  {self.directory}  |  [{self.harness}]"


# Message — normalized message from any adapter --------------------------------

class Message:
    """Normalized chat message."""
    def __init__(self, role, content, timestamp=0, tool_calls=None, tool_results=None):
        self.role = role or "unknown"
        self.content = content or ""
        self.timestamp = timestamp
        self.tool_calls = tool_calls or []
        self.tool_results = tool_results or []


# BaseAdapter ------------------------------------------------------------------

class BaseAdapter(ABC):
    """Abstract base for all harness adapters."""

    name = "unknown"
    display_name = "Unknown"
    storage_format = "unknown"

    @abstractmethod
    def detect(self):
        """Return True if this harness's storage is found on this machine."""
        pass

    @abstractmethod
    def list_sessions(self, directory=None, limit=20):
        """Return list of SessionInfo objects."""
        pass

    @abstractmethod
    def export_session(self, session_id, include_tools=True):
        """Return (title, directory, list[Message]) for the given session."""
        pass

    def status(self):
        """Return detection status string for --list-harnesses."""
        found = self.detect()
        return f"  [{'x' if found else ' '}] {self.display_name:30s}  [{self.storage_format}]"


# =============================================================================
# HIGH-CONFIDENCE ADAPTERS
# =============================================================================

# --- 1. Claude Code (JSONL) ---------------------------------------------------

class ClaudeCodeAdapter(BaseAdapter):
    name = "claude-code"
    display_name = "Claude Code"
    storage_format = "JSONL"

    def _projects_dir(self):
        return _home(".claude", "projects")

    def detect(self):
        return os.path.isdir(self._projects_dir())

    def _find_session_files(self, directory=None):
        """Find .jsonl session files, optionally filtered by project dir hash."""
        results = []
        projects_dir = self._projects_dir()
        if not os.path.isdir(projects_dir):
            return results
        for proj_dir in os.listdir(projects_dir):
            proj_path = os.path.join(projects_dir, proj_dir)
            if not os.path.isdir(proj_path):
                continue
            for f in glob.glob(os.path.join(proj_path, "*.jsonl")):
                results.append((f, proj_dir))
        return results

    def list_sessions(self, directory=None, limit=20):
        sessions = []
        for fpath, proj_dir in self._find_session_files():
            try:
                sid = os.path.splitext(os.path.basename(fpath))[0]
                title = "Untitled"
                ts = int(os.path.getmtime(fpath) * 1000)
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        data = json.loads(first_line)
                        if "cwd" in data:
                            proj_dir = data["cwd"]
                        ts_data = data.get("timestamp", 0)
                        if ts_data:
                            ts = int(ts_data) if ts_data > 1e12 else int(ts_data * 1000)
                    # Read last line for title hint
                    content = f.read()
                    lines = [l for l in content.split("\n") if l.strip()]
                    if lines:
                        last = json.loads(lines[-1])
                        if "message" in last:
                            msg = last["message"]
                            if isinstance(msg.get("content"), str):
                                title = msg["content"][:60]
                sessions.append(SessionInfo(sid, title, proj_dir, ts, self.name, {"file": fpath}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        sessions = self.list_sessions(limit=9999)
        target = None
        for s in sessions:
            if s.session_id == session_id or s.extra.get("file", "").endswith(session_id + ".jsonl"):
                target = s
                break
        if not target:
            return ("Unknown", "", [])
        messages = []
        fpath = target.extra["file"]
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = data.get("type", "unknown")
                msg = data.get("message", {})
                if isinstance(msg, dict):
                    role = msg.get("role", role)
                content = ""
                tool_calls = []
                raw_content = msg.get("content", "") if isinstance(msg, dict) else ""
                if isinstance(raw_content, str):
                    content = raw_content
                elif isinstance(raw_content, list):
                    for block in raw_content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                content += block.get("text", "")
                            elif block.get("type") == "tool_use" and include_tools:
                                tool_calls.append({
                                    "name": block.get("name", "unknown"),
                                    "args": block.get("input", {}),
                                })
                            elif block.get("type") == "tool_result" and include_tools:
                                tool_calls.append({
                                    "name": "tool_result",
                                    "result": str(block.get("content", ""))[:2000],
                                })
                ts = data.get("timestamp", 0)
                ts_ms = int(ts) if ts > 1e12 else int(ts * 1000) if ts else 0
                messages.append(Message(role, content, ts_ms, tool_calls))
        return (target.title, target.directory, messages)


# --- 2. Cursor (SQLite state.vscdb) -------------------------------------------

class CursorAdapter(BaseAdapter):
    name = "cursor"
    display_name = "Cursor"
    storage_format = "SQLite (state.vscdb: composerHeaders + cursorDiskKV)"

    # Bubble type -> role (verified against live Cursor storage):
    #   1 = user (plain `text`), 2 = assistant (markdown chunks in `text`,
    #   empty text = streaming/control fragment, skipped).
    # Messages live in cursorDiskKV under `bubbleId:<composerId>:<bubbleId>`
    # (fallback: serverBubbleId); order comes from
    # composerData:<id>.fullConversationHeadersOnly. Title = composerData.name.
    ROLE_MAP = {1: "user", 2: "assistant"}

    def _db_path(self):
        return _appdata("Cursor", "User", "globalStorage", "state.vscdb")

    def detect(self):
        return os.path.isfile(self._db_path())

    def _connect(self):
        path = self._db_path()
        if not os.path.isfile(path):
            return None
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _parse_ts(value):
        """ISO-8601 / epoch -> epoch ms (0 on failure)."""
        if not value:
            return 0
        try:
            if isinstance(value, (int, float)):
                return int(value) if value > 1e12 else int(value * 1000)
            s = str(value).strip().replace("Z", "+00:00")
            from datetime import datetime as _dt
            return int(_dt.fromisoformat(s).timestamp() * 1000)
        except (ValueError, OverflowError):
            return 0

    def _composer_name(self, conn, composer_id):
        try:
            c = conn.cursor()
            c.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (f"composerData:{composer_id}",))
            row = c.fetchone()
            if row and row[0]:
                data = json.loads(row[0])
                name = (data.get("name") or "").strip()
                if name:
                    return name
                # Fallback: first user bubble text (many composers are unnamed)
                for h in data.get("fullConversationHeadersOnly", []):
                    if h.get("type") != 1:
                        continue
                    bubble = self._fetch_bubble(conn, composer_id, h)
                    if bubble and (bubble.get("text") or "").strip():
                        return bubble["text"].strip()[:60]
                    break
        except (sqlite3.Error, ValueError):
            pass
        return "Untitled"

    def list_sessions(self, directory=None, limit=20):
        conn = self._connect()
        if not conn:
            return []
        sessions = []
        try:
            c = conn.cursor()
            try:
                c.execute(
                    "SELECT composerId, workspaceId, createdAt FROM composerHeaders "
                    "WHERE COALESCE(isArchived,0)=0 ORDER BY createdAt DESC LIMIT ?",
                    (limit,),
                )
            except sqlite3.OperationalError:
                # Very old schema without isArchived
                c.execute("SELECT composerId, workspaceId, createdAt FROM composerHeaders ORDER BY createdAt DESC LIMIT ?", (limit,))
            for row in c.fetchall():
                cid = row["composerId"]
                if cid == "empty-state-draft":
                    continue
                sessions.append(SessionInfo(
                    cid, self._composer_name(conn, cid),
                    row["workspaceId"] or "", row["createdAt"] or 0, self.name,
                ))
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
        return sessions

    def _fetch_bubble(self, conn, composer_id, header):
        c = conn.cursor()
        for bid in (header.get("bubbleId"), header.get("serverBubbleId")):
            if not bid:
                continue
            try:
                c.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (f"bubbleId:{composer_id}:{bid}",))
                row = c.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
            except (sqlite3.Error, ValueError):
                continue
        return None

    def export_session(self, session_id, include_tools=True):
        conn = self._connect()
        if not conn:
            return ("Unknown", "", [])
        messages = []
        title = "Unknown"
        try:
            c = conn.cursor()
            c.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (f"composerData:{session_id}",))
            row = c.fetchone()
            if not row or not row[0]:
                return ("Unknown", "", [])
            data = json.loads(row[0])
            title = (data.get("name") or "").strip() or session_id
            for h in data.get("fullConversationHeadersOnly", []):
                role = self.ROLE_MAP.get(h.get("type"), "unknown")
                bubble = self._fetch_bubble(conn, session_id, h)
                if not bubble:
                    continue
                ts = self._parse_ts(bubble.get("createdAt"))
                content = (bubble.get("text") or "").strip()
                tool_calls = []
                if include_tools:
                    for tr in bubble.get("toolResults", []) or []:
                        tool_calls.append({"name": "tool_result", "result": json.dumps(tr, ensure_ascii=False)[:2000]})
                    for sc in bubble.get("suggestedCodeBlocks", []) or []:
                        tool_calls.append({"name": "code_block", "result": json.dumps(sc, ensure_ascii=False)[:2000]})
                if not content and not tool_calls:
                    continue  # streaming/control fragment
                messages.append(Message(role, content, ts, tool_calls))
        except (sqlite3.OperationalError, ValueError):
            return ("Unknown", "", [])
        finally:
            conn.close()
        return (title, "", messages)


# --- 3. Opencode (SQLite opencode.db) -----------------------------------------

class OpencodeAdapter(BaseAdapter):
    name = "opencode"
    display_name = "Opencode"
    storage_format = "SQLite (opencode.db)"

    # Explicit override (wired from --db flag or OPENCODE_DB env). Set by main().
    _db_override = None

    def _candidates(self):
        cands = []
        if self._db_override:
            cands.append(self._db_override)
        env_db = os.environ.get("OPENCODE_DB")
        if env_db:
            cands.append(env_db)
        cands.extend([
            _localappdata("opencode", "opencode.db"),
            _home(".local", "share", "opencode", "opencode.db"),
        ])
        # Deduplicate, keep order
        seen, uniq = set(), []
        for p in cands:
            if p and p not in seen:
                seen.add(p)
                uniq.append(p)
        return uniq

    @staticmethod
    def _db_score(path):
        """Score a candidate DB file. Returns -1 if unusable, else size-based score.

        Guards against the known failure mode where a 0-byte placeholder
        (e.g. %LOCALAPPDATA%\\opencode\\opencode.db) shadows the real database:
        such files are skipped instead of silently yielding zero sessions.
        """
        try:
            if not path or not os.path.isfile(path):
                return -1
            size = os.path.getsize(path)
            if size < 4096:
                return -1
            with open(path, "rb") as f:
                if f.read(16) != b"SQLite format 3\x00":
                    return -1
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
            try:
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('session','message','part')")
                tables = {r[0] for r in c.fetchall()}
                if "session" not in tables:
                    return -1
                bonus = 0
                if "message" in tables:
                    bonus += 1
                if "part" in tables:
                    bonus += 1
                try:
                    c.execute("SELECT COUNT(*) FROM session")
                    n = c.fetchone()[0] or 0
                except sqlite3.OperationalError:
                    n = 0
                return size + bonus * 10**12 + min(n, 10**6)
            finally:
                conn.close()
        except (OSError, sqlite3.Error):
            return -1

    def _db_path(self):
        best, best_score = None, -1
        for p in self._candidates():
            s = self._db_score(p)
            if s > best_score:
                best, best_score = p, s
        return best

    def detect(self):
        return self._db_path() is not None

    def _connect(self):
        path = self._db_path()
        if not path:
            return None
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def list_sessions(self, directory=None, limit=20):
        conn = self._connect()
        if not conn:
            return []
        sessions = []
        try:
            c = conn.cursor()
            if directory:
                c.execute("SELECT id, title, directory, time_updated FROM session WHERE directory = ? ORDER BY time_updated DESC LIMIT ?", (directory, limit))
            else:
                c.execute("SELECT id, title, directory, time_updated FROM session ORDER BY time_updated DESC LIMIT ?", (limit,))
            for row in c.fetchall():
                sessions.append(SessionInfo(row["id"], row["title"], row["directory"], row["time_updated"] or 0, self.name))
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
        return sessions

    def export_session(self, session_id, include_tools=True):
        conn = self._connect()
        if not conn:
            return ("Unknown", "", [])
        try:
            c = conn.cursor()
            c.execute("SELECT title, directory FROM session WHERE id = ?", (session_id,))
            row = c.fetchone()
            title = row["title"] if row else "Unknown"
            directory = row["directory"] if row else ""
            c.execute("SELECT id, data, time_created FROM message WHERE session_id = ? ORDER BY time_created", (session_id,))
            messages = []
            for m in c.fetchall():
                data = json.loads(m["data"]) if m["data"] else {}
                role = data.get("role", "unknown")
                ts = m["time_created"] or 0
                msg_id = m["id"]
                c2 = conn.cursor()
                c2.execute("SELECT data FROM part WHERE message_id = ? ORDER BY time_created", (msg_id,))
                text_parts = []
                tool_parts = []
                for p in c2.fetchall():
                    pdata = json.loads(p["data"]) if p["data"] else {}
                    ptype = pdata.get("type", "")
                    if ptype == "text":
                        t = pdata.get("text", "").strip()
                        if t:
                            text_parts.append(t)
                    elif ptype == "reasoning":
                        t = pdata.get("text", "").strip()
                        if t and include_tools:
                            tool_parts.append({"name": "reasoning", "result": t})
                    elif ptype == "tool" and include_tools:
                        # New opencode format:
                        # {"type":"tool","tool":"<name>","callID":"...","state":{"status","input","output"}}
                        state = pdata.get("state", {}) or {}
                        tool_parts.append({
                            "name": pdata.get("tool", "unknown"),
                            "args": state.get("input", {}),
                            "result": state.get("output", ""),
                            "status": state.get("status", ""),
                        })
                    elif ptype in ("tool_use", "tool_result") and include_tools:
                        # Legacy format (pre-2026 schemas)
                        tool_parts.append(json.dumps(pdata, ensure_ascii=False)[:2000])
                    elif ptype == "patch" and include_tools:
                        files = pdata.get("files", [])
                        tool_parts.append({"name": "patch", "result": "files: " + ", ".join(files) if files else "patch"})
                    elif ptype == "file" and include_tools:
                        tool_parts.append({"name": "file", "result": f"{pdata.get('filename', 'file')} ({pdata.get('mime', '?')})"})
                    # step-start / step-finish / compaction / unknown: skipped (envelope, no content)
                content = "\n\n".join(text_parts)
                messages.append(Message(role, content, ts, tool_parts))
            return (title, directory, messages)
        except sqlite3.OperationalError:
            return ("Unknown", "", [])
        finally:
            conn.close()


# --- 4/18/19. Cline / Kilo Code / Roo Code (per-task JSON) --------------------

class ClineFamilyAdapter(BaseAdapter):
    """Shared adapter for Cline, Kilo Code, Roo Code — same storage format."""
    storage_format = "JSON (per-task)"

    def __init__(self, name, display_name, ext_id):
        self.name = name
        self.display_name = display_name
        self.ext_id = ext_id

    def _tasks_dir(self):
        return _appdata("Code", "User", "globalStorage", self.ext_id, "tasks")

    def detect(self):
        return os.path.isdir(self._tasks_dir())

    def list_sessions(self, directory=None, limit=20):
        tasks_dir = self._tasks_dir()
        if not os.path.isdir(tasks_dir):
            return []
        sessions = []
        for task_dir in os.listdir(tasks_dir):
            api_file = os.path.join(tasks_dir, task_dir, "api Conversation history.json")
            if not os.path.isfile(api_file):
                api_file = os.path.join(tasks_dir, task_dir, "api_conversation_history.json")
            if not os.path.isfile(api_file):
                continue
            try:
                ts = int(os.path.getmtime(api_file) * 1000)
                title = task_dir
                ui_file = os.path.join(tasks_dir, task_dir, "ui_messages.json")
                if os.path.isfile(ui_file):
                    with open(ui_file, "r", encoding="utf-8", errors="replace") as f:
                        ui = json.load(f)
                        if isinstance(ui, list) and ui:
                            title = ui[0].get("text", task_dir)[:60]
                sessions.append(SessionInfo(task_dir, title, "", ts, self.name, {"dir": os.path.join(tasks_dir, task_dir)}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        tasks_dir = self._tasks_dir()
        task_path = os.path.join(tasks_dir, session_id)
        api_file = os.path.join(task_path, "api Conversation history.json")
        if not os.path.isfile(api_file):
            api_file = os.path.join(task_path, "api_conversation_history.json")
        if not os.path.isfile(api_file):
            return ("Unknown", "", [])
        with open(api_file, "r", encoding="utf-8", errors="replace") as f:
            raw_msgs = json.load(f)
        messages = []
        for m in raw_msgs:
            role = m.get("role", "unknown")
            content = ""
            tool_calls = []
            raw_content = m.get("content", "")
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, list):
                for block in raw_content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content += block.get("text", "")
                        elif block.get("type") == "tool_use" and include_tools:
                            tool_calls.append({"name": block.get("name", ""), "args": block.get("input", {})})
                        elif block.get("type") == "tool_result" and include_tools:
                            tool_calls.append({"name": "tool_result", "result": str(block.get("content", ""))[:2000]})
            messages.append(Message(role, content, 0, tool_calls))
        return (session_id, "", messages)


# --- 5. Aider (Markdown) -----------------------------------------------------

class AiderAdapter(BaseAdapter):
    name = "aider"
    display_name = "Aider"
    storage_format = "Markdown"

    def _history_file(self):
        return _home(".aider.chat.history.md")

    def detect(self):
        return os.path.isfile(self._history_file())

    def list_sessions(self, directory=None, limit=20):
        fpath = self._history_file()
        if not os.path.isfile(fpath):
            return []
        ts = int(os.path.getmtime(fpath) * 1000)
        return [SessionInfo("aider-history", "Aider Chat History", directory or "", ts, self.name, {"file": fpath})]

    def export_session(self, session_id, include_tools=True):
        fpath = self._history_file()
        if not os.path.isfile(fpath):
            return ("Unknown", "", [])
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Parse markdown into messages
        messages = []
        current_role = None
        current_text = []
        for line in content.split("\n"):
            if line.startswith("#### "):
                if current_role and current_text:
                    messages.append(Message(current_role, "\n".join(current_text), 0))
                role_str = line[5:].strip().rstrip(":").lower()
                current_role = role_str if role_str in ("user", "assistant") else "unknown"
                current_text = []
            else:
                if current_role:
                    current_text.append(line)
        if current_role and current_text:
            messages.append(Message(current_role, "\n".join(current_text), 0))
        return ("Aider Chat History", "", messages)


# --- 6. Continue (SQLite sessions.db) ----------------------------------------

class ContinueAdapter(BaseAdapter):
    name = "continue"
    display_name = "Continue"
    storage_format = "JSON"

    def _sessions_dir(self):
        return _home(".continue", "sessions")

    def detect(self):
        return os.path.isdir(self._sessions_dir())

    def list_sessions(self, directory=None, limit=20):
        sdir = self._sessions_dir()
        if not os.path.isdir(sdir):
            return []
        sessions = []
        for f in glob.glob(os.path.join(sdir, "*.json")):
            if f.endswith("sessions.json"):
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    data = json.load(fh)
                sid = data.get("sessionId", os.path.basename(f))
                title = data.get("title", "Untitled")
                ws = data.get("workspaceDirectory", "")
                ts_str = data.get("dateCreated", "0")
                ts = int(ts_str) if str(ts_str).isdigit() else 0
                sessions.append(SessionInfo(sid, title, ws, ts, self.name, {"file": f}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        sdir = self._sessions_dir()
        # Find the file matching session_id
        for f in glob.glob(os.path.join(sdir, "*.json")):
            if f.endswith("sessions.json"):
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    data = json.load(fh)
                if data.get("sessionId") == session_id:
                    title = data.get("title", session_id)
                    ws = data.get("workspaceDirectory", "")
                    messages = []
                    for item in data.get("history", []):
                        msg = item.get("message", {})
                        role = msg.get("role", "unknown")
                        content = ""
                        raw_content = msg.get("content", "")
                        if isinstance(raw_content, str):
                            content = raw_content
                        elif isinstance(raw_content, list):
                            for block in raw_content:
                                if isinstance(block, dict):
                                    if block.get("type") == "text" or "text" in block:
                                        content += block.get("text", "")
                        messages.append(Message(role, content, 0))
                    return (title, ws, messages)
            except Exception:
                continue
        return ("Unknown", "", [])


# --- 7. Goose (YAML) ----------------------------------------------------------

class GooseAdapter(BaseAdapter):
    name = "goose"
    display_name = "Goose"
    storage_format = "YAML"

    def _sessions_dir(self):
        if sys.platform == "win32":
            return _appdata("goose", "sessions")
        return _home(".local", "share", "goose", "sessions")

    def detect(self):
        return os.path.isdir(self._sessions_dir())

    def _parse_yaml_simple(self, fpath):
        """Minimal YAML parser for goose session files (no external deps)."""
        import re
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        messages = []
        current_msg = None
        for line in lines:
            line = line.rstrip("\n")
            m = re.match(r"^- role:\s*(\w+)", line)
            if m:
                if current_msg:
                    messages.append(current_msg)
                current_msg = {"role": m.group(1), "content": "", "tool_name": "", "tool_args": "", "tool_response": ""}
            elif current_msg is not None and ":" in line:
                key, _, val = line.strip().partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in current_msg:
                    current_msg[key] = val
        if current_msg:
            messages.append(current_msg)
        return messages

    def list_sessions(self, directory=None, limit=20):
        sdir = self._sessions_dir()
        if not os.path.isdir(sdir):
            return []
        sessions = []
        for f in glob.glob(os.path.join(sdir, "*.yaml")) + glob.glob(os.path.join(sdir, "*.yml")):
            try:
                ts = int(os.path.getmtime(f) * 1000)
                sid = os.path.splitext(os.path.basename(f))[0]
                sessions.append(SessionInfo(sid, sid, "", ts, self.name, {"file": f}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        sdir = self._sessions_dir()
        for f in glob.glob(os.path.join(sdir, "*.yaml")) + glob.glob(os.path.join(sdir, "*.yml")):
            if os.path.splitext(os.path.basename(f))[0] == session_id:
                raw_msgs = self._parse_yaml_simple(f)
                messages = []
                for rm in raw_msgs:
                    role = rm.get("role", "unknown")
                    content = rm.get("content", "")
                    tool_calls = []
                    if include_tools and rm.get("tool_name"):
                        tool_calls.append({"name": rm.get("tool_name", ""), "args": rm.get("tool_args", ""), "result": rm.get("tool_response", "")[:2000]})
                    messages.append(Message(role, content, 0, tool_calls))
                return (session_id, "", messages)
        return ("Unknown", "", [])


# --- 8. Codex CLI (JSONL) -----------------------------------------------------

class CodexAdapter(BaseAdapter):
    name = "codex"
    display_name = "Codex CLI"
    storage_format = "JSONL"

    def _sessions_dir(self):
        return _home(".codex", "sessions")

    def detect(self):
        return os.path.isdir(self._sessions_dir())

    def list_sessions(self, directory=None, limit=20):
        sdir = self._sessions_dir()
        if not os.path.isdir(sdir):
            return []
        sessions = []
        for f in glob.glob(os.path.join(sdir, "*.jsonl")):
            try:
                ts = int(os.path.getmtime(f) * 1000)
                sid = os.path.splitext(os.path.basename(f))[0]
                sessions.append(SessionInfo(sid, sid, "", ts, self.name, {"file": f}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        sdir = self._sessions_dir()
        for f in glob.glob(os.path.join(sdir, "*.jsonl")):
            if os.path.splitext(os.path.basename(f))[0] == session_id:
                messages = []
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        etype = data.get("type", "message")
                        if etype == "message":
                            role = data.get("role", "unknown")
                            content = data.get("content", "")
                            if isinstance(content, list):
                                content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                            messages.append(Message(role, content, 0))
                        elif etype == "function_call" and include_tools:
                            messages.append(Message("assistant", "", 0, [{"name": data.get("name", ""), "args": data.get("arguments", "")}]))
                        elif etype == "function_call_output" and include_tools:
                            messages.append(Message("tool", "", 0, [{"name": "result", "result": str(data.get("output", ""))[:2000]}]))
                return (session_id, "", messages)
        return ("Unknown", "", [])


# --- 9. Windsurf / Trae (VS Code SQLite) --------------------------------------

class VSCodeForkAdapter(BaseAdapter):
    """Shared adapter for Windsurf, Trae — VS Code fork SQLite storage.

    Verified against live installs:
    - Windsurf chats are indexed by `chat.ChatSessionStore.index`
      (`{"version":1,"entries":{...}}`) in the global state.vscdb and in
      User/workspaceStorage/*/state.vscdb. Empty entries = no sessions.
    - Trae keeps only session metadata in SQLite (`icube_session_agent_map`
      -> {sessionId: agent}, plus per-user ai-chat:* relation maps); message
      bodies live outside SQLite (IndexedDB), so export returns session
      metadata plus an honest stub instead of fake content.
    """
    storage_format = "SQLite (state.vscdb)"

    def __init__(self, name, display_name, app_name):
        self.name = name
        self.display_name = display_name
        self.app_name = app_name

    def _global_db(self):
        return _appdata(self.app_name, "User", "globalStorage", "state.vscdb")

    def _workspace_dbs(self):
        ws = _appdata(self.app_name, "User", "workspaceStorage")
        if not os.path.isdir(ws):
            return []
        return sorted(glob.glob(os.path.join(ws, "*", "state.vscdb")))

    def _all_dbs(self):
        dbs = [self._global_db()] + self._workspace_dbs()
        return [p for p in dbs if os.path.isfile(p)]

    def detect(self):
        return len(self._all_dbs()) > 0

    def _connect_ro(self, path):
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _read_value(self, db, key):
        try:
            conn = self._connect_ro(db)
            try:
                c = conn.cursor()
                c.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
                row = c.fetchone()
                return row[0] if row else None
            finally:
                conn.close()
        except sqlite3.Error:
            return None

    def _index_entries(self, db):
        raw = self._read_value(db, "chat.ChatSessionStore.index")
        if not raw:
            return {}
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            entries = data.get("entries", {})
            return entries if isinstance(entries, dict) else {}
        except (ValueError, AttributeError):
            return {}

    def _trae_sessions(self, db):
        raw = self._read_value(db, "icube_session_agent_map")
        if not raw:
            return {}
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            return data if isinstance(data, dict) else {}
        except (ValueError, AttributeError):
            return {}

    def list_sessions(self, directory=None, limit=20):
        sessions = []
        seen = set()
        for db in self._all_dbs():
            if self.app_name.lower() == "trae":
                for sid, agent in self._trae_sessions(db).items():
                    if sid in seen:
                        continue
                    seen.add(sid)
                    sessions.append(SessionInfo(sid, f"Trae session ({agent})", os.path.basename(os.path.dirname(db)), 0, self.name))
            else:
                for sid, entry in self._index_entries(db).items():
                    if sid in seen:
                        continue
                    seen.add(sid)
                    title = sid
                    if isinstance(entry, dict):
                        title = entry.get("title") or entry.get("name") or sid
                    sessions.append(SessionInfo(sid, title, os.path.basename(os.path.dirname(db)), 0, self.name))
            if len(sessions) >= limit:
                break
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        for db in self._all_dbs():
            for key in (f"chat.ChatSessionStore.{session_id}", f"cascade:{session_id}",
                        f"ai-chat:session:{session_id}"):
                raw = self._read_value(db, key)
                if raw:
                    try:
                        data = json.loads(raw) if isinstance(raw, str) else raw
                    except ValueError:
                        data = {"raw": str(raw)[:2000]}
                    title = data.get("title", session_id) if isinstance(data, dict) else session_id
                    messages = []
                    for m in data.get("messages", []) if isinstance(data, dict) else []:
                        role = m.get("role", "unknown")
                        content = m.get("content", "")
                        if isinstance(content, list):
                            content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
                        messages.append(Message(role, content, 0))
                    if messages:
                        return (title, "", messages)
        if self.app_name.lower() == "trae":
            for db in self._all_dbs():
                agent_map = self._trae_sessions(db)
                if session_id in agent_map:
                    return (f"Trae session ({agent_map[session_id]})", "",
                            [Message("system",
                                     f"Trae session '{session_id}' (agent: {agent_map[session_id]}). "
                                     "Message bodies are not stored in SQLite (they live in IndexedDB), "
                                     "so only session metadata can be exported. "
                                     "Copy the conversation from the Trae UI for a full export.", 0)])
        return (session_id, "", [Message("system",
                 f"{self.display_name} session '{session_id}' has no exportable content in SQLite. "
                 "The chat index is empty or the format is not yet documented. Please contribute.", 0)])


# --- 10. GitHub Copilot Chat (VS Code SQLite) --------------------------------

class CopilotChatAdapter(BaseAdapter):
    name = "copilot-chat"
    display_name = "GitHub Copilot Chat"
    storage_format = "SQLite (state.vscdb)"

    def _db_path(self):
        return _appdata("Code", "User", "globalStorage", "state.vscdb")

    def detect(self):
        return os.path.isfile(self._db_path())

    def list_sessions(self, directory=None, limit=20):
        # Copilot Chat sessions are mostly ephemeral; stored in ItemTable
        conn = sqlite3.connect(f"file:{self._db_path()}?mode=ro", uri=True) if self.detect() else None
        if not conn:
            return []
        sessions = []
        try:
            c = conn.cursor()
            c.execute("SELECT key FROM ItemTable WHERE key LIKE 'github.copilot%' LIMIT ?", (limit,))
            for row in c.fetchall():
                sessions.append(SessionInfo(row[0], row[0], "", 0, self.name))
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
        return sessions

    def export_session(self, session_id, include_tools=True):
        # Copilot Chat doesn't have a well-documented structured export
        return (session_id, "", [Message("system", f"Copilot Chat session '{session_id}' — format not fully supported. Please contribute.", 0)])


# --- 11. Cody (JSON) ----------------------------------------------------------

class CodyAdapter(BaseAdapter):
    name = "cody"
    display_name = "Cody (Sourcegraph)"
    storage_format = "JSON"

    def _storage_dir(self):
        return _appdata("Code", "User", "globalStorage", "sourcegraph.cody")

    def detect(self):
        return os.path.isdir(self._storage_dir())

    def list_sessions(self, directory=None, limit=20):
        sdir = os.path.join(self._storage_dir(), "chatSessions")
        if not os.path.isdir(sdir):
            return []
        sessions = []
        for f in glob.glob(os.path.join(sdir, "*.json")):
            try:
                ts = int(os.path.getmtime(f) * 1000)
                sid = os.path.splitext(os.path.basename(f))[0]
                sessions.append(SessionInfo(sid, sid, "", ts, self.name, {"file": f}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        sdir = os.path.join(self._storage_dir(), "chatSessions")
        for f in glob.glob(os.path.join(sdir, "*.json")):
            if os.path.splitext(os.path.basename(f))[0] == session_id:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    data = json.load(fh)
                title = data.get("title", session_id)
                messages = []
                for m in data.get("messages", []):
                    role = m.get("role", "unknown")
                    content = m.get("content", "")
                    messages.append(Message(role, content, 0))
                return (title, "", messages)
        return ("Unknown", "", [])


# --- 12. Warp (SQLite + JSON) -------------------------------------------------

class WarpAdapter(BaseAdapter):
    name = "warp"
    display_name = "Warp"
    storage_format = "SQLite + JSON"

    def _warp_dir(self):
        if sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/dev.warp.Warp-Stable")
        return _home(".warp")

    def detect(self):
        return os.path.isdir(self._warp_dir())

    def list_sessions(self, directory=None, limit=20):
        wdir = self._warp_dir()
        ai_sessions = os.path.join(wdir, "ai_sessions")
        if not os.path.isdir(ai_sessions):
            return []
        sessions = []
        for f in glob.glob(os.path.join(ai_sessions, "*.json")):
            try:
                ts = int(os.path.getmtime(f) * 1000)
                sid = os.path.splitext(os.path.basename(f))[0]
                sessions.append(SessionInfo(sid, sid, "", ts, self.name, {"file": f}))
            except Exception:
                continue
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions[:limit]

    def export_session(self, session_id, include_tools=True):
        wdir = self._warp_dir()
        ai_sessions = os.path.join(wdir, "ai_sessions")
        for f in glob.glob(os.path.join(ai_sessions, "*.json")):
            if os.path.splitext(os.path.basename(f))[0] == session_id:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    data = json.load(fh)
                title = data.get("title", session_id)
                messages = []
                for m in data.get("messages", []):
                    role = m.get("role", "unknown")
                    content = m.get("content", "")
                    messages.append(Message(role, content, 0))
                return (title, "", messages)
        return ("Unknown", "", [])


# --- 13. Zed AI (SQLite) ------------------------------------------------------

class ZedAdapter(BaseAdapter):
    name = "zed"
    display_name = "Zed AI"
    storage_format = "SQLite"

    def _zed_dir(self):
        if sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/Zed")
        if sys.platform == "win32":
            return _appdata("Zed")
        return os.path.join(os.path.expanduser("~"), ".config", "zed")

    def _db_path(self):
        return os.path.join(self._zed_dir(), "db.sqlite")

    def detect(self):
        return os.path.isfile(self._db_path())

    def list_sessions(self, directory=None, limit=20):
        if not self.detect():
            return []
        # Zed schema is not publicly documented; best-effort
        return [SessionInfo("zed-undocumented", "Zed (format undocumented)", "", 0, self.name)]

    def export_session(self, session_id, include_tools=True):
        return ("Zed", "", [Message("system", "Zed AI conversation format is not yet documented. Please contribute.", 0)])


# --- 14-17. Low-confidence: JetBrains AI, Amazon Q, Gemini, Tabnine ---------

class GenericVSCodeExtensionAdapter(BaseAdapter):
    """Generic adapter for VS Code extensions with proprietary chat storage."""
    storage_format = "SQLite (state.vscdb)"

    def __init__(self, name, display_name, ext_id, key_prefix):
        self.name = name
        self.display_name = display_name
        self.ext_id = ext_id
        self.key_prefix = key_prefix

    def _db_path(self):
        return _appdata("Code", "User", "globalStorage", "state.vscdb")

    def detect(self):
        return os.path.isfile(self._db_path())

    def list_sessions(self, directory=None, limit=20):
        if not self.detect():
            return []
        conn = sqlite3.connect(f"file:{self._db_path()}?mode=ro", uri=True)
        sessions = []
        try:
            c = conn.cursor()
            c.execute("SELECT key FROM ItemTable WHERE key LIKE ? LIMIT ?", (f"%{self.key_prefix}%", limit))
            for row in c.fetchall():
                sessions.append(SessionInfo(row[0], row[0], "", 0, self.name))
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
        return sessions

    def export_session(self, session_id, include_tools=True):
        return (session_id, "", [Message("system", f"{self.display_name} session format not fully supported. Please contribute.", 0)])


class JetBrainsAIAdapter(BaseAdapter):
    name = "jetbrains-ai"
    display_name = "JetBrains AI Assistant"
    storage_format = "XML"

    def _detect_dir(self):
        if sys.platform == "win32":
            return _appdata("JetBrains")
        if sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/JetBrains")
        return os.path.join(os.path.expanduser("~"), ".config", "JetBrains")

    def detect(self):
        return os.path.isdir(self._detect_dir())

    def list_sessions(self, directory=None, limit=20):
        return [SessionInfo("jetbrains-undocumented", "JetBrains AI (format undocumented)", "", 0, self.name)]

    def export_session(self, session_id, include_tools=True):
        return ("JetBrains AI", "", [Message("system", "JetBrains AI Assistant conversation format is not yet documented. Please contribute.", 0)])


# =============================================================================
# ADAPTER REGISTRY
# =============================================================================

ADAPTERS = [
    ClaudeCodeAdapter(),
    CursorAdapter(),
    OpencodeAdapter(),
    ClineFamilyAdapter("cline", "Cline", "saoudrizwan.claude-dev"),
    ClineFamilyAdapter("kilo-code", "Kilo Code", "kilocode.kilo-code"),
    ClineFamilyAdapter("roo-code", "Roo Code", "rooveterinaryinc.roo-cline"),
    AiderAdapter(),
    ContinueAdapter(),
    GooseAdapter(),
    CodexAdapter(),
    VSCodeForkAdapter("windsurf", "Windsurf", "Windsurf"),
    VSCodeForkAdapter("trae", "Trae", "Trae"),
    CopilotChatAdapter(),
    CodyAdapter(),
    WarpAdapter(),
    ZedAdapter(),
    JetBrainsAIAdapter(),
    GenericVSCodeExtensionAdapter("amazon-q", "Amazon Q Developer", "amazonwebservices.amazonq", "amazonq"),
    GenericVSCodeExtensionAdapter("gemini", "Gemini Code Assist", "google.codegpt", "gemini"),
    GenericVSCodeExtensionAdapter("tabnine", "Tabnine", "TabNine.tabnine-vscode", "tabnine"),
]


# =============================================================================
# EXPORT LOGIC
# =============================================================================

def format_role(role):
    mapping = {"user": "USER", "assistant": "ASSISTANT", "system": "SYSTEM", "tool": "TOOL"}
    return mapping.get(role, role.upper())


def render_markdown(title, directory, messages, include_tools=True, harness="unknown"):
    lines = []
    lines.append(f"# Chat Export: {title}")
    lines.append(f"- Harness: `{harness}`")
    lines.append(f"- Directory: `{directory}`" if directory else "")
    lines.append(f"- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Total messages: {len(messages)}")
    lines.append("")
    msg_num = 0
    for msg in messages:
        if not msg.content and (not msg.tool_calls or not include_tools):
            continue
        msg_num += 1
        ts = datetime.fromtimestamp(msg.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "N/A"
        lines.append("---")
        lines.append(f"## #{msg_num} | {format_role(msg.role)} | {ts}")
        lines.append("")
        if msg.content:
            lines.append(msg.content)
            lines.append("")
        if msg.tool_calls and include_tools:
            for tc in msg.tool_calls:
                if isinstance(tc, str):
                    # Legacy raw JSON blob
                    lines.append(f"[TOOL]\n{tc[:2000]}")
                    lines.append("")
                    continue
                tname = tc.get("name", "unknown")
                targs = tc.get("args", {})
                tresult = tc.get("result", None)
                tstatus = tc.get("status", "")
                label = f"[TOOL: {tname}]" + (f" ({tstatus})" if tstatus else "")
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
                lines.append("\n".join(parts))
                lines.append("")
    return "\n".join(lines)


def list_all_harnesses():
    print(f"Universal Chat Export v{VERSION}")
    print(f"Detected harnesses on this machine:\n")
    for adapter in ADAPTERS:
        print(adapter.status())
    print()


def list_sessions_all(directory=None, limit=20):
    all_sessions = []
    for adapter in ADAPTERS:
        if adapter.detect():
            try:
                sessions = adapter.list_sessions(directory=directory, limit=limit)
                all_sessions.extend(sessions)
            except Exception as e:
                print(f"  [{adapter.name}] error listing sessions: {e}", file=sys.stderr)
    all_sessions.sort(key=lambda s: s.timestamp, reverse=True)
    for s in all_sessions[:limit]:
        print(s.display())
    print(f"\n{len(all_sessions)} session(s) found.")
    return all_sessions


def find_adapter_for_session(session_id):
    """Find which adapter has this session."""
    for adapter in ADAPTERS:
        if adapter.detect():
            try:
                sessions = adapter.list_sessions(limit=9999)
                for s in sessions:
                    if s.session_id == session_id:
                        return adapter
            except Exception:
                continue
    return None


def main():
    parser = argparse.ArgumentParser(
        description=f"Universal Chat Export v{VERSION} — export chat history from 20+ AI coding tools"
    )
    parser.add_argument("--session-id", "-s", help="Specific session ID to export")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--directory", "-d", help="Project directory to filter sessions")
    parser.add_argument("--list", "-l", action="store_true", help="List recent sessions across all harnesses")
    parser.add_argument("--list-all", action="store_true", help="List all sessions")
    parser.add_argument("--list-harnesses", action="store_true", help="Show detected harnesses and exit")
    parser.add_argument("--no-tools", action="store_true", help="Exclude tool calls from export")
    parser.add_argument("--harness", help="Filter to a specific harness (e.g. opencode, cursor, claude-code)")
    parser.add_argument("--db", help="Custom database path (opencode only, overrides auto-detection)")
    args = parser.parse_args()

    if args.db:
        OpencodeAdapter._db_override = args.db

    if args.list_harnesses:
        list_all_harnesses()
        return

    if args.list or args.list_all:
        directory = args.directory or os.environ.get("OPENCODE_WORKSPACE_DIR") or None
        limit = 9999 if args.list_all else 20
        if args.harness:
            adapter = next((a for a in ADAPTERS if a.name == args.harness), None)
            if not adapter:
                print(f"Error: unknown harness '{args.harness}'. Use --list-harnesses to see options.", file=sys.stderr)
                sys.exit(1)
            if not adapter.detect():
                print(f"Error: {adapter.display_name} not detected on this machine.", file=sys.stderr)
                sys.exit(1)
            sessions = adapter.list_sessions(directory=directory, limit=limit)
            for s in sessions:
                print(s.display())
            print(f"\n{len(sessions)} session(s) found.")
        else:
            list_sessions_all(directory=directory, limit=limit)
        return

    # Export mode
    if args.harness:
        adapter = next((a for a in ADAPTERS if a.name == args.harness), None)
        if not adapter:
            print(f"Error: unknown harness '{args.harness}'. Use --list-harnesses to see options.", file=sys.stderr)
            sys.exit(1)
        if not adapter.detect():
            print(f"Error: {adapter.display_name} not detected on this machine.", file=sys.stderr)
            sys.exit(1)
    else:
        adapter = None
        if args.session_id:
            adapter = find_adapter_for_session(args.session_id)
            if not adapter:
                print(f"Error: session '{args.session_id}' not found in any harness. Use --list to see sessions.", file=sys.stderr)
                sys.exit(1)
        else:
            # Default to first detected adapter with sessions
            directory = args.directory or os.environ.get("OPENCODE_WORKSPACE_DIR") or os.getcwd()
            for a in ADAPTERS:
                if a.detect():
                    sessions = a.list_sessions(directory=directory, limit=1)
                    if sessions:
                        adapter = a
                        args.session_id = sessions[0].session_id
                        break
            if not adapter:
                print("Error: no sessions found in any harness. Use --list to see available sessions.", file=sys.stderr)
                sys.exit(1)

    title, directory, messages = adapter.export_session(args.session_id, include_tools=not args.no_tools)
    if not messages:
        print(f"No messages found for session {args.session_id} in {adapter.display_name}.", file=sys.stderr)
        sys.exit(1)

    md = render_markdown(title, directory, messages, include_tools=not args.no_tools, harness=adapter.name)
    output_path = args.output or os.path.join(os.getcwd(), f"chat_export_{args.session_id[:16]}.md")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Exported {len(messages)} messages from {adapter.display_name} to {output_path} ({os.path.getsize(output_path):,} bytes)")


if __name__ == "__main__":
    main()
