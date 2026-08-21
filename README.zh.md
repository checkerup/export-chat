[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![Русский](https://img.shields.io/badge/lang-Русский-red.svg)](README.ru.md) [![中文](https://img.shields.io/badge/lang-中文-green.svg)](README.zh.md)

# export-chat вЂ” дё­ж–‡иЇґжЋ

йЂљз”ЁиЃЉе¤©и®°еЅ•еЇје‡єе·Ґе…·пјЊж”ЇжЊЃ **20+ AI зј–зЁ‹е·Ґе…·/IDE**гЂ‚з›ґжЋҐд»ЋжЇЏдёЄе·Ґе…·зљ„жњ¬ењ°е­е‚Ёпј€SQLiteгЂЃJSONгЂЃJSONLгЂЃMarkdownгЂЃYAMLпј‰иЇ»еЏ–еЇ№иЇќпјЊе№¶еЇје‡єдёєз»“жћ„еЊ–зљ„ Markdown ж–‡д»¶гЂ‚

## ж”ЇжЊЃзљ„е·Ґе…·

| # | е·Ґе…· | ж јејЏ | зЉ¶жЂЃ |
|---|------|------|------|
| 1 | Claude Code | JSONL | вњ… е®Њж•ґ |
| 2 | Cursor | SQLite (state.vscdb) | вњ… е®Њж•ґ |
| 3 | GitHub Copilot Chat | SQLite (VS Code) | вљ пёЏ йѓЁе€† |
| 4 | Windsurf | SQLite (state.vscdb) | вљ пёЏ йѓЁе€† |
| 5 | Continue | JSON | вњ… е®Њж•ґ |
| 6 | Cline | JSON (per-task) | вњ… е®Њж•ґ |
| 7 | Aider | Markdown | вњ… е®Њж•ґ |
| 8 | Codex CLI | JSONL | вњ… е®Њж•ґ |
| 9 | Opencode | SQLite (opencode.db) | вњ… е®Њж•ґ |
| 10 | Zed AI | SQLite | вљ пёЏ жњЄи®°еЅ• |
| 11 | Trae | SQLite (state.vscdb) | вљ пёЏ йѓЁе€† |
| 12 | JetBrains AI Assistant | XML | вљ пёЏ жњЄи®°еЅ• |
| 13 | Cody (Sourcegraph) | JSON | вњ… е®Њж•ґ |
| 14 | Amazon Q Developer | SQLite (VS Code) | вљ пёЏ йѓЁе€† |
| 15 | Gemini Code Assist | SQLite (VS Code) | вљ пёЏ йѓЁе€† |
| 16 | Tabnine | SQLite (VS Code) | вљ пёЏ йѓЁе€† |
| 17 | Warp | SQLite + JSON | вљ пёЏ йѓЁе€† |
| 18 | Kilo Code | JSON (per-task) | вњ… е®Њж•ґ |
| 19 | Roo Code | JSON (per-task) | вњ… е®Њж•ґ |
| 20 | Goose | YAML | вњ… е®Њж•ґ |

## е®‰иЈ…

е°†жЉЂиѓЅж–‡д»¶ж”ѕе…Ґ opencode жЉЂиѓЅз›®еЅ•пјљ

```
~/.config/opencode/skills/export-chat/SKILL.md
~/.config/opencode/skills/export-chat/export_chat.py
```

ж€–йЎ№з›®зє§е®‰иЈ…пјљ

```
.opencode/skills/export-chat/SKILL.md
.opencode/skills/export-chat/export_chat.py
```

е®‰иЈ…еђЋ**й‡ЌеђЇ opencode** д»ҐеЉ иЅЅжЉЂиѓЅгЂ‚

## дЅїз”Ёж–№жі•

### ењЁ opencode дё­

з›ґжЋҐи®©д»Јзђ†еЇје‡єиЃЉе¤©пјљ

- "еЇје‡єиї™дёЄеЇ№иЇќ"
- "дїќе­ж€‘д»¬зљ„иЃЉе¤©е€°ж–‡д»¶"
- "еЇје‡єиЃЉе¤©еЋ†еЏІ"
- "д»Ћ Cursor еЇје‡єиЃЉе¤©"
- "еЇје‡єж€‘зљ„ Continue дјљиЇќ"

д»Јзђ†е°†и°ѓз”ЁжЉЂиѓЅе№¶е°† Markdown ж–‡д»¶дїќе­е€°еЅ“е‰ЌйЎ№з›®з›®еЅ•гЂ‚

### е‘Ѕд»¤иЎЊ

```bash
# е€—е‡єжњ¬жњєжЈЂжµ‹е€°зљ„е·Ґе…·
python export_chat.py --list-harnesses

# е€—е‡єж‰Ђжњ‰жЈЂжµ‹е€°зљ„е·Ґе…·зљ„жњЂиї‘дјљиЇќ
python export_chat.py --list

# е€—е‡єж‰Ђжњ‰дјљиЇќ
python export_chat.py --list-all

# д»…е€—е‡єз‰№е®ље·Ґе…·зљ„дјљиЇќ
python export_chat.py --list --harness cursor
python export_chat.py --list --harness opencode
python export_chat.py --list --harness continue

# еЇје‡єз‰№е®љдјљиЇќпј€и‡ЄеЉЁжЈЂжµ‹е·Ґе…·пј‰
python export_chat.py -s "ses_abc123"

# жЊ‡е®ље·Ґе…·еЇје‡є
python export_chat.py -s "665f8904-..." --harness continue -o /tmp/chat.md

# д»…еЇје‡єж–‡жњ¬пј€дёЌеђ«е·Ґе…·и°ѓз”Ёпј‰
python export_chat.py -s "ses_abc123" --no-tools

# жЊ‰йЎ№з›®з›®еЅ•з­›йЂ‰
python export_chat.py --list -d /path/to/project

# и‡Єе®љд№‰ж•°жЌ®еє“и·Їеѕ„пј€ж—§з‰€пјЊд»… opencodeпј‰
python export_chat.py --db /path/to/opencode.db --list
```

## и„љжњ¬еЏ‚ж•°

| еЏ‚ж•° | з®Ђе†™ | иЇґжЋ |
|------|------|------|
| `--session-id` | `-s` | и¦ЃеЇје‡єзљ„дјљиЇќ ID |
| `--output` | `-o` | и‡Єе®љд№‰иѕ“е‡єж–‡д»¶и·Їеѕ„ |
| `--directory` | `-d` | з­›йЂ‰дјљиЇќзљ„йЎ№з›®з›®еЅ• |
| `--list` | `-l` | е€—е‡єж‰Ђжњ‰е·Ґе…·дё­жњЂиї‘зљ„ 20 дёЄдјљиЇќ |
| `--list-all` | | е€—е‡єж‰Ђжњ‰дјљиЇќ |
| `--list-harnesses` | | жѕз¤єж‰Ђжњ‰ 20 дёЄе·Ґе…·еЏЉжЈЂжµ‹зЉ¶жЂЃ |
| `--harness` | | з­›йЂ‰з‰№е®ље·Ґе…·пј€е¦‚ `opencode`гЂЃ`cursor`пј‰ |
| `--no-tools` | | еЇје‡єдё­жЋ’й™¤е·Ґе…·и°ѓз”Ё |
| `--db` | | и‡Єе®љд№‰ж•°жЌ®еє“и·Їеѕ„пј€ж—§з‰€пјЊд»… opencodeпј‰ |

## ж™єиѓЅж€Єж–­

- е·Ґе…·и°ѓз”ЁеЏ‚ж•°ж€Єж–­дёє 800 е­—з¬¦
- е·Ґе…·и°ѓз”Ёз»“жћњж€Єж–­дёє 2000 е­—з¬¦
- дЅїз”Ё `--no-tools` еЏЇиЋ·еѕ—д»…еЇ№иЇќзљ„е№Іе‡ЂеЇје‡є

## зі»з»џи¦Ѓж±‚

- Python 3.6+пј€ж— е¤–йѓЁдѕќиµ– вЂ” д»…ж ‡е‡†еє“пј‰
- еЇ№е·Ґе…·ж•°жЌ®еє“зљ„еЏЄиЇ»и®їй—®пј€дёЌдї®ж”№д»»дЅ•е†…е®№пј‰

## ж›ґж–°ж—Ґеї—

### v2.0.0 вЂ” 2026-08-18

**й‡Ќе¤§й‡Ќе†™пјљйЂљз”Ёе¤ље·Ґе…·ж”ЇжЊЃ**

- **ж”ЇжЊЃ 20 дёЄе·Ґе…·**пјљClaude CodeгЂЃCursorгЂЃGitHub Copilot ChatгЂЃWindsurfгЂЃContinueгЂЃClineгЂЃAiderгЂЃCodex CLIгЂЃOpencodeгЂЃZed AIгЂЃTraeгЂЃJetBrains AI AssistantгЂЃCodyгЂЃAmazon Q DeveloperгЂЃGemini Code AssistгЂЃTabnineгЂЃWarpгЂЃKilo CodeгЂЃRoo CodeгЂЃGoose
- **йЂ‚й…Ќе™Ёжћ¶жћ„**пјљжЇЏдёЄе·Ґе…·ж‹Ґжњ‰и‡Єе·±зљ„йЂ‚й…Ќе™ЁпјЊеЊ…еђ« `detect()`гЂЃ`list_sessions()`гЂЃ`export_session()` ж–№жі•
- **и·Ёе·Ґе…·жђњзґў**пјљ`--list` ж‰«жЏЏж‰Ђжњ‰жЈЂжµ‹е€°зљ„е·Ґе…·е№¶иЃљеђ€дјљиЇќ
- **е·Ґе…·з­›йЂ‰**пјљ`--harness <name>` з­›йЂ‰з‰№е®ље·Ґе…·
- **и‡ЄеЉЁжЈЂжµ‹**пјље­е‚ЁдЅЌзЅ®жЊ‰е№іеЏ°и‡ЄеЉЁжЈЂжµ‹пј€Windows/Linux/macOSпј‰
- **е®Ње…Ёеђ‘еђЋе…је®№**пјљv1.x е‘Ѕд»¤з»§з»­жњ‰ж•€

### v1.1 вЂ” 2026-08-18

**дї®е¤Ќпјљ**
- Windows Unicode еґ©жєѓпјљеЅ“ж‰“еЌ°еЊ…еђ«йќћ ASCII е­—з¬¦пј€иҐїй‡Ње°”е­—жЇЌгЂЃemojiгЂЃиґ§еёЃз¬¦еЏ·е¦‚ в‚Ѕпј‰зљ„дјљиЇќж ‡йўж—¶пјЊ`export_chat.py` ењЁй»и®¤жЋ§е€¶еЏ°зј–з Ѓдёє cp1251 ж€– cp437 зљ„ Windows дёЉеґ©жєѓгЂ‚и„љжњ¬зЋ°ењЁењЁеђЇеЉЁж—¶жЈЂжµ‹е€°йќћ UTF-8 зј–з Ѓж—¶и°ѓз”Ё `sys.stdout.reconfigure(encoding="utf-8")`гЂ‚

### v1.0 вЂ” е€ќе§‹з‰€жњ¬

- д»…ж”ЇжЊЃд»Ћ opencode SQLite ж•°жЌ®еє“еЇје‡є

## и®ёеЏЇиЇЃ

MIT