"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { insuranceApi, incidentsApi } from "@/lib/api";
import { cn, formatDateTime, formatNumber, statusColor } from "@/lib/utils";
import { FileText, Plus, X, Loader2, CheckCircle } from "lucide-react";

interface ClaimForm {
  incident_id: string;
  claimant_address: string;
  coverage_amount: string;
  claimed_amount: string;
  policy_id: string;
}

function SubmitClaimModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<ClaimForm>({
    incident_id: "", claimant_address: "", coverage_amount: "",
    claimed_amount: "", policy_id: "",
  });
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const { data: incidents } = useQuery({
    queryKey: ["incidents-for-claim"],
    queryFn: () => incidentsApi.list({ per_page: 50 }).then((r) => r.data),
  });

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => insuranceApi.submit(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insurance-claims"] });
      setDone(true);
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Failed to submit claim");
    },
  });

  const handleSubmit = (ev: React.FormEvent) => {
    ev.preventDefault();
    setError("");
    const coverage = parseFloat(form.coverage_amount);
    const claimed = parseFloat(form.claimed_amount);
    if (claimed > coverage) {
      setError("Claimed amount cannot exceed coverage amount");
      return;
    }
    mutation.mutate({
      incident_id: form.incident_id,
      claimant_address: form.claimant_address,
      coverage_amount: coverage,
      claimed_amount: claimed,
      policy_id: form.policy_id || undefined,
      claim_details: {},
    });
  };

  if (done) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
        <div className="w-full max-w-md bg-card border border-border rounded-2xl p-8 text-center space-y-4">
          <CheckCircle className="w-12 h-12 text-green-700 mx-auto" />
          <h2 className="text-lg font-bold">Claim Submitted</h2>
          <p className="text-muted-foreground text-sm">
            Your claim has been submitted and is queued for AI adjudication on GenLayer.
          </p>
          <button onClick={onClose} className="px-6 py-2.5 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-85 transition-opacity">
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Submit Insurance Claim</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">Incident</label>
            <select
              required
              value={form.incident_id}
              onChange={(e) => setForm((f) => ({ ...f, incident_id: e.target.value }))}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
            >
              <option value="">Select incident…</option>
              {incidents?.items?.map((inc: { id: string; title: string; network: string }) => (
                <option key={inc.id} value={inc.id}>
                  [{inc.network}] {inc.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Claimant Wallet Address</label>
            <input
              required
              type="text"
              value={form.claimant_address}
              onChange={(e) => setForm((f) => ({ ...f, claimant_address: e.target.value }))}
              placeholder="0x..."
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Coverage Amount (GEN)</label>
              <input
                required
                type="number"
                min="0"
                value={form.coverage_amount}
                onChange={(e) => setForm((f) => ({ ...f, coverage_amount: e.target.value }))}
                placeholder="e.g. 10000"
                className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Claimed Amount (GEN)</label>
              <input
                required
                type="number"
                min="0"
                value={form.claimed_amount}
                onChange={(e) => setForm((f) => ({ ...f, claimed_amount: e.target.value }))}
                placeholder="e.g. 8500"
                className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Policy ID (optional)</label>
            <input
              type="text"
              value={form.policy_id}
              onChange={(e) => setForm((f) => ({ ...f, policy_id: e.target.value }))}
              placeholder="POL-..."
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
            />
          </div>

          <div className="p-3 rounded-lg bg-secondary border border-border text-xs text-muted-foreground">
            Claims are adjudicated by the SlashSure AI on GenLayer StudioNet. The AI evaluates
            coverage eligibility, damage assessment, and payout recommendation.
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-border text-sm font-medium hover:bg-secondary/50 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={mutation.isPending}
              className="flex-1 py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2">
              {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {mutation.isPending ? "Submitting…" : "Submit Claim"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function InsurancePage() {
  const [showModal, setShowModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["insurance-claims", statusFilter, page],
    queryFn: () => insuranceApi.list({ status: statusFilter || undefined, page, per_page: 20 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const STATUSES = ["submitted", "ai_adjudication", "approved", "partial", "rejected", "paid"];

  return (
    <div className="space-y-6 animate-fade-in">
      {showModal && <SubmitClaimModal onClose={() => setShowModal(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Insurance Claims</h1>
          <p className="text-muted-foreground mt-1">AI-adjudicated insurance claims and payouts</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> Submit Claim
        </button>
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
                ? "bg-purple-600 border-purple-600 text-white"
                : "border-border text-muted-foreground hover:border-purple-500/50",
            )}
          >
            {s || "All statuses"}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <FileText className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold">All Claims</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Claim #", "Status", "Coverage", "Claimed", "Approved", "AI Eligible", "Confidence", "Submitted"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading && (
                <tr><td colSpan={8} className="px-6 py-16 text-center text-muted-foreground">Loading…</td></tr>
              )}
              {data?.items?.map((c: {
                id: string; claim_number: string; status: string;
                coverage_amount: number; claimed_amount: number; approved_amount?: number;
                ai_coverage_eligible?: boolean; ai_confidence_score?: number; submitted_at: string;
              }) => (
                <tr key={c.id} className="hover:bg-secondary transition-colors">
                  <td className="px-4 py-4 font-mono text-purple-400">{c.claim_number}</td>
                  <td className="px-4 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(c.status))}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono">{c.coverage_amount != null ? `${formatNumber(c.coverage_amount)} GEN` : "—"}</td>
                  <td className="px-4 py-4 font-mono">{c.claimed_amount != null ? `${formatNumber(c.claimed_amount)} GEN` : "—"}</td>
                  <td className="px-4 py-4 font-mono">
                    {c.approved_amount != null ? `${formatNumber(c.approved_amount)} GEN` : "—"}
                  </td>
                  <td className="px-4 py-4">
                    {c.ai_coverage_eligible === true ? (
                      <span className="text-green-700 text-xs">✓ Eligible</span>
                    ) : c.ai_coverage_eligible === false ? (
                      <span className="text-red-700 text-xs">✗ Ineligible</span>
                    ) : (
                      <span className="text-muted-foreground text-xs">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-4 font-mono">
                    {c.ai_confidence_score != null ? `${c.ai_confidence_score}%` : "—"}
                  </td>
                  <td className="px-4 py-4 text-xs text-muted-foreground whitespace-nowrap">
                    {formatDateTime(c.submitted_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isLoading && !data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">
              No claims submitted yet —{" "}
              <button onClick={() => setShowModal(true)} className="text-purple-400 hover:underline">
                submit one
              </button>
            </div>
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
