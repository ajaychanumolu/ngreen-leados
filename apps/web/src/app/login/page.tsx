"use client";

import { useRouter } from "next/navigation";

import { BrandMark } from "@/components/brand-mark";
import { useEffect, useState } from "react";

import { Button } from "@/components/button";
import { api, type Health } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  "owner@ngreen.demo",
  "researcher@ngreen.demo",
  "sales@ngreen.demo",
  "manager@ngreen.demo",
  "reader@ngreen.demo",
];

export default function LoginPage() {
  const router = useRouter();
  const { token, setToken } = useAuth();
  const [email, setEmail] = useState("owner@ngreen.demo");
  const [password, setPassword] = useState("demo-pass");
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (token) {
      router.replace("/overview");
    }
  }, [token, router]);

  useEffect(() => {
    api<Health>("/health", null)
      .then(setHealth)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const result = await api<{ access_token: string }>("/api/v1/auth/demo/login", null, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      router.replace("/overview");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign in failed.");
      setPending(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2">
      <section>
        <BrandMark />
        <h1 className="mt-6 max-w-xl text-4xl font-bold leading-tight md:text-5xl">
          Staff workspace for packaging lead research
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-8">
          Sign in to review packaging accounts and research candidates. Without a search key,
          discovery stays labeled DEMO. Calling is a later phase. This local sign-in is labeled
          DEMO until a Supabase project is connected.
        </p>
      </section>
      <section className="bg-muted rounded-xl p-8">
        <h2 className="text-2xl font-bold">Sign in</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {health ? `API ${health.status} · ${health.auth_mode} · ${health.database}` : "Checking API"}
        </p>
        <form className="mt-8 grid gap-4" onSubmit={onSubmit}>
          <label className="grid gap-2 text-sm">
            Work email
            <input
              className="rounded-xl border border-border bg-input px-3 py-3"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="grid gap-2 text-sm">
            Password
            <input
              className="rounded-xl border border-border bg-input px-3 py-3"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error ? <p role="alert">{error}</p> : null}
          <Button type="submit" disabled={pending}>
            {pending ? "Signing in" : "Sign in"}
          </Button>
        </form>
        <div className="mt-8 text-sm leading-6">
          <p className="font-medium">DEMO staff</p>
          <p className="mt-2">Shared password: demo-pass</p>
          <ul className="mt-2">
            {DEMO_ACCOUNTS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}
