/** Preview data for a Vercel walkthrough. Nothing here is a real buyer or a dialed call. */

const NOW = "2026-11-18T05:00:00Z";
const AGENT =
  "DEMO rehearsal only. N Green makes sustainable packaging for businesses that buy bags. Ask which product they use and whether they want a sample. Do not claim a number was dialed.";

type Account = {
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

type Contact = {
  id: string;
  company_id: string;
  company_name: string;
  display_name: string | null;
  role_title: string | null;
  email: string | null;
  phone: string | null;
  source_note: string;
  source_url: string | null;
  permission_basis: string;
  do_not_call: boolean;
};

type Call = {
  id: string;
  contact_id: string;
  company_id: string;
  company_name: string;
  transcript: string;
  outcome: string;
  summary: string;
  next_action: string;
  review_status: string;
  mode: string;
  dialed: boolean;
  do_not_call: boolean;
};

type Opportunity = {
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

const products = [
  { id: "prod-carry", name: "Carry Bags", company_count: 2 },
  { id: "prod-courier", name: "Courier Bags", company_count: 1 },
];

const industries = [
  { id: "ind-qc", name: "Q-Commerce / Quick Commerce", aliases: ["quick commerce"] },
  { id: "ind-pharma", name: "Pharma", aliases: ["pharmacy"] },
];

const accounts: Account[] = [
  account("demo-green", "DEMO Green Basket", "Pune", "research", 1, "Demo walkthrough"),
  account("demo-metro", "DEMO Metro Kitchen", "Bengaluru", "research", 1, "Demo walkthrough"),
  account("demo-lake", "DEMO Lake Pharmacy", "Hyderabad", "contacted", 1, "Demo walkthrough"),
  account("demo-hill", "DEMO Hill Stores", "Chennai", "research", 1, "Demo walkthrough"),
  account("ref-zepto", "Zepto", "India", "research", 0, "Reference target – not verified"),
  account("ref-blinkit", "Blinkit", "India", "research", 0, "Reference target – not verified"),
];

const contacts: Contact[] = [
  contact("c-green", "demo-green", "DEMO Green Basket", "buyer@green-basket.example", "+919000000001"),
  contact("c-metro", "demo-metro", "DEMO Metro Kitchen", "buyer@metro-kitchen.example", "+919000000002"),
  contact("c-lake", "demo-lake", "DEMO Lake Pharmacy", "buyer@lake-pharmacy.example", "+919000000003"),
  contact("c-hill", "demo-hill", "DEMO Hill Stores", "buyer@hill-stores.example", "+919000000004"),
];

const calls: Call[] = [
  call("call-metro", "c-metro", "demo-metro", "DEMO Metro Kitchen", "No answer. They did not lift the call.", "no_answer"),
  call(
    "call-lake",
    "c-lake",
    "demo-lake",
    "DEMO Lake Pharmacy",
    "Interested in Carry Bags and wants a sample next week.",
    "interested",
  ),
  call("call-hill", "c-hill", "demo-hill", "DEMO Hill Stores", "Not interested in packaging right now.", "not_interested"),
];

const opportunities: Opportunity[] = accounts.map((row) => ({
  id: `opp-${row.id}`,
  company_id: row.id,
  company_name: row.display_name,
  title: row.display_name,
  stage: row.stage ?? "research",
  value_inr: null,
  heuristic_note: null,
  review_label: row.review_label,
  updated_at: NOW,
}));

const runs: Record<string, unknown> = {};

export function mockEnabled() {
  if (process.env.NEXT_PUBLIC_MOCK === "true") return true;
  if (process.env.NEXT_PUBLIC_MOCK === "false") return false;
  return process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL;
}

export function mockApi(path: string, init: RequestInit = {}): unknown {
  const method = (init.method ?? "GET").toUpperCase();
  const url = path.split("?")[0];
  const body = typeof init.body === "string" ? (JSON.parse(init.body) as Record<string, unknown>) : {};

  if (method === "POST" && url === "/api/v1/auth/demo/login") {
    const email = String(body.email ?? "");
    const password = String(body.password ?? "");
    if (!email.endsWith("@ngreen.demo") || password !== "demo-pass") {
      throw new Error("That demo sign-in was not recognized.");
    }
    return { access_token: "mock-demo-token" };
  }

  if (url === "/health") {
    return {
      status: "ok",
      auth_mode: "demo",
      database: "mock",
      research_mode: "demo",
      worker: "inline",
      ai_mode: "mock",
      voice_mode: "disabled",
    };
  }
  if (url === "/api/v1/me") {
    return {
      user_id: "user-owner",
      email: "owner@ngreen.demo",
      display_name: "N Green owner",
      organization_id: "org-ngreen",
      organization_name: "N Green",
      role: "owner_admin",
      auth_mode: "demo",
    };
  }
  if (url === "/api/v1/overview") {
    return {
      accounts: accounts.length,
      reference_targets: accounts.filter((row) => row.review_label?.includes("not verified")).length,
      opportunities: opportunities.length,
      manual_contacts: contacts.length,
      research_candidates: 0,
      accounts_source: "preview",
      unavailable: [],
    };
  }
  if (url === "/api/v1/reports/funnel") {
    return funnel();
  }
  if (url === "/api/v1/products") return products;
  if (url === "/api/v1/industries") return industries;
  if (url === "/api/v1/members" || url === "/api/v1/team") {
    return [
      {
        id: "user-owner",
        user_id: "user-owner",
        email: "owner@ngreen.demo",
        display_name: "N Green owner",
        role: "owner_admin",
        open_tasks: 1,
        opportunities: opportunities.length,
      },
    ];
  }
  if (url === "/api/v1/contacts") {
    return { items: contacts, page: 1, page_size: 100, total: contacts.length };
  }
  if (url === "/api/v1/calls/scripts" && method === "GET") {
    return [{ id: "script-1", name: "DEMO buyer introduction", body: AGENT, approved: true }];
  }
  if (url.startsWith("/api/v1/calls/scripts/") && method === "PATCH") {
    return { id: "script-1", name: "DEMO buyer introduction", body: String(body.body ?? AGENT), approved: true };
  }
  if (url === "/api/v1/calls" && method === "GET") return calls;
  if (url === "/api/v1/calls/simulate" && method === "POST") return saveCall(body);
  if (url.startsWith("/api/v1/calls/") && method === "GET") {
    const found = calls.find((row) => row.id === url.split("/").pop());
    if (!found) throw new Error("Call not found.");
    return found;
  }
  if (url === "/api/v1/opportunities" && method === "GET") {
    return { items: opportunities, page: 1, page_size: 100, total: opportunities.length };
  }
  if (url.startsWith("/api/v1/opportunities/") && method === "PATCH") {
    const id = url.split("/")[4];
    const row = opportunities.find((item) => item.id === id);
    if (!row) throw new Error("Opportunity not found.");
    row.stage = String(body.to_stage ?? row.stage);
    const company = accounts.find((item) => item.id === row.company_id);
    if (company) company.stage = row.stage;
    return row;
  }
  if (url === "/api/v1/accounts" && method === "POST") return createAccount(body);
  if (url === "/api/v1/accounts" || url.startsWith("/api/v1/accounts?")) {
    return { items: accounts, page: 1, page_size: 100, total: accounts.length };
  }
  if (url.startsWith("/api/v1/accounts/") && method === "GET") return accountDetail(url.split("/")[4]);
  if (url === "/api/v1/contacts" && method === "POST") return addContact(body);
  if (url === "/api/v1/research/runs" && method === "GET") {
    return { items: Object.values(runs), total: Object.keys(runs).length };
  }
  if (url === "/api/v1/research/runs" && method === "POST") return createRun(body);
  if (url.startsWith("/api/v1/research/runs/")) return runs[url.split("/").pop() ?? ""] ?? emptyRun("missing");
  if (url === "/api/v1/tasks") {
    return {
      items: [
        {
          id: "task-1",
          title: "Follow up with DEMO Lake Pharmacy about a sample",
          status: "open",
          company_id: "demo-lake",
          due_on: "2026-11-25",
          owner_user_id: "user-owner",
          overdue: false,
          created_at: NOW,
        },
      ],
      page: 1,
      page_size: 100,
      total: 1,
    };
  }
  if (url.includes("/export")) return "display_name,city\nDEMO Green Basket,Pune\n";
  return method === "GET" ? [] : { ok: true };
}

function account(
  id: string,
  name: string,
  city: string,
  stage: string,
  contactCount: number,
  label: string,
): Account {
  return {
    id,
    display_name: name,
    normalized_name: name.toLowerCase(),
    city,
    state: null,
    country: "India",
    notes: "Preview row for the client walkthrough. Not a verified buyer.",
    source_origin: label.includes("not verified") ? "reference_sheet" : "manual",
    review_status: "pending",
    review_label: label,
    owner_user_id: "user-owner",
    owner_name: "N Green owner",
    industry_id: null,
    industry_name: null,
    tags: [],
    products: [],
    stage,
    contact_count: contactCount,
    created_at: NOW,
  };
}

function contact(id: string, companyId: string, companyName: string, email: string, phone: string): Contact {
  return {
    id,
    company_id: companyId,
    company_name: companyName,
    display_name: "Buyer desk",
    role_title: null,
    email,
    phone,
    source_note: "Preview contact. Not a real person.",
    source_url: null,
    permission_basis: "unknown",
    do_not_call: false,
  };
}

function call(
  id: string,
  contactId: string,
  companyId: string,
  companyName: string,
  buyer: string,
  outcome: string,
): Call {
  return {
    id,
    contact_id: contactId,
    company_id: companyId,
    company_name: companyName,
    transcript: `Agent: ${AGENT}\n\nBuyer: ${buyer}`,
    outcome,
    summary: buyer,
    next_action: outcome === "interested" ? "Prepare a sample." : "No further step in this preview.",
    review_status: "pending",
    mode: "demo",
    dialed: false,
    do_not_call: false,
  };
}

function funnel() {
  const stages = [
    "research",
    "validated_account",
    "outreach_eligible",
    "contacted",
    "interested",
    "meeting_scheduled",
    "sample_trial_requested",
    "quotation_sent",
    "negotiation",
    "won",
    "lost",
    "nurture",
  ].map((stage) => ({
    stage,
    count: opportunities.filter((row) => row.stage === stage).length,
    oldest_days: null,
  }));
  return {
    source: "preview",
    as_of: NOW,
    stages,
    candidates_stored: 0,
    candidates_pending: 0,
    candidates_approved: 0,
    candidates_rejected: 0,
    candidates_merged: 0,
    queries_ok: 0,
    results_stored: 0,
    known_skipped: 0,
    seller_skipped: 0,
    query_errors: 0,
    search_credits: 0,
    contact_search_credits: 0,
    model_tokens: 0,
    credits_per_stored_candidate: null,
    credits_per_approved_candidate: null,
    assessed: 0,
    average_fit: null,
    contradictions: 0,
    zero_fit: 0,
    rehearsals: calls.length,
    live_attempts: 0,
    calls_pending_review: calls.length,
    tasks_open: 1,
    tasks_overdue: 0,
    tasks_unassigned: 0,
    team: [],
    alerts: [],
    alerts_truncated: false,
    retry_queue: [],
    recent_spend: [],
    notes: ["Preview figures. No search was run and no number was dialed."],
  };
}

function saveCall(body: Record<string, unknown>) {
  const contact = contacts.find((row) => row.id === body.contact_id);
  if (!contact) throw new Error("Contact not found.");
  const transcript = String(body.transcript ?? "");
  const buyer = transcript.split("Buyer:")[1] ?? transcript;
  const low = buyer.toLowerCase();
  const outcome = low.includes("not interested")
    ? "not_interested"
    : low.includes("interested")
      ? "interested"
      : "no_answer";
  const saved = call(`call-${calls.length + 1}`, contact.id, contact.company_id, contact.company_name, buyer.trim(), outcome);
  calls.unshift(saved);
  if (outcome === "interested") {
    const opportunity = opportunities.find((row) => row.company_id === contact.company_id);
    const company = accounts.find((row) => row.id === contact.company_id);
    if (opportunity && !["contacted", "interested", "won"].includes(opportunity.stage)) {
      opportunity.stage = "contacted";
    }
    if (company) company.stage = opportunity?.stage ?? "contacted";
  }
  return saved;
}

function createAccount(body: Record<string, unknown>) {
  const name = String(body.display_name ?? "New lead");
  const row = account(`acc-${accounts.length + 1}`, name, String(body.city ?? ""), "research", 0, "Added in this preview");
  accounts.unshift(row);
  opportunities.unshift({
    id: `opp-${row.id}`,
    company_id: row.id,
    company_name: row.display_name,
    title: row.display_name,
    stage: "research",
    value_inr: null,
    heuristic_note: null,
    review_label: row.review_label,
    updated_at: NOW,
  });
  return row;
}

function addContact(body: Record<string, unknown>) {
  const company = accounts.find((row) => row.id === body.company_id);
  const row = contact(
    `c-${contacts.length + 1}`,
    String(body.company_id ?? ""),
    company?.display_name ?? "Lead",
    String(body.email ?? ""),
    String(body.phone ?? ""),
  );
  contacts.unshift(row);
  if (company) company.contact_count += 1;
  return row;
}

function accountDetail(id: string) {
  const row = accounts.find((item) => item.id === id);
  if (!row) throw new Error("Account not found.");
  return {
    ...row,
    needs: [],
    contacts: contacts.filter((item) => item.company_id === id),
    notes_log: [],
    opportunity_id: `opp-${id}`,
  };
}

function createRun(body: Record<string, unknown>) {
  const industry = industries.find((row) => row.id === body.industry_id);
  const run = emptyRun(`run-${Object.keys(runs).length + 1}`);
  run.geography = String(body.geography || "India");
  run.industry_filter = industry?.name ?? null;
  run.limit_companies = Number(body.limit_companies ?? 5);
  runs[String(run.id)] = run;
  return run;
}

function emptyRun(id: string) {
  return {
    id,
    status: "succeeded",
    mode: "demo",
    worker: "inline",
    geography: "India",
    product_name: "Carry Bags",
    industry_filter: null as string | null,
    limit_companies: 5,
    max_queries: 3,
    budget_credits: 5,
    spent_credits: 0,
    queries_total: 0,
    queries_done: 0,
    error_summary: "Preview only. This did not search the internet.",
    created_at: NOW,
    queries: [],
    candidates: [],
  };
}
