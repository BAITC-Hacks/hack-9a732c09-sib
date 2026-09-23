import type {
  CaseSummary,
  SegmentAggregate,
  SegmentAggregates,
} from "../api/types";
import {
  channelLabels,
  formatAmount,
  formatCompact,
  formatDecimal,
  formatInteger,
} from "../format";
import { SourceBadge } from "./SourceBadge";

interface CaseOverviewProps {
  summary: CaseSummary;
}

const segmentGroups: Array<{
  key: keyof SegmentAggregates;
  title: string;
  subtitle: string;
}> = [
  {
    key: "arpu_segment",
    title: "ARPU",
    subtitle: "Доходность абонента",
  },
  {
    key: "data_segment",
    title: "Data",
    subtitle: "Использование интернета",
  },
  {
    key: "call_segment",
    title: "Calls",
    subtitle: "Голосовая активность",
  },
];

function SegmentRows({ rows }: { rows: SegmentAggregate[] }) {
  if (rows.length === 0) {
    return (
      <tr>
        <td colSpan={3} className="table-empty">
          Нет данных о сегментах
        </td>
      </tr>
    );
  }

  return rows.map((row) => (
    <tr key={row.segment} className={row.segment === "UNKNOWN" ? "is-unknown" : undefined}>
      <th scope="row">
        {row.segment}
        {row.segment === "UNKNOWN" && (
          <span className="unknown-label" title="Пропуск в исходных данных">
            пропуск
          </span>
        )}
      </th>
      <td>{formatInteger(row.subscriber_count)}</td>
      <td>{formatAmount(row.baseline_total_arpu)}</td>
    </tr>
  ));
}

export function CaseOverview({ summary }: CaseOverviewProps) {
  const { constraints } = summary;

  return (
    <>
      <section className="overview panel" aria-labelledby="overview-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">01 · Контекст</p>
            <h2 id="overview-title">Синтетическая аудитория</h2>
          </div>
          <SourceBadge source={summary.source} />
        </div>

        <div className="metric-grid metric-grid--overview">
          <article className="metric-card metric-card--lead">
            <span>Абонентов</span>
            <strong title={formatInteger(summary.subscriber_count)}>
              {formatCompact(summary.subscriber_count)}
            </strong>
            <small>{formatInteger(summary.subscriber_count)} профилей</small>
          </article>
          <article className="metric-card">
            <span>Базовый ARPU</span>
            <strong title={formatAmount(summary.baseline_total_arpu)}>
              {formatCompact(summary.baseline_total_arpu)}
            </strong>
            <small>ден. ед., до кампаний</small>
          </article>
          <article className="metric-card">
            <span>Общий бюджет</span>
            <strong>{formatCompact(constraints.total_budget)}</strong>
            <small>{formatAmount(constraints.total_budget)}</small>
          </article>
          <article className="metric-card">
            <span>Лимит контактов</span>
            <strong>{formatCompact(constraints.max_total_contacts)}</strong>
            <small>пилоты + финальный план</small>
          </article>
        </div>

        <div className="constraint-strip" aria-label="Ограничения задачи">
          <div>
            <span>Пилоты</span>
            <strong>до {constraints.max_pilots}</strong>
          </div>
          <div>
            <span>Размер пилота</span>
            <strong>
              {constraints.min_pilot_customers}–{constraints.max_pilot_customers}
            </strong>
          </div>
          <div>
            <span>Финальные кампании</span>
            <strong>1–{constraints.max_campaigns}</strong>
          </div>
          <div>
            <span>На кампанию</span>
            <strong>до {formatInteger(constraints.max_customers_per_campaign)}</strong>
          </div>
        </div>
      </section>

      <section className="panel" aria-labelledby="channels-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">02 · Экономика контакта</p>
            <h2 id="channels-title">Доступные каналы</h2>
          </div>
          <p className="section-note">Цена и публичный multiplier</p>
        </div>

        {summary.channels.length === 0 ? (
          <p className="empty-state">Каналы отсутствуют.</p>
        ) : (
          <div className="channel-grid">
            {summary.channels.map((channel, index) => (
              <article className="channel-card" key={channel.name}>
                <div className="channel-card__index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </div>
                <h3>{channelLabels[channel.name]}</h3>
                <dl>
                  <div>
                    <dt>Контакт</dt>
                    <dd>{formatAmount(channel.cost_per_contact)}</dd>
                  </div>
                  <div>
                    <dt>Multiplier</dt>
                    <dd>{formatDecimal(channel.conversion_multiplier)}×</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel" aria-labelledby="segments-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">03 · Срезы</p>
            <h2 id="segments-title">Сегменты аудитории</h2>
          </div>
          <p className="section-note">
            UNKNOWN — пропуск, не фильтр кампании
          </p>
        </div>

        <div className="segment-grid">
          {segmentGroups.map((group) => (
            <div className="table-card" key={group.key}>
              <div className="table-card__heading">
                <h3>{group.title}</h3>
                <span>{group.subtitle}</span>
              </div>
              <div className="table-scroll" tabIndex={0}>
                <table>
                  <caption className="sr-only">Сегменты: {group.title}</caption>
                  <thead>
                    <tr>
                      <th scope="col">Сегмент</th>
                      <th scope="col">Абоненты</th>
                      <th scope="col">ARPU</th>
                    </tr>
                  </thead>
                  <tbody>
                    <SegmentRows rows={summary.segments[group.key]} />
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel" aria-labelledby="tariffs-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">04 · Каталог</p>
            <h2 id="tariffs-title">Тарифы</h2>
          </div>
          <span className="count-badge">{summary.tariffs.length}</span>
        </div>

        {summary.tariffs.length === 0 ? (
          <p className="empty-state">Тарифы отсутствуют.</p>
        ) : (
          <div className="tariff-grid">
            {summary.tariffs.map((tariff) => (
              <article className="tariff-card" key={tariff.tariff_plan_code}>
                <span>{tariff.tariff_plan_code.replace("tariff_", "T-")}</span>
                <strong>{formatAmount(tariff.price_tariff)}</strong>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
