"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AccountForm } from "@/components/account-form";
import { LEAD_SECTIONS, SectionNav } from "@/components/section-nav";
import { api, type Account, type Product } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function NewAccountPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [products, setProducts] = useState<string[]>([]);
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }
    api<Product[]>("/api/v1/products", token)
      .then((rows) => setProducts(rows.map((row) => row.name)))
      .catch(() => setProducts([]));
  }, [token]);

  return (
    <section className="max-w-2xl">
      <h1 className="text-4xl font-bold">Add lead</h1>
      <SectionNav label="Leads" items={LEAD_SECTIONS} />
      <p className="mt-4 text-lg leading-8">
        Type a company you already know, plus the email or mobile if you have it. This does not
        search the internet.
      </p>
      <AccountForm
        pending={pending}
        error={error}
        products={products}
        submitLabel="Save lead"
        contactEmail={email}
        contactPhone={phone}
        onContactEmail={setEmail}
        onContactPhone={setPhone}
        onSubmit={async (values) => {
          if (!token) {
            return;
          }
          setPending(true);
          setError(null);
          try {
            const created = await api<Account>("/api/v1/accounts", token, {
              method: "POST",
              body: JSON.stringify(values),
            });
            if (email.trim() || phone.trim()) {
              await api("/api/v1/contacts", token, {
                method: "POST",
                body: JSON.stringify({
                  company_id: created.id,
                  email: email.trim() || null,
                  phone: phone.trim() || null,
                  source_note: "Added by hand with the lead.",
                  permission_basis: "unknown",
                }),
              });
            }
            router.replace(`/accounts/${created.id}`);
          } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Save failed.");
            setPending(false);
          }
        }}
      />
    </section>
  );
}
