export type Platform = "instagram" | "threads" | "x" | "youtube";

export interface Account {
  id: number;
  platform: Platform;
  handle: string;
  external_id: string;
  display_name: string;
  bio: string;
  profile_url: string;
  links: string[];
  followers: number | null;
  following: number | null;
  verified: boolean;
  created_at_platform: string | null;
  error: string;
  activity_count: number;
}

export interface Stats {
  total: number;
  timezone: string;
  first?: string;
  last?: string;
  span_days?: number;
  avg_per_day?: number;
  active_days?: number;
  by_type?: Record<string, number>;
  by_platform?: Record<string, number>;
  by_hour?: number[];
  most_active_hour?: number;
  most_active_day?: string;
  daily?: { date: string; count: number }[];
  heatmap: number[][];
  days: string[];
}

export interface Indicator {
  key: string;
  label: string;
  value: number;
  display: string;
  level: "low" | "medium" | "high";
  description: string;
}

export interface Signals {
  indicators: Indicator[];
  overall: "low" | "medium" | "high" | "insufficient";
  note: string;
}

export interface TopInteraction {
  handle: string;
  weight: number;
  platforms: string[];
  kinds: Record<string, number>;
  entity: string | null;
}

export interface AISummary {
  summary: string;
  topics: { topic: string; share_percent: number; sentiment: string; example_urls: string[] }[];
  notable_activities: { url: string; reason: string }[];
  risk_notes: string[];
}

export interface Analysis {
  stats?: Stats;
  signals?: Signals;
  top_interactions?: TopInteraction[];
  ai?: AISummary | null;
  ai_research?: string | null;
  ai_caveats?: string[];
  ai_error?: string;
  ai_enabled?: boolean;
}

export interface InvestigationSummary {
  id: number;
  title: string;
  subject_name: string;
  purpose: string;
  demo: boolean;
  status: "new" | "running" | "done" | "error";
  status_detail: string;
  created_at: string;
  collected_at: string | null;
}

export interface Investigation extends InvestigationSummary {
  accounts: Account[];
  analysis: Analysis;
}

export interface Activity {
  id: number;
  platform: Platform;
  handle: string;
  type: string;
  text: string;
  url: string;
  created_at: string;
  targets: { handle: string; kind: string }[];
  links: string[];
  metrics: Record<string, unknown>;
  source: string;
}

export interface Evidence {
  type: string;
  detail: string;
  url: string;
}

export interface Finding {
  id: number;
  entity_name: string;
  category: string;
  confidence: number;
  method: "rule" | "ai";
  rationale: string;
  evidence: Evidence[];
}

export interface WebFinding {
  id: number;
  title: string;
  url: string;
  snippet: string;
}

export interface GraphNode {
  id: string;
  label: string;
  platform: string;
  is_subject: boolean;
  weight: number;
  community: number;
  entity: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: { source: string; target: string; weight: number; kinds: Record<string, number> }[];
  top: TopInteraction[];
}

export interface Entity {
  id: number;
  name: string;
  category: string;
  handles: string[];
  domains: string[];
  keywords: string[];
}

export interface ConnectorStatus {
  connectors: { platform: Platform; configured: boolean; limitations: string }[];
  ai: { configured: boolean; model: string };
  timezone: string;
}

export interface AuditEntry {
  id: number;
  investigation_id: number | null;
  action: string;
  detail: string;
  created_at: string;
}

export interface Report {
  generated_at: string;
  investigation: InvestigationSummary;
  accounts: Account[];
  stats: Stats;
  signals: Signals;
  top_interactions: TopInteraction[];
  graph: GraphData;
  findings: Finding[];
  web_findings: WebFinding[];
  ai: AISummary | null;
  ai_research: string | null;
  ai_caveats: string[];
  ai_error: string;
  recent_activities: Activity[];
  limitations: { platform: string; text: string }[];
}
