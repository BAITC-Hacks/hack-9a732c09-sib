import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { AnalystApiClient } from "./api/client";
import { ApiError, RunPollingTimeoutError } from "./api/errors";
import type { MockScenario } from "./api/mockTransport";
import type {
  CaseSummary,
  RunAccepted,
  RunSnapshot,
  TerminalRun,
} from "./api/types";
import { CaseOverview } from "./components/CaseOverview";
import { RunLauncher } from "./components/RunLauncher";
import { RunResults } from "./components/RunResults";
import { RunStatus } from "./components/RunStatus";
import { SourceBadge } from "./components/SourceBadge";
import {
  createApiClient,
  readRuntimeConfig,
  type RuntimeConfig,
} from "./config";
import type { DisplayError, RunUiState } from "./runState";

type SummaryState =
  | { kind: "loading" }
  | { kind: "ready"; summary: CaseSummary }
  | { kind: "error"; error: DisplayError };

interface AppProps {
  client?: AnalystApiClient;
  runtimeConfig?: RuntimeConfig;
}

function isAbortError(error: unknown): boolean {
  return (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  );
}

function displayError(error: unknown, context: string): DisplayError {
  if (error instanceof ApiError) {
    return {
      title: context,
      message: error.message,
      code: error.code,
      status: error.status,
      details: error.details,
    };
  }
  if (error instanceof Error) {
    return {
      title: context,
      message: error.message,
      details: [],
    };
  }
  return {
    title: context,
    message: "Произошла неизвестная ошибка.",
    details: [],
  };
}

function SummarySkeleton() {
  return (
    <section className="panel skeleton-panel" aria-busy="true" aria-label="Загрузка обзора кейса">
      <span className="skeleton skeleton--label" />
      <span className="skeleton skeleton--title" />
      <div className="skeleton-grid">
        {Array.from({ length: 4 }, (_, index) => (
          <span className="skeleton skeleton--card" key={index} />
        ))}
      </div>
      <span className="sr-only">Загружаем данные кейса…</span>
    </section>
  );
}

export default function App({ client: injectedClient, runtimeConfig }: AppProps) {
  const config = useMemo(
    () => runtimeConfig ?? readRuntimeConfig(),
    [runtimeConfig],
  );
  const [scenario, setScenario] = useState<MockScenario>("completed");
  const client = useMemo(
    () => injectedClient ?? createApiClient(config, scenario),
    [config, injectedClient, scenario],
  );
  const [summaryState, setSummaryState] = useState<SummaryState>({ kind: "loading" });
  const [summaryReload, setSummaryReload] = useState(0);
  const [runState, setRunState] = useState<RunUiState>({ kind: "idle" });
  const runAbortRef = useRef<AbortController | null>(null);
  const runGenerationRef = useRef(0);

  useEffect(() => {
    const controller = new AbortController();
    setSummaryState({ kind: "loading" });
    client
      .getCaseSummary(controller.signal)
      .then((summary) => setSummaryState({ kind: "ready", summary }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setSummaryState({
            kind: "error",
            error: displayError(error, "Не удалось загрузить обзор кейса"),
          });
        }
      });
    return () => controller.abort();
  }, [client, summaryReload]);

  useEffect(
    () => () => {
      runGenerationRef.current += 1;
      runAbortRef.current?.abort();
    },
    [client],
  );

  const acceptUpdate = useCallback(
    (generation: number, update: RunUiState): void => {
      if (generation === runGenerationRef.current) {
        setRunState(update);
      }
    },
    [],
  );

  const applyAccepted = useCallback(
    (generation: number, accepted: RunAccepted): void => {
      acceptUpdate(generation, {
        kind: "polling",
        runId: accepted.run_id,
        lifecycleStatus: accepted.status,
        source: accepted.source,
      });
    },
    [acceptUpdate],
  );

  const applySnapshot = useCallback(
    (generation: number, snapshot: RunSnapshot): void => {
      if (snapshot.status === "completed") {
        acceptUpdate(generation, { kind: "completed", snapshot });
      } else if (snapshot.status === "failed") {
        acceptUpdate(generation, { kind: "failed", snapshot });
      } else {
        acceptUpdate(generation, {
          kind: "polling",
          runId: snapshot.run_id,
          lifecycleStatus: snapshot.status,
          source: snapshot.source,
        });
      }
    },
    [acceptUpdate],
  );

  const applyTerminal = useCallback(
    (generation: number, terminal: TerminalRun): void => {
      applySnapshot(generation, terminal);
    },
    [applySnapshot],
  );

  const handleFailure = useCallback(
    (generation: number, error: unknown, runId?: string): void => {
      if (isAbortError(error)) {
        return;
      }
      if (error instanceof RunPollingTimeoutError) {
        acceptUpdate(generation, {
          kind: "timeout",
          runId: error.runId,
          message: error.message,
        });
        return;
      }
      acceptUpdate(generation, {
        kind: "error",
        error: displayError(error, "API-запрос не выполнен"),
        ...(runId ? { runId } : {}),
      });
    },
    [acceptUpdate],
  );

  const startRun = useCallback(
    async (seed: number): Promise<void> => {
      runAbortRef.current?.abort();
      const controller = new AbortController();
      runAbortRef.current = controller;
      const generation = ++runGenerationRef.current;
      let acceptedRunId: string | undefined;
      setRunState({ kind: "submitting" });

      try {
        const terminal = await client.createAndPoll(
          { seed, mode: "mock" },
          {
            signal: controller.signal,
            onAccepted: (accepted) => {
              acceptedRunId = accepted.run_id;
              applyAccepted(generation, accepted);
            },
            onSnapshot: (snapshot) => applySnapshot(generation, snapshot),
          },
        );
        applyTerminal(generation, terminal);
      } catch (error: unknown) {
        handleFailure(generation, error, acceptedRunId);
      }
    },
    [applyAccepted, applySnapshot, applyTerminal, client, handleFailure],
  );

  const retryRun = useCallback(
    async (runId: string): Promise<void> => {
      runAbortRef.current?.abort();
      const controller = new AbortController();
      runAbortRef.current = controller;
      const generation = ++runGenerationRef.current;
      setRunState({
        kind: "polling",
        runId,
        lifecycleStatus: "running",
        source:
          summaryState.kind === "ready" ? summaryState.summary.source : "core",
      });

      try {
        const terminal = await client.pollRun(runId, {
          signal: controller.signal,
          onSnapshot: (snapshot) => applySnapshot(generation, snapshot),
        });
        applyTerminal(generation, terminal);
      } catch (error: unknown) {
        handleFailure(generation, error, runId);
      }
    },
    [applySnapshot, applyTerminal, client, handleFailure, summaryState],
  );

  function changeScenario(nextScenario: MockScenario): void {
    runGenerationRef.current += 1;
    runAbortRef.current?.abort();
    setRunState({ kind: "idle" });
    setScenario(nextScenario);
  }

  const isBusy = runState.kind === "submitting" || runState.kind === "polling";
  const currentSource =
    summaryState.kind === "ready" ? summaryState.summary.source : undefined;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="False Positive — наверх">
          <span className="brand__mark" aria-hidden="true">FP</span>
          <span>
            <strong>False Positive</strong>
            <small>Decision Lab</small>
          </span>
        </a>
        <div className="topbar__meta">
          {currentSource && <SourceBadge source={currentSource} />}
          <span className={`connection-pill ${config.useMocks ? "" : "connection-pill--live"}`}>
            {config.useMocks ? "Fixture transport" : "HTTP transport"}
          </span>
        </div>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="page-title">
          <div className="hero__copy">
            <p className="hero__kicker">
              <span aria-hidden="true">●</span> Тарифные кампании · аналитический стенд
            </p>
            <h1 id="page-title">
              Проверяем гипотезы.
              <span>Не выдаём шум за сигнал.</span>
            </h1>
            <p className="hero__lead">
              Управляемый запуск агента с прозрачными лимитами, пилотами и финальным планом — без переноса scoring-логики в браузер.
            </p>
          </div>
          <div className="hero__index" aria-hidden="true">
            <span>FP</span>
            <small>2026 / 09</small>
          </div>
        </section>

        <div className="workspace">
          <aside className="control-rail" aria-label="Управление запуском">
            <RunLauncher
              isMockMode={config.useMocks}
              isBusy={isBusy}
              scenario={scenario}
              onScenarioChange={changeScenario}
              onRun={(seed) => void startRun(seed)}
            />
            <RunStatus state={runState} onRetry={(runId) => void retryRun(runId)} />
          </aside>

          <div className="dashboard">
            {summaryState.kind === "loading" && <SummarySkeleton />}
            {summaryState.kind === "error" && (
              <section className="panel load-error" role="alert">
                <p className="eyebrow">Ошибка данных</p>
                <h2>{summaryState.error.title}</h2>
                <p>{summaryState.error.message}</p>
                <button className="secondary-button" type="button" onClick={() => setSummaryReload((value) => value + 1)}>
                  Повторить загрузку
                </button>
              </section>
            )}
            {summaryState.kind === "ready" && (
              <CaseOverview summary={summaryState.summary} />
            )}

            {runState.kind === "completed" && (
              <RunResults
                result={runState.snapshot}
                constraints={summaryState.kind === "ready" ? summaryState.summary.constraints : undefined}
              />
            )}

            {runState.kind === "failed" && (
              <section className="panel execution-failure" aria-labelledby="execution-failure-title">
                <p className="eyebrow">Terminal snapshot · failed</p>
                <h2 id="execution-failure-title">Стратегия не сформировала результат</h2>
                <p>{runState.snapshot.error.message}</p>
                <code>{runState.snapshot.error.code}</code>
                {runState.snapshot.warnings.length > 0 && (
                  <ul>
                    {runState.snapshot.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                )}
                <p className="failure-note">
                  Это сохранённый результат выполнения с HTTP 200, а не ошибка транспорта.
                </p>
              </section>
            )}
          </div>
        </div>
      </main>

      <footer>
        <span>False Positive · HackAlem</span>
        <span>API v1 · mock first · deterministic core</span>
      </footer>
    </div>
  );
}
