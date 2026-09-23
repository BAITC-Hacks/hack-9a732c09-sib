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

Python 3.13.15 — проверенный интерпретатор; стандартная библиотека используется
в core. Транзитивные distributions с фактическими версиями перечислены в
`requirements-dev.lock`; их собственные copyright/license notices остаются
в установленных пакетах. Lock не означает, что все dev-пакеты нужны judge.

### Frontend

Версии и лицензии прочитаны из `node_modules/*/package.json` после успешного
`npm ci`; точные integrity/resolved и транзитивные пакеты находятся в
`frontend/package-lock.json`.

| Компонент | Версия | Назначение | Лицензия metadata |
|---|---:|---|---|
| React | 19.0.0 | UI runtime | MIT |
| React DOM | 19.0.0 | DOM renderer | MIT |
| Vite | 6.1.0 | dev server / production build | MIT |
| @vitejs/plugin-react | 4.3.4 | React transform для Vite | MIT |
| TypeScript | 5.7.3 | строгая типизация/build | Apache-2.0 |
| Vitest | 3.0.5 | unit/component tests | MIT |
| jsdom | 26.0.0 | DOM environment tests | MIT |
| Testing Library React | 16.2.0 | компонентные тесты | MIT |
| Testing Library jest-dom | 6.6.3 | DOM assertions | MIT |
| Testing Library user-event | 14.6.1 | пользовательские взаимодействия в tests | MIT |
| @types/node | 22.13.4 | TypeScript types для Vite config | MIT |
| @types/react | 19.0.8 | React TypeScript types | MIT |
| @types/react-dom | 19.0.3 | React DOM TypeScript types | MIT |

Node.js 22.14.0 и npm 10.9.2 — фактически проверенные инструменты сборки;
portable-копии не входят в Git. Frontend не использует внешние UI-шаблоны,
web-fonts, изображения или icon packs. FastAPI и runtime LLM SDK всё ещё не
установлены и относятся к будущим этапам.

## AI-assisted development

Codex помог создать архитектуру, исходники, тесты, контракт и документацию.
Дополнительный AI reviewer работал только на чтение. Это раскрытие инструмента
разработки, не runtime-зависимость и не подтверждение качества hidden score.
