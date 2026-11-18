"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button, fieldClass } from "@/components/button";
import { LEAD_SECTIONS, SectionNav } from "@/components/section-nav";
import { ApiRequestError, api, type Industry, type Product, type ResearchRun } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type RunPage = { items: ResearchRun[]; total: number };

export default function ResearchPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [productId, setProductId] = useState("");
  const [industryId, setIndustryId] = useState("");
  const [geography, setGeography] = useState("");
  const [limitCompanies, setLimitCompanies] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    let cancelled = false;
    Promise.all([
      api<Product[]>("/api/v1/products", token),
      api<Industry[]>("/api/v1/industries", token),
      api<RunPage>("/api/v1/research/runs", token),
    ])
      .then(([productPage, industryPage, runPage]) => {
        if (cancelled) {
          return;
        }
        setIndustries(industryPage);
        setRuns(runPage.items);
        setProductId((current) => current || productPage[0]?.id || "");
        setIndustryId((current) => current || industryPage[0]?.id || "");
      })
      .catch((reason: Error) => {
        if (!cancelled) {
          setError(reason.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function start(event: React.FormEvent) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const run = await api<ResearchRun>("/api/v1/research/runs", token, {
        method: "POST",
        body: JSON.stringify({
          product_id: productId,
          industry_id: industryId,
          geography: geography.trim(),
          limit_companies: limitCompanies,
          max_queries: 3,
        }),
      });
      router.push(`/research/runs/${run.id}`);
    } catch (reason) {
      setError(reason instanceof ApiRequestError ? reason.message : "The search did not start.");
      setBusy(false);
    }
  }

  return (
    <section className="max-w-5xl">
      <h1 className="text-4xl font-bold leading-tight md:text-5xl">Research</h1>
      <SectionNav label="Leads" items={LEAD_SECTIONS} />
      <p className="mt-6 max-w-2xl text-lg leading-8">
        Pick an industry and how many companies to find. Location is optional. The agent searches
        for customers that use plastic packaging, such as Zepto, Blinkit, and Swiggy Instamart,
        and leaves out manufacturers and suppliers. It records a plastic item, email, or mobile
        only when a page says so.
      </p>
      {error ? (
        <p className="mt-6" role="alert">
          {error}
        </p>
      ) : null}
      <form onSubmit={start} className="mt-10 grid gap-4 rounded-xl bg-muted p-6 md:grid-cols-2">
        <label className="block md:col-span-2">
          <span className="mb-2 block text-sm font-medium text-muted-foreground">Industry</span>
          <select
            className={fieldClass}
            value={industryId}
            onChange={(event) => setIndustryId(event.target.value)}
            required
          >
            {industries.map((industry) => (
              <option key={industry.id} value={industry.id}>
                {industry.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-muted-foreground">Company limit</span>
          <input
            className={fieldClass}
            type="number"
            min={1}
            max={25}
            value={limitCompanies}
            onChange={(event) => setLimitCompanies(Number(event.target.value))}
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-muted-foreground">Location</span>
          <input
            className={fieldClass}
            value={geography}
            onChange={(event) => setGeography(event.target.value)}
            placeholder="Optional. Blank searches India"
          />
        </label>
        <div className="md:col-span-2">
          <Button type="submit" disabled={busy || !productId || !industryId}>
            {busy ? "Starting" : "Search customers"}
          </Button>
          <p className="mt-3 text-sm text-muted-foreground">
            A live search spends credits. Industry chooses who to look for. It is not written onto
            a company until you set it.
          </p>
        </div>
      </form>
      <h2 className="mt-12 text-2xl font-bold">Recent runs</h2>
      <ul className="mt-6 divide-y divide-border border-y border-border">
        {runs.map((run) => (
          <li key={run.id}>
            <Link href={`/research/runs/${run.id}`} className="flex flex-wrap items-baseline justify-between gap-3 py-4">
              <span className="font-bold">
                {run.industry_filter || run.product_name} · {run.geography}
              </span>
              <span className="text-sm text-muted-foreground">
                {run.mode} · {run.status} · {run.spent_credits}/{run.budget_credits} credits
              </span>
            </Link>
          </li>
        ))}
        {runs.length === 0 ? <li className="py-4">No searches yet.</li> : null}
      </ul>
    </section>
  );
}
