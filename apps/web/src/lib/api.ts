import { mockApi, mockEnabled } from "@/lib/mock-demo";

export type Health = {
  status: string;
  auth_mode: string;
  database: string;
  research_mode?: string;
  worker?: string;
  voice_mode?: string;
};

export type Me = {
  user_id: string;
  email: string;
  display_name: string;
  organization_id: string;
  organization_name: string;
  role: string;
  auth_mode: string;
};

export type Account = {
  id: string;
  display_name: string;
  normalized_name: string;
  city: string | null;
  state: string | null;
  country: string;
  notes: string | null;
  source_origin: string;
  review_status: string;
  review_label: string | null;
  owner_user_id: string | null;
  owner_name: string | null;
  industry_id: string | null;
  industry_name: string | null;
  tags: string[];
  products: string[];
  stage: string | null;
  contact_count: number;
  created_at: string;
};

export type Need = {
  id: string;
  product_name: string;
  need_status: string;
  evidence_note: string | null;
};

export type Contact = {
  id: string;
  company_id: string;
  company_name: string;
  display_name: string | null;
  role_title: string | null;
  email: string | null;
  phone: string | null;
  source_note: string;
  source_url?: string | null;
  permission_basis: string;
  do_not_call?: boolean;
  call_allowed?: boolean;
  call_reasons?: string[];
};

export type NoteEntry = {
  id: string;
  body: string;
  author_name: string;
  created_at: string;
};

export type AccountDetail = Account & {
  needs: Need[];
  contacts: Contact[];
  notes_log: NoteEntry[];
  opportunity_id: string | null;
};

export type Product = { id: string; name: string; company_count: number };
export type Industry = { id: string; name: string; aliases: string[] };
export type Member = { id: string; email: string; display_name: string; role: string };

export type Opportunity = {
  id: string;
  company_id: string;
  company_name: string;
  title: string;
  stage: string;
  value_inr: number | null;
  heuristic_note: string | null;
  review_label: string | null;
  updated_at: string;
};

export type OpportunityPage = {
  items: Opportunity[];
  page: number;
  page_size: number;
  total: number;
};

export type ImportRow = {
  row_number: number;
  status: string;
  display_name: string | null;
  message: string;
  match_id: string | null;
};

export type ImportPreview = {
  ready: number;
  errors: number;
  duplicates: number;
  rows: ImportRow[];
};

export type ImportCommit = {
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  rows: ImportRow[];
};

export type TaskItem = {
  id: string;
  title: string;
  status: string;
  company_id: string | null;
  due_on: string | null;
  owner_user_id: string | null;
  overdue: boolean;
  created_at: string;
};

export type TeamMember = {
  user_id: string;
  display_name: string;
  role: string;
};

export type FunnelReport = {
  source: string;
  as_of: string;
  stages: { stage: string; count: number; oldest_days: number | null }[];
  candidates_stored: number;
  candidates_pending: number;
  candidates_approved: number;
  candidates_rejected: number;
  candidates_merged: number;
  queries_ok: number;
  results_stored: number;
  known_skipped: number;
  seller_skipped: number;
  query_errors: number;
  search_credits: number;
  contact_search_credits: number;
  model_tokens: number;
  credits_per_stored_candidate: number | null;
  credits_per_approved_candidate: number | null;
  assessed: number;
  average_fit: number | null;
  contradictions: number;
  zero_fit: number;
  rehearsals: number;
  live_attempts: number;
  calls_pending_review: number;
  tasks_open: number;
  tasks_overdue: number;
  tasks_unassigned: number;
  team: (TeamMember & { open_tasks: number; opportunities: number })[];
  alerts: { kind: string; summary: string; entity_id: string }[];
  alerts_truncated: boolean;
  retry_queue: {
    run_id: string;
    status: string;
    error_summary: string | null;
    spent_credits: number;
  }[];
  recent_spend: { id: string; kind: string; units: number; mode: string; created_at: string }[];
  notes: string[];
};

export type TaskPage = { items: TaskItem[]; page: number; page_size: number; total: number };
export type ContactPage = { items: Contact[]; page: number; page_size: number; total: number };

export type AccountPage = {
  items: Account[];
  page: number;
  page_size: number;
  total: number;
};

export type ResearchSource = {
  id: string;
  provider: string;
  canonical_url: string;
  page_title: string;
  domain: string;
  snippet: string;
  retrieved_at: string;
};

export type ResearchAssessment = {
  fit_total: number;
  reasons: string[];
  industry_alignment: number;
  product_fit: number;
  operational_scale: number;
  geography_supply: number;
  buyer_relevant_evidence: number;
  source_freshness: number;
  contradiction: boolean;
  dropped_claims: number;
  provider: string;
  model_name: string;
  prompt_version: string;
  claims: { quote: string; kind: string }[];
};

export type ResearchCandidate = {
  id: string;
  display_name: string;
  canonical_domain: string | null;
  status: string;
  review_label: string;
  duplicate_company_id: string | null;
  company_id: string | null;
  plastic_items?: string[];
  snippet_emails?: string[];
  snippet_phones?: string[];
  sources: ResearchSource[];
  assessment: ResearchAssessment | null;
};

export type ResearchRun = {
  id: string;
  status: string;
  mode: string;
  worker: string;
  geography: string;
  product_name: string;
  industry_filter: string | null;
  limit_companies: number;
  max_queries: number;
  budget_credits: number;
  spent_credits: number;
  queries_total: number;
  queries_done: number;
  error_summary: string | null;
  created_at: string;
  queries: {
    id: string;
    position: number;
    query_text: string;
    status: string;
    result_count: number;
    known_skipped: number;
    seller_skipped?: number;
    error: string | null;
  }[];
  candidates: ResearchCandidate[];
};

export type Overview = {
  accounts: number;
  reference_targets: number;
  opportunities: number;
  manual_contacts: number;
  research_candidates: number;
  accounts_source: string;
  unavailable: string[];
};

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function api<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
  if (mockEnabled()) {
    return mockApi(path, init) as T;
  }
  const headers = new Headers(init.headers);
  if (init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers, cache: "no-store" });
  } catch {
    throw new ApiRequestError(0, "network", "The API is not reachable.");
  }
  const body = (await response.json().catch(() => ({}))) as { code?: string; message?: string };
  if (!response.ok) {
    throw new ApiRequestError(
      response.status,
      body.code ?? "error",
      body.message ?? "The request failed.",
    );
  }
  return body as T;
}

export async function apiText(path: string, token: string | null): Promise<string> {
  if (mockEnabled()) {
    return String(mockApi(path));
  }
  const headers = new Headers();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { headers, cache: "no-store" });
  } catch {
    throw new ApiRequestError(0, "network", "The API is not reachable.");
  }
  const text = await response.text();
  if (!response.ok) {
    let code = "error";
    let message = "The request failed.";
    try {
      const body = JSON.parse(text) as { code?: string; message?: string };
      code = body.code ?? code;
      message = body.message ?? message;
    } catch {
      message = "The request failed.";
    }
    throw new ApiRequestError(response.status, code, message);
  }
  return text;
}
