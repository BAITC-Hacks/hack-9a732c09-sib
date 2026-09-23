# INTEGRATION — проверка работоспособности по требованиям

Дата: 2026-09-23. Статус: COMPLETED в scope проверки Python/judge.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Исходный HEAD: 464b4c2/main, дерево чистое. Git-операций записи не было.

Пользователь попросил объяснить, как проверить агента по требованиям.
Preflight обнаружил рассогласование: runtime уже возвращает priorities-v2
и typed errors, тесты ожидают старый order/ValueError. Исправлены тестовые
ответы и ожидания; добавлены проверки валидации, ties, отказов и ошибок
транспорта без сети. Production-код и политика стратегии не менялись.

README/state после объединения веток описывали старый baseline и отсутствие
frontend. Исправлены инструкции по фактическому коду; сохранены исторические
handoff. Frontend существует, но новый сквозной UI E2E не заявляется PASS.
Ключи/.env, API-контракт и organizer-owned файлы не редактировались.

## Проверки

- Preflight verifier: FAIL — 105 passed / 3 failed (старые LLM mocks).
- Финальный verifier: PASS, 15 organizer SHA256; 123 tests, 14.72s.
- В pytest включён настоящий Uvicorn HTTP smoke; один warning Starlette.
- local_eval seed42: технически завершён; net≈−11.63, финансовый FAIL,
  19 пилотов + 1 финал, 3001 контакт, cost=0.
- local_eval --runs 10: завершены все, прибыльны 4/10, медиана≈−4624,
  min≈−13553, max≈78332. Это offline, не OpenAI.
- make_submission дважды: одинаковые байты; SHA256
  08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10.
- git diff --check: PASS, нет whitespace errors.
- Live OpenAI priorities-v2: NOT_RUN, без платных API-вызовов.
- Frontend build/test/UI E2E: NOT_RUN, Node/npm недоступны в PATH.

## Повторить

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe scripts/verify_core.py
git diff --check
```

Verifier включает все три штатные команды организаторов, отключает LLM,
проверяет повторяемость CSV и сохраняет существующий файл.
Для фактического API-советника отдельно:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_strategy.py --provider openai --runs 1
```

Этот запуск платный; нужен локальный ключ. Проверять
`adaptive.rows[0].external_advisor_used` и warnings. Статус финансового
PASS не доказывает вызов модели. Новый prompt требует новых live-замеров.
Продолжение: UI/HTTP интеграция, live smoke и незавершённый scope ADR 0004;
технические проверки не обещают положительный hidden score.
