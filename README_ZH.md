# export-chat — 中文说明

通用聊天记录导出工具，支持 **20+ AI 编程工具/IDE**。直接从每个工具的本地存储（SQLite、JSON、JSONL、Markdown、YAML）读取对话，并导出为结构化的 Markdown 文件。

## 支持的工具

| # | 工具 | 格式 | 状态 |
|---|------|------|------|
| 1 | Claude Code | JSONL | ✅ 完整 |
| 2 | Cursor | SQLite (state.vscdb) | ✅ 完整 |
| 3 | GitHub Copilot Chat | SQLite (VS Code) | ⚠️ 部分 |
| 4 | Windsurf | SQLite (state.vscdb) | ⚠️ 部分 |
| 5 | Continue | JSON | ✅ 完整 |
| 6 | Cline | JSON (per-task) | ✅ 完整 |
| 7 | Aider | Markdown | ✅ 完整 |
| 8 | Codex CLI | JSONL | ✅ 完整 |
| 9 | Opencode | SQLite (opencode.db) | ✅ 完整 |
| 10 | Zed AI | SQLite | ⚠️ 未记录 |
| 11 | Trae | SQLite (state.vscdb) | ⚠️ 部分 |
| 12 | JetBrains AI Assistant | XML | ⚠️ 未记录 |
| 13 | Cody (Sourcegraph) | JSON | ✅ 完整 |
| 14 | Amazon Q Developer | SQLite (VS Code) | ⚠️ 部分 |
| 15 | Gemini Code Assist | SQLite (VS Code) | ⚠️ 部分 |
| 16 | Tabnine | SQLite (VS Code) | ⚠️ 部分 |
| 17 | Warp | SQLite + JSON | ⚠️ 部分 |
| 18 | Kilo Code | JSON (per-task) | ✅ 完整 |
| 19 | Roo Code | JSON (per-task) | ✅ 完整 |
| 20 | Goose | YAML | ✅ 完整 |

## 安装

将技能文件放入 opencode 技能目录：

```
~/.config/opencode/skills/export-chat/SKILL.md
~/.config/opencode/skills/export-chat/export_chat.py
```

或项目级安装：

```
.opencode/skills/export-chat/SKILL.md
.opencode/skills/export-chat/export_chat.py
```

安装后**重启 opencode** 以加载技能。

## 使用方法

### 在 opencode 中

直接让代理导出聊天：

- "导出这个对话"
- "保存我们的聊天到文件"
- "导出聊天历史"
- "从 Cursor 导出聊天"
- "导出我的 Continue 会话"

代理将调用技能并将 Markdown 文件保存到当前项目目录。

### 命令行

```bash
# 列出本机检测到的工具
python export_chat.py --list-harnesses

# 列出所有检测到的工具的最近会话
python export_chat.py --list

# 列出所有会话
python export_chat.py --list-all

# 仅列出特定工具的会话
python export_chat.py --list --harness cursor
python export_chat.py --list --harness opencode
python export_chat.py --list --harness continue

# 导出特定会话（自动检测工具）
python export_chat.py -s "ses_abc123"

# 指定工具导出
python export_chat.py -s "665f8904-..." --harness continue -o /tmp/chat.md

# 仅导出文本（不含工具调用）
python export_chat.py -s "ses_abc123" --no-tools

# 按项目目录筛选
python export_chat.py --list -d /path/to/project

# 自定义数据库路径（旧版，仅 opencode）
python export_chat.py --db /path/to/opencode.db --list
```

## 脚本参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--session-id` | `-s` | 要导出的会话 ID |
| `--output` | `-o` | 自定义输出文件路径 |
| `--directory` | `-d` | 筛选会话的项目目录 |
| `--list` | `-l` | 列出所有工具中最近的 20 个会话 |
| `--list-all` | | 列出所有会话 |
| `--list-harnesses` | | 显示所有 20 个工具及检测状态 |
| `--harness` | | 筛选特定工具（如 `opencode`、`cursor`） |
| `--no-tools` | | 导出中排除工具调用 |
| `--db` | | 自定义数据库路径（旧版，仅 opencode） |

## 智能截断

- 工具调用参数截断为 800 字符
- 工具调用结果截断为 2000 字符
- 使用 `--no-tools` 可获得仅对话的干净导出

## 系统要求

- Python 3.6+（无外部依赖 — 仅标准库）
- 对工具数据库的只读访问（不修改任何内容）

## 更新日志

### v2.0.0 — 2026-08-18

**重大重写：通用多工具支持**

- **支持 20 个工具**：Claude Code、Cursor、GitHub Copilot Chat、Windsurf、Continue、Cline、Aider、Codex CLI、Opencode、Zed AI、Trae、JetBrains AI Assistant、Cody、Amazon Q Developer、Gemini Code Assist、Tabnine、Warp、Kilo Code、Roo Code、Goose
- **适配器架构**：每个工具拥有自己的适配器，包含 `detect()`、`list_sessions()`、`export_session()` 方法
- **跨工具搜索**：`--list` 扫描所有检测到的工具并聚合会话
- **工具筛选**：`--harness <name>` 筛选特定工具
- **自动检测**：存储位置按平台自动检测（Windows/Linux/macOS）
- **完全向后兼容**：v1.x 命令继续有效

### v1.1 — 2026-08-18

**修复：**
- Windows Unicode 崩溃：当打印包含非 ASCII 字符（西里尔字母、emoji、货币符号如 ₽）的会话标题时，`export_chat.py` 在默认控制台编码为 cp1251 或 cp437 的 Windows 上崩溃。脚本现在在启动时检测到非 UTF-8 编码时调用 `sys.stdout.reconfigure(encoding="utf-8")`。

### v1.0 — 初始版本

- 仅支持从 opencode SQLite 数据库导出

## 许可证

MIT
