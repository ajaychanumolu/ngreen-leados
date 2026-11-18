"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BackLink } from "@/components/back-link";
import { api, type ContactPage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ContactsPage() {
  const { token } = useAuth();
  const [page, setPage] = useState<ContactPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api<ContactPage>("/api/v1/contacts?page_size=100", token)
      .then(setPage)
      .catch((reason: Error) => setError(reason.message));
  }, [token]);

  return (
    <section>
      <BackLink href="/research" label="Back to leads" />
      <h1 className="text-4xl font-bold md:text-5xl">Contacts</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8">
        Contacts are typed by staff or taken from an official public page. A public email is not
        permission to call. Unknown permission and do-not-call both block a live call. No call is
        placed from this screen.
      </p>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      {!page && !error ? <p className="mt-10">Loading</p> : null}
      {page && page.total === 0 ? (
        <p className="mt-10 bg-muted rounded-xl p-8 text-lg">No contacts yet. Add one from an account.</p>
      ) : null}
      {page && page.items.length > 0 ? (
        <table className="mt-10 w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border">
              <th className="py-3 pr-4 font-bold">Person</th>
              <th className="py-3 pr-4 font-bold">Account</th>
              <th className="py-3 pr-4 font-bold">Permission</th>
              <th className="py-3 font-bold">Call</th>
            </tr>
          </thead>
          <tbody>
            {page.items.map((contact) => (
              <tr key={contact.id} className="border-b border-border">
                <td className="py-4 pr-4">{contact.display_name ?? contact.email ?? contact.phone}</td>
                <td className="py-4 pr-4">
                  <Link href={`/accounts/${contact.company_id}`} className="underline">
                    {contact.company_name}
                  </Link>
                </td>
                <td className="py-4 pr-4">
                  {contact.permission_basis.replaceAll("_", " ")}
                  {contact.do_not_call ? " · do not call" : ""}
                  {contact.source_url ? (
                    <a className="mt-1 block underline" href={contact.source_url}>
                      Source page
                    </a>
                  ) : null}
                </td>
                <td className="py-4">
                  {contact.call_allowed ? "Allowed" : "Blocked"}
                  {contact.call_reasons?.[0] ? ` · ${contact.call_reasons[0]}` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
