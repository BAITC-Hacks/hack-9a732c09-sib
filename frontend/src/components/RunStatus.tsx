import { formatDate } from "../format";
import type { RunUiState } from "../runState";
import { SourceBadge } from "./SourceBadge";

interface RunStatusProps {
  state: RunUiState;
  onRetry: (runId: string) => void;
}

const statusLabels = {
  queued: "В очереди",
  running: "Выполняется",
  completed: "Результат готов — подтверждаем GET",
  failed: "Ошибка зафиксирована — получаем детали",
} as const;

function ProgressSteps({ state }: { state: RunUiState }) {
  const current =
    state.kind === "idle"
      ? 0
      : state.kind === "submitting"
        ? 1
        : state.kind === "polling"
          ? 2
          : 3;

  return (
    <ol className="run-steps" aria-label="Этапы запуска">
      {["Запрос", "Расчёт", "Результат"].map((label, index) => {
        const number = index + 1;
        const className =
          number < current
            ? "is-complete"
            : number === current
              ? "is-current"
              : "";
        return (
          <li className={className} key={label} aria-current={number === current ? "step" : undefined}>
            <span>{number < current ? "✓" : number}</span>
            {label}
          </li>
        );
      })}
    </ol>
  );
}

export function RunStatus({ state, onRetry }: RunStatusProps) {
  return (
    <section className="run-status" aria-labelledby="run-status-title">
      <div className="run-status__heading">
        <p className="eyebrow">Статус</p>
        <h2 id="run-status-title">Контур запуска</h2>
      </div>
      <ProgressSteps state={state} />

      <div className="run-status__body" aria-live="polite">
        {state.kind === "idle" && (
          <div className="status-copy">
            <span className="status-icon" aria-hidden="true">○</span>
            <div>
              <strong>Готов к запуску</strong>
              <p>Выберите seed и начните новый изолированный прогон.</p>
            </div>
          </div>
        )}

        {state.kind === "submitting" && (
          <div className="status-copy">
            <span className="spinner" aria-hidden="true" />
            <div>
              <strong>Отправляем POST</strong>
              <p>Ждём подтверждение 202 от API.</p>
            </div>
          </div>
        )}

        {state.kind === "polling" && (
          <>
            <div className="status-copy">
              <span className="spinner" aria-hidden="true" />
              <div>
                <strong>{statusLabels[state.lifecycleStatus]}</strong>
                <p>GET повторяется до terminal snapshot.</p>
              </div>
            </div>
            <dl className="run-meta">
              <div>
                <dt>Run ID</dt>
                <dd title={state.runId}>{state.runId}</dd>
              </div>
              <div>
                <dt>Источник</dt>
                <dd><SourceBadge source={state.source} /></dd>
              </div>
            </dl>
          </>
        )}

        {state.kind === "completed" && (
          <>
            <div className="status-copy status-copy--success">
              <span className="status-icon" aria-hidden="true">✓</span>
              <div>
                <strong>Прогон завершён</strong>
                <p>{formatDate(state.snapshot.completed_at)}</p>
              </div>
            </div>
            <SourceBadge source={state.snapshot.source} />
          </>
        )}

        {state.kind === "failed" && (
          <div className="status-copy status-copy--error" role="alert">
            <span className="status-icon" aria-hidden="true">!</span>
            <div>
              <strong>Выполнение завершилось ошибкой</strong>
              <p>{state.snapshot.error.message}</p>
              <code>{state.snapshot.error.code}</code>
            </div>
          </div>
        )}

        {state.kind === "timeout" && (
          <div className="status-copy status-copy--warning" role="alert">
            <span className="status-icon" aria-hidden="true">⌛</span>
            <div>
              <strong>Превышено время ожидания</strong>
              <p>{state.message}</p>
              <button className="text-button" type="button" onClick={() => onRetry(state.runId)}>
                Повторить GET этого запуска
              </button>
            </div>
          </div>
        )}

        {state.kind === "error" && (
          <div className="status-copy status-copy--error" role="alert">
            <span className="status-icon" aria-hidden="true">!</span>
            <div>
              <strong>{state.error.title}</strong>
              <p>{state.error.message}</p>
              {(state.error.status || state.error.code) && (
                <code>
                  {state.error.status ? `HTTP ${state.error.status}` : ""}
                  {state.error.status && state.error.code ? " · " : ""}
                  {state.error.code}
                </code>
              )}
              {state.error.details.length > 0 && (
                <ul>
                  {state.error.details.map((detail) => <li key={detail}>{detail}</li>)}
                </ul>
              )}
              {state.runId && (
                <button className="text-button" type="button" onClick={() => onRetry(state.runId!)}>
                  Повторить GET этого запуска
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
