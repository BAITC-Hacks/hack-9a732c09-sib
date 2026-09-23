# Текущее состояние

Обновлено: 2026-09-23. Активная роль: INTEGRATION (проверка требований агента).
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Наблюдаемый HEAD: 464b4c2, ветка main. До правок рабочее дерево чистое.
Codex не выполнял Git-операций записи. После человеческого объединения веток
активные README/state содержали старое описание baseline; синхронизированы
с фактическим runtime и завершёнными handoff без переписывания истории.

| Стадия | Статус | Состояние |
|---|---|---|
| Architecture / Core | IMPLEMENTED | Adaptive offline engine, judge boundary, контракты; 15 organizer hashes PASS |
| Optional OpenAI | IMPLEMENTED / LIVE CHECK PENDING | Явный opt-in; priorities-v2, typed fallback, тестовые ответы PASS; новый live-вызов NOT_RUN |
| Frontend | IMPLEMENTED / INTEGRATION PENDING | React/Vite, fixtures/HTTP client; 18 tests/build по историческому handoff 02 |
| Backend | IMPLEMENTED | FastAPI, runner, DTO, in-memory очередь; 39 backend tests и real HTTP smoke PASS |
| Final integration | IN_PROGRESS | Python/judge PASS; актуальные frontend build и UI E2E NOT_RUN |

## Работает

`agent.py:Agent.act(env) -> list[dict]` использует общий runtime factory.
Режим по умолчанию `off`: без сети/секретов, `.env` не читается. Core строит
гипотезы по публичным данным, проводит до 20 пилотов с подтверждениями,
возвращает 1–10 кампаний при доступных ресурсах или минимальный fallback.
Масштабирование требует трёх положительных наблюдений и положительной
осторожной оценки net; поправка на шум эвристическая, не гарантия прибыли.

`FP_LLM_PROVIDER=openai` включает советника вне core. Ключ читается из
окружения или локального `.env`; одного ключа без opt-in недостаточно.
Один запрос/run, только агрегаты гипотез. Модель возвращает приоритеты
фиксированных ID; код строит перестановку. Ошибка даёт observable fallback.
NVIDIA отменена. Старые live-замеры не проверяют новый `priorities-v2`.

Backend: четыре `/api/v1` endpoint, свежая official mock env на run,
один вызов core внутри evaluator, строгий JSON, nullable ROI, CORS,
in-memory история/очередь. Отрицательный net остаётся `completed`.
Frontend присутствует; default fixtures не запускают агента. Для реального
run нужен backend и `VITE_USE_MOCKS=false`. OpenAPI v1 не менялся.

## Последняя фактическая проверка

Windows, Python 3.14.7, локальная `.venv`, `PYTHONUTF8=1`.
Обычный `python` в PATH — неработающий WindowsApps alias; используется
`.venv/Scripts/python.exe`. Verifier принудительно отключает LLM и запускает
весь pytest с уникальным временным каталогом.

| Команда / сценарий | Статус | Результат |
|---|---|---|
| scripts/verify_core.py до правок | FAIL | 105 passed / 3 failed: тесты ещё ожидали старый order и общий ValueError |
| scripts/verify_core.py после правок | PASS | Все встроенные проверки завершены, exit 0 |
| Organizer SHA256 | PASS | Все 15 файлов совпадают с manifest; в этой итерации не изменялись |
| Полный pytest | PASS | 123 passed, 14.72s; один Starlette deprecation warning |
| Реальный Uvicorn / HTTP smoke | PASS | В составе pytest; health/summary/POST/poll/404/422 |
| local_eval.py | PASS технически / FAIL финансово | 19 пилотов, 1 финал, 3001 контакт, cost=0, net≈−11.63 |
| local_eval.py --runs 10 | PASS технически | Прибыльны 4/10; медиана≈−4624, min≈−13553, max≈78332 |
| make_submission.py дважды | PASS | Одинаковый CSV, исходный файл сохранён verifier |
| git diff --check | PASS | Нет whitespace errors |
| Live OpenAI priorities-v2 | NOT_RUN | Проверка выполнялась без платных API-вызовов |
| Frontend tests/build, UI E2E | NOT_RUN | Node/npm недоступны в PATH; исторический frontend handoff не заменяет текущий E2E |

SHA256 сгенерированного CSV:
`08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10`.
Тесты обновлены под действующий формат LLM и проверяют неполные/невалидные
ответы, дубликаты ключей, ties, refusal, HTTP ошибки и сетевые таймауты.
Production-код, стратегия и пороги в этой итерации не менялись.

## Следующие проверки и ограничения

- Выполнить один live OpenAI smoke; `external_advisor_used=true` подтверждает
  принятый ответ. Затем отдельная серия seed для текущего prompt.
- Проверить frontend test/build и UI с настоящим HTTP backend;
  `source=mock_environment`, POST 202 → GET completed, пилоты/финал/KPI.
- Standalone HTML и расширенный trace из ADR 0004 пока не реализованы.
- Mock net не прогнозирует hidden score. Offline режим неустойчив;
  прежние OpenAI результаты относятся к прежней версии советника.
- API запускать из корня одним процессом; перезапуск теряет историю,
  отсутствуют TTL/отмена run и жёсткий timeout вычисления. Linux/macOS NOT_RUN.
- Человек проверяет diff и делает commit/push. Ключи и `.env` не включать.

Запуск: [README](../README.md), [backend](../backend/README.md),
[frontend](../frontend/README.md). Последний завершённый handoff:
[07-requirements-check-to-integration.md](handoffs/07-requirements-check-to-integration.md).
`VERIFICATION_REPORT.md` и прежние handoff — исторические результаты.
