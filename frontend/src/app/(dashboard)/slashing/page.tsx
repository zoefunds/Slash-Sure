"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { slashingApi } from "@/lib/api";
import { cn, formatDateTime, formatNumber, statusColor, truncateAddress } from "@/lib/utils";
import { Zap, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface SlashCase {
  id: string;
  case_number: string;
  violation_type: string;
  network: string;
  status: string;
  ai_fault_probability?: number;
  recommended_slash_percentage?: number;
  recommended_slash_amount?: number;
  stake_at_risk: number;
  on_chain_record_hash?: string;
  genlayer_tx_hash?: string;
  created_at: string;
}

function ApproveModal({
  caseItem,
  onClose,
}: {
  caseItem: SlashCase;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [approved, setApproved] = useState<boolean | null>(null);
  const [reason, setReason] = useState("");
  const [done, setDone] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: { approved: boolean; reason?: string }) =>
      slashingApi.approve(caseItem.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["slashing-cases"] });
      setDone(true);
    },
  });

  if (done) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
        <div className="w-full max-w-md bg-card border border-border rounded-2xl p-8 text-center space-y-4">
          <CheckCircle className="w-12 h-12 text-green-700 mx-auto" />
          <h2 className="text-lg font-bold">{approved ? "Slashing Approved" : "Case Rejected"}</h2>
          <p className="text-muted-foreground text-sm">The on-chain transaction has been submitted.</p>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-85 transition-opacity"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl p-6 shadow-2xl">
        <h2 className="text-lg font-bold mb-1">Review Case {caseItem.case_number}</h2>
        <p className="text-muted-foreground text-sm mb-6">
          Approve or reject this AI-recommended slashing decision
        </p>

        <div className="p-4 rounded-xl bg-secondary border border-border space-y-2 mb-6 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Violation</span>
            <span className="capitalize">{caseItem.violation_type?.replace(/_/g, " ")}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Network</span>
            <span>{caseItem.network}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">AI Fault Probability</span>
            <span className="text-orange-400 font-mono">
              {caseItem.ai_fault_probability !== undefined ? `${caseItem.ai_fault_probability}%` : "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Recommended Slash</span>
            <span className="text-red-700 font-mono">
              {caseItem.recommended_slash_amount !== undefined
                ? `${formatNumber(caseItem.recommended_slash_amount)} GEN`
                : "—"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Stake at Risk</span>
            <span className="font-mono">{formatNumber(caseItem.stake_at_risk)} GEN</span>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <label className="block text-sm font-medium">Reason (optional)</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Provide a reason for approval or rejection…"
            rows={3}
            className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm resize-none"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-lg border border-border text-sm font-medium hover:bg-secondary/50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => { setApproved(false); mutation.mutate({ approved: false, reason }); }}
            disabled={mutation.isPending}
            className="flex-1 py-2.5 rounded-lg bg-red-100 border border-red-200 hover:bg-red-200 text-red-700 text-sm font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {mutation.isPending && approved === false ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
            Reject
          </button>
          <button
            onClick={() => { setApproved(true); mutation.mutate({ approved: true, reason }); }}
            disabled={mutation.isPending}
            className="flex-1 py-2.5 rounded-lg bg-green-100 border border-green-200 hover:bg-green-200 text-green-700 text-sm font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {mutation.isPending && approved === true ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SlashingPage() {
  const [selected, setSelected] = useState<SlashCase | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["slashing-cases", statusFilter, page],
    queryFn: () => slashingApi.list({ status: statusFilter || undefined, page, per_page: 20 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const STATUSES = ["pending", "ai_analysis", "approved", "rejected", "executed", "appealed"];

  return (
    <div className="space-y-6 animate-fade-in">
      {selected && <ApproveModal caseItem={selected} onClose={() => setSelected(null)} />}

      <div>
        <h1 className="text-2xl font-bold">Slashing Cases</h1>
        <p className="text-muted-foreground mt-1">AI-generated slashing recommendations and decisions</p>
      </div>

      {/* Status filter */}
      <div className="flex gap-2 flex-wrap">
        {["", ...STATUSES].map((s) => (
          <button
            key={s || "all"}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize",
              statusFilter === s
                ? "bg-foreground border-foreground text-background"
                : "border-border text-muted-foreground hover:border-foreground/30",
            )}
          >
            {s || "All statuses"}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <Zap className="w-4 h-4 text-orange-400" />
          <h2 className="font-semibold">All Cases</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Case #", "Violation", "Network", "Status", "Fault Prob.", "Slash Amount", "Tx Hash", "Created", "Action"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading && (
                <tr><td colSpan={9} className="px-6 py-16 text-center text-muted-foreground">Loading…</td></tr>
              )}
              {data?.items?.map((c: SlashCase) => (
                <tr key={c.id} className="hover:bg-secondary transition-colors">
                  <td className="px-4 py-4 font-mono text-foreground whitespace-nowrap">{c.case_number}</td>
                  <td className="px-4 py-4 capitalize whitespace-nowrap">{c.violation_type?.replace(/_/g, " ")}</td>
                  <td className="px-4 py-4 text-muted-foreground">{c.network}</td>
                  <td className="px-4 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(c.status))}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono">
                    {c.ai_fault_probability !== undefined ? `${c.ai_fault_probability}%` : "—"}
                  </td>
                  <td className="px-4 py-4 font-mono text-red-700">
                    {c.recommended_slash_amount !== undefined
                      ? `${formatNumber(c.recommended_slash_amount)} GEN`
                      : "—"}
                  </td>
                  <td className="px-4 py-4 font-mono text-xs text-muted-foreground">
                    {c.genlayer_tx_hash ? truncateAddress(c.genlayer_tx_hash, 8) : "—"}
                  </td>
                  <td className="px-4 py-4 text-xs text-muted-foreground whitespace-nowrap">
                    {formatDateTime(c.created_at)}
                  </td>
                  <td className="px-4 py-4">
                    {c.status === "pending" || c.status === "ai_analysis" ? (
                      <button
                        onClick={() => setSelected(c)}
                        className="px-3 py-1.5 text-xs rounded border border-orange-500/30 text-orange-400 hover:bg-orange-500/10 transition-colors whitespace-nowrap"
                      >
                        Review
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isLoading && !data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">No slashing cases yet</div>
          )}
        </div>

        {(data?.total ?? 0) > 20 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-border">
            <span className="text-sm text-muted-foreground">
              Page {page} of {Math.ceil((data?.total ?? 0) / 20)}
            </span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-40 hover:bg-secondary/50">
                Prev
              </button>
              <button disabled={page >= Math.ceil((data?.total ?? 0) / 20)} onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-40 hover:bg-secondary/50">
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
