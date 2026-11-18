"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button, actionClass, fieldClass } from "@/components/button";
import { CALL_SECTIONS, SectionNav } from "@/components/section-nav";
import { ApiRequestError, api, type Contact, type ContactPage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Script = { id: string; name: string; body: string; approved: boolean };

type Rehearsal = {
  id: string;
  contact_id: string;
  company_name: string;
  transcript: string;
  outcome: string;
  review_status: string;
  dialed: boolean;
};

const FILTERS = [
  ["all", "All"],
  ["works", "Works"],
  ["stopped", "Does not work"],
  ["waiting", "Waiting"],
] as const;

type Filter = (typeof FILTERS)[number][0];

function hasContact(contact: Contact) {
  return Boolean(contact.email || contact.phone) && !contact.do_not_call;
}

function splitConversation(transcript: string) {
  const matched = transcript.match(/^Agent:\s*([\s\S]*?)\n\nBuyer:\s*([\s\S]*)$/);
  if (!matched) {
    return { agent: "", buyer: transcript };
  }
  return { agent: matched[1].trim(), buyer: matched[2].trim() };
}

const WORKS = new Set(["interested", "meeting_requested", "follow_up"]);
const STOPPED = new Set(["not_interested", "do_not_call", "wrong_number"]);

function resultOf(call: Rehearsal): Filter {
  if (call.review_status === "accepted") return "works";
  if (call.review_status === "rejected") return "stopped";
  if (WORKS.has(call.outcome)) return "works";
  if (STOPPED.has(call.outcome)) return "stopped";
  return "waiting";
}

function attempt(script: string) {
  const agent = script.trim().slice(0, 900);
  return `Agent: ${agent}\n\nBuyer: No answer. They did not lift the call.`.slice(0, 2000);
}

export default function CallingPage() {
  const { token } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [againId, setAgainId] = useState("");
  const view = pathname.startsWith("/calling/ready")
    ? "ready"
    : pathname.startsWith("/calling/completed") || pathname.startsWith("/calls/")
      ? "completed"
      : "talk";
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [calls, setCalls] = useState<Rehearsal[]>([]);
  const [script, setScript] = useState<Script | null>(null);
  const [draft, setDraft] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [openId, setOpenId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [role, setRole] = useState("");

  function load(current: string) {
    Promise.all([
      api<ContactPage>("/api/v1/contacts?page_size=100", current),
      api<Rehearsal[]>("/api/v1/calls", current),
      api<Script[]>("/api/v1/calls/scripts", current),
      api<{ role: string }>("/api/v1/me", current),
    ])
      .then(([page, rehearsals, scripts, me]) => {
        setContacts(page.items);
        setCalls(rehearsals);
        setScript(scripts[0] ?? null);
        setDraft(scripts[0]?.body ?? "");
        setRole(me.role);
      })
      .catch((reason: Error) => setError(reason.message));
  }

  useEffect(() => {
    if (!token) return;
    load(token);
  }, [token]);

  useEffect(() => {
    const again = new URLSearchParams(window.location.search).get("again") ?? "";
    setAgainId(again);
    if (again) {
      setSelected([again]);
    }
  }, [pathname]);

  const canCall = role === "owner_admin" || role === "sales_executive" || role === "manager";
  const called = new Set(calls.map((call) => call.contact_id));
  const ready = contacts.filter((contact) => {
    if (!hasContact(contact)) return false;
    if (contact.id === againId) return true;
    return !called.has(contact.id);
  });
  const missing = contacts.filter((contact) => !contact.email && !contact.phone && !contact.do_not_call);
  const shown = calls.filter((call) => filter === "all" || resultOf(call) === filter);

  function toggle(id: string) {
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  async function saveScript() {
    if (!token || !script) return;
    setBusy(true);
    setError(null);
    try {
      const saved = await api<Script>(`/api/v1/calls/scripts/${script.id}`, token, {
        method: "PATCH",
        body: JSON.stringify({ body: draft }),
      });
      setScript(saved);
      setDraft(saved.body);
      setNotice("Talk settings saved.");
    } catch (reason) {
      setError(reason instanceof ApiRequestError ? reason.message : "The script was not saved.");
    } finally {
      setBusy(false);
    }
  }

  async function place(ids: string[]) {
    if (!token || ids.length === 0) return;
    if (draft.trim().length < 8) {
      setError("Save how the agent should talk before calling.");
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      for (const id of ids) {
        await api("/api/v1/calls/simulate", token, {
          method: "POST",
          body: JSON.stringify({
            contact_id: id,
            script_id: script?.id ?? null,
            transcript: attempt(draft),
          }),
        });
      }
      setSelected([]);
      setNotice(
        ids.length === 1
          ? "Filed as waiting. They did not lift the call, and nothing was dialed."
          : `${ids.length} leads filed as waiting. They did not lift the call, and nothing was dialed.`,
      );
      load(token);
      router.push("/calling/completed");
    } catch (reason) {
      setError(reason instanceof ApiRequestError ? reason.message : "The call was not saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="max-w-5xl">
      <h1 className="text-4xl font-bold leading-tight md:text-5xl">
        {view === "ready" ? "Ready to call" : view === "completed" ? "Completed" : "Talk settings"}
      </h1>
      <SectionNav label="Calls" items={CALL_SECTIONS} />
      <p className="mt-6 max-w-2xl text-lg leading-8">
        {view === "talk"
          ? "This is how the agent should talk. Saving it does not place a call."
          : view === "ready"
            ? "Leads from research or from a lead you added by hand. Each one here has an email or a mobile. Choose one or several, then call. The agent files Works, Does not work, or Waiting when they do not lift the call."
            : "Click a company to read that conversation. Works moves the lead to Contacted. Waiting means they did not lift the call. Nothing is dialed."}
      </p>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      {notice ? <p className="mt-4 text-sm text-muted-foreground">{notice}</p> : null}

      {view === "talk" ? (
        <div className="mt-8">
          <textarea
            className={`${fieldClass} min-h-36`}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={!canCall}
          />
          {canCall ? (
            <div className="mt-4">
              <Button type="button" disabled={busy || draft.trim().length < 8} onClick={() => void saveScript()}>
                Save talk settings
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}

      {view === "ready" ? (
      <div className="mt-8">
        {canCall ? (
          <div className="mt-4 flex flex-wrap gap-3">
            <Button type="button" disabled={busy || selected.length === 0} onClick={() => void place(selected)}>
              {selected.length > 1 ? `Call ${selected.length} leads` : "Call this lead"}
            </Button>
            <Button
              type="button"
              tone="ink"
              disabled={ready.length === 0}
              onClick={() => setSelected(ready.map((contact) => contact.id))}
            >
              Select all
            </Button>
          </div>
        ) : null}
        <ul className="mt-6 grid gap-3">
          {ready.map((contact) => (
            <li key={contact.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-muted p-4">
              <label className="flex items-start gap-3">
                {canCall ? (
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={selected.includes(contact.id)}
                    onChange={() => toggle(contact.id)}
                  />
                ) : null}
                <span>
                  <span className="block font-bold">{contact.company_name}</span>
                  <span className="text-sm text-muted-foreground">
                    {contact.email || "No email"}
                    {" · "}
                    {contact.phone || "No mobile"}
                    {" · "}
                    {contact.source_url ? "Research" : "Added by hand"}
                  </span>
                </span>
              </label>
              {canCall ? (
                <Button type="button" tone="ink" disabled={busy} onClick={() => setSelected([contact.id])}>
                  Choose
                </Button>
              ) : null}
            </li>
          ))}
          {ready.length === 0 ? (
            <li className="text-muted-foreground">
              No lead with an email or mobile is waiting here. Called leads are in Completed.
            </li>
          ) : null}
        </ul>
        {missing.length > 0 ? (
          <div className="mt-6">
            <h3 className="font-bold">No contact information</h3>
            <ul className="mt-3 grid gap-2">
              {missing.map((contact) => (
                <li key={contact.id} className="text-sm text-muted-foreground">
                  {contact.company_name} · add an email or a mobile on the lead
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {!canCall && role ? (
          <p className="mt-6">Your role can read calls and cannot start one.</p>
        ) : null}
      </div>
      ) : null}

      {view === "completed" ? (
      <div className="mt-8">
        <div className="mt-4 flex flex-wrap gap-2">
          {FILTERS.map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={filter === value ? actionClass() : actionClass("ink")}
              onClick={() => setFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <ul className="mt-6 grid gap-4">
          {shown.map((call) => {
            const spoken = splitConversation(call.transcript);
            const status = resultOf(call);
            const label = status === "works" ? "works" : status === "stopped" ? "does not work" : "waiting";
            return (
            <li key={call.id} className="rounded-xl bg-muted p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <button
                  type="button"
                  className="text-left font-bold"
                  aria-expanded={openId === call.id}
                  onClick={() => setOpenId((current) => (current === call.id ? null : call.id))}
                >
                  {call.company_name}
                </button>
                <p className="text-sm text-muted-foreground">
                  {label}
                  {call.dialed ? "" : " · not dialed"}
                </p>
              </div>
              {openId === call.id ? (
                <div className="mt-3 grid gap-3">
                  <div className="rounded-xl bg-background p-4">
                    <p className="text-sm font-medium text-muted-foreground">Agent</p>
                    <p className="mt-2 whitespace-pre-wrap leading-6">{spoken.agent || "The saved talk script was not stored on this call."}</p>
                  </div>
                  {status === "waiting" ? (
                    <p className="text-sm text-muted-foreground">They did not lift the call.</p>
                  ) : (
                    <div className="rounded-xl bg-background p-4">
                      <p className="text-sm font-medium text-muted-foreground">They said</p>
                      <p className="mt-2 whitespace-pre-wrap leading-6">{spoken.buyer}</p>
                    </div>
                  )}
                </div>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-3">
                {status === "works" ? (
                  <Link href="/crm" className="self-center text-sm text-muted-foreground">
                    In Contacted
                  </Link>
                ) : null}
                {status === "waiting" ? (
                  <Link href={`/calling/ready?again=${call.contact_id}`} className={actionClass("ink")}>
                    Call again
                  </Link>
                ) : null}
              </div>
            </li>
            );
          })}
          {shown.length === 0 ? <li className="text-muted-foreground">No calls in this filter.</li> : null}
        </ul>
      </div>
      ) : null}
    </section>
  );
}
