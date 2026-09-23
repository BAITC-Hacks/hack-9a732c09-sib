import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import caseSummaryFixture from "../../../contracts/examples/case-summary.json";
import runCompletedFixture from "../../../contracts/examples/run-completed.json";

import type { CaseSummary, RunCompleted } from "../api/types";
import { CaseOverview } from "./CaseOverview";
import { RunResults } from "./RunResults";

describe("empty and nullable presentation", () => {
  it("renders explicit empty states for missing case collections", () => {
    const summary = structuredClone(
      caseSummaryFixture,
    ) as unknown as CaseSummary;
    summary.channels = [];
    summary.tariffs = [];
    summary.segments = {
      arpu_segment: [],
      data_segment: [],
      call_segment: [],
    };

    render(<CaseOverview summary={summary} />);

    expect(screen.getByText("Каналы отсутствуют.")).toBeInTheDocument();
    expect(screen.getByText("Тарифы отсутствуют.")).toBeInTheDocument();
    expect(screen.getAllByText("Нет данных о сегментах")).toHaveLength(3);
  });

  it("does not turn empty observations or nullable metrics into zeroes", () => {
    const result = structuredClone(
      runCompletedFixture,
    ) as unknown as RunCompleted;
    result.pilots = [];
    result.n_pilots = 0;
    result.campaigns_detail = [];
    result.warnings = [];
    result.roi = null;
    result.risk_score_pct = null;

    render(<RunResults result={result} />);

    expect(screen.getByText("Пилоты не проводились.")).toBeInTheDocument();
    expect(screen.getByText("Детализация отсутствует.")).toBeInTheDocument();
    expect(screen.getByText("Предупреждений нет.")).toBeInTheDocument();
    expect(screen.getByText("Не рассчитывается")).toBeInTheDocument();
    expect(screen.getByText("Не рассчитан")).toBeInTheDocument();
  });
});
