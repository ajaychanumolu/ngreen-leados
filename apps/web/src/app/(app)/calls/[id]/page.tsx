"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BackLink } from "@/components/back-link";
import { Button } from "@/components/button";
import { CALL_SECTIONS, SectionNav } from "@/components/section-nav";
import { ApiRequestError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Rehearsal = {
  id: string;
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

export default function CallPage() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const [call, setCall] = useState<Rehearsal | null>(null);
  const [role, setRole] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    api<Rehearsal>(`/api/v1/calls/${params.id}`, token)
      .then(setCall)
      .catch((reason: Error) => setError(reason.message));
    api<{ role: string }>("/api/v1/me", token)
      .then((me) => setRole(me.role))
      .catch(() => setRole(""));
  }, [token, params.id]);

  const canReview = role === "owner_admin" || role === "sales_executive" || role === "manager";

  function review(action: "accept" | "reject") {
    if (!token) return;
    setBusy(true);
    setError(null);
    api<Rehearsal>(`/api/v1/calls/${params.id}/review`, token, {
      method: "POST",
      body: JSON.stringify({ action }),
    })
      .then((next) => {
        setCall(next);
        setBusy(false);
      })
      .catch((reason: Error) => {
        setError(reason instanceof ApiRequestError ? reason.message : "Review failed.");
        setBusy(false);
      });
  }

  if (!call) {
    return <p>{error ?? "Loading"}</p>;
  }

  return (
    <section className="max-w-3xl">
      <SectionNav label="Calls" items={CALL_SECTIONS} />
      <BackLink href="/calling/completed" label="Back to completed" />
      <p className="text-sm font-medium text-muted-foreground">
        {call.dialed ? "Dialed" : "Not dialed"} · {call.review_status}
      </p>
      <h1 className="mt-3 text-4xl font-bold">{call.company_name}</h1>
      <h2 className="mt-8 text-xl font-bold">Conversation</h2>
      <p className="mt-4 whitespace-pre-wrap rounded-xl bg-muted p-6 leading-7">{call.transcript}</p>
      <p className="mt-6 leading-8">{call.summary}</p>
      <p className="mt-4 text-sm text-muted-foreground">
        {call.outcome.replaceAll("_", " ")}
        {call.do_not_call ? " · do not call" : ""}
      </p>
      <p className="mt-6 leading-7">Suggested next step: {call.next_action}</p>
      {error ? (
        <p className="mt-6" role="alert">
          {error}
        </p>
      ) : null}
      {canReview && call.review_status === "pending" ? (
        <div className="mt-6 flex flex-wrap gap-3">
          <Button disabled={busy} onClick={() => review("accept")}>
            Move to CRM
          </Button>
          <Button tone="ink" disabled={busy} onClick={() => review("reject")}>
            Do not continue
          </Button>
        </div>
      ) : null}
      <p className="mt-8">
        <Link className="text-sm font-medium text-muted-foreground" href={`/accounts/${call.company_id}`}>
          Open account
        </Link>
      </p>
    </section>
  );
}
