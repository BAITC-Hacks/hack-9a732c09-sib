# Ответственность этапов

| Этап | Основная зона | Общие файлы |
|---|---|---|
| ARCHITECT / CORE | agent.py, false_positive/**, contracts/**, tests/**, scripts/**, docs/config | Все необходимые для bootstrap |
| FRONTEND | frontend/** | README, PROJECT_STATE, PROGRESS, новый handoff |
| BACKEND | backend/**, tests/backend/** | README, PROJECT_STATE, PROGRESS, новый handoff |
| INTEGRATION | Все зоны при подтверждённой необходимости | Сохранение judge-контракта, запись решений |

Organizer-owned файлы из `organizer-manifest.json` и `data/**` неизменяемы.
Последовательность не даёт права переписывать чужой слой без причины.

Изменение API: сначала причина в новом ADR/handoff, затем совместимое
дополнение. В одном наборе изменений обновить OpenAPI, JSON fixtures,
существующие frontend types/client, backend schemas/routes, contract tests,
README и PROJECT_STATE. Переименования/удаления v1 избегать. При сомнении
сохранить интерфейс и передать проблему Integration.
