# False Positive — Beeline Tariff Marketing Campaigns

Агент решает, каким абонентам предложить смену тарифа, какой тариф и канал
выбрать. В кейсе 23 441 абонент, бюджет 100 000 у.е., максимум 15 000 контактов
и 20 пилотов. Пилоты и финальные кампании расходуют общие ресурсы. Итог —
1–10 кампаний; критерий — прирост ARPU за вычетом затрат на коммуникации.

Агент строит гипотезы по публичным сегментам и тарифам, проверяет их пилотами
и масштабирует только после повторных положительных наблюдений. При отсутствии
подтверждений выбирается небольшой допустимый fallback. По умолчанию работа
полностью offline; optional OpenAI-советник может только переставить гипотезы
и при ошибке заменяется детерминированным порядком.

Работают два контура:

- Judge: `agent.py:Agent.act(env) -> list[dict]`, независимое ядро `false_positive/`.
- Demo: React/Vite dashboard → FastAPI `backend.app.main:app` (`/api/v1`) →
  отдельная mock-среда и официальный evaluator для KPI.

Последняя интеграционная проверка: 108 Python-тестов, 28 frontend-тестов и
production build проходят; `scripts/verify_core.py` подтверждает все 15
organizer SHA256 и два одинаковых экспорта `submission.csv`. Реальный
frontend client проверен против FastAPI с CORS и lifecycle `running → completed`.
На seed 42 финансовый результат около −12, а в 10 seed прибыльны 4: это
известная нестабильность стратегии, а не технический PASS по прибыли.

## Быстрый запуск demo

Команды из корня, PowerShell. В текущей рабочей копии `.venv` подготовлена.
В новом клоне сначала создайте её установленным Python: `py -3 -m venv .venv`
(или `python -m venv .venv`, если Python доступен в PATH).

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
$env:FP_LLM_PROVIDER = 'off'
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

API: `http://127.0.0.1:8000`, интерактивная документация: `/docs`.
Во втором терминале запустите dashboard с настоящим API:

```powershell
cd frontend
npm ci
$env:VITE_USE_MOCKS = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1
```

Откройте `http://127.0.0.1:5173`. Vite dev и preview фиксируют этот порт,
разрешённый backend CORS. Для повторяемого smoke при запущенном API:

```powershell
cd frontend
$env:API_BASE_URL = 'http://127.0.0.1:8000'
npm run smoke:live
```

## Как тестировать агента

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
`make_submission.py` создаёт `submission.csv`. Для воспроизводимого экспорта
обязательно оставляйте `FP_LLM_PROVIDER=off`: сетевые ответы модели могут
изменить порядок гипотез. Подробности — [PROJECT_STATE](docs/PROJECT_STATE.md).

## Документация и работа команды

[Архитектура](docs/ARCHITECTURE.md), [API v1](contracts/README.md),
[состояние](docs/PROJECT_STATE.md), [правила](AGENTS.md),
[интеграционный handoff](docs/handoffs/07-integration-to-submission.md).
Данные синтетические; источники — [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
Codex оставляет рабочее дерево для review; commit/push выполняет человек.
