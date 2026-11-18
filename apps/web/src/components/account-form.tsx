"use client";

import { useState } from "react";

import { Button, fieldClass } from "@/components/button";

export type AccountValues = {
  display_name: string;
  city: string | null;
  state: string | null;
  notes: string | null;
  product_names?: string[];
};

export function AccountForm({
  initial,
  pending,
  error,
  submitLabel,
  products,
  contactEmail,
  contactPhone,
  onContactEmail,
  onContactPhone,
  onSubmit,
}: {
  initial?: AccountValues;
  pending: boolean;
  error: string | null;
  submitLabel: string;
  products?: string[];
  contactEmail?: string;
  contactPhone?: string;
  onContactEmail?: (value: string) => void;
  onContactPhone?: (value: string) => void;
  onSubmit: (values: AccountValues) => Promise<void>;
}) {
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [city, setCity] = useState(initial?.city ?? "");
  const [state, setState] = useState(initial?.state ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [selected, setSelected] = useState<string[]>(initial?.product_names ?? []);

  return (
    <form
      className="mt-8 grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({
          display_name: displayName,
          city: city.trim() ? city : null,
          state: state.trim() ? state : null,
          notes: notes.trim() ? notes : null,
          product_names: products ? selected : undefined,
        });
      }}
    >
      <label className="grid gap-2 text-sm">
        Company name
        <input
          className={fieldClass}
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          required
          maxLength={200}
        />
      </label>
      <label className="grid gap-2 text-sm">
        City
        <input
          className={fieldClass}
          value={city}
          onChange={(event) => setCity(event.target.value)}
          maxLength={120}
        />
      </label>
      <label className="grid gap-2 text-sm">
        State
        <input
          className={fieldClass}
          value={state}
          onChange={(event) => setState(event.target.value)}
          maxLength={120}
        />
      </label>
      <label className="grid gap-2 text-sm">
        Notes
        <textarea
          className={`${fieldClass} min-h-28`}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          maxLength={2000}
        />
      </label>
      {products ? (
        <fieldset className="grid gap-2">
          <legend className="text-sm">Product hypotheses</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {products.map((name) => (
              <label key={name} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(name)}
                  onChange={(event) => {
                    setSelected((current) =>
                      event.target.checked
                        ? [...current, name]
                        : current.filter((item) => item !== name),
                    );
                  }}
                />
                {name}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}
      {onContactEmail && onContactPhone ? (
        <>
          <label className="grid gap-2 text-sm">
            Email
            <input
              className={fieldClass}
              type="email"
              value={contactEmail ?? ""}
              onChange={(event) => onContactEmail(event.target.value)}
              placeholder="name@company.com"
            />
          </label>
          <label className="grid gap-2 text-sm">
            Mobile
            <input
              className={fieldClass}
              value={contactPhone ?? ""}
              onChange={(event) => onContactPhone(event.target.value)}
              placeholder="+91..."
            />
          </label>
        </>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
      <div>
        <Button type="submit" disabled={pending}>
          {pending ? "Saving" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
