# INTEGRATION — README для самостоятельной технической проверки

Дата: 2026-09-23. Статус: COMPLETED в scope документации.
Commit: TO_BE_FILLED_AFTER_HUMAN_COMMIT
Исходный HEAD: 43241e5/main, дерево чистое. Git-операций записи не было.

Пользователь предоставил пункт 5.4.15 и попросил проверить README.
До правок не хватало явного стека/минимальной версии Python, полной env-таблицы
и самодостаточного запуска UI с backend. Корневой README дополнен по
фактическим requirements, runtime и frontend config. Обновлён .env.example;
реальный .env, исходники, зависимости, тесты и organizer-файлы не менялись.

| Требование 5.4.15 | Где в корневом README |
|---|---|
| Описание решения и назначения | Вводные абзацы: выбор аудитории, тарифа, канала, ограничения и итог |
| Архитектура | Схема и пять шагов алгоритма; границы core/runtime/API/UI |
| Технологии | Таблица Python/pandas/NumPy/FastAPI/React/TypeScript/Vite/OpenAI |
| Установка | Новый clone, Python/venv/pip, данные, npm ci; Windows и эквивалент Linux/macOS |
| Запуск | Backend и frontend отдельными терминалами, адреса/порты и остановка |
| Зависимости | Требования к Python/Node и ссылки на runtime/dev manifests и lockfile |
| Параметры окружения | Значения по умолчанию, место задания, приоритет и opt-in OpenAI |
| Проверка основного сценария | CLI/CSV/verifier, HTTP smoke, UI seed → completed → KPI/пилоты/финал |

README покрывает перечисленные сведения. Это проверка содержания и
согласованности инструкций, а не подтверждение допуска организатором.

Проверки до/после: scripts/verify_core.py PASS; 15 organizer hashes;
123 pytest tests (14.79s до, 15.03s после), включая настоящий Uvicorn HTTP
smoke; local_eval seed42 и 10 seed завершены; два одинаковых CSV.
SHA256 CSV: 08f012ca973d18a33ef258addf0312719b27b04f5bc355d3c2f2dce338c63a10.
Финансовые результаты не менялись: seed42≈−11.63, прибыльны 4/10 offline.
pip check PASS. Локальные ссылки README и git diff --check проверены.

NOT_RUN: новая установка в чистом clone/venv (использовано существующее
окружение), Linux/macOS, live OpenAI priorities-v2, актуальный frontend
build/UI E2E (Node/npm недоступны в PATH). Предыдущий frontend handoff
сохраняет свои исторические результаты; здесь они не переобъявлены PASS.

Далее: проверить HTTP UI и live OpenAI по корневому README. Для независимого
экспертного запуска следовать разделу установки и затем verify_core.py.
Человек проверяет diff и выполняет commit/push; секреты не включать.
