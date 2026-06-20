"use client";
import { useQuery } from "@tanstack/react-query";
import { insuranceApi } from "@/lib/api";
import { cn, formatDateTime, formatNumber, statusColor } from "@/lib/utils";
import { FileText, Plus } from "lucide-react";

export default function InsurancePage() {
  const { data } = useQuery({
    queryKey: ["insurance-claims"],
    queryFn: () => insuranceApi.list().then((r) => r.data),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Insurance Claims</h1>
          <p className="text-muted-foreground mt-1">AI-adjudicated insurance claims and payouts</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Submit Claim
        </button>
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <FileText className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold">All Claims</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/30">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Claim #</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Coverage</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Claimed</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Approved</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">AI Eligible</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Confidence</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Submitted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.items?.map((c: { id: string; claim_number: string; status: string; coverage_amount: number; claimed_amount: number; approved_amount?: number; ai_coverage_eligible?: boolean; ai_confidence_score?: number; submitted_at: string }) => (
                <tr key={c.id} className="hover:bg-secondary/20 transition-colors cursor-pointer">
                  <td className="px-6 py-4 font-mono text-purple-400">{c.claim_number}</td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(c.status))}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono">{formatNumber(c.coverage_amount)} GEN</td>
                  <td className="px-6 py-4 font-mono">{formatNumber(c.claimed_amount)} GEN</td>
                  <td className="px-6 py-4 font-mono">
                    {c.approved_amount !== undefined ? `${formatNumber(c.approved_amount)} GEN` : "—"}
                  </td>
                  <td className="px-6 py-4">
                    {c.ai_coverage_eligible === true ? (
                      <span className="text-green-400 text-xs">✓ Eligible</span>
                    ) : c.ai_coverage_eligible === false ? (
                      <span className="text-red-400 text-xs">✗ Not Eligible</span>
                    ) : (
                      <span className="text-muted-foreground text-xs">Pending</span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono">
                    {c.ai_confidence_score !== undefined ? `${c.ai_confidence_score}%` : "—"}
                  </td>
                  <td className="px-6 py-4 text-xs text-muted-foreground">{formatDateTime(c.submitted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">No claims submitted yet</div>
          )}
        </div>
      </div>
    </div>
  );
}
