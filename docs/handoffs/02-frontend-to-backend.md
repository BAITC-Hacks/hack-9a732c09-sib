# Handoff 02 — FRONTEND → BACKEND

Статус: DONE (frontend scope; incident working-copy verifier описан ниже).
Дата/время: 2026-09-23T16:24:27+05:00.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT

## Выполненная цель и фактические изменения

Создан React 19 + Vite 6 + TypeScript dashboard аналитика, который полностью
работает без backend на зафиксированных JSON fixtures и готов переключиться на
HTTP одним env-флагом. OpenAPI, contract fixtures, judge/core и organizer-owned
файлы Frontend не менял.

- Tooling: `frontend/package.json`, воспроизводимый `package-lock.json`,
  tsconfig, Vite/Vitest config, `index.html`, `.env.example`.
- UI: `src/App.tsx`, `styles.css`, `format.ts`, `runState.ts`, components для
  case overview, запуска/status и результата.
- Экран: аудитория/лимиты, каналы, 21 тариф, три группы сегментов, seed/run,
  lifecycle, KPI, остатки, пилоты, финальные кампании, evaluator detail,
  warnings и явный fixture notice.
- Состояния: loading, empty, summary error/retry, queued/running, completed,
  negative completed, stored failed, HTTP error/retry, timeout/retry.
- Доступность: landmarks/headings, labels, seed validation, `aria-live`, alerts,
  captions/scope, focus-visible, keyboard form и responsive tables/layout.
- Tests: 18 Vitest/RTL tests для client polling, POST/GET boundary, HTTP status/
  ErrorResponse, fixture lifecycle, instant/zero-cost/negative cases, empty и UI.
- Документация: root/frontend README, `.env.example`, PROJECT_STATE, PROGRESS,
  THIRD_PARTY_NOTICES, handoff index и этот новый handoff.

## Решения и замороженные интерфейсы

Единственная граница UI с API — `frontend/src/api/client.ts`:
`AnalystApiClient.getCaseSummary`, `createAndPoll`, `pollRun`. DTO находятся в
`frontend/src/api/types.ts`; structured errors — `errors.ts`; реализации —
`httpTransport.ts` и `mockTransport.ts`; выбор транспорта — `src/config.ts`.

HTTP paths уже содержат prefix:

```text
GET  /api/v1/case/summary
POST /api/v1/runs
GET  /api/v1/runs/{run_id}
```

`VITE_API_BASE_URL` должен быть origin без `/api/v1`; клиент намеренно отклоняет
base URL с этим suffix. `VITE_USE_MOCKS=true` — default и fixture mode;
`false` — HTTP. Для browser dev на `http://localhost:5173` Backend потребуется
совместимый CORS или тот же origin/proxy на Integration.

Клиент после любого POST 202 всегда делает немедленный GET, даже если accepted
metadata говорит completed/failed. Pending опрашивается раз в секунду, deadline
5 минут охватывает и зависший fetch; unmount/new run отменяет fetch и delay.
Retry после timeout/HTTP error делает только GET прежнего `run_id`.

Backend обязан сохранить контрактную семантику:

- runtime `source=mock_environment`; `mock_fixture` только для статических demo;
- failed run — stored `RunFailed` с HTTP 200, HTTP 404/422/500 — `ErrorResponse`;
- negative net — `completed`, не execution failure;
- `n_campaigns` и `campaigns` — только финальный план; pilots отдельно;
- `campaigns_detail.gross_lift` до дедупликации и не образует общий lift;
- `roi=null` при нулевой стоимости с warning, `risk_score_pct` nullable;
- UNKNOWN допустим в summary aggregate, но не в campaign filter;
- строгий JSON без NaN/Infinity; время UTC ISO-8601.

OpenAPI v1 не менялся, ADR не требовался.

## Проверки

Проверенные версии: Node.js 22.14.0, npm 10.9.2, Python 3.13.15.

| Команда | PASS/FAIL/NOT_RUN | Фактический результат |
|---|---|---|
| npm ci | PASS | 184 packages из lockfile |
| npm test | PASS | 5 files, 18 tests |
| npm run build | PASS | tsc + Vite, 46 modules, JS gzip 70.82 kB |
| Vite dev smoke | PASS | HTML, TS modules и contract fixture import — HTTP 200 |
| python local_eval.py | PASS | net≈4042, 3 пилота, 1 финальная кампания |
| python local_eval.py --runs 10 | PASS | 6/10 прибыльных, без invalid/technical падений (`PYTHONUTF8=1`) |
| python make_submission.py | PASS | до/после SHA256 `d66c27…f5a77e` |
| python -m pytest | PASS | 44 passed in 5.56 s |
| python -m pip check | PASS | No broken requirements found |
| python scripts/verify_core.py, working copy | FAIL | первый report — `agent_template.py`; все 14 text entries имеют CRLF, PDF совпадает |
| python scripts/verify_core.py, clean `git archive HEAD` | PASS | 15 hashes, 44 tests, eval, 10 runs, submission ×2 |
| Backend/API browser E2E | NOT_RUN | Реальный backend ещё не реализован |

## Нереализованное и риски

HTTP client не проверен против живого FastAPI; возможные CORS/timing/DTO проблемы
остаются для Backend/Integration. Fixture KPI иллюстративны. Mock timeout в UI
сокращён до 5 секунд только для демонстрации; HTTP сохраняет 5 минут. Frontend
не выполняет strategy/scoring и поэтому не может компенсировать ошибочные DTO.

В текущей Windows working copy все 14 текстовых organizer entries имеют CRLF;
PDF совпадает. Verifier первым сообщает `agent_template.py` с SHA256
`739ec3…edf62f`; его LF bytes дают manifest `4eb369…b5eb10d`, и та же проверка
подтверждена для остальных 13 text entries. Git status до Frontend был clean,
эти файлы не редактировались и не включены в diff. Чистый архив HEAD проходит
полный verifier. Человек до commit должен восстановить рабочие байты из
проверенного HEAD/исходного пакета и повторить verifier; не включать organizer
normalization в Frontend commit.

Первый `local_eval.py --runs 10` после вычисления всех seed завершился на
Unicode `⚠` в cp1251; повтор с `PYTHONUTF8=1` PASS. Это console environment,
не изменение judge.

## Следующему агенту

Read-order: AGENTS → README → ARCHITECTURE → PROJECT_STATE → COLLABORATION →
OpenAPI + contracts/README → этот handoff → `.codex/prompts/03-backend.md` →
`frontend/src/api/{types,client,httpTransport}.ts` и fixtures.

Реализовать FastAPI строго по существующему OpenAPI/client: summary из всех
публичных данных, свежая official mock env на run, wrapper ровно один раз
вызывает StrategyEngine, evaluator формирует KPI, in-memory run store принимает
POST как 202 и отдаёт snapshots через GET. Проверить CORS для Vite origin,
ErrorResponse normalization, malformed trace → failed, null/finite JSON и
frontend HTTP mode. Не подменять runtime fixture и не запускать Agent повторно
для KPI.

Ожидаемый commit message:
`feat(frontend): add analyst dashboard with mock transport`
