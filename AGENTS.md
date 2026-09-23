# Обязательный порядок чтения

1. `AGENTS.md` (этот файл).
2. Корневой `README.md`.
3. `docs/ARCHITECTURE.md`.
4. `docs/PROJECT_STATE.md`.
5. `docs/COLLABORATION.md`.
6. `contracts/openapi.yaml` и `contracts/README.md`.
7. Последний завершённый файл в `docs/handoffs/` (не `.template`).
8. Промпт своей роли в `.codex/prompts/`.

Это один проект False Positive. Репозиторий — общая память независимых
Codex-сессий; предыдущие чаты недоступны. Работа участников и редактирование
строго последовательны: ARCHITECT/CORE → FRONTEND → BACKEND → INTEGRATION.
Новый участник начинает после подтверждённого человеческого push и pull.

## Pre-flight до изменений

```sh
git status --short
git branch --show-current
git log --oneline -n 10
python scripts/verify_core.py
```

Сохранить чужие изменения; записать существующие ошибки. Прочитать также
`docs/OWNERSHIP.md`. Текущая ветка — `main`; не менять её автоматически.

## Инварианты

- `agent.py:Agent.act(env) -> list[dict]` — обязательная судейская граница.
- Core в `false_positive/` не зависит от backend/frontend, HTTP, Pydantic,
  БД, секретов, LLM или интернета. Обязательный advisor — детерминированный.
- Agent читает только публичный интерфейс среды. Нельзя читать скрытую модель,
  замыкания или внутренние атрибуты; исходники среды не читаются в runtime.
- Не менять organizer-owned файлы из `docs/organizer-manifest.json`, включая
  `data/**`. Их байтовая целостность проверяется verifier.
- Приоритет: фактический судейский код → ТЗ → положение → OpenAPI → ADR → prompts.
- Финальный план 1–10 кампаний, пилоты и финал делят бюджет и контакты.
- Demo использует отдельный FastAPI backend и официальный mock environment;
  React-клиент работает по `/api/v1`. Сейчас эти приложения не реализованы.
- Не подгонять baseline под mock score, не добавлять сложную инфраструктуру.

## Ownership и общий контракт

FRONTEND меняет `frontend/**`, BACKEND — `backend/**` и свои тесты.
Общие README/state/progress и новый handoff обновляет каждая роль.
INTEGRATION устраняет подтверждённые несовместимости. Подробности — OWNERSHIP.
По умолчанию OpenAPI v1 заморожен. Необходимое изменение обосновать ADR;
одновременно обновить контракт, fixtures, существующие клиенты/DTO, тесты,
README и PROJECT_STATE. Предпочитать совместимые дополнения.

## Проверки и завершение

До и после изменений — `python scripts/verify_core.py`; отдельно обязательны
`python local_eval.py`, `python local_eval.py --runs 10`,
`python make_submission.py`, `python -m pytest`, `git diff --check`.
Добавлять проверки своего слоя (build/API/E2E), не заявлять выдуманный PASS.
Недоступную проверку обозначать FAIL/NOT_RUN с точной причиной.

Каждая сессия обновляет PROJECT_STATE (состояние), дописывает PROGRESS
(история), создаёт новый handoff, исправляет README по факту. Завершённые
handoff не переписывать. До ручного commit использовать
`TO_BE_FILLED_AFTER_HUMAN_COMMIT`. Все решения должны остаться в файлах.

Codex не выполняет commit/push/pull/merge/rebase/checkout; это делает человек.
Запрещены reset --hard, clean, force push и уничтожение чужих изменений.
Не добавлять секреты, личные пути и аккаунты. Не объявлять UI/API/E2E готовыми
до реализации. Завершение = законченный scope роли, фактические проверки,
обновлённая память и конкретный handoff, готовый для человеческого review.
