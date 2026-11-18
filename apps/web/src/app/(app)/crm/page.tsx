"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button, fieldClass } from "@/components/button";
import { CRM_SECTIONS, SectionNav } from "@/components/section-nav";
import { api, type Me, type Opportunity, type OpportunityPage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const STAGES = [
  ["research", "Research"],
  ["validated_account", "Validated account"],
  ["outreach_eligible", "Outreach eligible"],
  ["contacted", "Contacted"],
  ["interested", "Interested"],
  ["meeting_scheduled", "Meeting scheduled"],
  ["sample_trial_requested", "Sample / trial"],
  ["quotation_sent", "Quotation sent"],
  ["negotiation", "Negotiation"],
  ["won", "Won"],
  ["lost", "Lost"],
  ["nurture", "Nurture"],
] as const;

export default function CrmPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Opportunity[]>([]);
  const [total, setTotal] = useState(0);
  const [canMove, setCanMove] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load(activeToken: string) {
    api<OpportunityPage>("/api/v1/opportunities?page_size=100", activeToken)
      .then((page) => {
        setRows(page.items);
        setTotal(page.total);
      })
      .catch((reason: Error) => setError(reason.message));
  }

  useEffect(() => {
    if (!token) return;
    load(token);
    api<Me>("/api/v1/me", token)
      .then((me) => setCanMove(["owner_admin", "sales_executive", "manager"].includes(me.role)))
      .catch(() => setCanMove(false));
  }, [token]);

  return (
    <section>
      <h1 className="text-4xl font-bold md:text-5xl">Pipeline</h1>
      <SectionNav label="CRM" items={CRM_SECTIONS} />
      <p className="mt-4 max-w-2xl text-lg leading-8">
        A completed call that works moves the lead to Contacted. Outreach Eligible stays blocked
        until permission is recorded. Nothing is marked won from a call alone.
      </p>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      {total > rows.length ? (
        <p className="mt-4 text-sm">Showing {rows.length} of {total} opportunities.</p>
      ) : null}
      {!rows.length && !error ? <p className="mt-10">Loading</p> : null}
      <div className="mt-10 flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(([stage, label]) => {
          const cards = rows.filter((row) => row.stage === stage);
          return (
            <div key={stage} className="w-72 shrink-0 rounded-xl bg-muted p-3">
              <h2 className="text-sm font-medium text-muted-foreground">
                {label} · {cards.length}
              </h2>
              <ul className="mt-3 grid gap-3">
                {cards.map((card) => (
                  <li key={card.id} className="rounded-xl bg-card p-3 shadow-sm">
                    <Link href={`/accounts/${card.company_id}`} className="font-bold underline">
                      {card.company_name}
                    </Link>
                    {card.review_label ? <p className="mt-2 text-sm">{card.review_label}</p> : null}
                    {card.value_inr !== null ? (
                      <p className="mt-2 text-sm">Staff-entered value (INR) {card.value_inr}</p>
                    ) : null}
                    {card.heuristic_note ? (
                      <p className="mt-2 text-sm">Staff heuristic, not a forecast: {card.heuristic_note}</p>
                    ) : null}
                    {canMove ? (
                      <StageMove
                        opportunity={card}
                        onMoved={() => {
                          if (token) load(token);
                        }}
                      />
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function StageMove({ opportunity, onMoved }: { opportunity: Opportunity; onMoved: () => void }) {
  const { token } = useAuth();
  const [stage, setStage] = useState(opportunity.stage);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  return (
    <form
      className="mt-3 grid gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (!token) return;
        setError(null);
        api<Opportunity>(`/api/v1/opportunities/${opportunity.id}/stage`, token, {
          method: "PATCH",
          body: JSON.stringify({ to_stage: stage, reason }),
        })
          .then(() => {
            setReason("");
            onMoved();
          })
          .catch((reasonError: Error) => setError(reasonError.message));
      }}
    >
      <select className={fieldClass} value={stage} onChange={(event) => setStage(event.target.value)}>
        {STAGES.map(([value, label]) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>
      <input
        className={fieldClass}
        placeholder="Reason"
        value={reason}
        onChange={(event) => setReason(event.target.value)}
        minLength={3}
        required
      />
      {error ? <p role="alert" className="text-sm">{error}</p> : null}
      <Button type="submit" tone="ink">Move stage</Button>
    </form>
  );
}
