"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, type Health, type Me } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/overview", label: "Home" },
  { href: "/research", label: "Leads" },
  { href: "/calling", label: "Calls" },
  { href: "/crm", label: "CRM" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { token, setToken } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    api<Me>("/api/v1/me", token)
      .then((profile) => {
        if (!cancelled) {
          setMe(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setToken(null);
          router.replace("/login");
        }
      });
    api<Health>("/health", null)
      .then((status) => {
        if (!cancelled) {
          setHealth(status);
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
  }, [token, router, setToken]);

  if (!token || !me) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <p className="text-base">Loading</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground md:grid md:grid-cols-[280px_1fr]">
      <aside className="border-b border-sidebar-border bg-sidebar text-sidebar-foreground md:border-r md:border-b-0">
        <div className="flex items-center justify-between px-6 py-5">
          <Link href="/overview" className="block" aria-label="N Green Sustainable Packaging">
            <BrandMark />
          </Link>
          <button
            className="md:hidden"
            type="button"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
        <nav className={`${open ? "block" : "hidden"} px-3 pb-6 md:block`} aria-label="Primary">
          {NAV.map((item) => {
            const active =
              pathname === item.href ||
              pathname.startsWith(`${item.href}/`) ||
              (item.href === "/calling" && pathname.startsWith("/calls")) ||
              (item.href === "/research" &&
                (pathname.startsWith("/accounts") || pathname.startsWith("/contacts"))) ||
              (item.href === "/crm" && pathname.startsWith("/tasks"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-xl px-3 py-2 text-sm ${active ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}`}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            );
          })}
          <button
            className="mt-6 rounded-xl px-3 py-2 text-left text-sm text-muted-foreground"
            type="button"
            onClick={() => {
              setToken(null);
              router.replace("/login");
            }}
          >
            Sign out
          </button>
        </nav>
      </aside>
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-4 text-sm text-muted-foreground md:px-10">
          <p>
            {me.organization_name} · {me.display_name} · {me.role.replaceAll("_", " ")}
          </p>
          <p>
            {health?.auth_mode === "demo" ? "DEMO sign-in" : "Staff sign-in"}
            {health?.database === "sqlite" ? " · local database" : ""}
            {health?.research_mode === "live" ? " · live search" : " · DEMO search"}
            {health?.voice_mode === "armed" ? " · live calling armed" : " · live calling disabled"}
          </p>
        </div>
        {error ? <p className="px-6 py-3 text-sm md:px-10">{error}</p> : null}
        <div className="px-6 py-10 md:px-10 md:py-14">{children}</div>
      </div>
    </div>
  );
}
