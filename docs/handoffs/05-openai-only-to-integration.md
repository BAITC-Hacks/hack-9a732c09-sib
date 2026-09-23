# INTEGRATION → следующий участник: OpenAI only

Дата: 2026-09-23. Статус: COMPLETED в указанном scope.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
HEAD: cb803de / main. Существующие незакоммиченные изменения из handoff 04 сохранены.

Пользователь отменил NVIDIA после отсутствия Казахстана в форме верификации.
Удалены её endpoint, модель, настройки `.env.example` и allowlist, CLI choice.
Поддерживаются `FP_LLM_PROVIDER=openai` и `off` (default). Старое значение
`nvidia` отклоняется до чтения файла и сетевого запроса. Локальный `.env`
не редактировался; оставшиеся NVIDIA-переменные не используются.

OpenAI Responses payload/model, core strategy, backend API DTO, OpenAPI,
organizer files/data и submission content не изменены в этой итерации.
Исторические handoff/benchmarks сохранены. ADR 0003 заменяет только выбор
провайдеров ADR 0002. Настройки запуска и активная документация обновлены.

Проверки через `.venv/Scripts/python.exe`, PYTHONUTF8=1, provider off:

- pytest: 107 passed, 15.18s, включая реальный HTTP smoke; один Starlette warning.
  Уникальный basetemp внутри .venv, cache отключён из-за прежних Windows permissions.
- local_eval.py: корректно завершён, scorer FAIL из-за net≈−11.63 (seed42).
- local_eval.py --runs 10: корректно завершены все seed; 4/10 положительных,
  min≈−13553, median≈−4624. Финансовой устойчивости не заявляем.
- make_submission.py через verify_submission: два одинаковых экспорта,
  SHA256 08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10.
- verify_core.py до/после: FAIL, прежние CRLF, первая ошибка agent_template.py.
- git diff --check: PASS.
- Новые live LLM calls: NOT_RUN, OpenAI payload/model не менялись; предыдущая
  проверка 11 реальных OpenAI-ответов описана в handoff 04 и benchmarks.
- UI/E2E: NOT_RUN, frontend отсутствует.

Пользовательский вопрос о $50 не означает новый запрос развернуть инфраструктуру:
если это Brev credits, они относятся к вычислениям/хранению и могут использоваться
через веб-консоль отдельно от API Catalog. Точный сервис не подтверждён.
GPU/CPU-инстансы не создавались; ключи/кредиты не менялись.

Дальше: использовать OpenAI для LLM demo, off для повторяемого submission;
реализовать frontend, выполнить UI/API/E2E; восстановить organizer byte integrity
перед итоговым verifier. Review и commit/push остаются человеку.
