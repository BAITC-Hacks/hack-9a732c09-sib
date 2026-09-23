# Handoff 07 — INTEGRATION → SUBMISSION

Дата: 2026-09-23. Commit: `TO_BE_FILLED_AFTER_HUMAN_COMMIT`.

## Что объединено

- React/Vite dashboard использует frozen OpenAPI v1 через `HttpTransport`.
- FastAPI отдаёт `/api/v1`, CORS для localhost/127.0.0.1:5173 и lifecycle
  POST 202 → GET polling.
- `frontend/scripts/live-api-smoke.mjs` добавлен как повторяемая проверка
  реального client/API сценария (`npm run smoke:live`).
- Vite dev/preview фиксируют порт 5173; URL и режим fixtures валидируются
  строго, чтобы live-demo не переключался незаметно.
- LLM tests приведены к актуальной Responses priorities schema; socket smoke
  принудительно запускается с `FP_LLM_PROVIDER=off`.

## Фактические проверки

| Проверка | Статус | Результат |
|---|---|---|
| `python -m pip check` | PASS | Broken requirements отсутствуют |
| `python -m pytest -p no:cacheprovider -q` | PASS | 108 passed, 1 deprecation warning |
| `python scripts/verify_core.py` | PASS | hashes, eval, два одинаковых submission exports |
| `python local_eval.py --runs 10` | PASS | все runs завершены, 4/10 финансово положительны |
| `npm ci && npm test && npm run build` | PASS | 28 frontend tests, production build |
| `npm run smoke:live` | PASS | CORS + summary + POST 202 + real polling |
| Vite preview на 5173 | PASS | app shell 200 и разрешённый CORS origin |
| `npm audit --omit=dev` | PASS | 0 production vulnerabilities |

## Открытые ограничения

- Финансовый знак нестабилен: seed 42 около −12; это не скрывается UI/API.
- 2 moderate advisory остаются только в dev Vitest; исправление требует major
  upgrade до Vitest 5. Production audit чист.
- Browser visual automation и live OpenAI call не запускались. Offline default
  и API/client boundary проверены.

## Перед commit

```powershell
git diff --check
git status --short
```

Не менять organizer-manifest файлы. Рекомендуется human commit с сообщением
`integration: verify frontend, backend and judge workflow`.
