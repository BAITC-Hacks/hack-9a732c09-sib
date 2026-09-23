# API v1 — зафиксированная семантика

`openapi.yaml` (OpenAPI 3.1) — источник истины. `campaign.schema.json` содержит
ту же Campaign-схему для проверки judge/CSV. HTTP-сервер реализован в
`backend/`; запуск и проверки описаны в `backend/README.md`. Схема v1 неизменна.

- Origin по умолчанию `http://localhost:8000`, пути уже включают `/api/v1`.
  `VITE_API_BASE_URL` задаёт origin без `/api/v1`.
- POST `{seed: 42, mode: "mock"}` всегда отвечает 202 и метаданными.
  Даже если status уже completed/failed, клиент затем запрашивает GET.
- queued/running GET содержит только метаданные. Клиент опрашивает раз в
  секунду, прекращает на completed/failed, отменяет запросы при размонтировании;
  через 5 минут показывает timeout с возможностью повторить GET.
- failed GET — HTTP 200 с Error, warnings и completed_at. HTTP 404 означает
  неизвестный/утраченный после перезапуска run. HTTP 422/500 — ErrorResponse.
  Ошибки FastAPI нужно привести к этому формату.
- Отрицательный net не является технической ошибкой: status остаётся completed.
- source=mock_fixture только у статических примеров; scored demo использует
  mock_environment. core допустим в метаданных принятого запуска.
- Время — ISO-8601 UTC. Seed — целое 0..4294967295. JSON строго без NaN/Infinity.

## KPI и соответствие scorer

`campaigns` и `n_campaigns` — только финальные кампании (1–10).
`n_pilots=len(pilots)`. В `scoring_core` n_campaigns включает пилоты: backend
обязан преобразовать его, а не скопировать.
`campaigns_detail` содержит сначала пилоты, затем финал; `kind` и `index`
ссылаются на соответствующий массив. `gross_lift` строки до дедупликации,
поэтому сумма строк может превышать общий `gross_arpu_lift`.

Формулы после пилотов И финальных кампаний:

```text
net_arpu_gain = gross_arpu_lift - total_cost
total_arpu_after = baseline_total_arpu + net_arpu_gain
growth_vs_baseline_pct = 100 * net_arpu_gain / baseline_total_arpu
coverage_pct = 100 * unique_customers_targeted / subscriber_count
remaining_budget = 100000 - total_cost
remaining_contacts = 15000 - total_contacts
roi = gross_arpu_lift / total_cost; при total_cost=0 → null + warning
```

risk_score_pct — процент уникальных клиентов с отрицательным эффектом после
дедупликации, либо null, если не рассчитан. Это не прогноз вероятности убытка.
Пилотный observed_lift_total зашумлён; из него нельзя собрать scored KPI.
Остатки в PilotObservation относятся к моменту пилота, а в RunCompleted —
к полному прогону. Core resources_after_plan — прогноз расходов по публичным
сегментам, а не изменение env и не истинный score.

## Fixtures

`examples/*.json` — демонстрационные данные. Summary агрегирован из публичных
CSV, completed сценарий сконструирован, не является результатом baseline.
Пустой сегмент CSV представлен как `UNKNOWN` в агрегатах; это не допустимое
значение фильтра кампании. Backend должен сохранять всех абонентов в summary.
Source всегда mock_fixture. Генератор `python scripts/build_contract_examples.py`
воспроизводит их с фиксированными UUID/временем. Не подменять ими runtime API.
Есть queued, running, completed, failed, HTTP-error и health примеры.

Изменения контракта проходят протокол docs/OWNERSHIP.md и contract tests.
