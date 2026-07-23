"use client";

import { isValidElement, type ReactNode } from "react";
import { X, ExternalLink } from "lucide-react";
import { cn, formatDateTime, formatNumber, truncateAddress } from "@/lib/utils";

type Section = { label: string; value: ReactNode };

type RecordDetailDrawerProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  sections: Section[];
  raw?: Record<string, unknown> | null;
  isLoading?: boolean;
  actions?: ReactNode;
  onClose: () => void;
};

function JsonValue({ value }: { value: unknown }) {
  if (isValidElement(value)) return value;
  if (value === null || value === undefined || value === "") return <span className="text-muted-foreground">—</span>;
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  if (typeof value === "number") return <span className="font-mono">{Number.isFinite(value) ? formatNumber(value) : String(value)}</span>;
  if (typeof value === "string") {
    if (value.startsWith("http://") || value.startsWith("https://")) {
      return (
        <a href={value} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-foreground underline break-all">
          {value}
          <ExternalLink className="w-3 h-3" />
        </a>
      );
    }
    if (value.startsWith("0x") && value.length > 12) return <span className="font-mono">{truncateAddress(value, 8)}</span>;
    if (/\d{4}-\d{2}-\d{2}T/.test(value) || /\d{4}-\d{2}-\d{2}/.test(value)) return <span>{formatDateTime(value)}</span>;
    return <span className="break-words">{value}</span>;
  }
  if (Array.isArray(value)) return <span>{value.length} item{value.length === 1 ? "" : "s"}</span>;
  if (typeof value === "object") return <span className="text-muted-foreground">Object</span>;
  return <span>{String(value)}</span>;
}

export function RecordDetailDrawer({
  open,
  title,
  subtitle,
  sections,
  raw,
  isLoading,
  actions,
  onClose,
}: RecordDetailDrawerProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm">
      <button aria-label="Close details" onClick={onClose} className="absolute inset-0 cursor-default" />
      <aside className="absolute right-0 top-0 h-full w-full max-w-xl bg-card border-l border-border shadow-2xl overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border bg-card/95 backdrop-blur px-6 py-5">
          <div className="min-w-0">
            <h2 className="text-lg font-bold truncate">{title}</h2>
            {subtitle && <p className="text-sm text-muted-foreground mt-1 break-words">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="shrink-0 rounded-lg border border-border p-2 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
          <div className="grid gap-4 md:grid-cols-2">
            {isLoading && sections.length === 0 ? (
              <div className="md:col-span-2 rounded-xl border border-border bg-secondary/20 p-4 text-sm text-muted-foreground">
                Loading details…
              </div>
            ) : null}
            {sections.map((section) => (
              <div key={section.label} className="rounded-xl border border-border bg-secondary/30 p-4">
                <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">{section.label}</div>
                <div className={cn("text-sm break-words", typeof section.value === "string" ? "" : "space-y-1")}>
                  <JsonValue value={section.value as unknown} />
                </div>
              </div>
            ))}
          </div>

          {raw && (
            <div className="rounded-xl border border-border bg-secondary/20 p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground mb-3">Full record</div>
              <pre className="text-xs leading-relaxed whitespace-pre-wrap break-words font-mono text-foreground/90">
                {JSON.stringify(raw, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
