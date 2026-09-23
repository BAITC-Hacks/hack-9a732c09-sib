import type { CampaignFilters, ChannelName, Source } from "./api/types";

const numberFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

const preciseFormatter = new Intl.NumberFormat("ru-RU", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const compactFormatter = new Intl.NumberFormat("ru-RU", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  dateStyle: "medium",
  timeStyle: "medium",
});

export const channelLabels: Record<ChannelName, string> = {
  push: "Push",
  sms: "SMS",
  digital_ads: "Digital Ads",
  call: "Звонок",
};

export const sourceLabels: Record<Source, string> = {
  core: "Core metadata",
  mock_environment: "Mock environment",
  mock_fixture: "Демо-данные · fixture",
};

export function formatInteger(value: number): string {
  return numberFormatter.format(value);
}

export function formatDecimal(value: number): string {
  return preciseFormatter.format(value);
}

export function formatCompact(value: number): string {
  return compactFormatter.format(value);
}

export function formatAmount(value: number): string {
  return `${preciseFormatter.format(value)} ден. ед.`;
}

export function formatPercent(value: number): string {
  return `${preciseFormatter.format(value)}%`;
}

export function formatRatio(value: number): string {
  return `${preciseFormatter.format(value)}×`;
}

export function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

export function formatDuration(value: number): string {
  return value < 1_000
    ? `${preciseFormatter.format(value)} мс`
    : `${preciseFormatter.format(value / 1_000)} с`;
}

export function describeFilters(filters: CampaignFilters): string[] {
  const result: string[] = [];
  if (filters.filter_current_tariff) {
    result.push(`Текущий тариф: ${filters.filter_current_tariff}`);
  }
  if (filters.filter_arpu_segment) {
    result.push(`ARPU: ${filters.filter_arpu_segment}`);
  }
  if (filters.filter_data_segment) {
    result.push(`Данные: ${filters.filter_data_segment}`);
  }
  if (filters.filter_call_segment) {
    result.push(`Звонки: ${filters.filter_call_segment}`);
  }
  return result;
}
