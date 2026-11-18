import type { Metadata } from "next";
import { DM_Sans, Geist_Mono } from "next/font/google";
import { cookies } from "next/headers";

import { AuthProvider } from "@/lib/auth";

import "./globals.css";

const sans = DM_Sans({ subsets: ["latin"], variable: "--font-dm" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export const metadata: Metadata = {
  title: "N Green LeadOS",
  description: "Staff workspace for N Green lead research and accounts.",
  icons: { icon: "/brand/mark.svg" },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const token = (await cookies()).get("leados_demo_token")?.value ?? null;
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="bg-background font-sans text-foreground antialiased">
        <AuthProvider initialToken={token}>{children}</AuthProvider>
      </body>
    </html>
  );
}
