import { useId, useState, type FormEvent } from "react";

import type { MockScenario } from "../api/mockTransport";

interface RunLauncherProps {
  isMockMode: boolean;
  isBusy: boolean;
  scenario: MockScenario;
  onScenarioChange: (scenario: MockScenario) => void;
  onRun: (seed: number) => void;
}

const maxSeed = 4_294_967_295;

const scenarios: Array<{ value: MockScenario; label: string }> = [
  { value: "completed", label: "Успешный прогон" },
  { value: "instant", label: "Мгновенный результат" },
  { value: "zero-cost", label: "Нулевая стоимость / ROI null" },
  { value: "negative", label: "Отрицательный результат" },
  { value: "failed", label: "Ошибка выполнения" },
  { value: "http-error", label: "HTTP-ошибка" },
  { value: "timeout", label: "Тайм-аут (5 с в demo)" },
];

export function RunLauncher({
  isMockMode,
  isBusy,
  scenario,
  onScenarioChange,
  onRun,
}: RunLauncherProps) {
  const [seed, setSeed] = useState("42");
  const seedId = useId();
  const scenarioId = useId();
  const parsedSeed = Number(seed);
  const seedIsValid =
    seed.trim() !== "" &&
    Number.isSafeInteger(parsedSeed) &&
    parsedSeed >= 0 &&
    parsedSeed <= maxSeed;

  function submit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (seedIsValid) {
      onRun(parsedSeed);
    }
  }

  return (
    <form className="launcher" onSubmit={submit} noValidate>
      <div className="launcher__heading">
        <div>
          <p className="eyebrow">Новый эксперимент</p>
          <h2>Запустить агента</h2>
        </div>
        <span className="mode-pill">mode: mock</span>
      </div>

      <label className="field" htmlFor={seedId}>
        <span>Seed</span>
        <input
          id={seedId}
          name="seed"
          type="number"
          inputMode="numeric"
          min="0"
          max={String(maxSeed)}
          step="1"
          value={seed}
          aria-describedby={`${seedId}-hint`}
          aria-invalid={!seedIsValid}
          onChange={(event) => setSeed(event.target.value)}
        />
      </label>
      <p className={`field-hint ${seedIsValid ? "" : "field-hint--error"}`} id={`${seedId}-hint`}>
        {seedIsValid
          ? "Целое число от 0 до 4 294 967 295"
          : "Введите целое число в допустимом диапазоне."}
      </p>

      {isMockMode && (
        <label className="field" htmlFor={scenarioId}>
          <span>Fixture-сценарий</span>
          <select
            id={scenarioId}
            value={scenario}
            onChange={(event) =>
              onScenarioChange(event.target.value as MockScenario)
            }
          >
            {scenarios.map((item) => (
              <option value={item.value} key={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      )}

      <button className="primary-button" type="submit" disabled={isBusy || !seedIsValid}>
        <span>{isBusy ? "Идёт расчёт" : "Запустить прогон"}</span>
        <span aria-hidden="true">↗</span>
      </button>

      <p className="launcher__footnote">
        {isMockMode
          ? "Демонстрационные ответы из contracts/examples; это не score стратегии."
          : "Запрос будет отправлен в изолированную mock-среду backend."}
      </p>
    </form>
  );
}
