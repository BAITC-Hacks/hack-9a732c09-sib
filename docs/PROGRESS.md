# Журнал подтверждённых результатов

Не заполнять будущие часы заранее. Каждая следующая сессия дописывает строку
с реальной проверкой и своим участником/ролью, не переписывая прошлые записи.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T14:56:53+05:00 | Участник 1 + Codex | ARCHITECT / CORE | TO_BE_FILLED_AFTER_HUMAN_COMMIT | Agent/core, API v1, 7 fixtures, 3 role prompts, handoff | python scripts/verify_core.py; python -m pytest; git diff --check | PASS: 44 tests, 15 organizer hashes, 3 пилота, 10 seed без падений, CSV повторяем; 6/10 seed прибыльны |
| 2026-09-23T16:24:27+05:00 | Участник 2 + Codex | FRONTEND | TO_BE_FILLED_AFTER_HUMAN_COMMIT | React/Vite dashboard, typed API client, fixture/HTTP transports, 18 tests, handoff 02 | npm ci; npm test; npm run build; Python judge checks | PASS frontend: 18 tests/build/dev smoke; PASS pytest/eval/submission; working-copy verifier FAIL на pre-existing CRLF organizer-файла, clean HEAD archive verifier PASS |

Первичный pre-flight: в репозитории только README/config и неотслеживаемый
мастер-промпт; organizer-файлы позже предоставлены человеком и скопированы
без изменения байтов. Системный Python не был виден из песочницы; проверен
Python 3.13.15 и создан локальный venv. Первый contract test выявил отсутствующие
CSV-сегменты; исправлено на UNKNOWN, успешные проверки повторены.

Внешние человеческие commits появились в ходе этой же сессии: ff3b9a7,
cf8970d. Агент историю не создавал/не переписывал; новые финальные документы
остаются для последующего review и commit.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T15:20:01+05:00 | Участник + Codex | BACKEND | TO_BE_FILLED_AFTER_HUMAN_COMMIT | FastAPI v1, DTO, runner, память/очередь, CORS, smoke, 38 backend tests, документация | python -m pytest -q; local_eval.py; local_eval.py --runs 10; make_submission.py; pip check; git diff --check | PASS: 82 tests, real Uvicorn HTTP smoke, 6/10 seed прибыльны. Verifier FAIL: существующие CRLF в 14 organizer-файлах; UI/E2E NOT_RUN, frontend отсутствует |

Backend начат по прямому запросу пользователя до frontend; OpenAPI v1 и
core не изменены. Исходный HEAD d0c33eb/main, чужое изменение `.gitignore`
сохранено. Создана локальная `.venv` Python 3.14.7; backend зависимости
отделены от judge. Короткий python alias не работает, используется venv.
Установка зависимостей из песочницы была недоступна из-за сети; разрешённая
установка завершилась успешно.

До/после verifier останавливается на agent_template.py: все HEAD blobs
совпадают с manifest, 14 дисковых текстовых файлов отличаются только LF/CRLF.
Organizer-файлы не правились. Исходные 44 tests PASS. Первый backend test
неверно считал seed 0 убыточным; исправлен на seed 1. Первый CLI --runs 10
падал на печати ⚠ в CP1251; повтор с PYTHONUTF8=1 PASS. Последний общий
pytest: 82 passed, один warning Starlette про httpx TestClient.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T17:25:32+05:00 | Участник + Codex | INTEGRATION | TO_BE_FILLED_AFTER_HUMAN_COMMIT | LLM regression tests, актуальные инструкции/state, handoff 07 | scripts/verify_core.py (pytest/eval/10seed/CSV×2) | PASS: 123 tests, 15 hashes, real HTTP smoke, повторяемый CSV; offline прибыльны 4/10, seed42 net≈−11.63. Live API и UI E2E NOT_RUN |

Исходный HEAD 464b4c2/main, дерево чистое. Preflight: 3 failed/105 passed
из-за старых order/ValueError ожиданий при действующем priorities-v2.
Тесты согласованы с runtime; дополнительно проверены malformed/duplicate JSON,
ties, incomplete/refusal, HTTP ошибки и timeout без сети. Стратегия, production
код, organizer-файлы, контракт и `.env` не менялись. После merge активные
документы содержали старый baseline и отсутствие frontend; исправлено по
фактическим файлам. Существующие исторические записи/handoff сохранены.
Node/npm недоступны в PATH, frontend проверки не повторялись. Платные API
не вызывались; прежние OpenAI замеры не подтверждают новый prompt.
