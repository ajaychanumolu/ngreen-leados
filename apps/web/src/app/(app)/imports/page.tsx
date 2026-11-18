"use client";

import { useEffect, useState } from "react";

import { BackLink } from "@/components/back-link";
import { Button, fieldClass } from "@/components/button";
import { api, type ImportCommit, type ImportPreview, type Me } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const SAMPLE = "display_name,city,state,country,notes,products,tags,owner_email";

export default function ImportsPage() {
  const { token } = useAuth();
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [report, setReport] = useState<ImportCommit | null>(null);
  const [updateRows, setUpdateRows] = useState<number[]>([]);
  const [role, setRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!token) return;
    api<Me>("/api/v1/me", token)
      .then((me) => setRole(me.role))
      .catch(() => setRole("read_only"));
  }, [token]);

  const canImport = role !== null && ["owner_admin", "researcher", "manager"].includes(role);

  if (role === null) {
    return (
      <section>
        <h1 className="text-4xl font-bold">Imports</h1>
        <p className="mt-4">Loading</p>
      </section>
    );
  }

  if (!canImport) {
    return (
      <section className="max-w-3xl">
        <h1 className="text-4xl font-bold">Imports</h1>
        <p className="mt-4 text-lg leading-8">Your role can open this screen and cannot upload a CSV.</p>
      </section>
    );
  }

  return (
    <section className="max-w-4xl">
      <BackLink href="/research" label="Back to leads" />
      <h1 className="text-4xl font-bold md:text-5xl">Imports</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8">
        Preview does not write. Duplicates stay out unless you choose to update that row. Unknown
        products and empty names are reported and skipped.
      </p>
      <form
        className="mt-8 grid gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (!token) return;
          setPending(true);
          setError(null);
          setReport(null);
          api<ImportPreview>("/api/v1/imports/preview", token, {
            method: "POST",
            body: JSON.stringify({ csv_text: csvText }),
          })
            .then((result) => {
              setPreview(result);
              setUpdateRows([]);
            })
            .catch((reason: Error) => setError(reason.message))
            .finally(() => setPending(false));
        }}
      >
        <label className="grid gap-2 text-sm">
          CSV file
          <input
            className={fieldClass}
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              file.text().then(setCsvText).catch(() => setError("Could not read that file."));
            }}
          />
        </label>
        <textarea
          className={`${fieldClass} min-h-40 font-mono text-sm`}
          value={csvText}
          placeholder={SAMPLE}
          onChange={(event) => setCsvText(event.target.value)}
          required
        />
        {error ? <p role="alert">{error}</p> : null}
        <div><Button type="submit" disabled={pending}>Preview</Button></div>
      </form>
      {preview ? (
        <div className="mt-10">
          <p>
            Ready {preview.ready} · Errors {preview.errors} · Duplicates {preview.duplicates}
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-left">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-3 pr-4 font-bold">Row</th>
                  <th className="py-3 pr-4 font-bold">Company</th>
                  <th className="py-3 pr-4 font-bold">Status</th>
                  <th className="py-3 font-bold">Detail</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row) => (
                  <tr key={row.row_number} className="border-b border-border">
                    <td className="py-3 pr-4">{row.row_number}</td>
                    <td className="py-3 pr-4">{row.display_name ?? "—"}</td>
                    <td className="py-3 pr-4">{row.status}</td>
                    <td className="py-3">
                      {row.message}
                      {row.status === "duplicate" && row.match_id ? (
                        <label className="mt-2 flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={updateRows.includes(row.row_number)}
                            onChange={(event) => {
                              setUpdateRows((current) =>
                                event.target.checked
                                  ? [...current, row.row_number]
                                  : current.filter((item) => item !== row.row_number),
                              );
                            }}
                          />
                          Update the existing account
                        </label>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-6">
            <Button
              type="button"
              disabled={pending}
              onClick={() => {
                if (!token) return;
                setPending(true);
                setError(null);
                api<ImportCommit>("/api/v1/imports/commit", token, {
                  method: "POST",
                  body: JSON.stringify({ csv_text: csvText, update_rows: updateRows }),
                })
                  .then(setReport)
                  .catch((reason: Error) => setError(reason.message))
                  .finally(() => setPending(false));
              }}
            >
              Commit accepted rows
            </Button>
          </div>
        </div>
      ) : null}
      {report ? (
        <p className="mt-6 bg-muted rounded-xl p-6">
          Created {report.created}. Updated {report.updated}. Skipped {report.skipped}. Failed{" "}
          {report.failed}.
        </p>
      ) : null}
    </section>
  );
}
