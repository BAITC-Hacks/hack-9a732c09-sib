# Этап 2 — FRONTEND, команда False Positive

Ты новая независимая Codex-сессия. Прошлый чат недоступен, состояние берётся
только из репозитория. Начать после человеческого review/commit/push текущего этапа
и `git pull --ff-only` участником Frontend. Сам не выполняй pull/commit/push,
checkout/merge/rebase/reset/clean. Не создавай параллельную ветку.

Сначала прочитай по порядку: AGENTS.md → README.md → docs/ARCHITECTURE.md →
docs/PROJECT_STATE.md → docs/COLLABORATION.md → contracts/openapi.yaml и
contracts/README.md → последний завершённый handoff из PROJECT_STATE
(не исторический handoff 01 и не .template) → этот role prompt →
docs/OWNERSHIP.md → frontend/README.md → contracts/examples/*.json.

Проверь `git status --short`, ветку и последние 10 commits. Если дерево грязное,
разбери и сохрани чужие изменения. До редактирования запусти
`python scripts/verify_core.py`, запиши исходные ошибки. Не считай будущую
функцию реализованной только потому, что она упоминается в документации.

Реализуй React + Vite + TypeScript приложение аналитика в frontend/.
Backend уже реализован: сверить реальные ответы по backend/README.md.
Поддержать fixtures для автономной разработки, проверить HTTP-режим с сервером.
Переменные `VITE_USE_MOCKS=false` и `VITE_API_BASE_URL=http://localhost:8000`
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
Для полного verifier установить backend/requirements-dev.txt (включает root dev).
Запиши проверенные Node/npm версии без предположений. Обнови README,
PROJECT_STATE, допиши PROGRESS и THIRD_PARTY_NOTICES, создай новый
handoff с очередным свободным номером `<NN>-frontend-to-integration.md`, перечислив client paths,
ожидания к API, проверки и ограничения. Старый handoff не переписывай.

Критерий завершения: UI работает по fixtures и с существующим backend,
реальный транспорт проверен, build/tests пройдены, judge сохранён,
контекст передан Integration. Финал — изменения, реальные PASS/FAIL/NOT_RUN,
риски и рекомендация commit, без выполнения commit/push.
