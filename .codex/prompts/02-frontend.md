# Этап 2 — FRONTEND, команда False Positive

Ты новая независимая Codex-сессия. Прошлый чат недоступен, состояние берётся
только из репозитория. Начать после человеческого review/commit/push ARCHITECT
и `git pull --ff-only` участником Frontend. Сам не выполняй pull/commit/push,
checkout/merge/rebase/reset/clean. Не создавай параллельную ветку.

Сначала прочитай по порядку: AGENTS.md → README.md → docs/ARCHITECTURE.md →
docs/PROJECT_STATE.md → docs/COLLABORATION.md → contracts/openapi.yaml и
contracts/README.md → последний завершённый handoff (ожидается
docs/handoffs/01-architecture-to-frontend.md) → этот role prompt →
docs/OWNERSHIP.md → frontend/README.md → contracts/examples/*.json.

Проверь `git status --short`, ветку и последние 10 commits. Если дерево грязное,
разбери и сохрани чужие изменения. До редактирования запусти
`python scripts/verify_core.py`, запиши исходные ошибки. Не считай будущую
функцию реализованной только потому, что она упоминается в документации.

Реализуй React + Vite + TypeScript приложение аналитика в frontend/.
Backend на этом этапе может отсутствовать: начинать в mock-mode по fixtures.
Переменные `VITE_USE_MOCKS=true` и `VITE_API_BASE_URL=http://localhost:8000`
(origin, без /api/v1). Один типизированный API client, взаимозаменяемые mock
и HTTP transports, статусы queued/running/completed/failed и HTTP ошибки.
POST всегда 202, затем GET, включая мгновенно завершённый запуск.

Сценарий: обзор синтетической аудитории, лимитов, тарифов и каналов; seed и
запуск; progress; KPI, пилоты, финальные кампании, предупреждения. Обозначь
mock_fixture, nullable ROI/risk, отрицательный результат и UNKNOWN сегменты.
Поддержи loading/empty/error, адаптивность, клавиатуру и понятные подписи.
Не суммируй detail gross как общий lift; не путай пилоты с финальными кампаниями.

Не импортируй Python, не копируй стратегию или scoring в браузер, не меняй
agent.py/false_positive/organizer файлы. Не ломай OpenAPI. Если изменение
неизбежно — ADR и атомарный протокол OWNERSHIP с fixtures/types/tests/docs.

Добавь frontend package.json, lockfile, фактические setup/env инструкции.
Запусти build и тесты состояния/client, затем core verifier и git diff --check.
Запиши проверенные Node/npm версии без предположений. Обнови README,
PROJECT_STATE, допиши PROGRESS и THIRD_PARTY_NOTICES, создай новый
docs/handoffs/02-frontend-to-backend.md по template, перечислив client paths,
ожидания к API, проверки и ограничения. Старый handoff не переписывай.

Критерий завершения: UI работает без backend по согласованным fixtures,
реальный транспорт готов к подключению, build/tests пройдены, judge сохранён,
контекст передан Backend. Финал — изменения, реальные PASS/FAIL/NOT_RUN,
риски и рекомендация commit, без выполнения commit/push.
