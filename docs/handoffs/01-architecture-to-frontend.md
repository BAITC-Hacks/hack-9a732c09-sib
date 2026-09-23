# Handoff 01 — ARCHITECT / CORE → FRONTEND

Статус: DONE (архитектурный scope, передача после человеческого review/push).
Дата/время: 2026-09-23T14:56:53+05:00.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Ожидаемый commit message:
`chore(architecture): bootstrap sequential multi-agent project`

## Выполненная цель

Создан рабочий судейский контур, минимальная стратегия с пилотами и fallback,
стабильный API v1 и достаточно контекста для независимой Frontend-сессии.
44 tests проходят, submission воспроизводится. Frontend/Backend ещё нет.

## Изменения и созданные файлы

- Judge: `agent.py`, `submission.csv`, `requirements.txt`.
- Core: `false_positive/agent.py`, `__init__.py`,
  `domain/{models,protocols,constraints}.py`, `strategy/{engine,baseline,fallback}.py`,
  `advisors/base.py`, `observability/trace.py` и package init-файлы.
- Контракт: `contracts/openapi.yaml`, `campaign.schema.json`, `README.md`,
  examples/{case-summary,run-accepted,run-running,run-completed,run-failed,error,health}.json.
- Проверки: `tests/{support,test_agent_contract,test_core_models,test_contract_fixtures,test_verification}.py`,
  `tests/__init__.py`, `scripts/{verify_core,build_contract_examples}.py`,
  `requirements-dev.txt`, `requirements-dev.lock`.
- Память: AGENTS.md, docs/{ARCHITECTURE,COLLABORATION,OWNERSHIP,PROJECT_STATE,PROGRESS,
  VERIFICATION_REPORT}.md, decisions/0001-sequential-modular-monorepo.md,
  organizer-manifest.json, handoffs/README.md, этот handoff и два будущих template.
- Подготовка: frontend/README.md, backend/README.md,
  `.codex/prompts/{02-frontend,03-backend,04-integration}.md`.
- Документация/настройки: README.md, THIRD_PARTY_NOTICES.md, .env.example,
  .gitignore, .gitattributes.
- Организатор: импортировано 15 исходных файлов, весь data/** и CSV сохранены
  побайтно; точный список — organizer-manifest.json.
- Исходный мастер-промпт сохранён без редактирования.

## Решения и неизменяемые границы

Два runtime-контура, общее offline core, dataclass/Protocol без Pydantic,
contract-first, строго последовательная передача через repository-as-memory.
Не менять `Agent.act(env) -> list[dict]`, `StrategyEngine.run(...)->StrategyRun`
и API v1 без протокола OWNERSHIP. Judge не зависит от UI/API/интернета.

В API n_campaigns — только финал, details — финал и пилоты, status — lifecycle.
Остатки API относятся к полному прогону, ROI при нулевой стоимости — null.
Полная семантика обязательна к чтению в contracts/README.md.

## Реальные проверки

| Команда | Статус | Результат |
|---|---|---|
| python local_eval.py | PASS | 3 пилота + 1 финальная кампания, 1285 контактов, cost=0, net≈4042 |
| python local_eval.py --runs 10 | PASS | Все технически валидны; 6 прибыльных, 4 отрицательных |
| python make_submission.py ×2 | PASS | 1 кампания, побайтовое совпадение |
| python scripts/verify_core.py | PASS | 44 tests и 15 organizer SHA256, official commands |
| python -m pytest | PASS | 44 passed |
| python -m pip check | PASS | Зависимости согласованы |
| git diff --check | PASS | Нет whitespace errors |
| Frontend / Backend / E2E | NOT_RUN | Это будущие этапы |

Первая версия summary fixture не учитывала пустой CSV-сегмент; исправлено на
UNKNOWN и проверено повторно. Python 3.13.15, Windows; другие ОС не проверены.
SHA256 submission:
`d66c27b06351cd839ae3944d019ed2fd8bcdbaef1f6367ed5be81362cbf5a77e`.

## Намеренно не реализовано и риски

Нет продвинутой стратегии, UI, API, runtime LLM и E2E. Baseline меняет знак
score между seed. Fixtures — иллюстрации, не результат запуска Agent.
UNKNOWN — только агрегатная метка, не campaign filter. Fallback требует
непустую доступную ячейку; подробности и обработка malformed pilot response
в ARCHITECTURE. Основное положение отдельно не предоставлено.

В середине сессии внешний автор сделал commit/merge до завершения всех файлов.
Наблюдаемый HEAD `cf8970d` не является финальным commit этой передачи.
Не начинать следующий этап по нему без завершённого человеческого review/push.

## Точный read-order следующей сессии

1. AGENTS.md.
2. README.md.
3. docs/ARCHITECTURE.md.
4. docs/PROJECT_STATE.md.
5. docs/COLLABORATION.md.
6. contracts/openapi.yaml и contracts/README.md.
7. Этот завершённый handoff.
8. `.codex/prompts/02-frontend.md`.
9. docs/OWNERSHIP.md, frontend/README.md, contracts/examples/*.json.

## Точная задача Frontend

После человеческого pull и pre-flight verifier создать React/Vite/TypeScript
интерфейс аналитика в frontend/: обзор кейса, seed/запуск, состояния процесса,
KPI, пилоты, финальный план и предупреждения. Сначала mock-mode по fixtures,
один типизированный API client с mock и HTTP transports. Конфигурация:
VITE_USE_MOCKS и VITE_API_BASE_URL (origin без /api/v1). Не дублировать Python
логику, не менять judge/organizer, не ломать контракт. Проверить build/tests,
обновить README/state/progress/notices, создать новый 02-frontend-to-backend.md
по template. Не переписывать этот handoff и не выполнять commit/push из Codex.
