import type {
  Activity,
  AuditEntry,
  ConnectorStatus,
  Entity,
  Finding,
  GraphData,
  Investigation,
  InvestigationSummary,
  Report,
  WebFinding,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init);
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* respons bukan JSON */
    }
    throw new Error(msg);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export interface NewInvestigation {
  title: string;
  subject_name: string;
  purpose: string;
  demo: boolean;
  accounts: { platform: string; handle: string }[];
}

export const api = {
  listInvestigations: () => request<InvestigationSummary[]>("/investigations"),
  getInvestigation: (id: number) => request<Investigation>(`/investigations/${id}`),
  createInvestigation: (body: NewInvestigation) =>
    request<Investigation>("/investigations", json("POST", body)),
  deleteInvestigation: (id: number) =>
    request<void>(`/investigations/${id}`, { method: "DELETE" }),
  collect: (id: number, useAi = true) =>
    request<InvestigationSummary>(`/investigations/${id}/collect?use_ai=${useAi}`, {
      method: "POST",
    }),
  importFile: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ imported: number; skipped: number; errors: string[] }>(
      `/investigations/${id}/import`,
      { method: "POST", body: form },
    );
  },
  timeline: (id: number, params: Record<string, string | number | undefined>) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") q.set(k, String(v));
    return request<{ total: number; items: Activity[] }>(`/investigations/${id}/timeline?${q}`);
  },
  graph: (id: number) => request<GraphData>(`/investigations/${id}/graph`),
  affiliations: (id: number) => request<Finding[]>(`/investigations/${id}/affiliations`),
  webFindings: (id: number) => request<WebFinding[]>(`/investigations/${id}/web-findings`),
  report: (id: number) => request<Report>(`/investigations/${id}/report`),
  entities: () => request<Entity[]>("/entities"),
  createEntity: (body: Omit<Entity, "id">) => request<Entity>("/entities", json("POST", body)),
  deleteEntity: (id: number) => request<void>(`/entities/${id}`, { method: "DELETE" }),
  connectorStatus: () => request<ConnectorStatus>("/connectors/status"),
  audit: (investigationId?: number) =>
    request<AuditEntry[]>(`/audit${investigationId ? `?investigation_id=${investigationId}` : ""}`),
};
