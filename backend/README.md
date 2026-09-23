# Backend — рабочий API v1

FastAPI `backend.app.main:app` запускает существующий core ровно один раз
на run через wrapper для `local_eval.evaluate_agent`. Evaluator создаёт
свежую официальную mock-среду и считает KPI с точными пилотными ID.
Backend реализован по прямому запросу пользователя до frontend; контракт
`contracts/openapi.yaml` сохранён. Фактического frontend client пока нет.

## Запуск

Команды из корня репозитория: evaluator читает относительные CSV-пути.
Приложение не меняет cwd. Если окружения нет: `py -3 -m venv .venv`.
Проверено на Windows / Python 3.14.7.

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Для запуска без тестов достаточно `backend/requirements.txt`.
Freeze dev-окружения: `backend/requirements-dev.lock`.
На Linux/macOS используйте `.venv/bin/python`; эти ОС пока не проверены.
API: `http://127.0.0.1:8000`, Swagger UI: `http://127.0.0.1:8000/docs`.
В Swagger выполните POST, скопируйте run_id и вызовите GET.

## Endpoints и ручной тест

| Метод и путь | Результат |
|---|---|
| GET `/api/v1/health` | Доступность процесса |
| GET `/api/v1/case/summary` | Агрегаты публичных CSV, ограничения, каналы, тарифы |
| POST `/api/v1/runs` | `{ "seed": 42, "mode": "mock" }` → 202 и метаданные |
| GET `/api/v1/runs/{run_id}` | queued / running / completed / failed |

В другом PowerShell-терминале:

```powershell
$apiBase = 'http://127.0.0.1:8000'
Invoke-RestMethod "$apiBase/api/v1/health"
Invoke-RestMethod "$apiBase/api/v1/case/summary"
$acceptedRun = Invoke-RestMethod "$apiBase/api/v1/runs" -Method Post -ContentType 'application/json' -Body '{"seed":42,"mode":"mock"}'
do {
    Start-Sleep -Seconds 1
    $snapshot = Invoke-RestMethod "$apiBase/api/v1/runs/$($acceptedRun.run_id)"
} while ($snapshot.status -in @('queued', 'running'))
$snapshot | ConvertTo-Json -Depth 10
```

Один worker-поток исполняет вычисления; POST быстро возвращает queued,
следующие задания ждут, health/GET остаются доступны. Для UI polling:
интервал 1 секунда и timeout 5 минут.

## Семантика

- `source=mock_environment`; fixtures не используются runtime API.
- `n_campaigns` — только финал; details — пилоты, затем финал с kind/index.
  Общий gross берётся из evaluator после дедупликации, не из суммы строк
  или noisy pilot observations.
- Остатки учитывают пилоты и финал. При бесплатном push `roi=null` и warning.
  NaN/Infinity не публикуются. Отрицательный net сохраняет status completed.
- Исключения и неполный trace дают сохранённый failed, GET отвечает HTTP 200.
  Неизвестный UUID → 404, неверный UUID/body → 422, техническая ошибка → 500.
  Ошибки имеют ErrorResponse, без stack trace и входных секретных значений.
- Все 23 441 абонент учитываются в summary; пропуски → UNKNOWN.
  Индивидуальные записи абонентов API не возвращает.
- Storage — память одного процесса. Перезапуск/--reload теряет run IDs.
  Не запускайте несколько Uvicorn workers: память между ними не общая.
- Нет БД/auth или внешних маркетинговых отправок. Это локальное demo.
  LLM-советник опционален через общий runtime, по умолчанию выключен.
  Очередь и история в памяти до перезапуска; TTL, отмена и жёсткий timeout
  вычисления не реализованы.

## CORS и frontend

По умолчанию разрешены `http://localhost:5173` и `http://127.0.0.1:5173`.
Другой локальный порт задаётся в окружении процесса перед стартом:

```powershell
$env:BACKEND_CORS_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
```

Пустая строка отключает разрешённые origins. Wildcard и внешние hosts
запрещены; credentials отключены. CORS читается из окружения процесса.
Для LLM перед запуском Uvicorn задайте `$env:FP_LLM_PROVIDER='openai'`:
тогда ключ/модель читаются из корневого `.env`. Режим `'off'`
не читает файл и не требует ключей. Подробности — [корневой README](../README.md#llm-советник).
Будущий frontend: `VITE_USE_MOCKS=false`,
`VITE_API_BASE_URL=http://localhost:8000` (origin без `/api/v1`).
UI build и UI/E2E пока NOT_RUN: frontend отсутствует.

## Проверки

```powershell
$env:PYTHONUTF8 = '1'
$env:FP_LLM_PROVIDER = 'off'
.\.venv\Scripts\python.exe -m pytest tests/backend -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m backend.smoke
```

Последняя команда требует запущенный сервер. `test_live_http.py` сам
поднимает Uvicorn на свободном localhost-порту и завершает после smoke.
Проверены mock KPI, один вызов core, strict JSON, seed isolation, lifecycle,
неполный trace, failed/404/422/500, CORS и paid/zero-cost ROI.
Последний pytest: 108 passed (69 core/runtime + 39 backend); один warning Starlette
о будущем переходе TestClient с httpx на httpx2. Полный verifier PASS после
восстановления исходных LF и проверки 15 SHA256. Judge-команды завершаются;
отрицательный финансовый результат в local_eval помечается scorer как FAIL.
Verifier теперь запускает весь pytest с уникальным временным каталогом и
принудительным provider off; нужны backend/requirements-dev.txt.
Детали — [handoff](../docs/handoffs/06-verification-to-frontend.md).

Справочники реализации: [FastAPI concurrency](https://fastapi.tiangolo.com/async/),
[Pydantic configuration](https://docs.pydantic.dev/latest/api/config/).
