import type {
  Campaign,
  CampaignDetail,
  Constraints,
  PilotObservation,
  RunCompleted,
} from "../api/types";
import {
  channelLabels,
  describeFilters,
  formatAmount,
  formatDuration,
  formatInteger,
  formatPercent,
  formatRatio,
} from "../format";
import { SourceBadge } from "./SourceBadge";

interface RunResultsProps {
  result: RunCompleted;
  constraints?: Constraints;
}

function FilterList({ filters }: { filters: Campaign }) {
  const descriptions = describeFilters(filters);
  if (descriptions.length === 0) {
    return <span className="muted">Без сегментных ограничений</span>;
  }
  return (
    <div className="filter-list">
      {descriptions.map((description) => <span key={description}>{description}</span>)}
    </div>
  );
}

function PilotRows({ pilots }: { pilots: PilotObservation[] }) {
  if (pilots.length === 0) {
    return (
      <tr>
        <td colSpan={7} className="table-empty">Пилоты не проводились.</td>
      </tr>
    );
  }
  return pilots.map((pilot) => (
    <tr key={pilot.pilot}>
      <th scope="row">{pilot.pilot}</th>
      <td>{pilot.target_tariff}</td>
      <td>{channelLabels[pilot.channel]}</td>
      <td>{formatInteger(pilot.n_customers)}</td>
      <td>{formatAmount(pilot.cost)}</td>
      <td className={pilot.observed_lift_total < 0 ? "value-negative" : undefined}>
        {formatAmount(pilot.observed_lift_total)}
      </td>
      <td>
        <div className="filter-list filter-list--compact">
          {describeFilters(pilot.filters).length > 0
            ? describeFilters(pilot.filters).map((item) => <span key={item}>{item}</span>)
            : <span className="muted">Без ограничений</span>}
        </div>
      </td>
    </tr>
  ));
}

function DetailRows({ details }: { details: CampaignDetail[] }) {
  if (details.length === 0) {
    return (
      <tr>
        <td colSpan={7} className="table-empty">Детализация отсутствует.</td>
      </tr>
    );
  }
  return details.map((detail) => {
    const caps = [
      detail.capped_at_campaign_limit && "лимит кампании",
      detail.capped_at_reach_budget && "лимит контактов",
      detail.capped_at_money_budget && "лимит бюджета",
    ].filter(Boolean);
    return (
      <tr key={`${detail.kind}-${detail.index}-${detail.name}`}>
        <td>
          <span className={`kind-badge kind-badge--${detail.kind}`}>
            {detail.kind === "pilot" ? "Пилот" : "Финал"}
          </span>
        </td>
        <th scope="row">{detail.name || `#${detail.index + 1}`}</th>
        <td>{channelLabels[detail.channel]}</td>
        <td>{formatInteger(detail.n_contacts)}</td>
        <td>{formatAmount(detail.cost)}</td>
        <td className={detail.gross_lift < 0 ? "value-negative" : undefined}>
          {formatAmount(detail.gross_lift)}
        </td>
        <td>{caps.length > 0 ? caps.join(", ") : "—"}</td>
      </tr>
    );
  });
}

function ResourceMeter({
  label,
  remaining,
  total,
  formatter,
}: {
  label: string;
  remaining: number;
  total: number;
  formatter: (value: number) => string;
}) {
  const used = Math.max(0, total - remaining);
  return (
    <article className="resource-meter">
      <div>
        <span>{label}</span>
        <strong>{formatter(remaining)}</strong>
      </div>
      <progress max={total} value={used} aria-label={`${label}: использовано ${formatter(used)}`} />
      <small>Использовано {formatter(used)} из {formatter(total)}</small>
    </article>
  );
}

export function RunResults({ result, constraints }: RunResultsProps) {
  const isNegative = result.net_arpu_gain < 0;
  const budgetTotal = constraints?.total_budget ?? result.total_cost + result.remaining_budget;
  const contactsTotal = constraints?.max_total_contacts ?? result.total_contacts + result.remaining_contacts;

  return (
    <section className="results" aria-labelledby="results-title">
      <div className={`outcome ${isNegative ? "outcome--negative" : "outcome--positive"}`}>
        <div>
          <p className="eyebrow">05 · Итог эксперимента</p>
          <h2 id="results-title">
            {isNegative ? "Финансовый результат отрицательный" : "Финансовый результат положительный"}
          </h2>
          <p>
            Статус <strong>completed</strong>: расчёт технически завершён независимо от знака net.
          </p>
        </div>
        <div className="outcome__value">
          <span>Net ARPU gain</span>
          <strong>{formatAmount(result.net_arpu_gain)}</strong>
        </div>
      </div>

      <div className="result-meta">
        <SourceBadge source={result.source} />
        <span>Run: <code>{result.run_id}</code></span>
        <span>Расчёт: {formatDuration(result.duration_ms)}</span>
      </div>

      {result.source === "mock_fixture" && (
        <div className="fixture-notice" role="note">
          <strong>Демонстрационный fixture.</strong> Эти KPI иллюстрируют контракт и не являются фактическим запуском стратегии.
        </div>
      )}

      <div className="metric-grid metric-grid--results">
        <article className="metric-card metric-card--lead">
          <span>Общий gross lift</span>
          <strong>{formatAmount(result.gross_arpu_lift)}</strong>
          <small>после дедупликации</small>
        </article>
        <article className="metric-card">
          <span>Стоимость</span>
          <strong>{formatAmount(result.total_cost)}</strong>
          <small>пилоты + финальный план</small>
        </article>
        <article className="metric-card">
          <span>Рост к baseline</span>
          <strong className={result.growth_vs_baseline_pct < 0 ? "value-negative" : undefined}>
            {formatPercent(result.growth_vs_baseline_pct)}
          </strong>
          <small>готовый процент API</small>
        </article>
        <article className="metric-card">
          <span>ROI</span>
          <strong>{result.roi === null ? "Не рассчитывается" : formatRatio(result.roi)}</strong>
          <small>{result.roi === null ? "стоимость равна нулю" : "gross lift / cost"}</small>
        </article>
        <article className="metric-card">
          <span>Risk score</span>
          <strong>{result.risk_score_pct === null ? "Не рассчитан" : formatPercent(result.risk_score_pct)}</strong>
          <small>доля клиентов с negative effect</small>
        </article>
        <article className="metric-card">
          <span>Охват</span>
          <strong>{formatPercent(result.coverage_pct)}</strong>
          <small>{formatInteger(result.unique_customers_targeted)} уникальных</small>
        </article>
        <article className="metric-card">
          <span>Пилоты</span>
          <strong>{formatInteger(result.n_pilots)}</strong>
          <small>наблюдения до финала</small>
        </article>
        <article className="metric-card">
          <span>Финальные кампании</span>
          <strong>{formatInteger(result.n_campaigns)}</strong>
          <small>пилоты не включены</small>
        </article>
      </div>

      <section className="result-section" aria-labelledby="resources-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">После всего прогона</p>
            <h3 id="resources-title">Остатки ресурсов</h3>
          </div>
          <span>{formatInteger(result.total_contacts)} контактов использовано</span>
        </div>
        <div className="resource-grid">
          <ResourceMeter label="Свободный бюджет" remaining={result.remaining_budget} total={budgetTotal} formatter={formatAmount} />
          <ResourceMeter label="Свободные контакты" remaining={result.remaining_contacts} total={contactsTotal} formatter={formatInteger} />
        </div>
      </section>

      <section className="result-section" aria-labelledby="pilots-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">Исследование</p>
            <h3 id="pilots-title">Пилотные наблюдения</h3>
          </div>
          <span className="count-badge">{result.pilots.length}</span>
        </div>
        <p className="section-note section-note--block">
          Observed lift зашумлён; остатки в строке относятся к моменту конкретного пилота.
        </p>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <caption className="sr-only">Пилотные наблюдения</caption>
            <thead>
              <tr>
                <th scope="col">Пилот</th>
                <th scope="col">Цель</th>
                <th scope="col">Канал</th>
                <th scope="col">Контакты</th>
                <th scope="col">Стоимость</th>
                <th scope="col">Observed lift</th>
                <th scope="col">Фильтры</th>
              </tr>
            </thead>
            <tbody><PilotRows pilots={result.pilots} /></tbody>
          </table>
        </div>
      </section>

      <section className="result-section" aria-labelledby="campaigns-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">Решение агента</p>
            <h3 id="campaigns-title">Финальные кампании</h3>
          </div>
          <span className="count-badge">{result.campaigns.length}</span>
        </div>
        {result.campaigns.length === 0 ? (
          <p className="empty-state">Финальный план отсутствует.</p>
        ) : (
          <div className="campaign-grid">
            {result.campaigns.map((campaign, index) => (
              <article className="campaign-card" key={`${campaign.campaign_name ?? "campaign"}-${index}`}>
                <div className="campaign-card__topline">
                  <span>Финал · {String(index + 1).padStart(2, "0")}</span>
                  <span className="channel-pill">{channelLabels[campaign.channel]}</span>
                </div>
                <h4>{campaign.campaign_name || `Кампания №${index + 1}`}</h4>
                <div className="campaign-card__route">
                  <span>Целевой тариф</span>
                  <strong>{campaign.target_tariff}</strong>
                </div>
                <FilterList filters={campaign} />
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="result-section" aria-labelledby="details-title">
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">Диагностика</p>
            <h3 id="details-title">Детализация evaluator</h3>
          </div>
        </div>
        <div className="no-sum-note">
          <strong>Не суммировать gross lift строк.</strong> Значения показаны до межкампанейской дедупликации; общий показатель находится в KPI выше.
        </div>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <caption className="sr-only">Детализация пилотов и финальных кампаний</caption>
            <thead>
              <tr>
                <th scope="col">Этап</th>
                <th scope="col">Название</th>
                <th scope="col">Канал</th>
                <th scope="col">Контакты</th>
                <th scope="col">Стоимость</th>
                <th scope="col">Gross до дедуп.</th>
                <th scope="col">Ограничения</th>
              </tr>
            </thead>
            <tbody><DetailRows details={result.campaigns_detail} /></tbody>
          </table>
        </div>
      </section>

      <section className="warnings-panel" aria-labelledby="warnings-title">
        <div>
          <p className="eyebrow">Контроль качества</p>
          <h3 id="warnings-title">Предупреждения</h3>
        </div>
        {result.warnings.length === 0 ? (
          <p className="empty-state empty-state--inline">Предупреждений нет.</p>
        ) : (
          <ul>
            {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        )}
      </section>
    </section>
  );
}
