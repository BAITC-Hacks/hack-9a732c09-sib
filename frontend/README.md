# Frontend — NOT_STARTED

Этап 2: React + Vite + TypeScript, интерфейс аналитика маркетинга.
Сейчас здесь только инструкции; `package.json`, UI, build и test ещё нет.
Начать с `.codex/prompts/02-frontend.md` после человеческого pull bootstrap.

Источник истины — `contracts/openapi.yaml` и `contracts/README.md`.
Mock source — `contracts/examples/*.json`; не копировать стратегию из Python.

Будущие переменные (пока не читаются приложением):

```dotenv
VITE_USE_MOCKS=true
VITE_API_BASE_URL=http://localhost:8000
```

Base URL — origin без `/api/v1`; пути клиента уже имеют этот prefix.
Сделать единый типизированный client interface и два транспорта: fixture и
HTTP. Mock-mode должен воспроизводить queued → running → completed и failed,
HTTP ошибки и timeout. Fixtures явно помечать в UI. Не выдавать их за runtime.

Пользовательский сценарий: обзор аудитории/лимитов/каналов → seed и запуск
mock-агента → состояние процесса → KPI, пилоты, финальный план, предупреждения
и ограничения. Показать source, свободный бюджет/охват после всего прогона,
нулевую стоимость и nullable ROI/risk. Поддержать пустые/loading/error состояния,
понятные подписи, доступность и адаптивную компоновку.

API n_campaigns означает финал; campaigns_detail включает пилоты. Не суммировать
gross строк, не трактовать negative net как failed. UNKNOWN в summary означает
отсутствующий сегмент данных и не является фильтром кампании.

Mock и HTTP обязаны использовать одинаковые типы и методы; переключение
`VITE_USE_MOCKS=false` не требует переписывания UI. Никаких Python imports,
API-ключей или дублирования расчёта score.

Добавить воспроизводимый lockfile, `npm run build`, осмысленные tests client/
состояний UI. Зафиксировать фактически проверенные Node/npm версии.
В конце повторить core verifier, обновить README/state/progress/notices,
создать новый `docs/handoffs/02-frontend-to-backend.md`; Git делает человек.
