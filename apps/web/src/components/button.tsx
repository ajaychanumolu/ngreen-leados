import { ArrowRight } from "lucide-react";

export const fieldClass =
  "w-full rounded-xl border border-border bg-input px-3 py-3 text-base text-foreground shadow-sm";

export function actionClass(tone: "action" | "ink" = "action") {
  const color =
    tone === "ink"
      ? "bg-secondary text-secondary-foreground"
      : "bg-primary text-primary-foreground";
  return `inline-flex items-center justify-center gap-3 rounded-xl px-5 py-3 text-sm font-medium shadow-sm disabled:opacity-50 ${color}`;
}

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: "action" | "ink";
};

export function Button({ tone = "action", className = "", children, ...props }: Props) {
  return (
    <button className={`${actionClass(tone)} ${className}`} {...props}>
      {children}
      <ArrowRight aria-hidden size={18} />
    </button>
  );
}
