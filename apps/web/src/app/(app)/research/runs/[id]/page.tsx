"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BackLink } from "@/components/back-link";
import { Button } from "@/components/button";
import { LEAD_SECTIONS, SectionNav } from "@/components/section-nav";
import { ApiRequestError, api, type ResearchRun } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ResearchRunPage() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    let cancelled = false;
    api<ResearchRun>(`/api/v1/research/runs/${params.id}`, token)
      .then((next) => {
        if (!cancelled) {
          setRun(next);
        }
      })
      .catch((reason: Error) => {
        if (!cancelled) {
          setError(reason.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token, params.id]);

  const status = run?.status;
  useEffect(() => {
    if (!token || (status !== "queued" && status !== "running")) {
      return;
    }
    const timer = setInterval(() => {
      api<ResearchRun>(`/api/v1/research/runs/${params.id}`, token)
        .then(setRun)
        .catch((reason: Error) => setError(reason.message));
    }, 2000);
    return () => clearInterval(timer);
  }, [token, params.id, status]);

  async function act(path: string, body?: object) {
    if (!token) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api(path, token, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
      setRun(await api<ResearchRun>(`/api/v1/research/runs/${params.id}`, token));
    } catch (reason) {
      setError(reason instanceof ApiRequestError ? reason.message : "That action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!run) {
    return <p>{error ?? "Loading"}</p>;
  }

  const live = run.mode === "live";

  return (
    <section className="max-w-5xl">
      <SectionNav label="Leads" items={LEAD_SECTIONS} />
      <BackLink href="/research" label="Back to research" />
      <p className="text-sm font-medium text-muted-foreground">
        {live ? "Live search" : "DEMO search"} · {run.status}
      </p>
      <h1 className="mt-3 text-4xl font-bold leading-tight">
        {run.product_name} · {run.geography}
      </h1>
      <p className="mt-6 max-w-2xl leading-8">
        {live
          ? "Results are possible buyers of this packaging. Supplier and manufacturer pages are left out. A link is not proof of a purchase."
          : "These names and example.com links are fixtures. They are not businesses that buy packaging."}
        {run.industry_filter
          ? ` Industry “${run.industry_filter}” was only a search filter.`
          : " No industry was used as a search filter, and none is assigned to a candidate."}
      </p>
      <p className="mt-4 text-sm">
        Progress {run.queries_done}/{run.queries_total || run.max_queries} queries · {run.spent_credits} of{" "}
        {run.budget_credits} credits · worker {run.worker}
      </p>
      {run.error_summary ? (
        <p className="mt-4" role="alert">
          {run.error_summary}
        </p>
      ) : null}
      {error ? (
        <p className="mt-4" role="alert">
          {error}
        </p>
      ) : null}
      <div className="mt-6 flex flex-wrap gap-4">
        {run.status === "queued" || run.status === "running" ? (
          <Button tone="ink" disabled={busy} onClick={() => act(`/api/v1/research/runs/${run.id}/cancel`)}>
            Cancel
          </Button>
        ) : null}
        {run.status === "failed" || run.status === "cancelled" || run.status === "capped" ? (
          <Button disabled={busy} onClick={() => act(`/api/v1/research/runs/${run.id}/retry`)}>
            Retry
          </Button>
        ) : null}
        <Link href="/research" className="self-center text-sm font-medium text-muted-foreground">
          All runs
        </Link>
      </div>
      <h2 className="mt-12 text-2xl font-bold">Queries</h2>
      <ul className="mt-4 divide-y divide-border border-y border-border">
        {run.queries.map((query) => (
          <li key={query.id} className="py-4">
            <p className="font-bold">{query.query_text}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {query.status}
              {query.known_skipped ? ` · ${query.known_skipped} already stored` : ""}
              {query.seller_skipped ? ` · ${query.seller_skipped} not a buyer, left out` : ""}
              {query.error ? ` · ${query.error}` : ""}
            </p>
          </li>
        ))}
      </ul>
      <h2 className="mt-12 text-2xl font-bold">Candidates</h2>
      <ul className="mt-4 grid gap-6">
        {run.candidates.map((candidate) => (
          <li key={candidate.id} className="bg-muted rounded-xl p-6">
            <p className="text-sm font-medium text-muted-foreground">{candidate.review_label}</p>
            <h3 className="mt-2 text-2xl font-bold">{candidate.display_name}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{candidate.status}</p>
            {candidate.assessment ? (
              <div className="mt-4">
                <p className="font-bold">
                  Research priority {candidate.assessment.fit_total}/100 · {candidate.assessment.provider}
                </p>
                <p className="mt-1 text-sm">
                  This score cites stored snippets. It is not proof of a purchase.
                  {candidate.assessment.dropped_claims
                    ? ` ${candidate.assessment.dropped_claims} unsupported claim${candidate.assessment.dropped_claims === 1 ? "" : "s"} dropped.`
                    : ""}
                  {candidate.assessment.contradiction ? " Sources contradict a packaging claim." : ""}
                </p>
                <ul className="mt-3 list-disc pl-5">
                  {candidate.assessment.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
                {candidate.assessment.claims.length ? (
                  <ul className="mt-3 grid gap-2">
                    {candidate.assessment.claims.map((claim) => (
                      <li key={`${claim.kind}-${claim.quote}`} className="text-sm">
                        <span className="font-medium">{claim.kind}</span> “{claim.quote}”
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
            <p className="mt-4 text-sm">
              Plastic items in the page:{" "}
              {candidate.plastic_items?.length ? candidate.plastic_items.join(", ") : "none named"}
            </p>
            <p className="mt-1 text-sm">
              Email: {candidate.snippet_emails?.length ? candidate.snippet_emails.join(", ") : "not in the page"}
              {" · "}
              Mobile: {candidate.snippet_phones?.length ? candidate.snippet_phones.join(", ") : "not in the page"}
            </p>
            <ul className="mt-4 grid gap-3">
              {candidate.sources.map((source) => (
                <li key={source.id}>
                  <a className="font-bold underline" href={source.canonical_url} target="_blank" rel="noreferrer">
                    {source.page_title || source.canonical_url}
                  </a>
                  <p className="mt-1 text-sm">{source.domain}</p>
                  <p className="mt-1 leading-7">{source.snippet}</p>
                </li>
              ))}
            </ul>
            {candidate.status === "pending" ? (
              <div className="mt-4 flex flex-wrap gap-3">
                {candidate.duplicate_company_id ? (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      act(`/api/v1/research/candidates/${candidate.id}/review`, {
                        action: "merge",
                        target_company_id: candidate.duplicate_company_id,
                      })
                    }
                  >
                    Merge into existing account
                  </Button>
                ) : (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      act(`/api/v1/research/candidates/${candidate.id}/review`, { action: "approve" })
                    }
                  >
                    Add as unverified account
                  </Button>
                )}
                <Button
                  tone="ink"
                  disabled={busy}
                  onClick={() => act(`/api/v1/research/candidates/${candidate.id}/review`, { action: "reject" })}
                >
                  Reject
                </Button>
              </div>
            ) : null}
            {candidate.company_id ? (
              <Link href={`/accounts/${candidate.company_id}`} className="mt-4 inline-block text-sm font-medium text-muted-foreground">
                Open account
              </Link>
            ) : null}
          </li>
        ))}
        {run.candidates.length === 0 ? (
          <li>No new leads. Accounts and earlier search results were left out.</li>
        ) : null}
      </ul>
    </section>
  );
}
