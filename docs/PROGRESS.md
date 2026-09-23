# Журнал подтверждённых результатов

Не заполнять будущие часы заранее. Каждая следующая сессия дописывает строку
с реальной проверкой и своим участником/ролью, не переписывая прошлые записи.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T14:56:53+05:00 | Участник 1 + Codex | ARCHITECT / CORE | TO_BE_FILLED_AFTER_HUMAN_COMMIT | Agent/core, API v1, 7 fixtures, 3 role prompts, handoff | python scripts/verify_core.py; python -m pytest; git diff --check | PASS: 44 tests, 15 organizer hashes, 3 пилота, 10 seed без падений, CSV повторяем; 6/10 seed прибыльны |

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
| 2026-09-23T16:26:15+05:00 | Участник + Codex | CORE / INTEGRATION | TO_BE_FILLED_AFTER_HUMAN_COMMIT | Adaptive pilots/gate/fallback, legacy benchmark, NVIDIA/OpenAI adapters, обновлённые backend проверки, ADR 0002, handoff 04 | pytest; local_eval.py; --runs 10; evaluate_strategy.py; make_submission.py; verify_submission(); verify_core.py; git diff --check | 108 tests PASS и HTTP smoke; CSV повторяем в off; verifier FAIL CRLF. Offline holdout mean +7248, 23/40 прибыльны. OpenAI 10/10 live ответов, 8/10 прибыльны. NVIDIA 401; UI/E2E NOT_RUN |

Исходный HEAD cb803de/main, рабочее дерево чистое. Пользователь разрешил
улучшение устойчивости и использование ключей; выбрал NVIDIA основной,
OpenAI переключаемой альтернативой. Organizer-файлы/data/OpenAPI не менялись.
Ключи не выводились и не правились; пользователь сам обновил OpenAI-ключ.
Default остаётся offline, сеть только по opt-in, максимум один запрос/run.

Первая policy с двумя подтверждениями ухудшила нижний хвост (−90616) и была
отклонена; отчёт сохранён. Финальная policy с тремя положительными пилотами
и penalty 2 заморожена до holdout 100–139. На этих seed средний net вырос
с −15132 до +7248, худший с −41114 до −17109. На 0–9 доля прибыльных
снизилась с 6/10 до 4/10, медиана отрицательная; улучшение не безусловное.
Seed42 offline: net −11.63, scorer FAIL при корректно завершённом запуске.

NVIDIA inference 401 даже с моделью из каталога. Обновлённый OpenAI дал
HTTP 200 и реальные structured responses: smoke42 и 10 диагностических
прогонов. Все 11 ответов приняты; серия 0–9 mean≈359451, min≈−4388, 8/10
положительных. Это не гарантия hidden score или воспроизводимости LLM.
Меню пользователя Compute/Agents/Launchables похоже на Brev; объяснены
различия compute-кредитов, Brev API keys и hosted NIM API по официальным docs.

Первый full pytest: 78 PASS/5 ERROR из-за PermissionError системного temp;
повтор в уникальной .venv/pytest-adaptive-* с отключённым cache — PASS.
Read-only review выявил незащищённое чтение .env: исправлено и проверено
двумя тестами; LLM-недетерминизм экспорта документирован. Финальный pytest
108 PASS, 14.75s, один Starlette warning. CSV сознательно регенерирован
в off; verify_submission дважды подтвердил одинаковые байты. Pre/post
verifier по-прежнему останавливается на существующем CRLF agent_template.py.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T16:35:56+05:00 | Участник + Codex | INTEGRATION | TO_BE_FILLED_AFTER_HUMAN_COMMIT | Удаление NVIDIA по запросу, OpenAI/off, ADR 0003, handoff 05 | pytest; local_eval.py; --runs 10; verify_submission(); verify_core.py; git diff --check | 107 tests PASS, real HTTP smoke; CSV повторяем, offline 4/10 прибыльны; verifier FAIL прежний CRLF |

Удалены NVIDIA endpoint, model/env whitelist/example и CLI choice. OpenAI
payload/model и политика core не менялись, default off сохранён. Тесты
невалидных ответов используют Responses envelope, missing-key/fallback
проверяются через OpenAI; старое имя провайдера отклоняется до чтения `.env`.
Существующие незакоммиченные изменения, локальные секреты, исторические
handoff и benchmarks сохранены. Новых платных запросов не выполнялось.
Проверено 107 tests/15.18s, один Starlette warning. Judge seed42 net≈−11.63,
на 0–9 4/10 прибыльны — неизменённый offline результат. Два экспорта CSV
совпали; pre/post verifier FAIL agent_template.py из-за прежнего CRLF.

Пользователь дополнительно спросил про использование $50 без API-ключа.
Разъяснено условно: если кредит в Brev, вычисления доступны через консоль
отдельно от API Catalog; точный сервис начисления без URL не подтверждён.
Никаких серверов не создавалось, кредиты не тратились.

| Время | Участник | Роль | Commit/placeholder | Промежуточный артефакт | Команда проверки | Результат |
|---|---|---|---|---|---|---|
| 2026-09-23T16:42:05+05:00 | Участник + Codex | INTEGRATION | TO_BE_FILLED_AFTER_HUMAN_COMMIT | Восстановление исходных LF, полный offline verifier, frontend onboarding, handoff 06 | python scripts/verify_core.py; git diff --check | PASS: 15 organizer SHA256, 108 tests, real HTTP smoke, оба CLI-прогона, два одинаковых CSV; net по-прежнему неустойчив |

По запросу быстро завершить оставшиеся нюансы устранён наследованный блокер:
14 дисковых файлов имели только CRLF вместо LF. До записи каждый результат
преобразования проверен по исходному manifest, затем все 15 SHA256 совпали.
Manifest, .gitattributes и содержимое organizer/data не модифицировались;
восстановлены исходные байты. Preflight verifier FAIL, финальный PASS.

Verifier теперь запускает весь pytest (runtime/backend включены), использует
свежий временный каталог и отключает cache, а в subprocess принудительно
выставляет FP_LLM_PROVIDER=off. Regression проверяет, что родительский openai
не меняется. Фактический полный запуск из окружения openai: 108 passed,
15.94s; новых внешних API-запросов нет. local_eval seed42 net≈−11.63, 0–9:
4/10 прибыльны; финансовый FAIL не скрывается техническим PASS.

Read-only review нашёл устаревший frontend prompt: актуализирован для уже
работающего backend и передачи в Integration. README явно требует
backend/requirements-dev.txt для полного verifier. Существующие изменения,
секреты и исторические handoff сохранены, commit/push не выполнялись.
