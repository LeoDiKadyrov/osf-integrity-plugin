# OSF Assistant — Design Spec
**Date:** 2026-05-01  
**Status:** Approved

---

## Overview

OSF Assistant — это опенсорсный плагин для Claude Code с MCP-интерфейсом, который помогает исследователям (прежде всего студентам) соблюдать стандарты Open Science с самого начала работы над исследованием.

**Цель MVP:** Сформировать правильные методологические привычки у людей, которые ещё не писали научных работ, через структурированный диалог и автоматизацию рутинных шагов.

**Целевая аудитория:** Студенты-исследователи, независимые учёные. Open source.

---

## Архитектура

Монорепо: Claude Code плагин (скиллы) + Python MCP-сервер. Скиллы ведут диалог с пользователем и вызывают MCP-инструменты для реальной работы (API-запросы, генерация файлов). Одна кодовая база, два интерфейса — Claude Code и любой MCP-совместимый клиент (Cursor и др.).

```
osf-assistant/
  plugin.json              ← Claude Code plugin manifest
  skills/
    preregister.md         ← v1: пошаговый диалог пререгистрации
    find-evidence.md       ← v1: поиск доказательной базы
  mcp/
    server.py              ← точка входа FastMCP-сервера
    tools/
      preregistration.py   ← generate_preregistration + osf_upload
      evidence.py          ← search_evidence + format_evidence_table
    templates/
      osf_standard.json    ← шаблон OSF Standard Pre-Registration
      aspredicted.json     ← шаблон AsPredicted
  tests/
    test_preregistration.py
    test_evidence.py
  pyproject.toml
  .env.example
  README.md
```

**Tech stack:**
- Python 3.11+
- `fastmcp` — MCP-сервер
- OSF REST API — загрузка пререгистраций (Personal Access Token)
- Semantic Scholar Academic Graph API — поиск статей (без авторизации для базовых запросов)

---

## Поток данных

### Пререгистрация
```
Пользователь
  → invoкает скилл preregister
  → Скилл ведёт диалог (9 этапов, один вопрос за раз)
  → Вызывает MCP: generate_preregistration(data, template)
  → Файл сохраняется локально: preregistration_YYYY-MM-DD.md
  → Опционально: osf_upload(token, project_id, file_path) → URL
```

### Поиск доказательной базы
```
Пользователь описывает гипотезу
  → Скилл формулирует поисковые запросы
  → Вызывает MCP: search_evidence(queries, limit)
  → Агрегация + дедупликация результатов
  → format_evidence_table(papers) → Markdown-таблица
  → Предложение добавить в раздел литературы пререгистрации
```

---

## Скиллы (v1)

### `preregister`
Ведёт исследователя через 9 обязательных этапов. Пропуск этапа невозможен — если пользователь не знает ответа, скилл объясняет зачем это нужно и помогает сформулировать.

| Этап | Содержание |
|------|------------|
| 1 | Тема и контекст исследования |
| 2 | Явная формулировка H0 и H1 |
| 3 | Дизайн (between/within-subjects, лонгитюд, наблюдение) |
| 4 | Переменные: IV, DV, ковариаты, способ измерения |
| 5 | Выборка: планируемый N, критерии включения/исключения |
| 6 | План анализа: тест, порог α, поправки на множественные сравнения |
| 7 | Выбор шаблона: OSF Standard или AsPredicted |
| 8 | Генерация файла через MCP |
| 9 | Опциональная заливка в OSF |

### `find-evidence`
Принимает гипотезу → формулирует запросы → возвращает структурированную таблицу статей с полями: авторы, год, N, effect size (если доступен в метаданных), дизайн, doi. Effect size не галлюцинируется — поле остаётся пустым если данных нет.

---

## MCP-инструменты (v1)

### `generate_preregistration(data: dict, template: str) → str`
Заполняет выбранный шаблон данными из диалога. Сохраняет файл в `OUTPUT_DIR/preregistration_YYYY-MM-DD.md`. Возвращает путь к файлу.

### `osf_upload(token: str, project_id: str, file_path: str) → str`
Загружает файл в OSF-проект через REST API. Возвращает URL пререгистрации. Недоступен без токена — остальные инструменты работают независимо.

### `search_evidence(queries: list[str], limit: int = 10) → list[dict]`
Запросы к Semantic Scholar API. Агрегирует, дедуплицирует. Возвращает список `[title, authors, year, n, effect_size, design, doi]`.

### `format_evidence_table(papers: list[dict]) → str`
Форматирует результаты в Markdown-таблицу. Утилита, не делает внешних запросов.

---

## Установка и конфигурация

```bash
git clone https://github.com/user/osf-assistant
cd osf-assistant
pip install -e .
```

Конфигурация через `.env`:
```
OSF_TOKEN=        # опционально — только для заливки в OSF
OSF_PROJECT_ID=   # опционально
OUTPUT_DIR=./preregistrations
```

Без токена OSF весь функционал работает локально. Студент может начать пользоваться сразу.

`plugin.json` регистрирует скиллы и MCP-сервер — одна команда подключает всё в Claude Code.

---

## Вне скоупа v1

- `check-bias` скилл и MCP-инструмент
- `power-analysis` скилл и MCP-инструмент
- Веб-интерфейс
- Командная/лабораторная синхронизация
- Интеграция с Obsidian/Notion
