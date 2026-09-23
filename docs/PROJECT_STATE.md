# Текущее состояние проекта

Дата интеграционной проверки: 2026-09-23. Базовый commit до этих локальных
правок: `464b4c2`; commit/push остаются за человеком.

## Слои

| Слой | Статус | Проверенный результат |
|---|---|---|
| Judge/core | READY | `agent.py` сохраняет сигнатуру, offline по умолчанию, submission повторяем |
| Optional LLM | READY, optional | Один OpenAI request/run, строгая схема priorities, безопасный fallback |
| Backend API | READY | FastAPI `/api/v1`, in-memory lifecycle, CORS и реальный HTTP smoke |
| Frontend | READY | React/Vite dashboard, mock/live transport, строгая config validation |
| UI/API integration | READY | Реальный client прошёл CORS, summary, POST 202 и `running → completed` |
| Organizer files | INTACT | 15 из 15 SHA256 совпадают с `docs/organizer-manifest.json` |

## Выполненные проверки

| Команда / сценарий | Статус | Фактический результат |
|---|---|---|
| `python -m pip check` | PASS | Broken requirements отсутствуют |
| `python -m pytest -p no:cacheprovider -q` | PASS | 108 passed, 1 Starlette deprecation warning |
| `python scripts/verify_core.py` | PASS | 15 hashes, pytest, два eval и два идентичных CSV exports |
| `python local_eval.py --runs 10` | PASS | Все запуски завершены без нарушения лимитов |
| `npm ci && npm test && npm run build` | PASS | 6 файлов, 28 тестов; TypeScript/Vite build проходит |
| `npm run smoke:live` с FastAPI | PASS | CORS, summary, настоящий `HttpTransport`, POST 202 и polling |
| Vite production preview на 5173 | PASS | App shell 200, backend CORS разрешает origin |
| `npm audit --omit=dev` | PASS | 0 production vulnerabilities |

## Ограничения и риски

- Финансовая устойчивость **не подтверждена**: seed 42 даёт около −12, из
  seed 0–9 прибыльны 4. Это следует показывать как риск стратегии, не как
  техническую ошибку API/UI.
- В `npm audit` остаются 2 moderate advisory только в dev-зависимости Vitest.
  Их исправление требует major upgrade Vitest 5; production audit чист.
- Visual browser automation не настроена. Повторяемый live smoke исполняет
  реальные frontend modules через Vite и отдельно проверяет CORS preflight.
- Optional OpenAI mode не проверялся реальным ключом в этой интеграционной
  сессии; default/offline путь полностью проверен.

## Инварианты

- Не менять organizer-owned файлы из manifest.
- `FP_LLM_PROVIDER=off` обязателен для verifier и submission.
- API prefix `/api/v1`, POST run → HTTP 202, frontend делает обязательный GET.
- `n_campaigns` содержит только финальные кампании; nullable ROI/risk
  остаются nullable во всех слоях.
- Dev и preview frontend используют 5173, разрешённый default backend CORS.

Следующие действия для человека: изучить
[handoff 07](handoffs/07-integration-to-submission.md), проверить `git diff`,
создать commit и при необходимости отдельно принять решение о major-upgrade
Vitest.
