# Handoff 03 — BACKEND → FRONTEND / INTEGRATION

Статус: DONE в scope backend MVP; UI/E2E и общий integrity gate не завершены.
Дата/время: 2026-09-23T15:20:01+05:00.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Исходный HEAD: d0c33eb, ветка main.
Ожидаемый commit message: `feat(backend): implement mock strategy API v1`.

## Выполненная цель и изменения

По прямому запросу пользователя backend реализован до frontend. Предыдущий
завершённый handoff — 01; завершённого 02 нет, frontend содержит только README.
Пользователю объяснены назначение агента, тестирование и запуск API.

- `backend/app/schemas.py`: Pydantic DTO по API v1, strict validation.
- `backend/app/runner.py`: Engine один раз внутри официального evaluator;
  проверки успешного возврата, pilot/final counters, details и расходов.
- `backend/app/service.py`: память, lock, один worker/очередь, lifecycle.
- `backend/app/main.py`: четыре endpoint, UUID/body validation, CORS,
  ErrorResponse 404/422/500 без exception text во внешних ответах.
- `backend/app/summary.py`: публичные агрегаты, UNKNOWN, все абоненты.
- `backend/smoke.py`: повторяемая HTTP-проверка работающего сервера.
- Отдельные requirements/dev/lock, `.env.example`, package init.
- `tests/backend/`: 38 tests — контракт, runner, lifecycle, изоляция,
  ошибки, CORS, настоящий Uvicorn и HTTP smoke.
- README, backend README, PROJECT_STATE, PROGRESS, notices и этот handoff;
  в contracts/README исправлено устаревшее утверждение об отсутствии сервера.

Core, OpenAPI/fixtures, organizer-файлы и frontend не изменялись. ADR для
контракта не нужен: endpoints и DTO соответствуют существующему v1.
Чужое изменение `.gitignore` (`public/*`) сохранено. Codex не выполнял
commit/push/pull/merge/rebase/checkout. Дополнительный reviewer работал
только на чтение; редактирование выполнял один агент последовательно.

## Решения и замороженные границы

Сохранены `Agent.act(env) -> list[dict]`, `StrategyEngine.run -> StrategyRun`,
API v1. Agent не запускается повторно ради KPI. Только официальный evaluator
работает с точными пилотными ID; backend/core не читают internals среды.

POST всегда 202 + queued metadata. GET failed — 200; отрицательный net —
completed. n_campaigns — только финал, details — пилоты/финал с kind/index.
Остатки после полного score; ROI при cost=0 — null + warning. Не-finite KPI,
неполный trace или проглоченное evaluator исключение → failed без частичных KPI.
Summary и runs имеют source=mock_environment. Fixtures не используются runtime.

Один worker-поток ограничивает вычисления, event loop доступен для запросов.
UUID/store принадлежат процессу. CORS читает BACKEND_CORS_ORIGINS из process
environment, только local origins, без credentials. `.env` не читается.

## Проверки

Из корня через `.venv/Scripts/python.exe`, Windows / Python 3.14.7.
Для CLI: PYTHONUTF8=1. Стандартный python alias здесь не работает.

| Команда | Статус | Фактический результат |
|---|---|---|
| python scripts/verify_core.py до/после | FAIL | Organizer file changed: agent_template.py; причина ниже |
| python local_eval.py | PASS | 3 пилота, 1 финал, 1285 контактов, cost=0, net=4042.1274 |
| python local_eval.py --runs 10 | PASS | 6/10 прибыльны, min≈−41150, max≈6960, без падений |
| python make_submission.py | PASS | 1 финал, содержательных изменений CSV нет |
| scripts.verify_core.verify_submission() | PASS | Два экспорта побайтно совпали; SHA256 d66c27b06351cd839ae3944d019ed2fd8bcdbaef1f6367ed5be81362cbf5a77e |
| python -m pytest -q | PASS | 82 passed, 28.12s: 44 core + 38 backend |
| test_uvicorn_real_http | PASS | Отдельный сервер, health/summary/POST/poll/404/422 |
| python -m pip check | PASS | No broken requirements found |
| git diff --check | PASS | Нет whitespace errors |
| Frontend build/tests, VITE_USE_MOCKS=false UI/E2E | NOT_RUN | Frontend отсутствует |

Один StarletteDeprecationWarning: httpx TestClient устаревает в пользу httpx2.
Первые промежуточные ошибки: тест ошибочно ожидал отрицательный net seed 0,
исправлен на seed 1; CLI --runs 10 падал при печати ⚠ в CP1251, повтор с
PYTHONUTF8=1 прошёл. Сетевая установка зависимостей потребовала разрешённого
запуска вне песочницы и успешно завершилась. Исходные 44 tests тоже PASS.

## Нереализованное и риски

Verifier не проходит из-за существующего состояния organizer-файлов:
14 текстовых файлов на диске CRLF, manifest и Git HEAD — LF. Все 15 HEAD blobs
совпадают с manifest; все 14 текстовых disk hashes совпадают после только
CRLF→LF, PDF совпадает сразу. `git ls-files --eol`: `i/lf w/crlf attr/-text`.
Содержательных изменений нет; organizer/manifest/.gitattributes не правились.
Нужно восстановить проверенные HEAD bytes человеком/отдельной интеграцией
и повторить gate. До этого общий verifier остаётся FAIL.

Frontend отсутствует, UI/API E2E не подтверждён. API запускать из корня,
одним Uvicorn-процессом. Перезапуск теряет run IDs. Нет TTL/отмены/жёсткого
runtime timeout, auth, БД и внешних отправок. Это локальное demo.
Baseline не оптимизирован, net неустойчив. Linux/macOS не проверены.

## Следующему агенту

Read-order: AGENTS → README → ARCHITECTURE → PROJECT_STATE → COLLABORATION →
OpenAPI + contracts/README → этот handoff → prompt своей роли → OWNERSHIP.

После человеческого review/commit/push реализовать frontend по
`.codex/prompts/02-frontend.md`, используя уже работающий API и fixtures.
Затем `.codex/prompts/04-integration.md`: UI с VITE_USE_MOCKS=false,
errors/polling/CORS, core/API/build tests, verifier после восстановления
organizer bytes. Не создавать backend повторно.

Запуск: `python -m uvicorn backend.app.main:app --reload`.
Smoke во втором терминале: `python -m backend.smoke`.
Точные PowerShell-команды — backend/README.md.
