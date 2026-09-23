# Текущее состояние

Обновлено: 2026-09-23T16:42:05+05:00.
Текущий этап: adaptive core + optional LLM реализованы; frontend впереди.
Активная роль: CORE / INTEGRATION по прямому запросу пользователя.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Наблюдаемый HEAD: cb803de, ветка main. Сохранены незакоммиченные изменения
предыдущей итерации adaptive/runtime/backend.

| Стадия | Статус | Состояние |
|---|---|---|
| Architecture / Core | IMPLEMENTED | Повторные пилоты, gate, небольшой fallback, legacy для сравнения |
| Runtime LLM | IMPLEMENTED | OpenAI Responses; режимы openai/off, NVIDIA отменена пользователем |
| Frontend | NOT_STARTED | Только README/role prompt и внешние JSON fixtures |
| Backend | IMPLEMENTED | FastAPI v1, очередь/память, 39 tests и реальный HTTP smoke |
| Final integration | PARTIAL | Agent/API gate PASS; нужны frontend и UI/E2E |

Пользователь отменил NVIDIA после проблемы верификации для Казахстана.
OpenAI остаётся единственным LLM-провайдером, default off сохранён.
Удалены NVIDIA endpoint/настройки/CLI choice; см. ADR 0003. Core-политика
и OpenAPI v1 не менялись. В заключительной проверке восстановлены исходные
LF в 14 organizer-файлах с точным SHA256 manifest; содержательных изменений
нет. Codex не выполнял Git-операций записи и не менял локальный `.env`.

## Работает

Core читает только публичный env. До 20 пилотов; минимум три положительных
наблюдения и осторожная оценка net для масштабирования. При отсутствии
подтверждений выбирается минимальная по экспозиции допустимая ячейка.
Порог неопределённости эвристический, прибыль не гарантирует. Старый baseline
сохранён в strategy/legacy.py. Политика и границы — ADR 0002.

Новый runtime вне false_positive/ подключает LLM только при явном
FP_LLM_PROVIDER=openai в окружении процесса. Default off не читает
.env и не вызывает сеть. Один запрос модели на run; только порядок публичных
гипотез, JSON validation, timeout и deterministic fallback с warning. Ключи
берутся из процесса/игнорируемого .env; OPEN_AI_API_KEY также поддерживается.
Ошибки чтения файла защищены fallback, ключи не попадают в trace/DTO.

OpenAI после обновления ключа пользователем: реальный smoke и 10 seed дали
11 принятых ответов на предыдущей итерации. После удаления NVIDIA новые
платные запросы не выполнялись: OpenAI payload/model не изменены.
Исторические NVIDIA 401 и benchmarks сохранены. Остаточные NVIDIA-переменные
в `.env` игнорируются. Старый FP_LLM_PROVIDER=nvidia в терминале нужно заменить
на openai/off: иначе он явно отклоняется до чтения ключей и сетевого запроса.

Backend использует ту же runtime factory. POST → 202/queued; один worker,
GET → queued/running/completed/failed. KPI считает официальный evaluator
с точными pilot ID; strict JSON, nullable ROI, агрегаты публичных CSV.
Fixtures остаются иллюстративными mock_fixture; реальные ответы API имеют
source=mock_environment. UI/БД/UI-E2E пока нет.

## Последние фактические проверки

Windows, Python 3.14.7 в .venv. Короткий python — неработающий WindowsApps alias;
использованы .venv/Scripts/python.exe, PYTHONUTF8=1 и provider off, если не указано иное.

| Команда / сценарий | Статус | Результат |
|---|---|---|
| verify_core.py до/после | FAIL → PASS | Восстановлены исходные LF; 15 SHA256, полный pytest, judge CLI и CSV проходят |
| local_eval.py | COMPLETED / SCORE FAIL | seed42: 19 пилотов, 1 финал, 3001 контакт, cost0, net≈−11.63 |
| local_eval.py --runs 10 | COMPLETED / UNSTABLE | 4/10 прибыльны, median≈−4624, min≈−13553, max≈78332 |
| Offline holdout 100–139, предыдущая итерация | COMPLETED | 23/40 прибыльны; mean +7248 против −15132 legacy; min −17109 против −41114 |
| OpenAI smoke seed42, предыдущая итерация | PASS INTEGRATION | external_advisor_used=true, net≈587846 |
| OpenAI 0–9, предыдущая итерация | PASS INTEGRATION / UNSTABLE | 10/10 ответов приняты, 8/10 прибыльны, mean≈359451, min≈−4388 |
| make_submission.py + verify_submission() | PASS | CSV обновлён; два повторных экспорта побайтно совпадают |
| python -m pytest | PASS | 108 passed, 15.94 s; 69 core/runtime + 39 backend, 1 Starlette warning |
| Real Uvicorn HTTP smoke | PASS | В составе pytest: сервер/health/summary/POST/poll/errors |
| git diff --check | PASS | Нет whitespace errors |
| Frontend build, UI/E2E | NOT_RUN | Нет frontend package/client/UI |

На предыдущей итерации первый полный pytest: 78 passed, 5 errors — PermissionError
старого системного временного каталога. Повтор с уникальным
--basetemp .venv/pytest-adaptive-<id> -p no:cacheprovider прошёл; старые
каталоги не удалялись и права не менялись.

Теперь verifier сам использует TemporaryDirectory и отключает pytest cache;
запускает все tests, а не только исходные четыре файла. Для этого нужны
backend/requirements-dev.txt. В дочерних процессах принудительно provider off:
проверено при provider openai в родительском окружении, новый regression test
подтверждает сохранение родительской настройки. Новых API-вызовов не было.

Отчёты — [benchmarks](benchmarks/README.md). Первый вариант с двумя
подтверждениями был отклонён после большого убытка и сохранён отдельно.
Финальная offline-политика заморожена до seed 100–139. На диагностических
0–9 улучшились среднее/нижний хвост, но ухудшились медиана и доля прибыльных
прогонов. OpenAI проверен на небольшой диагностической серии, не на holdout.
Mock не предсказывает hidden score, сетевой режим не воспроизводим по seed.

## Byte integrity и следующий шаг

Проблема byte integrity закрыта: перед записью проверено, что исключительно
CRLF→LF даёт исходный SHA256 для каждого из 14 файлов. После восстановления
все 15 файлов совпадают с manifest; manifest и .gitattributes не менялись.
Исходные blobs/логика/data сохраняются, полный verifier PASS.

- Для LLM-тестов и demo задавать FP_LLM_PROVIDER=openai.
- Перед воспроизводимым экспортом submission обязательно явно
  FP_LLM_PROVIDER=off. Текущий CSV содержит минимальный fallback seed42.
- Дальше frontend по обновлённому prompt 02: использовать готовый backend,
  проверить HTTP transport и передать следующий handoff Integration; затем UI/E2E.
- Backend: один процесс, cwd корень, память без TTL/отмены/БД/auth;
  перезапуск теряет runs. Linux/macOS пока не проверены.
- Человеческий review и ручной commit/push.

Запуск — [README](../README.md). Последний завершённый handoff:
[06-verification-to-frontend.md](handoffs/06-verification-to-frontend.md).
VERIFICATION_REPORT.md и handoff 01/03/04/05 — исторические отчёты.
