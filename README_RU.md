# export-chat — README на русском

Универсальный инструмент экспорта истории чатов для **20+ AI-харнессов/IDE**. Читает диалоги напрямую из локального хранилища каждого инструмента (SQLite, JSON, JSONL, Markdown, YAML) и экспортирует в структурированный Markdown-файл.

## Поддерживаемые харнессы

| # | Харнесс | Формат | Статус |
|---|---------|--------|--------|
| 1 | Claude Code | JSONL | ✅ Полная |
| 2 | Cursor | SQLite (state.vscdb) | ✅ Полная |
| 3 | GitHub Copilot Chat | SQLite (VS Code) | ⚠️ Частичная |
| 4 | Windsurf | SQLite (state.vscdb) | ⚠️ Частичная |
| 5 | Continue | JSON | ✅ Полная |
| 6 | Cline | JSON (per-task) | ✅ Полная |
| 7 | Aider | Markdown | ✅ Полная |
| 8 | Codex CLI | JSONL | ✅ Полная |
| 9 | Opencode | SQLite (opencode.db) | ✅ Полная |
| 10 | Zed AI | SQLite | ⚠️ Недокументировано |
| 11 | Trae | SQLite (state.vscdb) | ⚠️ Частичная |
| 12 | JetBrains AI Assistant | XML | ⚠️ Недокументировано |
| 13 | Cody (Sourcegraph) | JSON | ✅ Полная |
| 14 | Amazon Q Developer | SQLite (VS Code) | ⚠️ Частичная |
| 15 | Gemini Code Assist | SQLite (VS Code) | ⚠️ Частичная |
| 16 | Tabnine | SQLite (VS Code) | ⚠️ Частичная |
| 17 | Warp | SQLite + JSON | ⚠️ Частичная |
| 18 | Kilo Code | JSON (per-task) | ✅ Полная |
| 19 | Roo Code | JSON (per-task) | ✅ Полная |
| 20 | Goose | YAML | ✅ Полная |

## Установка

Поместите файлы скилла в директорию скиллов opencode:

```
~/.config/opencode/skills/export-chat/SKILL.md
~/.config/opencode/skills/export-chat/export_chat.py
```

Или для установки в конкретный проект:

```
.opencode/skills/export-chat/SKILL.md
.opencode/skills/export-chat/export_chat.py
```

После установки **перезапустите opencode**, чтобы скилл загрузился.

## Использование

### Внутри opencode

Просто попросите агента экспортировать чат:

- "экспортируй этот чат"
- "сохрани наш разговор в файл"
- "выгрузи историю чата"
- "экспортируй чат из Cursor"
- "экспортируй мою сессию Continue"

Агент вызовет скилл и сохранит Markdown-файл в директорию текущего проекта.

### Командная строка

```bash
# Список обнаруженных харнессов на этой машине
python export_chat.py --list-harnesses

# Список недавних сессий по ВСЕМ обнаруженным харнессам
python export_chat.py --list

# Список всех сессий
python export_chat.py --list-all

# Список сессий только из конкретного харнесса
python export_chat.py --list --harness cursor
python export_chat.py --list --harness opencode
python export_chat.py --list --harness continue

# Экспорт конкретной сессии (авто-определение харнесса)
python export_chat.py -s "ses_abc123"

# Экспорт с указанием харнесса
python export_chat.py -s "665f8904-..." --harness continue -o /tmp/chat.md

# Экспорт только текста (без вызовов инструментов)
python export_chat.py -s "ses_abc123" --no-tools

# Фильтр по директории проекта
python export_chat.py --list -d /path/to/project

# Пользовательский путь к БД (legacy, только для opencode)
python export_chat.py --db /path/to/opencode.db --list
```

## Флаги скрипта

| Флаг | Краткий | Описание |
|------|---------|----------|
| `--session-id` | `-s` | ID сессии для экспорта |
| `--output` | `-o` | Пользовательский путь к файлу |
| `--directory` | `-d` | Директория проекта для фильтрации сессий |
| `--list` | `-l` | Список 20 недавних сессий по всем харнессам |
| `--list-all` | | Список всех сессий |
| `--list-harnesses` | | Показать все 20 харнессов и статус обнаружения |
| `--harness` | | Фильтр по конкретному харнессу (например, `opencode`, `cursor`) |
| `--no-tools` | | Исключить вызовы инструментов из экспорта |
| `--db` | | Пользовательский путь к БД (legacy, только opencode) |

## Умное усечение

- Аргументы вызовов инструментов усекаются до 800 символов
- Результаты вызовов инструментов усекаются до 2000 символов
- Используйте `--no-tools` для чистого экспорта только диалога

## Требования

- Python 3.6+ (без внешних зависимостей — только стандартная библиотека)
- Доступ только для чтения к базам данных харнессов (ничего не изменяет)

## Журнал изменений

### v2.0.0 — 2026-08-18

**Крупное переписывание: универсальная поддержка нескольких харнессов**

- **20 харнессов поддерживается**: Claude Code, Cursor, GitHub Copilot Chat, Windsurf, Continue, Cline, Aider, Codex CLI, Opencode, Zed AI, Trae, JetBrains AI Assistant, Cody, Amazon Q Developer, Gemini Code Assist, Tabnine, Warp, Kilo Code, Roo Code, Goose
- **Архитектура адаптеров**: каждый харнесс имеет свой адаптер с методами `detect()`, `list_sessions()`, `export_session()`
- **Кросс-харнессовый поиск**: `--list` сканирует все обнаруженные харнессы и агрегирует сессии
- **Фильтр по харнессу**: `--harness <name>` фильтрует по конкретному инструменту
- **Авто-определение**: места хранения авто-определяются по платформе (Windows/Linux/macOS)
- **Полная обратная совместимость**: команды v1.x продолжают работать

### v1.1 — 2026-08-18

**Исправлено:**
- Краш на Windows при Unicode: `export_chat.py` падал с `UnicodeEncodeError: 'charmap' codec can't encode character` при выводе заголовков сессий с не-ASCII символами (кириллица, эмодзи, знак ₽). Скрипт теперь вызывает `sys.stdout.reconfigure(encoding="utf-8")` при запуске.

### v1.0 — Начальный релиз

- Экспорт только из opencode (SQLite)

## Лицензия

MIT
