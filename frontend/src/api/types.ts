export type Source = "core" | "mock_environment" | "mock_fixture";
export type RunStatus = "queued" | "running" | "completed" | "failed";
export type ChannelName = "push" | "sms" | "digital_ads" | "call";

export interface ApiErrorBody {
  code: string;
  message: string;
  details: string[];
}

export interface ErrorResponse {
  error: ApiErrorBody;
}

export interface Constraints {
  total_budget: number;
  max_total_contacts: number;
  max_pilots: number;
  min_pilot_customers: number;
  max_pilot_customers: number;
  max_campaigns: number;
  max_customers_per_campaign: number;
}

export interface Channel {
  name: ChannelName;
  cost_per_contact: number;
  conversion_multiplier: number;
}

export interface SegmentAggregate {
  segment: string;
  subscriber_count: number;
  baseline_total_arpu: number;
}

export interface SegmentAggregates {
  arpu_segment: SegmentAggregate[];
  data_segment: SegmentAggregate[];
  call_segment: SegmentAggregate[];
}

export interface Tariff {
  tariff_plan_code: string;
  price_tariff: number;
}

export interface CaseSummary {
  source: Source;
  subscriber_count: number;
  baseline_total_arpu: number;
  constraints: Constraints;
  channels: Channel[];
  segments: SegmentAggregates;
  tariffs: Tariff[];
  generated_at: string;
}

export interface CampaignFilters {
  filter_arpu_segment?: "LOW" | "MID" | "HIGH" | null;
  filter_data_segment?: "NON_USER" | "LITE" | "HEAVY" | null;
  filter_call_segment?: "LOW" | "MEDIUM" | "HIGH" | null;
  filter_current_tariff?: string | null;
}

export interface Campaign extends CampaignFilters {
  campaign_name?: string;
  target_tariff: string;
  channel: ChannelName;
}

export interface PilotObservation {
  pilot: string;
  target_tariff: string;
  channel: ChannelName;
  n_customers: number;
  cost: number;
  observed_lift_ratio: number;
  observed_lift_total: number;
  remaining_budget: number;
  remaining_contacts: number;
  filters: CampaignFilters;
}

export interface CampaignDetail {
  kind: "pilot" | "final";
  index: number;
  name: string;
  channel: ChannelName;
  cost: number;
  n_contacts: number;
  gross_lift: number;
  n_negative: number;
  capped_at_campaign_limit: boolean;
  capped_at_reach_budget: boolean;
  capped_at_money_budget: boolean;
}

export interface RunRequest {
  seed: number;
  mode: "mock";
}

export interface RunAccepted {
  run_id: string;
  status: RunStatus;
  created_at: string;
  source: Source;
}

export interface RunPending {
  run_id: string;
  status: "queued" | "running";
  created_at: string;
  source: Source;
}

export interface RunFailed {
  run_id: string;
  status: "failed";
  created_at: string;
  completed_at: string;
  source: Source;
  error: ApiErrorBody;
  warnings: string[];
}

export interface RunCompleted {
  run_id: string;
  status: "completed";
  source: Source;
  created_at: string;
  completed_at: string;
  baseline_total_arpu: number;
  gross_arpu_lift: number;
  total_cost: number;
  net_arpu_gain: number;
  total_arpu_after: number;
  growth_vs_baseline_pct: number;
  n_pilots: number;
  n_campaigns: number;
  total_contacts: number;
  unique_customers_targeted: number;
  coverage_pct: number;
  roi: number | null;
  risk_score_pct: number | null;
  remaining_budget: number;
  remaining_contacts: number;
  pilots: PilotObservation[];
  campaigns: Campaign[];
  campaigns_detail: CampaignDetail[];
  warnings: string[];
  duration_ms: number;
  error: null;
}

export type RunSnapshot = RunPending | RunCompleted | RunFailed;
export type TerminalRun = RunCompleted | RunFailed;

export interface ApiTransport {
  getCaseSummary(signal?: AbortSignal): Promise<CaseSummary>;
  createRun(request: RunRequest, signal?: AbortSignal): Promise<RunAccepted>;
  getRun(runId: string, signal?: AbortSignal): Promise<RunSnapshot>;
}
