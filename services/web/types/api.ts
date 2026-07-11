export type Kpis = {
  active_calls: number;
  todays_calls: number;
  total_calls: number;
  average_duration_seconds: number;
  average_latency_ms: number;
  success_rate: number;
  failed_calls: number;
  live_sessions: number;
};

export type DashboardOverview = {
  kpis: Kpis;
  provider_usage: Record<string, number>;
  system_status: Record<string, string>;
  providers: Record<string, string>;
  roadmap: string[];
};

export type SeriesPoint = { name: string; value: number };
