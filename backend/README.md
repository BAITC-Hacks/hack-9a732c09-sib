# Backend — NOT_STARTED

Этап 3: FastAPI, import target `backend.app.main:app`. Сейчас нет приложения,
routes, requirements или работающего API. Начать после Frontend handoff с
`.codex/prompts/03-backend.md` и фактического frontend API client.

Источник истины — `contracts/openapi.yaml` и `contracts/README.md`.
Отдельные `backend/requirements.txt`; FastAPI не добавлять в judge requirements.
Pydantic DTO адаптируют dataclass core, не становятся его зависимостью.

Структура: routes → StrategyRunner service → общее ядро и опубликованный
локальный evaluator. Конкретная схема wrapper описана в ARCHITECTURE.md:
один вызов Engine, сохранение trace, evaluator возвращает scored mock KPI.
Никаких моделей эффектов/internals в core, никаких стратегий в routes.
Demo использует только organizer mock environment и свежую env на каждый run.

In-memory storage достаточно, после перезапуска старый run_id → 404.
Каждый POST → 202 и metadata; GET раскрывает snapshot. Синхронное завершение
допускается. Для дорогого run не блокировать event loop; предусмотреть простое
ограничение параллельных запусков. База данных и auth не нужны.

Особенно проверить: n_campaigns без пилотов, lifecycle отдельно от score,
остатки после финала, ROI null вместо Infinity, строгий JSON, неполный trace,
единый ErrorResponse для 422/404/500. Не реконструировать score из наблюдений.

Будущий запуск из корня: `python -m uvicorn backend.app.main:app --reload`.
Это плановая команда, сейчас не работает. CORS только из конфигурации для
локальных dev origins (например localhost:5173), без wildcard с credentials.
Добавлять .env.example только с реально читаемыми переменными, без секретов.

Тесты: HTTP status/schema каждого endpoint, failed и unknown run, request
validation, изоляция seed/run, mock evaluator mapping, strict JSON, CORS.
Проверить реальный HTTP-клиент Frontend с `VITE_USE_MOCKS=false` и полный smoke.
Повторить core verifier; обновить state/progress/README/notices и новый
`docs/handoffs/03-backend-to-integration.md`. Git-операции делает человек.
