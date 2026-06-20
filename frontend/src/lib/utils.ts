import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number, decimals = 2): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(decimals)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(decimals)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(decimals)}K`;
  return n.toFixed(decimals);
}

export function formatDate(d: string | Date): string {
  return new Date(d).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
}

export function formatDateTime(d: string | Date): string {
  return new Date(d).toLocaleString("en-US", {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical": return "text-red-700 bg-red-100 border-red-200";
    case "high": return "text-orange-700 bg-orange-100 border-orange-200";
    case "medium": return "text-amber-700 bg-amber-100 border-amber-200";
    case "low": return "text-blue-700 bg-blue-100 border-blue-200";
    default: return "text-muted-foreground bg-muted border-border";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "active": return "text-green-700 bg-green-100";
    case "slashed": return "text-red-700 bg-red-100";
    case "jailed": return "text-orange-700 bg-orange-100";
    case "suspended": return "text-amber-700 bg-amber-100";
    case "inactive": return "text-muted-foreground bg-muted";
    case "approved": return "text-green-700 bg-green-100";
    case "rejected": return "text-red-700 bg-red-100";
    case "pending": return "text-amber-700 bg-amber-100";
    case "executed": return "text-purple-700 bg-purple-100";
    default: return "text-muted-foreground bg-muted";
  }
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-green-700";
  if (score >= 60) return "text-amber-700";
  if (score >= 40) return "text-orange-700";
  return "text-red-700";
}

export function truncateAddress(addr: string, chars = 6): string {
  if (!addr) return "";
  return `${addr.slice(0, chars)}...${addr.slice(-4)}`;
}
