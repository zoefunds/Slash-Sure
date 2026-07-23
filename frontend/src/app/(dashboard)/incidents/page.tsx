"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { incidentsApi, operatorsApi } from "@/lib/api";
import { cn, formatDateTime, severityColor, statusColor } from "@/lib/utils";
import { AlertTriangle, Plus, X, Loader2 } from "lucide-react";

const NETWORKS = ["eigenlayer", "symbiotic", "babylon", "cosmos"];
const SEVERITIES = ["low", "medium", "high", "critical"];
const INCIDENT_TYPES = [
  { value: "double_sign", label: "Double Sign" },
  { value: "downtime", label: "Downtime" },
  { value: "protocol_violation", label: "Protocol Violation" },
  { value: "slashing_risk", label: "Slashing Risk" },
  { value: "stake_manipulation", label: "Stake Manipulation" },
  { value: "other", label: "Other" },
];

function ReportIncidentModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    title: "", network: "eigenlayer", severity: "medium",
    incident_type: "protocol_violation", operator_address: "", description: "",
    evidence_url: "", evidence_title: "", evidence_block_number: "",
  });
  const [error, setError] = useState("");
  const [txResult, setTxResult] = useState<{ tx_hash?: string; status?: string } | null>(null);

  const { data: operators } = useQuery({
    queryKey: ["operators"],
    queryFn: () => operatorsApi.list().then((r) => r.data),
  });

  const mutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const created = await incidentsApi.create(data);
      return created;
    },
    onSuccess: async (res, variables) => {
      qc.invalidateQueries({ queryKey: ["incidents"] });
      setTxResult(null);
      const incidentId = res.data?.id as string | undefined;
      if (!incidentId) {
        onClose();
        return;
      }
      const webEvidence = await incidentsApi.addWebEvidence(incidentId, {
        incident_type: variables.incident_type,
        network: variables.network,
        title: variables.evidence_title,
        evidence_url: variables.evidence_url,
        operator_address: variables.operator_address,
        block_number: variables.evidence_block_number ? Number(variables.evidence_block_number) : undefined,
        description: variables.description,
      });
      setTxResult(webEvidence.data?.on_chain || null);
      qc.invalidateQueries({ queryKey: ["incidents"] });
      setTimeout(onClose, 1200);
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Failed to report incident");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate({
      title: form.title,
      network: form.network,
      severity: form.severity,
      incident_type: form.incident_type,
      operator_address: form.operator_address,
      description: form.description,
      evidence_url: form.evidence_url,
      evidence_title: form.evidence_title,
      evidence_block_number: form.evidence_block_number,
    });
  };

  const inputCls = "w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold">Report Incident</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
        )}
        {txResult?.tx_hash && (
          <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
            On-chain tx {txResult.tx_hash} finalized as {txResult.status || "pending"}.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">Incident Title *</label>
            <input
              required
              value={form.title}
              onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="e.g. Double-sign detected on EigenLayer"
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Incident Type *</label>
            <select
              required
              value={form.incident_type}
              onChange={(e) => setForm(f => ({ ...f, incident_type: e.target.value }))}
              className={inputCls}
            >
              {INCIDENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Network *</label>
              <select
                required
                value={form.network}
                onChange={(e) => setForm(f => ({ ...f, network: e.target.value }))}
                className={inputCls}
              >
                {NETWORKS.map(n => <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Severity *</label>
              <select
                required
                value={form.severity}
                onChange={(e) => setForm(f => ({ ...f, severity: e.target.value }))}
                className={inputCls}
              >
                {SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Operator *</label>
            <select
              required
              value={form.operator_address}
              onChange={(e) => setForm(f => ({ ...f, operator_address: e.target.value }))}
              className={inputCls}
            >
              <option value="">Select operator…</option>
              {operators?.items?.map((op: { id: string; name: string; address: string }) => (
                <option key={op.id} value={op.address}>{op.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Description *</label>
            <textarea
              required
              value={form.description}
              onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Describe the violation in detail…"
              rows={3}
              className={inputCls + " resize-none"}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Evidence Title *</label>
            <input
              required
              value={form.evidence_title}
              onChange={(e) => setForm(f => ({ ...f, evidence_title: e.target.value }))}
              placeholder="e.g. validator dashboard snapshot"
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Evidence URL *</label>
            <input
              required
              value={form.evidence_url}
              onChange={(e) => setForm(f => ({ ...f, evidence_url: e.target.value }))}
              placeholder="https://..."
              className={inputCls}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Evidence Block Number *</label>
            <input
              required
              type="number"
              min="0"
              value={form.evidence_block_number}
              onChange={(e) => setForm(f => ({ ...f, evidence_block_number: e.target.value }))}
              placeholder="e.g. 1234567"
              className={inputCls}
            />
          </div>

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-border text-sm font-medium hover:bg-secondary transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={mutation.isPending}
              className="flex-1 py-2.5 rounded-lg bg-foreground text-background disabled:opacity-50 text-sm font-semibold hover:opacity-85 transition-opacity flex items-center justify-center gap-2">
              {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {mutation.isPending ? "Reporting…" : "Report + Evidence"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function IncidentsPage() {
  const [showModal, setShowModal] = useState(false);

  const { data } = useQuery({
    queryKey: ["incidents"],
    queryFn: () => incidentsApi.list().then((r) => r.data),
    refetchInterval: 10_000,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {showModal && <ReportIncidentModal onClose={() => setShowModal(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Incidents</h1>
          <p className="text-sm text-muted-foreground mt-0.5">All detected protocol violations and security events</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-85 transition-opacity"
        >
          <Plus className="w-4 h-4" /> Report Incident
        </button>
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <h2 className="font-semibold text-sm">All Incidents</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Title", "Network", "Severity", "Status", "AI Score", "Detected"].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.items?.map((i: {
                id: string; title: string; network: string; severity: string;
                status: string; ai_fault_probability?: number; detected_at: string;
              }) => (
                <tr key={i.id} className="hover:bg-secondary/50 transition-colors cursor-pointer">
                  <td className="px-5 py-3.5 font-medium">{i.title}</td>
                  <td className="px-5 py-3.5 text-muted-foreground capitalize">{i.network}</td>
                  <td className="px-5 py-3.5">
                    <span className={cn("px-2 py-0.5 rounded text-xs font-medium border", severityColor(i.severity))}>{i.severity}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={cn("px-2 py-0.5 rounded text-xs font-medium", statusColor(i.status))}>{i.status}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    {i.ai_fault_probability !== undefined
                      ? <span className="font-mono text-xs">{i.ai_fault_probability}%</span>
                      : <span className="text-muted-foreground text-xs">Pending</span>}
                  </td>
                  <td className="px-5 py-3.5 text-muted-foreground text-xs">{formatDateTime(i.detected_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.items?.length && (
            <div className="px-5 py-16 text-center text-muted-foreground text-sm">
              No incidents recorded —{" "}
              <button onClick={() => setShowModal(true)} className="underline hover:text-foreground transition-colors">
                report one
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
