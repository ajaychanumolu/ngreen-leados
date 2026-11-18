"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AccountForm } from "@/components/account-form";
import { BackLink } from "@/components/back-link";
import { Button, fieldClass } from "@/components/button";
import { LEAD_SECTIONS, SectionNav } from "@/components/section-nav";
import {
  api,
  type AccountDetail,
  type Industry,
  type Me,
  type Member,
  type Need,
  type Product,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

const NEED_STATUS = [
  ["hypothesis", "Hypothesis"],
  ["publicly_evidenced", "Publicly evidenced"],
  ["buyer_confirmed", "Buyer confirmed"],
  ["rejected", "Rejected"],
] as const;

export default function AccountDetailPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [account, setAccount] = useState<AccountDetail | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [canWrite, setCanWrite] = useState(false);
  const [canResearch, setCanResearch] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tag, setTag] = useState("");
  const [productName, setProductName] = useState("");
  const [note, setNote] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactNote, setContactNote] = useState("");
  const [permission, setPermission] = useState("unknown");

  const load = useCallback(
    (activeToken: string) => {
      api<AccountDetail>(`/api/v1/accounts/${params.id}`, activeToken)
        .then(setAccount)
        .catch((reason: Error) => setError(reason.message));
    },
    [params.id],
  );

  useEffect(() => {
    if (!token) {
      return;
    }
    load(token);
    api<Me>("/api/v1/me", token)
      .then((me) => {
        setCanWrite(me.role !== "read_only");
        setCanResearch(me.role === "owner_admin" || me.role === "researcher" || me.role === "manager");
      })
      .catch(() => setCanWrite(false));
    api<Product[]>("/api/v1/products", token).then(setProducts).catch(() => setProducts([]));
    api<Industry[]>("/api/v1/industries", token).then(setIndustries).catch(() => setIndustries([]));
    api<Member[]>("/api/v1/members", token).then(setMembers).catch(() => setMembers([]));
  }, [token, load]);

  async function patch(extra: Record<string, unknown>) {
    if (!token || !account) return;
    setPending(true);
    setError(null);
    try {
      const updated = await api<AccountDetail>(`/api/v1/accounts/${account.id}`, token, {
        method: "PATCH",
        body: JSON.stringify({
          display_name: account.display_name,
          city: account.city,
          state: account.state,
          notes: account.notes,
          ...extra,
        }),
      });
      setAccount(updated);
      setSaved(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Save failed.");
    } finally {
      setPending(false);
    }
  }

  if (error && !account) {
    return <p role="alert">{error}</p>;
  }
  if (!account) {
    return <p>Loading</p>;
  }

  return (
    <section className="max-w-3xl">
      <SectionNav label="Leads" items={LEAD_SECTIONS} />
      <BackLink href="/accounts" label="Back to saved leads" />
      {account.review_label ? (
        <p className="bg-muted px-4 py-3 text-sm font-bold">{account.review_label}</p>
      ) : null}
      <p className="mt-4 text-sm text-muted-foreground">
        {account.source_origin.replaceAll("_", " ")} · review {account.review_status}
        {account.stage ? ` · ${account.stage.replaceAll("_", " ")}` : ""}
      </p>
      <h1 className="mt-3 text-4xl font-bold">{account.display_name}</h1>
      <p className="mt-4 leading-7">
        {account.city ?? "City not set"}
        {account.state ? `, ${account.state}` : ""} · {account.country}
      </p>
      <p className="mt-2 text-sm">
        Industry: {account.industry_name ?? "Unassigned"}. Owner: {account.owner_name ?? "Unassigned"}.
      </p>
      {canWrite ? (
        <AccountForm
          initial={account}
          pending={pending}
          error={error}
          submitLabel="Save changes"
          onSubmit={async (values) => {
            if (!token) return;
            setPending(true);
            setSaved(false);
            setError(null);
            try {
              const updated = await api<AccountDetail>(`/api/v1/accounts/${account.id}`, token, {
                method: "PATCH",
                body: JSON.stringify(values),
              });
              setAccount(updated);
              setSaved(true);
            } catch (reason) {
              setError(reason instanceof Error ? reason.message : "Save failed.");
            } finally {
              setPending(false);
            }
          }}
        />
      ) : (
        <p className="mt-8">Your role can view this account and cannot edit it.</p>
      )}
      {saved ? <p className="mt-4">Saved.</p> : null}

      {canWrite ? (
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <label className="grid gap-2 text-sm">
            Industry
            <select
              className={fieldClass}
              value={account.industry_id ?? ""}
              onChange={(event) => void patch({ industry_id: event.target.value || null })}
            >
              <option value="">Unassigned</option>
              {industries.map((industry) => (
                <option key={industry.id} value={industry.id}>
                  {industry.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            Owner
            <select
              className={fieldClass}
              value={account.owner_user_id ?? ""}
              onChange={(event) => void patch({ owner_user_id: event.target.value || null })}
            >
              <option value="">Unassigned</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      <h2 className="mt-12 text-2xl font-bold">Tags</h2>
      <p className="mt-2">{account.tags.length ? account.tags.join(", ") : "No tags."}</p>
      {canWrite ? (
        <form
          className="mt-4 flex flex-wrap gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token || !tag.trim()) return;
            setPending(true);
            api<AccountDetail>(`/api/v1/accounts/${account.id}/tags`, token, {
              method: "POST",
              body: JSON.stringify({ tag }),
            })
              .then((updated) => {
                setAccount(updated);
                setTag("");
              })
              .catch((reason: Error) => setError(reason.message))
              .finally(() => setPending(false));
          }}
        >
          <input className={`${fieldClass} max-w-xs`} value={tag} onChange={(event) => setTag(event.target.value)} placeholder="Tag" />
          <Button type="submit" tone="ink" disabled={pending}>Add tag</Button>
        </form>
      ) : null}

      <h2 className="mt-12 text-2xl font-bold">Product needs</h2>
      <p className="mt-2 leading-7">
        A hypothesis stays a hypothesis until someone records a source. Empty sheet categories can
        still be added by hand.
      </p>
      <ul className="mt-6 grid gap-4">
        {account.needs.map((need) => (
          <li key={need.id} className="bg-muted rounded-xl p-4">
            <NeedEditor
              need={need}
              canWrite={canWrite}
              onSave={async (needStatus, evidence) => {
                if (!token) return;
                const updated = await api<Need>(
                  `/api/v1/accounts/${account.id}/product-needs/${need.id}`,
                  token,
                  {
                    method: "PATCH",
                    body: JSON.stringify({ need_status: needStatus, evidence_note: evidence }),
                  },
                );
                setAccount({
                  ...account,
                  needs: account.needs.map((item) => (item.id === updated.id ? updated : item)),
                });
              }}
            />
          </li>
        ))}
      </ul>
      {canWrite ? (
        <form
          className="mt-4 flex flex-wrap items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token || !productName) return;
            api<Need>(`/api/v1/accounts/${account.id}/product-needs`, token, {
              method: "POST",
              body: JSON.stringify({ product_name: productName }),
            })
              .then(() => load(token))
              .catch((reason: Error) => setError(reason.message));
          }}
        >
          <label className="grid gap-2 text-sm">
            Add product
            <select className={fieldClass} value={productName} onChange={(event) => setProductName(event.target.value)}>
              <option value="">Select</option>
              {products.map((product) => (
                <option key={product.id} value={product.name}>{product.name}</option>
              ))}
            </select>
          </label>
          <Button type="submit" tone="ink">Add product</Button>
        </form>
      ) : null}

      <h2 className="mt-12 text-2xl font-bold">Contacts</h2>
      <p className="mt-2 leading-7">
        Only an email or mobile your team types in, or one found on an official page, appears here.
        A public address is not permission to call.
      </p>
      {account.contacts.length === 0 ? <p className="mt-4">No contacts yet.</p> : null}
      <ul className="mt-4 grid gap-3">
        {account.contacts.map((contact) => (
          <li key={contact.id} className="border border-border p-4">
            <p className="font-bold">{contact.display_name ?? contact.email ?? contact.phone}</p>
            <p className="text-sm">
              {contact.email ?? "No email"}
              {" · "}
              {contact.phone ?? "No mobile"}
            </p>
            <p className="text-sm">
              Permission: {contact.permission_basis.replaceAll("_", " ")}
              {contact.do_not_call ? " · do not call" : ""}
            </p>
            <p className="mt-1 text-sm">{contact.source_note}</p>
            {contact.source_url ? (
              <a className="text-sm underline" href={contact.source_url}>
                Source page
              </a>
            ) : null}
          </li>
        ))}
      </ul>
      {canResearch ? (
        <div className="mt-4">
          <Button
            type="button"
            tone="ink"
            disabled={pending}
            onClick={() => {
              if (!token) return;
              setPending(true);
              setError(null);
              setNotice(null);
              api<{ message: string }>(`/api/v1/contacts/discover`, token, {
                method: "POST",
                body: JSON.stringify({ company_id: account.id }),
              })
                .then((result) => {
                  setNotice(result.message);
                  load(token);
                })
                .catch((reason: Error) => setError(reason.message))
                .finally(() => setPending(false));
            }}
          >
            Find public email and mobile
          </Button>
          {notice ? <p className="mt-3 text-sm">{notice}</p> : null}
        </div>
      ) : null}
      {canWrite ? (
        <form
          className="mt-4 grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token) return;
            api(`/api/v1/contacts`, token, {
              method: "POST",
              body: JSON.stringify({
                company_id: account.id,
                display_name: contactName || null,
                email: contactEmail.trim() || null,
                phone: contactPhone.trim() || null,
                source_note: contactNote,
                permission_basis: permission,
              }),
            })
              .then(() => {
                setContactName("");
                setContactEmail("");
                setContactPhone("");
                setContactNote("");
                setPermission("unknown");
                load(token);
              })
              .catch((reason: Error) => setError(reason.message));
          }}
        >
          <input className={fieldClass} placeholder="Name you already know" value={contactName} onChange={(event) => setContactName(event.target.value)} />
          <input className={fieldClass} type="email" placeholder="Email" value={contactEmail} onChange={(event) => setContactEmail(event.target.value)} />
          <input className={fieldClass} placeholder="Mobile" value={contactPhone} onChange={(event) => setContactPhone(event.target.value)} />
          <textarea className={`${fieldClass} min-h-24`} placeholder="How your team knows this person" value={contactNote} onChange={(event) => setContactNote(event.target.value)} required minLength={3} />
          <select className={fieldClass} value={permission} onChange={(event) => setPermission(event.target.value)}>
            <option value="unknown">Permission unknown</option>
            <option value="recorded_consent">Recorded consent</option>
            <option value="existing_business_relationship">Existing business relationship</option>
          </select>
          <div><Button type="submit" tone="ink">Add contact</Button></div>
        </form>
      ) : null}

      <h2 className="mt-12 text-2xl font-bold">Notes</h2>
      <ul className="mt-4 grid gap-3">
        {account.notes_log.map((entry) => (
          <li key={entry.id}>
            <p>{entry.body}</p>
            <p className="text-sm">{entry.author_name}</p>
          </li>
        ))}
      </ul>
      {canWrite ? (
        <form
          className="mt-4 grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token || !note.trim()) return;
            api(`/api/v1/accounts/${account.id}/notes`, token, {
              method: "POST",
              body: JSON.stringify({ body: note }),
            })
              .then(() => {
                setNote("");
                load(token);
              })
              .catch((reason: Error) => setError(reason.message));
          }}
        >
          <textarea className={`${fieldClass} min-h-24`} value={note} onChange={(event) => setNote(event.target.value)} />
          <div><Button type="submit" tone="ink">Add note</Button></div>
        </form>
      ) : null}
    </section>
  );
}

function NeedEditor({
  need,
  canWrite,
  onSave,
}: {
  need: Need;
  canWrite: boolean;
  onSave: (status: string, evidence: string | null) => Promise<void>;
}) {
  const [status, setStatus] = useState(need.need_status);
  const [evidence, setEvidence] = useState(need.evidence_note ?? "");
  const [message, setMessage] = useState<string | null>(null);

  return (
    <form
      className="grid gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        setMessage(null);
        onSave(status, evidence.trim() ? evidence : null).catch((reason: Error) => setMessage(reason.message));
      }}
    >
      <p className="font-bold">{need.product_name}</p>
      <p className="text-sm">Status: {need.need_status.replaceAll("_", " ")}</p>
      {need.evidence_note ? <p className="text-sm">{need.evidence_note}</p> : null}
      {canWrite ? (
        <>
          <select className={fieldClass} value={status} onChange={(event) => setStatus(event.target.value)}>
            {NEED_STATUS.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <textarea
            className={`${fieldClass} min-h-20`}
            placeholder="Source note, required past hypothesis"
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
          />
          {message ? <p role="alert">{message}</p> : null}
          <div><Button type="submit" tone="ink">Save need</Button></div>
        </>
      ) : null}
    </form>
  );
}
