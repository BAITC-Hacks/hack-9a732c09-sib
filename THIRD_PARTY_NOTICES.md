# Сторонние компоненты

## Организатор

PARTICIPANT_GUIDE, agent_template, environment, mock_environment, scoring_core,
local_eval, make_submission, CSV-справочники и data/** предоставлены в пакете
Beeline Tariff Marketing Campaigns Case. Все 15 файлов импортированы без
изменения содержимого; список и SHA256 — `docs/organizer-manifest.json`.
Данные синтетические, предоставлены организатором, не являются реальными
данными Beeline. Отдельная лицензия пакета не обнаружена; наличие данных
не означает разрешение на любое внешнее использование.

## Реально установленные прямые зависимости

### Python / judge tooling

Версии и лицензии ниже прочитаны из METADATA установленных distributions,
не предполагаются по памяти. Полные тексты — в dist-info/licenses пакетов.

| Компонент | Версия | Назначение | Метаданные лицензии |
|---|---|---|---|
| pandas | 2.3.3 | DataFrame и organizer runtime | BSD 3-Clause License |
| NumPy | 2.5.3 | Organizer runtime | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pytest | 9.1.1 | Тесты | MIT |
| jsonschema | 4.26.0 | JSON/fixture validation | MIT |
| PyYAML | 6.0.3 | Чтение OpenAPI YAML | MIT |
| openapi-spec-validator | 0.7.2 | Валидация OpenAPI 3.1 | Apache-2.0 |

Python 3.13.15 проверен на архитектурном этапе, Python 3.14.7 — на backend.
Стандартная библиотека используется в core. Транзитивные distributions перечислены в
`requirements-dev.lock`; их собственные copyright/license notices остаются
в установленных пакетах. Lock не означает, что все dev-пакеты нужны judge.

React/Vite/TypeScript/FastAPI пока не установлены и не являются использованными
компонентами проекта. Их notices добавляют соответствующие будущие этапы.
Внешних UI-шаблонов, изображений или runtime LLM SDK сейчас нет.

## AI-assisted development

Codex помог создать архитектуру, исходники, тесты, контракт и документацию.
Дополнительный AI reviewer работал только на чтение. Это раскрытие инструмента
разработки, не runtime-зависимость и не подтверждение качества hidden score.
