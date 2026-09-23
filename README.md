# False Positive — Beeline Tariff Marketing Campaigns

Агент решает, каким абонентам предложить смену тарифа, какой тариф и канал
выбрать. В кейсе 23 441 абонент, бюджет 100 000 у.е., максимум 15 000 контактов
и 20 пилотов. Пилоты и финальные кампании расходуют общие ресурсы. Итог —
1–10 кампаний; критерий — прирост ARPU за вычетом затрат на коммуникации.

Агент строит гипотезы по публичным сегментам и тарифам, проверяет их пилотами
и допускает масштабирование после трёх положительных наблюдений с поправкой
на неопределённость. До 20 пилотов делят бюджет и контакты с финалом.
При отсутствии подтверждений выбирается небольшой допустимый fallback.
Это эвристическая защита от шумных пилотов, не гарантия прибыли.

По умолчанию агент работает без сети. Опциональный LLM-советник ранжирует
гипотезы через OpenAI. Модель не меняет лимиты и не отменяет проверку пилотами.

Работают два контура:

- Judge: `agent.py:Agent.act(env) -> list[dict]`, независимое ядро `false_positive/`.
- Demo: FastAPI `backend.app.main:app`, четыре endpoint `/api/v1`, отдельная
  mock-среда на запуск и официальный evaluator для KPI. Frontend ещё не создан.

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

Для полного verifier нужны `backend/requirements-dev.txt` (установка выше).
Одна команда выполняет весь pytest, проверку исходных SHA256, оба judge-прогона
и два экспорта CSV. Она принудительно отключает LLM в дочерних процессах:

```powershell
.\.venv\Scripts\python.exe scripts/verify_core.py
```

Отдельные команды для диагностики:

```powershell
$env:PYTHONUTF8 = '1'
$env:FP_LLM_PROVIDER = 'off'
.\.venv\Scripts\python.exe local_eval.py
.\.venv\Scripts\python.exe local_eval.py --runs 10
.\.venv\Scripts\python.exe make_submission.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/verify_core.py
git diff --check
```

Один прогон показывает пилоты, затраты и net; десять seed — устойчивость.
`make_submission.py` создаёт `submission.csv`. Для повторяемого экспорта
обязательно `FP_LLM_PROVIDER=off`: сетевые ответы не гарантируют одинаковый
план. Seed 42 без LLM: 19 пилотов, 1 финал, 3 001 контакт, net≈−12;
scorer пишет FAIL из-за финансового знака, агент не падает.

Сравнение с сохранённым старым baseline:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_strategy.py --baseline --runs 10
.\.venv\Scripts\python.exe scripts/evaluate_strategy.py --baseline --start-seed 100 --runs 40
```

На отложенных seed 100–139 средний net изменился с −15 132 до +7 248,
худший с −41 114 до −17 109; прибыльны 23/40 вместо 17/40. На диагностических
seed 0–9 прибыльны только 4/10 вместо 6/10, несмотря на улучшение среднего
и худшего результата. Устойчивость не решена полностью. Все отчёты и
ограничения — [benchmarks](docs/benchmarks/README.md). Mock воспроизводит
механику судейства, но не скрытые эффекты финала.

Последняя проверка: 108 tests PASS, включая реальный HTTP smoke; полный
verifier PASS. Восстановлены исходные LF в 14 organizer-файлах: все 15 SHA256
совпадают с manifest. Это технический PASS; прибыльность остаётся неустойчивой.
Подробности — [PROJECT_STATE](docs/PROJECT_STATE.md).

## LLM-советник

Ключи остаются в игнорируемом `.env`; имена настроек — в `.env.example`.
Поддерживаются `OPENAI_API_KEY` и прежнее имя `OPEN_AI_API_KEY`.
Файл читается только при включённом LLM-режиме; переменные процесса важнее.

```powershell
# Диагностика OpenAI: один запрос модели на прогон.
.\.venv\Scripts\python.exe scripts/evaluate_strategy.py --provider openai --runs 1

# Включение для официального CLI и backend, запущенных из этого терминала.
$env:FP_LLM_PROVIDER = 'openai'
.\.venv\Scripts\python.exe local_eval.py --runs 10
# Для backend затем запустите uvicorn командой выше.
```

OpenAI проверен реальными запросами: 10/10 ответов приняты, 8/10 mock-прогонов
прибыльны. Это диагностические mock-результаты, не прогноз hidden score.
Доступны режимы `openai` и `off`; настройки других провайдеров не используются.

`external_advisor_used=true` в отчёте сравнения означает принятый ответ модели.
При ошибке/таймауте/невалидном JSON используется детерминированный порядок,
а в warnings сохраняется `hypothesis_advisor_fallback:<тип ошибки>`.
В сеть уходят только агрегаты сегментов и публичные тарифы/каналы.
На run допускается один запрос, timeout 15 с; автоматических повторов нет.

## Документация и работа команды

[Архитектура](docs/ARCHITECTURE.md), [API v1](contracts/README.md),
[состояние](docs/PROJECT_STATE.md), [правила](AGENTS.md),
[актуальный handoff](docs/handoffs/06-verification-to-frontend.md).
Данные синтетические; источники — [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
Codex оставляет рабочее дерево для review; commit/push выполняет человек.
