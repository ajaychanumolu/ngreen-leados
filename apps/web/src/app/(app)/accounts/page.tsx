"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ArrowRight } from "lucide-react";

import { actionClass, fieldClass } from "@/components/button";
import { LEAD_SECTIONS, SectionNav } from "@/components/section-nav";
import { api, apiText, type AccountPage, type Product } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AccountsPage() {
  const { token } = useAuth();
  const [page, setPage] = useState<AccountPage | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [product, setProduct] = useState("");
  const [filters, setFilters] = useState({ q: "", source: "", product: "" });

  useEffect(() => {
    if (!token) {
      return;
    }
    const params = new URLSearchParams({ page_size: "100" });
    if (filters.q) params.set("q", filters.q);
    if (filters.source) params.set("source_origin", filters.source);
    if (filters.product) params.set("product", filters.product);
    api<Product[]>("/api/v1/products", token).then(setProducts).catch(() => setProducts([]));
    api<AccountPage>(`/api/v1/accounts?${params.toString()}`, token)
      .then(setPage)
      .catch((reason: Error) => setError(reason.message));
  }, [token, filters]);

  async function exportCsv() {
    if (!token) return;
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.source) params.set("source_origin", filters.source);
    if (filters.product) params.set("product", filters.product);
    const query = params.toString();
    const suffix = query ? `?${query}` : "";
    try {
      const text = await apiText(`/api/v1/accounts/export${suffix}`, token);
      const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "accounts.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Export failed.");
    }
  }

  return (
    <section>
      <h1 className="text-4xl font-bold md:text-5xl">Saved leads</h1>
      <SectionNav label="Leads" items={LEAD_SECTIONS} />
      <p className="mt-6 max-w-2xl text-lg leading-8">
        Companies already saved. Reference targets are unverified hypotheses, not confirmed buyers.
      </p>
      <div className="mt-6">
        <button type="button" className={actionClass("ink")} onClick={() => void exportCsv()}>
          Export CSV
          <ArrowRight aria-hidden size={18} />
        </button>
      </div>
      <form
        className="mt-8 grid gap-3 md:grid-cols-[1fr_180px_220px_auto]"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(null);
          setFilters({ q, source, product });
        }}
      >
        <input
          className={fieldClass}
          placeholder="Search company"
          value={q}
          onChange={(event) => setQ(event.target.value)}
        />
        <select className={fieldClass} value={source} onChange={(event) => setSource(event.target.value)}>
          <option value="">All sources</option>
          <option value="reference_sheet">Reference sheet</option>
          <option value="manual">Manual</option>
          <option value="csv_import">CSV import</option>
        </select>
        <select className={fieldClass} value={product} onChange={(event) => setProduct(event.target.value)}>
          <option value="">All products</option>
          {products.map((item) => (
            <option key={item.id} value={item.name}>
              {item.name}
            </option>
          ))}
        </select>
        <button type="submit" className={actionClass("ink")}>
          Filter
          <ArrowRight aria-hidden size={18} />
        </button>
      </form>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      {!page && !error ? <p className="mt-10">Loading</p> : null}
      {page && page.items.length === 0 ? (
        <p className="mt-10 bg-muted rounded-xl p-8 text-lg">No accounts match these filters.</p>
      ) : null}
      {page && page.items.length > 0 ? (
        <div className="mt-10 overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left">
            <thead>
              <tr className="border-b border-border">
                <th className="py-3 pr-4 font-bold">Company</th>
                <th className="py-3 pr-4 font-bold">City</th>
                <th className="py-3 pr-4 font-bold">Products</th>
                <th className="py-3 pr-4 font-bold">Stage</th>
                <th className="py-3 font-bold">Review</th>
              </tr>
            </thead>
            <tbody>
              {page.items.map((account) => (
                <tr key={account.id} className="border-b border-border">
                  <td className="py-4 pr-4">
                    <Link href={`/accounts/${account.id}`} className="font-bold underline">
                      {account.display_name}
                    </Link>
                    {account.review_label ? (
                      <p className="mt-1 text-sm">{account.review_label}</p>
                    ) : null}
                  </td>
                  <td className="py-4 pr-4">{account.city ?? "—"}</td>
                  <td className="py-4 pr-4">{account.products.join(", ") || "—"}</td>
                  <td className="py-4 pr-4">{account.stage?.replaceAll("_", " ") ?? "—"}</td>
                  <td className="py-4">{account.review_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-sm">{page.total} from the database</p>
        </div>
      ) : null}
    </section>
  );
}
