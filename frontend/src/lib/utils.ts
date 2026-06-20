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
    case "critical": return "text-red-400 bg-red-400/10 border-red-400/20";
    case "high": return "text-orange-400 bg-orange-400/10 border-orange-400/20";
    case "medium": return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
    case "low": return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    default: return "text-muted-foreground bg-muted border-border";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "active": return "text-green-400 bg-green-400/10";
    case "slashed": return "text-red-400 bg-red-400/10";
    case "jailed": return "text-orange-400 bg-orange-400/10";
    case "suspended": return "text-yellow-400 bg-yellow-400/10";
    case "inactive": return "text-muted-foreground bg-muted";
    case "approved": return "text-green-400 bg-green-400/10";
    case "rejected": return "text-red-400 bg-red-400/10";
    case "pending": return "text-yellow-400 bg-yellow-400/10";
    case "executed": return "text-purple-400 bg-purple-400/10";
    default: return "text-muted-foreground bg-muted";
  }
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-green-400";
  if (score >= 60) return "text-yellow-400";
  if (score >= 40) return "text-orange-400";
  return "text-red-400";
}

export function truncateAddress(addr: string, chars = 6): string {
  if (!addr) return "";
  return `${addr.slice(0, chars)}...${addr.slice(-4)}`;
}
