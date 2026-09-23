# INTEGRATION → FRONTEND: технические проверки проходят

Дата: 2026-09-23. Статус: COMPLETED в scope текущего agent/backend.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
HEAD: cb803de/main; предыдущие незакоммиченные изменения сохранены.

Пользователь попросил быстро завершить оставшиеся нюансы. Закрыта проблема
organizer byte integrity: 14 файлов восстановлены только CRLF→LF после
проверки каждого ожидаемого SHA256. Все 15 файлов теперь точно совпадают
с manifest, содержимое/логика/data/manifest не менялись.

`scripts/verify_core.py` теперь принудительно запускает дочерние проверки
с FP_LLM_PROVIDER=off, весь pytest в уникальном временном каталоге без cache,
оба local_eval-прогона и два экспорта submission. Родительская настройка
провайдера не изменяется. Для запуска нужны backend/requirements-dev.txt.
Обновлён frontend prompt: backend уже работает, следующий handoff в Integration.

## Фактическая проверка

- Preflight verifier: FAIL на прежнем CRLF agent_template.py.
- Финальный `python scripts/verify_core.py`: PASS, включая 15 SHA256.
- Полный pytest: 108 passed, 15.94s, 1 Starlette deprecation warning;
  backend HTTP smoke включён. Добавлен regression изоляции LLM-режима verifier.
- local_eval.py: завершён, seed42 net≈−11.63, финансовый scorer FAIL.
- local_eval.py --runs 10: все завершены, 4/10 прибыльны; стратегия неустойчива.
- make_submission.py дважды: одинаковый CSV, SHA256
  08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10.
- git diff --check: PASS.
- Новые live API calls: NOT_RUN, не требовались; OpenAI ранее проверен.
- Frontend/UI/E2E: NOT_RUN, UI пока отсутствует.

Запуск из корня в PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe scripts/verify_core.py
```

Для LLM demo `$env:FP_LLM_PROVIDER='openai'`, затем Uvicorn по backend README.
Сеть опциональна, default off; NVIDIA отменена. API v1 и core-политика
в этой итерации не менялись. `.env` не редактировался.

Следующий scope — frontend по `.codex/prompts/02-frontend.md`, проверка
реального HTTP transport и UI/E2E. Прибыльность на hidden effects не обещана;
не принимать технический PASS за положительный net. Человек проверяет diff,
делает commit/push; Codex историю и ветку не менял.
