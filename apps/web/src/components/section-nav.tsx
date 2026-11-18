"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { actionClass } from "@/components/button";

export type SectionItem = {
  href: string;
  label: string;
  active: (pathname: string) => boolean;
};

export function SectionNav({ label, items }: { label: string; items: SectionItem[] }) {
  const pathname = usePathname();
  return (
    <nav className="mt-6 flex flex-wrap gap-3" aria-label={label}>
      {items.map((item) => {
        const current = item.active(pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={current ? actionClass() : actionClass("ink")}
            aria-current={current ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export const LEAD_SECTIONS: SectionItem[] = [
  {
    href: "/research",
    label: "Research",
    active: (pathname) => pathname.startsWith("/research"),
  },
  {
    href: "/accounts/new",
    label: "Add lead",
    active: (pathname) => pathname === "/accounts/new",
  },
  {
    href: "/accounts",
    label: "Saved leads",
    active: (pathname) =>
      pathname === "/accounts" ||
      (pathname.startsWith("/accounts/") && !pathname.startsWith("/accounts/new")),
  },
];

export const CALL_SECTIONS: SectionItem[] = [
  { href: "/calling", label: "Talk settings", active: (pathname) => pathname === "/calling" },
  {
    href: "/calling/ready",
    label: "Ready to call",
    active: (pathname) => pathname.startsWith("/calling/ready"),
  },
  {
    href: "/calling/completed",
    label: "Completed",
    active: (pathname) =>
      pathname.startsWith("/calling/completed") || pathname.startsWith("/calls/"),
  },
];

export const CRM_SECTIONS: SectionItem[] = [
  { href: "/crm", label: "Pipeline", active: (pathname) => pathname === "/crm" },
  { href: "/tasks", label: "Follow-ups", active: (pathname) => pathname.startsWith("/tasks") },
];
