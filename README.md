# False Positive — Beeline Tariff Marketing Campaigns

Агент решает, каким абонентам предложить смену тарифа, какой тариф и канал
выбрать. В кейсе 23 441 абонент, бюджет 100 000 у.е., максимум 15 000 контактов
и 20 пилотов. Пилоты и финальные кампании расходуют общие ресурсы. Итог —
1–10 кампаний; критерий — прирост ARPU за вычетом затрат на коммуникации.

Текущий агент строит гипотезы по публичным сегментам и ценам, проводит до
20 пилотов с повторными подтверждениями и масштабирует подтверждённые
кампании. При отсутствии подтверждений выбирает минимальный доступный
fallback. По умолчанию работает без сети. Опциональный OpenAI-советник
меняет порядок гипотез; решения о запуске по-прежнему проверяются пилотами.

Работают два контура:

- Judge: `agent.py:Agent.act(env) -> list[dict]`, независимое ядро `false_positive/`.
- Demo: FastAPI `backend.app.main:app`, четыре endpoint `/api/v1`, отдельная
  mock-среда на запуск и официальный evaluator для KPI. React frontend
  реализован; сквозная проверка UI с текущим backend ещё не выполнена.

## Быстрый запуск backend

Команды из корня, PowerShell. В текущей рабочей копии `.venv` подготовлена.
В новом клоне сначала создайте её установленным Python: `py -3 -m venv .venv`
(или `python -m venv .venv`, если Python доступен в PATH).

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

API: `http://127.0.0.1:8000`, интерактивная документация: `/docs`.
Во втором терминале:

```powershell
.\.venv\Scripts\python.exe -m backend.smoke
```

Сценарий: POST `/api/v1/runs` с `{"seed":42,"mode":"mock"}` → 202 и `run_id`
→ GET `/api/v1/runs/{run_id}` до `completed` или `failed`.
Детали и PowerShell-пример: [backend/README.md](backend/README.md).

## Как тестировать агента

Из корня проекта в PowerShell. Команды организаторов:

```powershell
$env:PYTHONUTF8 = '1'
$env:FP_LLM_PROVIDER = 'off'
.\.venv\Scripts\python.exe local_eval.py
.\.venv\Scripts\python.exe local_eval.py --runs 10
.\.venv\Scripts\python.exe make_submission.py
```

Один прогон показывает пилоты, затраты и net; десять seed — устойчивость.
`make_submission.py` создаёт `submission.csv`. Mock использует судейский
скоринг, но эффекты искусственные: результат не прогнозирует балл финала.

Полная автоматическая проверка (нужны `backend/requirements-dev.txt`):

```powershell
.\.venv\Scripts\python.exe scripts/verify_core.py
git diff --check
```

Verifier сам отключает LLM, проверяет 15 organizer SHA256, весь pytest,
обе команды local_eval и два одинаковых экспорта CSV. Существующий CSV
сохраняется; несовпадение с новым результатом требует явной регенерации.
Успех: exit code 0 и строка
`PASS all core/runtime/backend/contract/judge checks (offline)`.

Проверено 2026-09-23: **123 tests PASS**, включая реальный HTTP smoke;
полный verifier PASS. Offline seed42: 19 пилотов, 1 финальная кампания,
3 001 контакт, net≈−11.63; seed0–9: прибыльны 4/10, медиана≈−4 624.
`Статус: FAIL` в local_eval обозначает неположительный net, а не обязательно
ошибку исполнения. Строка «Кампаний» включает пилоты; лимит 1–10 относится
к финальному плану. Остатки env внизу отчёта учитывают только пилоты;
итоговые расходы/контакты показаны в общем результате scorer.

## LLM-советник

В локальном `.env` задайте `OPENAI_API_KEY` и при необходимости
`OPENAI_MODEL` (по умолчанию `gpt-4.1-mini`). Поддерживается прежнее имя
ключа `OPEN_AI_API_KEY`. Файл с ключом не включать в submission/Git.
Одного ключа недостаточно: для штатных команд явно включите режим:

```powershell
$env:FP_LLM_PROVIDER = 'openai'
.\.venv\Scripts\python.exe local_eval.py
.\.venv\Scripts\python.exe local_eval.py --runs 10
```

Эти команды обращаются к платному API. Чтобы увидеть, был ли ответ модели
принят, используйте диагностический запуск (один API-запрос на run):

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_strategy.py --provider openai --runs 1
```

В `adaptive.rows` проверьте `external_advisor_used: true` и `warnings`.
При недоступном ключе/сети или неверном ответе агент продолжает работу через
deterministic fallback; финансовый PASS сам по себе не доказывает работу API.
Для повторяемого offline submission верните `$env:FP_LLM_PROVIDER='off'`
перед `make_submission.py`. LLM-режим не гарантирует одинаковый CSV по seed.
NVIDIA отключена. Новый формат `priorities-v2` проверен заглушками API;
live-вызов этого формата в текущей проверке NOT_RUN. Сохранённые OpenAI
замеры относятся к прежнему формату, см. [benchmarks](docs/benchmarks/README.md).

## Frontend

Инструкция и переключение fixtures/HTTP: [frontend/README.md](frontend/README.md).
Проверки отдельные: `npm --prefix frontend ci`, `npm --prefix frontend test`,
`npm --prefix frontend run build`; нужен Node `>=20.19 <23`.
Для работы настоящего агента выберите `VITE_USE_MOCKS=false` и запустите
backend. Режим fixtures показывает заранее подготовленные данные.
В текущей сессии frontend build/UI E2E NOT_RUN: Node/npm недоступны в PATH.

## Документация и работа команды

[Архитектура](docs/ARCHITECTURE.md), [API v1](contracts/README.md),
[состояние](docs/PROJECT_STATE.md), [правила](AGENTS.md),
[последний handoff](docs/handoffs/07-requirements-check-to-integration.md).
Данные синтетические; источники — [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
Codex оставляет рабочее дерево для review; commit/push выполняет человек.
