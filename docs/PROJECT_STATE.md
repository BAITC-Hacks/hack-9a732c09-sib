# Текущее состояние

Обновлено: 2026-09-23T15:20:01+05:00.
Текущий этап: BACKEND MVP реализован, frontend и интеграция впереди.
Активная роль: BACKEND.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Наблюдаемый HEAD: cb803de, ветка main. Сохранены незакоммиченные изменения
предыдущей итерации adaptive/runtime/backend.

| Стадия | Статус | Состояние |
|---|---|---|
| Architecture / Core | DONE | Judge/baseline/контракты, 44 tests; verifier блокируется существующими окончаниями строк |
| Frontend | NOT_STARTED | Только README/role prompt и внешние JSON fixtures |
| Backend | IMPLEMENTED | FastAPI, runner, DTO, in-memory очередь, 38 tests, реальный HTTP smoke |
| Final integration | NOT_STARTED | Нужны frontend, UI/E2E и восстановление organizer byte integrity |

Пользователь явно попросил начать backend в текущем клоне; обычная
последовательность FRONTEND → BACKEND изменена для этой сессии. Завершённого
frontend handoff/client нет. Codex не делал Git-операций записи.
Существовавшее изменение `.gitignore` (`public/*`) сохранено без правок.

## Работает

Core неизменён: до трёх пилотов, финальный план/fallback, без сети/LLM/ключей.
API `backend.app.main:app`: все четыре endpoint `/api/v1`. POST → 202/queued,
отдельный worker выполняет один run за раз; GET → queued/running/completed/failed.
UUID и результаты хранятся в памяти. Каждый запуск вызывает Engine ровно
один раз внутри официального evaluator. KPI учитывают точные пилотные ID;
неполный trace не публикуется. Строгий JSON, nullable ROI, счётчики финала,
нормализованные ошибки, настраиваемый local CORS, summary из публичных CSV.

Fixtures по-прежнему иллюстративные mock_fixture; реальные ответы API —
mock_environment. UI, runtime LLM, БД и UI/E2E отсутствуют.

## Последние фактические проверки

Windows, Python 3.14.7, локальная .venv, backend dependencies установлены.
Короткий python в PATH указывает на неработающий WindowsApps alias.
Команды ниже выполнены через `.venv/Scripts/python.exe`; для CLI установлен
PYTHONUTF8=1, чтобы официальный Unicode-вывод работал в Windows.

| Команда / сценарий | Статус | Результат |
|---|---|---|
| python scripts/verify_core.py, до/после | FAIL | Существующие CRLF вместо LF в 14 organizer-файлах; первая ошибка agent_template.py |
| python local_eval.py | PASS | 3 пилота, 1 финал, 1285 контактов, cost=0, net≈4042 |
| python local_eval.py --runs 10 | PASS | 10 завершённых прогонов; 6/10 прибыльны, min≈−41150, max≈6960 |
| python make_submission.py | PASS | 1 финал, содержимое соответствует существующему submission |
| scripts.verify_core.verify_submission() | PASS | Два экспорта побайтно совпали; существующий CSV сохранён |
| python -m pytest -q | PASS | 82 passed, 28.12s: 44 core + 38 backend; 1 Starlette deprecation warning |
| Real Uvicorn / HTTP smoke | PASS | В pytest: сервер на localhost, health/summary/POST/poll/404/422 |
| python -m pip check | PASS | No broken requirements found |
| git diff --check | PASS | Нет whitespace errors |
| Frontend build/tests, UI/E2E с VITE_USE_MOCKS=false | NOT_RUN | Нет frontend package.json, client, UI и завершённого handoff |

Первый backend test run: 35 passed / 1 failed из-за неверного предположения
теста об отрицательном seed 0; исправлен на фактически отрицательный seed 1.
Первый multi-seed CLI завершил вычисления, но упал на UnicodeEncodeError
символа ⚠ в CP1251. Повтор с PYTHONUTF8=1 — PASS.

## Существующая проблема byte integrity

Все 15 organizer-файлов в Git HEAD точно совпадают с SHA256 manifest.
На диске 14 текстовых файлов имеют CRLF вместо LF (`i/lf w/crlf attr/-text`);
после только CRLF→LF каждый hash совпадает. PDF совпадает сразу. Содержательных
изменений нет. Backend-сессия не меняла эти файлы, manifest или .gitattributes.
Полный verifier нельзя объявить PASS до восстановления побайтного состояния
человеком/отдельной согласованной интеграцией.

## Ограничения и следующий шаг

- Baseline не оптимизирован, net неустойчив. Mock не прогнозирует hidden score.
  UNKNOWN в summary не является допустимым campaign filter.
- API запускать из корня, одним процессом Uvicorn. Перезапуск теряет историю;
  очередь/история в памяти, без TTL/отмены/жёсткого timeout выполнения.
- Совместимость UI с API ещё не проверена; OpenAPI v1 неизменён.
- Реализовать frontend по `.codex/prompts/02-frontend.md` с учётом готового
  backend, затем выполнить integration prompt.
- Перед ручным commit/push проверить diff/untracked, устранить/подтвердить
  organizer endings и повторить verifier. Linux/macOS пока не проверены.

Запуск: [README](../README.md), [backend README](../backend/README.md).
Последний завершённый handoff:
[03-backend-to-integration.md](handoffs/03-backend-to-integration.md).
VERIFICATION_REPORT.md — исторический архитектурный отчёт, не текущая проверка.
