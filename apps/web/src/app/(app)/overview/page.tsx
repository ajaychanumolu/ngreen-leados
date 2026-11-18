"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiRequestError, api, type ContactPage, type FunnelReport, type Overview } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type CallRow = { contact_id: string; outcome: string; review_status: string };

const STAGES = [
  ["research", "Research"],
  ["validated_account", "Validated"],
  ["outreach_eligible", "Outreach eligible"],
  ["contacted", "Contacted"],
  ["interested", "Interested"],
  ["meeting_scheduled", "Meeting"],
  ["sample_trial_requested", "Sample / trial"],
  ["quotation_sent", "Quotation"],
  ["negotiation", "Negotiation"],
  ["won", "Won"],
  ["lost", "Lost"],
  ["nurture", "Nurture"],
] as const;

const WORKS = new Set(["interested", "meeting_requested", "follow_up"]);
const STOPPED = new Set(["not_interested", "do_not_call", "wrong_number"]);

function bucket(call: CallRow) {
  if (call.review_status === "accepted") return "works";
  if (call.review_status === "rejected") return "stopped";
  if (WORKS.has(call.outcome)) return "works";
  if (STOPPED.has(call.outcome)) return "stopped";
  return "waiting";
}

export default function OverviewPage() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [report, setReport] = useState<FunnelReport | null>(null);
  const [ready, setReady] = useState<number | null>(null);
  const [calls, setCalls] = useState({ works: 0, stopped: 0, waiting: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api<Overview>("/api/v1/overview", token),
      api<FunnelReport>("/api/v1/reports/funnel", token).catch((reason: Error) =>
        reason instanceof ApiRequestError && reason.status === 403 ? null : Promise.reject(reason),
      ),
      api<CallRow[]>("/api/v1/calls", token).catch(() => [] as CallRow[]),
      api<ContactPage>("/api/v1/contacts?page_size=100", token).catch(() => null),
    ])
      .then(([summary, funnel, rehearsals, contacts]) => {
        setOverview(summary);
        setReport(funnel);
        const called = new Set(rehearsals.map((call) => call.contact_id));
        const waitingToCall =
          contacts?.items.filter(
            (contact) => (contact.email || contact.phone) && !contact.do_not_call && !called.has(contact.id),
          ).length ?? null;
        setReady(waitingToCall);
        setCalls({
          total: rehearsals.length,
          works: rehearsals.filter((call) => bucket(call) === "works").length,
          stopped: rehearsals.filter((call) => bucket(call) === "stopped").length,
          waiting: rehearsals.filter((call) => bucket(call) === "waiting").length,
        });
      })
      .catch((reason: Error) => setError(reason instanceof ApiRequestError ? reason.message : reason.message));
  }, [token]);

  const stageCount = new Map(report?.stages.map((stage) => [stage.stage, stage.count]) ?? []);
  const busiest = Math.max(1, ...[...stageCount.values()]);

  return (
    <section className="max-w-6xl">
      <h1 className="text-4xl font-bold leading-tight md:text-5xl">Home</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8">
        Leads, calls, and the pipeline in one place. Counts are stored rows. Nothing here is a forecast.
      </p>
      {error ? (
        <p className="mt-6" role="alert">
          {error}
        </p>
      ) : null}

      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat href="/accounts" label="Saved leads" value={overview?.accounts} hint="Research and hand entry" />
        <Stat href="/research" label="Waiting for review" value={overview?.research_candidates} hint="Search results not approved" />
        <Stat href="/calling/ready" label="Ready to call" value={ready} hint="Email or mobile, not called yet" />
        <Stat href="/crm" label="In CRM" value={overview?.opportunities} hint="Open pipeline rows" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-5">
        <div className="rounded-xl bg-muted p-5 lg:col-span-3">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-xl font-bold">Pipeline</h2>
            <Link href="/crm" className="text-sm text-muted-foreground">
              Open CRM
            </Link>
          </div>
          {report ? (
            <ul className="mt-5 grid gap-3">
              {STAGES.map(([stage, label]) => {
                const count = stageCount.get(stage) ?? 0;
                return (
                  <li key={stage} className="grid grid-cols-[8.5rem_1fr_2rem] items-center gap-3 text-sm">
                    <span>{label}</span>
                    <span className="h-2 overflow-hidden rounded-full bg-background">
                      <span
                        className="block h-2 rounded-full bg-[var(--brand)]"
                        style={{ width: count === 0 ? "0%" : `${Math.max(8, (count / busiest) * 100)}%` }}
                      />
                    </span>
                    <span className="text-right font-medium tabular-nums">{count}</span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="mt-5 text-sm text-muted-foreground">
              {overview ? "Pipeline counts are not available for this role." : "Loading"}
            </p>
          )}
        </div>

        <div className="grid gap-4 lg:col-span-2">
          <div className="rounded-xl bg-muted p-5">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="text-xl font-bold">Calls</h2>
              <Link href="/calling/completed" className="text-sm text-muted-foreground">
                Completed
              </Link>
            </div>
            <dl className="mt-5 grid grid-cols-3 gap-3">
              <Split label="Works" value={calls.works} href="/calling/completed" />
              <Split label="Does not work" value={calls.stopped} href="/calling/completed" />
              <Split label="Waiting" value={calls.waiting} href="/calling/completed" />
            </dl>
            <p className="mt-4 text-sm text-muted-foreground">
              {calls.total} saved {calls.total === 1 ? "call" : "calls"}. Works moves a lead to Contacted. Waiting means they did not lift the call. Nothing is dialed.
            </p>
          </div>
          <div className="rounded-xl bg-muted p-5">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="text-xl font-bold">Follow-ups</h2>
              <Link href="/tasks" className="text-sm text-muted-foreground">
                Open list
              </Link>
            </div>
            <dl className="mt-5 grid grid-cols-2 gap-3">
              <Split label="Open" value={report?.tasks_open ?? null} href="/tasks" />
              <Split label="Overdue" value={report?.tasks_overdue ?? null} href="/tasks" />
            </dl>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Stat href="/research" label="Approved leads" value={report?.candidates_approved ?? null} hint="A person approved the result" />
        <Stat href="/research" label="Search credits" value={report?.search_credits ?? null} hint="Provider units already spent" />
        <Stat href="/accounts" label="Reference targets" value={overview?.reference_targets ?? null} hint="Unverified hypotheses" />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Link href="/research" className="rounded-xl border border-border p-5">
          <h2 className="font-bold">Leads</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">Search for customers, or add a lead by hand.</p>
        </Link>
        <Link href="/calling" className="rounded-xl border border-border p-5">
          <h2 className="font-bold">Calls</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">Set how the agent talks, then call the leads that have contact information.</p>
        </Link>
        <Link href="/crm" className="rounded-xl border border-border p-5">
          <h2 className="font-bold">CRM</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">A call that works lands in Contacted. Later stages stay on the board.</p>
        </Link>
      </div>
    </section>
  );
}

function Stat({
  href,
  label,
  value,
  hint,
}: {
  href: string;
  label: string;
  value: number | null | undefined;
  hint: string;
}) {
  return (
    <Link href={href} className="rounded-xl bg-muted p-5">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-4xl font-bold tabular-nums">{value ?? "—"}</p>
      <p className="mt-2 text-sm text-muted-foreground">{hint}</p>
    </Link>
  );
}

function Split({ label, value, href }: { label: string; value: number | null; href: string }) {
  return (
    <Link href={href} className="rounded-xl bg-background p-3">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-2xl font-bold tabular-nums">{value ?? "—"}</dd>
    </Link>
  );
}
