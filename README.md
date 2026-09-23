# False Positive

Решение кейса Beeline Tariff Marketing Campaigns: детерминированный offline
агент для judge и отдельный демонстрационный интерфейс аналитика. Эти контуры
разделены намеренно: React-приложение не входит в судейский dependency graph и
не переносит стратегию или scoring в браузер.

## Текущий статус

- Architecture / Core: готов — `Agent.act(env)`, baseline с пилотами и fallback,
  44 Python-теста, воспроизводимый `submission.csv`.
- Frontend: готов к review — React 19 + Vite + TypeScript, mock-first dashboard,
  типизированные fixture/HTTP transports, 18 Vitest/RTL-тестов.
- Backend: ещё не реализован; HTTP-клиент ожидает контракт `/api/v1`.
- Сквозной E2E с реальным API: ещё не выполнялся.

Фактическая готовность, результаты проверок и известные проблемы находятся в
[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md). Архитектурные границы — в
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), API — в
[`contracts/openapi.yaml`](contracts/openapi.yaml) и
[`contracts/README.md`](contracts/README.md).

## Frontend без backend

Проверенное окружение: Node.js `22.14.0`, npm `10.9.2`.

```sh
cd frontend
npm ci
npm run dev
```

Приложение по умолчанию запускается с `VITE_USE_MOCKS=true` и импортирует
зафиксированные примеры из `contracts/examples/*.json`. В интерфейсе доступны
сценарии completed, мгновенного результата, нулевой стоимости/`ROI=null`,
отрицательного net, execution failure, HTTP error и timeout. Fixture всегда
помечен как демонстрационный и не выдаётся за фактический score стратегии.

Для будущего backend скопируйте `frontend/.env.example` в
`frontend/.env.local` и установите:

```dotenv
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000
```

Base URL — только origin, без `/api/v1`: пути добавляет клиент.

```sh
cd frontend
npm test
npm run build
```

Подробности setup, UI-семантики и структуры клиента — в
[`frontend/README.md`](frontend/README.md).

## Judge / Core

Python-зависимости разделены на минимальные runtime и dev-наборы:

```sh
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements-dev.lock
# POSIX:   .venv/bin/python -m pip install -r requirements-dev.lock
python scripts/verify_core.py
```

Обязательные отдельные команды:

```sh
python local_eval.py
python local_eval.py --runs 10
python make_submission.py
python -m pytest
```

На Windows-консоли с legacy code page для строки с символом предупреждения
может понадобиться `PYTHONUTF8=1`. Organizer-owned файлы из
`docs/organizer-manifest.json` и `data/**` нельзя редактировать.

## Карта репозитория

```text
agent.py, false_positive/   judge adapter и offline core
frontend/                   React/Vite интерфейс аналитика
backend/                    инструкции для следующего этапа (API ещё нет)
contracts/                  замороженный OpenAPI v1 и JSON fixtures
docs/                       архитектура, состояние, решения и handoff
tests/                      Python contract/core/judge tests
```

Работа этапов последовательная; правила review и передачи контекста описаны в
[`AGENTS.md`](AGENTS.md) и [`docs/COLLABORATION.md`](docs/COLLABORATION.md).
