# Текущее состояние

Обновлено: 2026-09-23T16:24:27+05:00.
Текущий этап: FRONTEND завершён, передача BACKEND.
Активная роль этой сессии: FRONTEND.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT

| Стадия | Статус | Состояние |
|---|---|---|
| Architecture / Core | DONE | Рабочий judge, baseline, OpenAPI v1, 44 Python tests |
| Frontend | DONE | React/Vite dashboard, fixture + HTTP transports, 18 tests, build |
| Backend | NOT_STARTED | Только README/role prompt и замороженный OpenAPI |
| Final integration | NOT_STARTED | Только role prompt; реального API E2E ещё нет |

## Работает

Корневой Agent по-прежнему делает до трёх пилотов через публичный env и
возвращает финальный план; `submission.csv` воспроизводится побайтно. Frontend
работает без backend на `contracts/examples/*.json`, показывает аудиторию,
лимиты, каналы, тарифы, запуск, lifecycle, KPI, пилоты, финальные кампании,
детализацию и warnings.

Единый `AnalystApiClient` использует взаимозаменяемые `MockTransport` и
`HttpTransport`. Реализованы обязательный GET после любого POST 202, немедленный
terminal snapshot, polling 1 секунда, deadline/abort, retry GET того же run,
структурированные HTTP errors и отдельный stored failed. Mock UI позволяет
проверить successful, instant, zero-cost/ROI null, negative completed, failed,
HTTP-error и timeout сценарии. OpenAPI/contract fixtures не менялись.

UI явно помечает `mock_fixture`, не суммирует detail gross, разделяет пилоты и
финальные кампании, показывает nullable ROI/risk и объясняет UNKNOWN. Есть
loading/empty/error состояния, keyboard focus, labels, live status, семантические
таблицы и адаптивная одно-/двухколоночная компоновка. Внешних UI-assets и
runtime-зависимостей от Python нет.

## Пока отсутствует

FastAPI backend, runtime `source=mock_environment`, интеграция с evaluator через
HTTP и сквозной browser/API E2E. HTTP transport проверен unit-тестами на
контрактных ответах, но не вызывал реальный сервер. Fixtures иллюстративны и не
являются запуском baseline.

## Последние реальные проверки

Проверенное окружение Frontend: Node.js 22.14.0, npm 10.9.2, Windows.
Python-проверки: Python 3.13.15 в локальной `.venv`; для Unicode-вывода Windows
использован `PYTHONUTF8=1`.

| Команда | Статус | Результат |
|---|---|---|
| npm ci | PASS | 184 packages установлены из lockfile |
| npm test | PASS | 5 files, 18 tests: client/HTTP/mock/states/UI |
| npm run build | PASS | TypeScript + Vite; 46 modules, JS 225.79 kB (gzip 70.82 kB) |
| Vite dev smoke | PASS | `/`, `src/main.tsx`, mock transport и внешний fixture import — HTTP 200 |
| python local_eval.py | PASS | 3 пилота, 1 финальная кампания, 1285 контактов, cost=0, net≈4042 |
| python local_eval.py --runs 10 | PASS | 10/10 технически валидны; 6 прибыльных, 4 отрицательных |
| python make_submission.py | PASS | SHA256 до/после совпал: `d66c27b…f5a77e` |
| python -m pytest | PASS | 44 passed in 5.56 s |
| python -m pip check | PASS | No broken requirements found |
| python scripts/verify_core.py (текущая working copy) | FAIL | verifier останавливается на `agent_template.py`; все 14 organizer text files имеют CRLF, PDF совпадает |
| python scripts/verify_core.py (чистый `git archive HEAD`) | PASS | 15 hashes, 44 tests, eval, 10 runs, submission ×2 |
| Backend API / browser E2E | NOT_RUN | Backend следующего этапа отсутствует |

Исходный pre-flight через короткий `python` не стартовал: в PATH был только
недоступный Windows Store alias, а переданная `.venv` отсутствовала. После
локального восстановления Python post-check выявил pre-existing CRLF во всех 14
текстовых organizer entries; PDF — единственный исходно совпадающий файл. Git
status до изменений был clean. LF-нормализация каждого из 14 файлов в памяти
даёт соответствующий manifest SHA256 (для первого `agent_template.py`:
`4eb369…b5eb10d`). Organizer-owned файлы не исправлялись и не входят в diff.
Чистый архив текущего HEAD проходит полный verifier, что подтверждает сохранность
закоммиченного judge; человеческий review должен восстановить рабочие байты из
проверенного HEAD/исходного пакета и повторить verifier до commit Frontend.

Первый `local_eval.py --runs 10` вычислил все seed, но завершился кодом 1 при
печати `⚠` через cp1251. Повтор с `PYTHONUTF8=1` — PASS; код не менялся.

## Известные ограничения и риски

- Реальный API может выявить CORS, timing или DTO-несовместимость; это проверит
  Backend/Integration, не Frontend fixtures.
- Mock timeout сокращён до 5 секунд только для демонстрации; обычный клиент и
  HTTP mode используют контрактные 5 минут.
- Baseline не оптимизирован: min net ≈−41150, max ≈6960; mock score не
  прогнозирует hidden score.
- UNKNOWN остаётся агрегатной меткой, не campaign filter. UI это показывает,
  но Backend также обязан сохранить всех абонентов в summary.
- Рабочая копия 14 organizer text files требует человеческого восстановления
  байтов; не включать их нормализацию в Frontend commit.

## Замороженные границы и следующий шаг

`agent.py:Agent.act(env) -> list[dict]`, `StrategyEngine.run`, Campaign schema и
OpenAPI v1 не менялись. Frontend contract boundary:
`frontend/src/api/{types,client,httpTransport,mockTransport}.ts`, конфигурация —
`frontend/src/config.ts`.

Следующий шаг: человек проверяет UI/diff, восстанавливает organizer working-copy
байты из доверенного источника, повторяет verifier + frontend tests/build,
делает commit/push. После pull участник Backend запускает
`.codex/prompts/03-backend.md` и реализует FastAPI по существующему клиенту.
Handoff: [02-frontend-to-backend.md](handoffs/02-frontend-to-backend.md).
