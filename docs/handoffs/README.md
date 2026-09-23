# Передача контекста

Последний завершённый handoff —
[`07-requirements-check-to-integration.md`](07-requirements-check-to-integration.md).
Он подтверждает Python/judge проверки, но не завершённый UI E2E.
Каждый следующий этап
создаёт новый `.md` по `.template`, не редактируя завершённые handoff.
Последний завершённый файл определяется по номеру и статусу, не по шаблону.
Результаты только фактические; неизвестные команды — NOT_RUN с причиной.

Будущие hash до человеческого commit: `TO_BE_FILLED_AFTER_HUMAN_COMMIT`.
