# Этап 4 — FINAL INTEGRATION, команда False Positive

Начинай после человеческого push Backend и pull последнего состояния.
Не используй прошлые чаты как источник истины. Не выполняй commit/push/pull,
checkout/merge/rebase/reset/clean и не уничтожай существующие изменения.

Read-order: AGENTS.md → README.md → docs/ARCHITECTURE.md → docs/PROJECT_STATE.md →
docs/COLLABORATION.md → contracts/openapi.yaml и contracts/README.md → последний
завершённый handoff (ожидается docs/handoffs/03-backend-to-integration.md) → этот prompt →
docs/OWNERSHIP.md → фактические frontend/backend README и конфигурация.

Сначала git status/branch/log и все имеющиеся проверки, до изменений:
python scripts/verify_core.py, python -m pytest, frontend build/tests,
backend tests и documented end-to-end smoke. Запиши исходные ошибки.
Не объявляй слой готовым по одному handoff, проверь работающий сценарий.

Исправляй реальные несовместимости с минимальным scope; сохраняй судейский
контракт. Judge проверь отдельно без API/UI/аккаунтов/сети: local_eval,
local_eval --runs 10, make_submission дважды с побайтовым сравнением,
лимиты, валидность кампаний и пилоты. Отрицательный mock score допустим для
bootstrap; не скрывай нестабильность и не подгоняй скрытую модель.

Demo проверь отдельно: summary → seed/POST → GET состояния → completed KPI,
кампании/пилоты → ошибки; реальный HTTP transport, CORS, nullable ROI/risk,
source и отсутствие расхождения контракта. При API изменении новый ADR и
одновременное обновление всех схем/fixtures/клиентов/tests/docs.

Актуализируй README с проверенными установкой и версиями, THIRD_PARTY_NOTICES,
submission.csv, PROJECT_STATE и PROGRESS. Проверь отсутствие секретов,
личных путей, ложных claims и изменение organizer manifest. Не переписывай
завершённые handoff; создай 04-integration-to-submission.md с фактическими
результатами. Финальный отчёт: реальные PASS/FAIL/NOT_RUN, незакрытые критерии,
Git status/diff check, инструкции эксперту и рекомендация commit. Commit и
push оставь человеку.
