# export-chat — README на русском

Универсальный инструмент экспорта истории чатов для **20+ AI-харнессов/IDE**. Читает диалоги напрямую из локального хранилища каждого инструмента (SQLite, JSON, JSONL, Markdown, YAML) и экспортирует в структурированный Markdown-файл.

## Поддерживаемые харнессы

| # | Харнесс | Формат | Статус |
|---|---------|--------|--------|
| 1 | Claude Code | JSONL | ✅ Полная |
| 2 | Cursor | SQLite (state.vscdb: composerHeaders + бабблы cursorDiskKV) | ✅ Полная (проверено) |
| 3 | GitHub Copilot Chat | SQLite (VS Code) | ⚠️ Частичная |
| 4 | Windsurf | SQLite (state.vscdb + workspaceStorage, ChatSessionStore.index) | ⚠️ Частичная |
| 5 | Continue | JSON | ✅ Полная (проверено) |
| 6 | Cline | JSON (per-task) | ✅ Полная |
| 7 | Aider | Markdown | ✅ Полная |
| 8 | Codex CLI | JSONL | ✅ Полная |
| 9 | Opencode | SQLite (opencode.db, ранжированное авто-определение) | ✅ Полная (проверено) |
| 10 | Zed AI | SQLite | ⚠️ Недокументировано |
| 11 | Trae | SQLite (только метаданные сессий; тела — в IndexedDB) | ⚠️ Только метаданные |
| 12 | JetBrains AI Assistant | XML | ⚠️ Недокументировано |
| 13 | Cody (Sourcegraph) | JSON | ✅ Полная |
| 14 | Amazon Q Developer | SQLite (VS Code) | ⚠️ Частичная |
| 15 | Gemini Code Assist | SQLite (VS Code) | ⚠️ Частичная |
| 16 | Tabnine | SQLite (VS Code) | ⚠️ Частичная |
| 17 | Warp | SQLite + JSON | ⚠️ Частичная |
| 18 | Kilo Code | JSON (per-task) | ✅ Полная |
| 19 | Roo Code | JSON (per-task) | ✅ Полная |
| 20 | Goose | YAML | ✅ Полная |

_✅ Полная (проверено) = протестировано живьём 30.09.2026: список сессий + полный экспорт с реальными телами сообщений. ✅ Полная без пометки = код полный под документированный формат, но живых данных на тестовой машине нет. ⚠️ = best-effort с честным fallback: инструмент сообщает, что нашёл, а не молчит (Trae отдаёт метаданные сессий, т.к. тела лежат в IndexedDB, а не SQLite; форматы Zed/JetBrains недокументированы)._

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

# Пользовательский путь к БД (только opencode; перекрывает авто-определение, или переменная OPENCODE_DB)
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
| `--db` | | Пользовательский путь к БД opencode (перекрывает ранжированное авто-определение; или переменная `OPENCODE_DB`) |

## Умное усечение

- Аргументы вызовов инструментов усекаются до 800 символов
- Результаты вызовов инструментов усекаются до 2000 символов
- Используйте `--no-tools` для чистого экспорта только диалога

## Требования

- Python 3.6+ (без внешних зависимостей — только стандартная библиотека)
- Доступ только для чтения к базам данных харнессов (ничего не изменяет)

## Журнал изменений

### v2.2.0 — 2026-09-30

**Живой аудит всех 20 харнессов + фиксы Cursor/Trae/Windsurf**

- **Cursor переписан (проверено живьём)**: сообщения читаются из бабблов `cursorDiskKV` (`bubbleId:<composerId>:<bubbleId>`, роли 1=user / 2=assistant, порядок из `fullConversationHeadersOnly`); заголовки из `composerData.name` с fallback на первое сообщение юзера; пустые композеры честно сообщают об отсутствии сообщений. Тест: экспорт на 83 сообщения с реальным заголовком и таймстампами.
- **Trae (проверено живьём)**: сессии из `icube_session_agent_map` (глобальная + workspaceStorage БД); экспорт отдаёт метаданные с честной заглушкой (тела — в IndexedDB, не в SQLite).
- **Windsurf (проверено живьём)**: индекс сессий из `chat.ChatSessionStore.index` по всем БД (на тестовой машине пуст → корректно 0 сессий).
- **Continue**: подхват контент-блоков без явного `type`, но с полем `text`.
- Таблица поддержки теперь различает проверенные живьём, полные по коду и best-effort адаптеры.

### v2.1.0 — 2026-09-30

**Смена формата хранения opencode**

- **Ранжированное авто-определение БД**: кандидаты оцениваются по валидности (размер + SQLite-магия + таблица `session`), а не по порядку — 0-байтная заглушка в `%LOCALAPPDATA%\opencode\opencode.db` больше не затеняет реальную базу 1.4 ГБ.
- **Флаг `--db` реально работает** (раньше парсился и игнорировался); поддержана переменная `OPENCODE_DB`.
- **Новые типы `part`**: `tool` (через `state.{input,output,status}`), `reasoning`, `patch`, `file`; `step-*`/`compaction` пропускаются как конверт. Legacy `tool_use`/`tool_result` по-прежнему рендерятся.

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
