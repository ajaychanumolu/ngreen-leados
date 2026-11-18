"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BackLink } from "@/components/back-link";
import { Button } from "@/components/button";
import { api, apiText, type FunnelReport } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ReportsPage() {
  const { token } = useAuth();
  const [report, setReport] = useState<FunnelReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api<FunnelReport>("/api/v1/reports/funnel", token)
      .then(setReport)
      .catch((reason: Error) => setError(reason.message));
  }, [token]);

  const max = Math.max(1, ...(report?.stages.map((stage) => stage.count) ?? [1]));
  const noOpportunities = report?.stages.every((stage) => stage.count === 0) ?? false;

  return (
    <section className="max-w-5xl">
      <BackLink href="/overview" label="Back to home" />
      <h1 className="text-4xl font-bold md:text-5xl">Reports</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8">
        These figures are queries on stored rows
        {report ? ` as of ${report.as_of}` : ""}. Credits are provider units. This screen does not
        estimate revenue or a purchase.
      </p>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      {!report && !error ? <p className="mt-10">Loading</p> : null}
      {report ? (
        <>
          <ul className="mt-6 max-w-2xl list-disc pl-5 text-sm leading-6">
            {report.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>

          <h2 className="mt-12 text-2xl font-bold">Pipeline</h2>
          {noOpportunities ? (
            <p className="mt-4 bg-muted rounded-xl p-6">No opportunities are stored.</p>
          ) : null}
          <ul className="mt-6 grid gap-4">
            {report.stages.map((stage) => (
              <li key={stage.stage}>
                <div className="flex items-baseline justify-between gap-4 text-sm">
                  <span className="font-medium">{stage.stage.replaceAll("_", " ")}</span>
                  <span>
                    {stage.count}
                    {stage.oldest_days === null ? "" : ` · oldest ${stage.oldest_days} days`}
                  </span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-chart-2"
                    style={{ width: `${(stage.count / max) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>

          <h2 className="mt-12 text-2xl font-bold">Research yield</h2>
          <div className="mt-6 grid gap-8 sm:grid-cols-3">
            <Figure label="Candidates stored" value={report.candidates_stored} />
            <Figure label="Approved by a person" value={report.candidates_approved} />
            <Figure label="Search credits" value={report.search_credits} />
          </div>
          <p className="mt-4 text-sm leading-6">
            Queries finished {report.queries_ok}. Candidates written on those queries{" "}
            {report.results_stored}. The candidate total above is what is still stored. Already
            known, left out {report.known_skipped}. Not a buyer, left out {report.seller_skipped}.
            Query errors {report.query_errors}. Contact-search credits{" "}
            {report.contact_search_credits}. Model tokens {report.model_tokens}. Pending{" "}
            {report.candidates_pending}. Rejected {report.candidates_rejected}. Merged{" "}
            {report.candidates_merged}.
          </p>
          <p className="mt-3 leading-7">
            {ratio(
              "Credits per stored candidate",
              report.credits_per_stored_candidate,
              "Not enough stored candidates to divide search credits.",
            )}
          </p>
          <p className="mt-2 leading-7">
            {ratio(
              "Credits per approved candidate",
              report.credits_per_approved_candidate,
              "Not enough approved candidates to divide search credits.",
            )}
          </p>

          <h2 className="mt-12 text-2xl font-bold">Lead quality</h2>
          {report.assessed === 0 ? (
            <p className="mt-4 bg-muted rounded-xl p-6">No fit scores are stored.</p>
          ) : (
            <p className="mt-4 leading-7">
              {report.assessed} assessments. Average fit {report.average_fit}. Contradictions{" "}
              {report.contradictions}. Fit of zero {report.zero_fit}. A fit score is a research
              priority, not a purchase.
            </p>
          )}

          <h2 className="mt-12 text-2xl font-bold">Calling</h2>
          <p className="mt-4 leading-7">
            Rehearsals {report.rehearsals}. Live attempts {report.live_attempts}. Waiting for review{" "}
            {report.calls_pending_review}. Open tasks {report.tasks_open}. Overdue{" "}
            {report.tasks_overdue}. Unassigned open tasks {report.tasks_unassigned}.
          </p>

          <h2 className="mt-12 text-2xl font-bold">Delivery</h2>
          {report.alerts.length === 0 ? (
            <p className="mt-4 bg-muted rounded-xl p-6">No delivery problems are stored.</p>
          ) : (
            <ul className="mt-4 grid gap-3">
              {report.alerts.map((alert) => (
                <li key={`${alert.kind}-${alert.entity_id}-${alert.summary}`} className="border-b border-border py-3">
                  <p className="text-sm font-medium text-muted-foreground">{alert.kind.replaceAll("_", " ")}</p>
                  <p>{alert.summary}</p>
                </li>
              ))}
            </ul>
          )}
          {report.alerts_truncated ? (
            <p className="mt-3 text-sm">Showing the first 40 problems.</p>
          ) : null}

          <h2 className="mt-12 text-2xl font-bold">Retry queue</h2>
          {report.retry_queue.length === 0 ? (
            <p className="mt-4 bg-muted rounded-xl p-6">No research run is waiting to be retried.</p>
          ) : (
            <ul className="mt-4 grid gap-3">
              {report.retry_queue.map((run) => (
                <li key={run.run_id} className="border-b border-border py-3">
                  <Link href={`/research/runs/${run.run_id}`} className="font-medium">
                    {run.status}
                  </Link>
                  <p className="text-sm">
                    {run.spent_credits} search credits on this run.
                    {run.error_summary ? ` ${run.error_summary}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}

          <h2 className="mt-12 text-2xl font-bold">Team</h2>
          <table className="mt-4 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 font-medium">Name</th>
                <th className="py-2 font-medium">Role</th>
                <th className="py-2 font-medium">Open tasks</th>
                <th className="py-2 font-medium">Opportunities</th>
              </tr>
            </thead>
            <tbody>
              {report.team.map((member) => (
                <tr key={member.user_id} className="border-b border-border">
                  <td className="py-2">{member.display_name}</td>
                  <td className="py-2">{member.role.replaceAll("_", " ")}</td>
                  <td className="py-2">{member.open_tasks}</td>
                  <td className="py-2">{member.opportunities}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 className="mt-12 text-2xl font-bold">Spend log</h2>
          {report.recent_spend.length === 0 ? (
            <p className="mt-4 bg-muted rounded-xl p-6">No provider usage is stored.</p>
          ) : (
            <ul className="mt-4 grid gap-2">
              {report.recent_spend.map((line) => (
                <li key={line.id} className="flex flex-wrap justify-between gap-3 border-b border-border py-2 text-sm">
                  <span className="font-medium">{line.kind.replaceAll("_", " ")}</span>
                  <span>
                    {line.units} · {line.mode} · {line.created_at.slice(0, 10)}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-10">
            <Button
              type="button"
              tone="ink"
              onClick={() => {
                if (!token) return;
                apiText("/api/v1/reports/export", token)
                  .then((text) => {
                    const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = "leados-report.csv";
                    link.click();
                    URL.revokeObjectURL(url);
                  })
                  .catch((reason: Error) => setError(reason.message));
              }}
            >
              Export CSV
            </Button>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Figure({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-4xl font-bold">{value}</p>
    </div>
  );
}

function ratio(label: string, value: number | null, empty: string) {
  return value === null ? empty : `${label}: ${value}.`;
}
