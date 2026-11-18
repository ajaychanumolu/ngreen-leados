"use client";

import Link from "next/link";

export function BackLink({ href, label }: { href: string; label: string }) {
  return (
    <p className="mb-6">
      <Link href={href} className="text-sm text-muted-foreground">
        ← {label}
      </Link>
    </p>
  );
}
