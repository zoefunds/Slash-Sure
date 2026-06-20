"use client";
import { useQuery } from "@tanstack/react-query";
import { slashingApi } from "@/lib/api";
import { cn, formatDateTime, formatNumber, statusColor, truncateAddress } from "@/lib/utils";
import { Zap } from "lucide-react";

export default function SlashingPage() {
  const { data } = useQuery({
    queryKey: ["slashing-cases"],
    queryFn: () => slashingApi.list().then((r) => r.data),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Slashing Cases</h1>
        <p className="text-muted-foreground mt-1">AI-generated slashing recommendations and decisions</p>
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <Zap className="w-4 h-4 text-orange-400" />
          <h2 className="font-semibold">All Cases</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/30">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Case #</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Violation</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Network</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Fault Prob.</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Slash %</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">On-Chain Hash</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.items?.map((c: { id: string; case_number: string; violation_type: string; network: string; status: string; ai_fault_probability?: number; recommended_slash_percentage?: number; on_chain_record_hash?: string; created_at: string }) => (
                <tr key={c.id} className="hover:bg-secondary/20 transition-colors cursor-pointer">
                  <td className="px-6 py-4 font-mono text-blue-400">{c.case_number}</td>
                  <td className="px-6 py-4 capitalize">{c.violation_type?.replace(/_/g, " ")}</td>
                  <td className="px-6 py-4 text-muted-foreground">{c.network}</td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(c.status))}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono">
                    {c.ai_fault_probability !== undefined ? `${c.ai_fault_probability}%` : "—"}
                  </td>
                  <td className="px-6 py-4 font-mono">
                    {c.recommended_slash_percentage !== undefined
                      ? `${(c.recommended_slash_percentage / 100).toFixed(2)}%`
                      : "—"}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                    {c.on_chain_record_hash ? truncateAddress(c.on_chain_record_hash, 8) : "—"}
                  </td>
                  <td className="px-6 py-4 text-xs text-muted-foreground">{formatDateTime(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">No slashing cases yet</div>
          )}
        </div>
      </div>
    </div>
  );
}
