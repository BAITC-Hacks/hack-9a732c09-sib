# Frontend — analyst dashboard

Статус: реализован в mock-first режиме и интегрирован с FastAPI по
замороженному OpenAPI v1. Fixtures остаются явным демонстрационным режимом;
`VITE_USE_MOCKS=false` включает настоящий HTTP transport.

## Проверенное окружение и запуск

- Node.js `22.14.0`.
- npm `10.9.2`.
- Windows; lockfile создан npm lockfile v3.

```sh
cd frontend
npm ci
npm run dev
```

Откройте `http://localhost:5173`. Dev и preview фиксируют порт 5173, чтобы
не расходиться с backend CORS. Production-проверка:

```sh
npm test
npm run build
npm run preview
```

Интеграционная проверка: 6 test files / 28 tests PASS, TypeScript + Vite build
PASS и реальный POST → GET smoke против FastAPI. `dist/` и `node_modules/` не
входят в Git.

## Конфигурация

Скопируйте `.env.example` в `.env.local` при необходимости:

```dotenv
VITE_USE_MOCKS=true
VITE_API_BASE_URL=http://localhost:8000
```

- `VITE_USE_MOCKS=true` выбирает `MockTransport` и JSON из
  `../contracts/examples/`. Это значение используется и по умолчанию, если
  переменная не задана.
- `VITE_USE_MOCKS=false` выбирает `HttpTransport` без изменений компонентов.
- Любое другое значение `VITE_USE_MOCKS` отклоняется, чтобы live-demo не
  переключился молча на fixtures.
- `VITE_API_BASE_URL` — HTTP(S) origin без path, query, fragment или
  credentials; клиент сам добавляет `/api/v1`.

Mock selector покрывает обычный и мгновенный completed, zero-cost/nullable ROI,
negative completed, stored failed, HTTP error и timeout. Для наглядности timeout
fixture сокращён до 5 секунд; обычный client и HTTP mode используют 5 минут.

## Структура

```text
src/api/types.ts             DTO, соответствующие OpenAPI v1
src/api/client.ts            POST → обязательный GET и polling
src/api/errors.ts            структурированные HTTP/timeout ошибки
src/api/httpTransport.ts     fetch transport для /api/v1
src/api/mockTransport.ts     клонированные contract fixtures и demo-сценарии
src/config.ts                единственная точка выбора транспорта/env
src/components/              обзор кейса, запуск, status и результаты
src/App.tsx                  orchestration, AbortController и UI state
src/**/*.test.ts(x)          client, transport, state и component tests
```

`AnalystApiClient` — единственная граница UI с данными. После любого POST 202
он делает GET, даже если metadata уже сообщает `completed`/`failed`. Первый GET
выполняется сразу; затем polling раз в секунду, общий deadline 5 минут. Pending
fetch и delay отменяются при новом запуске/размонтировании. После timeout или
HTTP error UI повторяет GET того же `run_id`, не создаёт новый run.

## Семантика интерфейса

- `queued`, `running`, `completed`, `failed` — lifecycle, а не знак прибыли.
- Negative `net_arpu_gain` остаётся completed и получает отдельную business
  подпись, не техническую ошибку.
- Stored failed приходит как HTTP 200; HTTP 404/422/500 декодируются из
  `ErrorResponse`.
- `n_campaigns` и секция «Финальные кампании» не включают пилоты.
- `campaigns_detail.gross_lift` показан как диагностическое значение до
  дедупликации; строки явно запрещено суммировать в общий lift.
- `roi=null` означает нулевую стоимость, `risk_score_pct=null` — «не рассчитан».
- `UNKNOWN` означает пропуск в исходных сегментах и не предлагается как filter.
- Остатки результата относятся ко всему прогону; остатки в пилоте — к моменту
  пилота. Денежные значения подписаны нейтрально «ден. ед.», как в контракте.

Есть loading, idle/empty, summary error/retry, polling, execution-failed,
HTTP-error/retry и timeout/retry состояния. Таблицы имеют captions/scope,
status использует `aria-live`, поля имеют labels и validation, виден keyboard
focus, широкие таблицы прокручиваются, layout перестраивается до одной колонки.
Внешние шрифты, картинки, API-ключи и Python-код не используются.

## Ограничения следующего этапа

HTTP transport собран и протестирован на контрактных ответах, но реальный
FastAPI backend и сквозной E2E ещё отсутствуют. Backend должен вернуть runtime
`source=mock_environment`, строгое JSON без NaN/Infinity и сохранить семантику,
описанную в `contracts/README.md`. OpenAPI и organizer-owned файлы Frontend не
менял.
