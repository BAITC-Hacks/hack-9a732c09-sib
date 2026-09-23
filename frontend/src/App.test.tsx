import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { AnalystApiClient } from "./api/client";
import { MockTransport } from "./api/mockTransport";
import App from "./App";

const mockRuntime = {
  useMocks: true,
  apiBaseUrl: "http://localhost:8000",
};

function instantClient(
  scenario: "instant" | "zero-cost" | "negative" | "failed" = "instant",
) {
  return new AnalystApiClient(
    new MockTransport({ scenario, latencyMs: 0 }),
    { pollIntervalMs: 0 },
  );
}

describe("analyst dashboard", () => {
  it("labels fixture data, UNKNOWN segments, nullable risk, pilots and final plan", async () => {
    const user = userEvent.setup();
    render(<App client={instantClient("zero-cost")} runtimeConfig={mockRuntime} />);

    expect(screen.getByLabelText("Загрузка обзора кейса")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Синтетическая аудитория" })).toBeInTheDocument();
    expect(screen.getAllByText("Демо-данные · fixture").length).toBeGreaterThan(0);
    expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThan(0);
    expect(screen.getByText("UNKNOWN — пропуск, не фильтр кампании")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Запустить прогон/i }));

    expect(await screen.findByRole("heading", { name: "Финансовый результат положительный" })).toBeInTheDocument();
    expect(screen.getByText("Не рассчитан")).toBeInTheDocument();
    expect(screen.getByText("Не рассчитывается")).toBeInTheDocument();
    expect(screen.getByText("стоимость равна нулю")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Пилотные наблюдения" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Финальные кампании" })).toBeInTheDocument();
    expect(screen.getByText(/Не суммировать gross lift строк/)).toBeInTheDocument();
    expect(screen.getByText("пилоты не включены")).toBeInTheDocument();
  });

  it("presents negative net as a completed business outcome", async () => {
    const user = userEvent.setup();
    render(<App client={instantClient("negative")} runtimeConfig={mockRuntime} />);
    await screen.findByRole("heading", { name: "Синтетическая аудитория" });

    await user.click(screen.getByRole("button", { name: /Запустить прогон/i }));

    expect(await screen.findByRole("heading", { name: "Финансовый результат отрицательный" })).toBeInTheDocument();
    expect(screen.getByText(/расчёт технически завершён независимо от знака net/i)).toHaveTextContent("completed");
    expect(screen.queryByText("Стратегия не сформировала результат")).not.toBeInTheDocument();
  });

  it("distinguishes stored execution failure from an HTTP error", async () => {
    const user = userEvent.setup();
    render(<App client={instantClient("failed")} runtimeConfig={mockRuntime} />);
    await screen.findByRole("heading", { name: "Синтетическая аудитория" });

    await user.click(screen.getByRole("button", { name: /Запустить прогон/i }));

    expect(await screen.findByRole("heading", { name: "Стратегия не сформировала результат" })).toBeInTheDocument();
    expect(screen.getByText(/сохранённый результат выполнения с HTTP 200/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("RUN_FAILED").length).toBeGreaterThan(0));
  });
});
