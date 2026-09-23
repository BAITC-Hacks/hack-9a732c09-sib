# Этап 3 — BACKEND, команда False Positive

Ты новая независимая Codex-сессия. Работай только с актуальным репозиторием
после человеческого push Frontend и pull участником Backend. Git commit/push/
pull/checkout/merge/rebase и уничтожающие команды самостоятельно не выполняй.

Сначала прочитай: AGENTS.md → README.md → docs/ARCHITECTURE.md →
docs/PROJECT_STATE.md → docs/COLLABORATION.md → contracts/openapi.yaml и
contracts/README.md → последний завершённый handoff (ожидается
docs/handoffs/02-frontend-to-backend.md) → этот prompt → docs/OWNERSHIP.md → backend/README.md →
фактический frontend API client/types/mock transport и fixtures.
Не предполагай, что Frontend готов: проверь его handoff и файлы.

Pre-flight: git status --short, ветка, последние commits;
python scripts/verify_core.py и существующие frontend build/tests.
Сохрани чужие изменения и запиши исходные ошибки до правок.

Реализуй FastAPI backend с import `backend.app.main:app`, ровно по API v1,
который уже использует UI. Отдельные backend dependencies и Pydantic DTO.
Routes только HTTP; бизнес-логика в общем false_positive core. StrategyRunner
вызывает Engine один раз через wrapper, опубликованный local_eval evaluator
используется для настоящего mock score и точных pilot IDs. См. ARCHITECTURE.
Только официальный mock environment для demo, новая env на каждый запуск.
Никакого доступа core к internals/модели, никаких повторных прогонов ради KPI.

Реализуй четыре endpoints, in-memory run storage, полную lifecycle/error
схему; POST 202 даже при синхронном completed. Отрицательный net не failed.
Преобразуй n_campaigns, остатки, nullable ROI, strict JSON, campaign details
kind/index. При исключении Agent, которое evaluator перехватил, или неполном
trace не показывай completed с выдуманными KPI.

CORS только локальные dev origins из конфигурации, без БД/auth. Запуск из
корня; не менять process-wide cwd внутри запросов. Не блокировать event loop
долгим вычислением; обеспечить изоляцию запусков. Не менять frontend без
подтверждённой необходимости. Не менять OpenAPI несовместимо: ADR и полный
протокол обновления contracts/fixtures/client/DTO/tests/docs.

Запусти backend endpoint/contract tests, core verifier, frontend build/tests,
реальный end-to-end smoke с VITE_USE_MOCKS=false. Проверь 404/422/500, failed,
нулевую стоимость, CORS, одинаковый seed. Обнови README, PROJECT_STATE,
PROGRESS, THIRD_PARTY_NOTICES; создай 03-backend-to-integration.md по template,
не изменяя старые handoff. Укажи реальные команды, PASS/FAIL/NOT_RUN и риски.
Критерий завершения: API и UI совместимы, core независим, память актуальна.
Предложи commit message; commit/push выполняет человек.
