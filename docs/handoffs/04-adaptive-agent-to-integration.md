# CORE / INTEGRATION → следующий участник

Дата: 2026-09-23. Статус: COMPLETED в указанном scope.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Исходный HEAD: cb803de / main, рабочее дерево перед началом чистое.
Commit/push/pull и переключений веток Codex не выполнял.

## Scope и результат

Пользователь поручил улучшить устойчивость агента после убыточных seed и
использовать выданные API. Выбор: NVIDIA основная, OpenAI переключаемая
альтернатива. Изменения относятся к core/runtime и адаптации backend-тестов;
OpenAPI v1, organizer-файлы, data, frontend не менялись.

Реализованы публичный генератор гипотез, повторные пилоты, эвристический
порог масштабирования, отдельное подтверждение платного канала и fallback
малой экспозиции. Прежний baseline сохранён для сравнения. Новый runtime
вне core подключает максимум один LLM-запрос ранжирования за run; ответы
не могут изменить ресурсы, кампании или gate. Core без сети и ключей.
См. ADR 0002 и `docs/benchmarks/README.md` для точной политики и результатов.

`FP_LLM_PROVIDER` читается из окружения процесса: off (default), nvidia,
openai. Для LLM ключи/модели можно читать из корневого игнорируемого `.env`.
Старое имя `OPEN_AI_API_KEY` поддерживается; ключи не печатались и не менялись
агентом. HTTP failures и повреждённая конфигурация дают fallback с warning.

OpenAI после обновления ключа пользователем реально работает: один smoke
и серия 10 seed, модель использована во всех 11 запусках. NVIDIA inference
пока HTTP 401, это открытый внешний блокер. Пользователь уточнил только
«$50 NVIDIA API tokens» и меню Compute / Agents / Launchables. Это похоже
на Brev, но без URL платформа активации/особый gateway не установлены.
Оставлен NVIDIA endpoint API Catalog, без выдуманного URL и авторизации.

## Проверено

- 108 tests PASS, 14.75 s, включая реальный Uvicorn HTTP smoke;
  один Starlette deprecation warning. Тесты без реальных API-вызовов.
- `local_eval.py` завершён: seed42, 19 пилотов, 1 финал, 3001 контакт,
  cost0, net≈−11.63; финансовый статус scorer FAIL.
- `local_eval.py --runs 10`: все вычисления завершены, 4/10 прибыльны,
  min≈−13553, median≈−4624, max≈78332. Не называть это финансовым PASS.
- Offline holdout 100–139: средний net +7248 вместо −15132 legacy,
  min −17109 вместо −41114, положительных 23/40 вместо 17/40.
- OpenAI 0–9: 10/10 реальных ответов приняты, 8/10 прибыльны, mean≈359451,
  min≈−4388. Это диагностика, не отложенное доказательство преимущества.
- `make_submission.py` и два последующих экспорта: PASS, SHA256
  `08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10`.
  CSV теперь содержит минимальный fallback seed42. Экспорт был с provider off.
- `verify_core.py` до/после: FAIL, существующий CRLF в organizer files,
  первая ошибка agent_template.py. Organizer-файлы и manifest не правились.
- `git diff --check`: PASS, нет whitespace errors.
- UI/E2E: NOT_RUN, frontend не реализован.

Первый полный pytest этой сессии: 78 PASS, 5 ERROR из-за PermissionError
старого системного pytest temp. Успешный повтор использовал уникальный
`--basetemp .venv/pytest-adaptive-<id> -p no:cacheprovider` без удаления
старых каталогов. Первоначальные неудачные policy benchmarks сохранены.
Review дополнительно выявил .env read failure вне fallback; исправлено
с двумя тестами. Ограничение воспроизводимости LLM явно внесено в README.

## Следующий шаг

1. Для работы сейчас выбрать `FP_LLM_PROVIDER=openai`; для NVIDIA создать/
   активировать корректный ключ API Catalog либо выяснить gateway у организаторов,
   затем повторить `scripts/evaluate_strategy.py --provider nvidia --runs 1`.
   Успех определяется external_advisor_used=true, не отсутствием падения CLI.
2. Перед сдачей/повторяемым экспортом явно `FP_LLM_PROVIDER=off`.
   LLM-сетевые запуски по одному seed могут давать разные планы.
3. Не считать текущую политику окончательной: часть seed убыточна, offline
   часто не масштабирует ни одну гипотезу. Оценивать дальнейшие изменения
   на новых seed и сценариях без подгонки под скрытую модель.
4. Реализовать frontend, затем UI/API/E2E integration. Общий контракт не менялся.
5. Человеческий review diff/untracked, organizer byte integrity, commit/push.

Ограничения backend прежние: один процесс, память без TTL/отмены/БД/auth,
сервер запускается из корня. Runtime LLM доступен через общий engine factory;
API DTO сохранились. Исторические handoff 01/03 не редактировались.
