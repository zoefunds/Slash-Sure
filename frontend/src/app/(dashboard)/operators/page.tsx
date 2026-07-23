"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CONTRACT_ADDRESS, authApi, operatorsApi } from "@/lib/api";
import { cn, formatNumber, statusColor, truncateAddress } from "@/lib/utils";
import { Users, Plus, X, Loader2, Wallet, ArrowRight } from "lucide-react";
import { RecordDetailDrawer } from "@/components/dashboard/RecordDetailDrawer";

interface OperatorForm {
  name: string;
  address: string;
  network: string;
  total_stake: string;
  commission_rate: string;
  description: string;
  website: string;
}

const NETWORKS = ["eigenlayer", "symbiotic", "babylon", "cosmos"];

function AddOperatorModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<OperatorForm>({
    name: "", address: "", network: "eigenlayer",
    total_stake: "", commission_rate: "0", description: "", website: "",
  });
  const [error, setError] = useState("");
  const [txResult, setTxResult] = useState<{ tx_hash?: string | null; status?: string } | null>(null);

  const { data: balanceData, isLoading: balanceLoading } = useQuery({
    queryKey: ["wallet-balance"],
    queryFn: () => authApi.balance().then((r) => r.data),
  });

  const stakeGen = Number(form.total_stake || 0);
  const balanceGen = Number(balanceData?.balance_gen || 0);
  const insufficientBalance = stakeGen > 0 && balanceData && stakeGen > balanceGen;

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => operatorsApi.create(data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["operators", CONTRACT_ADDRESS] });
      setTxResult(res.data?.on_chain || null);
      if (res.data?.on_chain?.status === "finalized" || res.data?.on_chain?.status === "already_registered") {
        setTimeout(onClose, 1200);
      }
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Failed to register operator");
    },
  });

  const handleSubmit = (ev: React.FormEvent) => {
    ev.preventDefault();
    setError("");
    if (insufficientBalance) {
      setError("Your GEN balance is lower than the stake amount.");
      return;
    }
    mutation.mutate({
      name: form.name,
      address: form.address,
      network: form.network,
      total_stake: parseFloat(form.total_stake) || 0,
      commission_rate: parseFloat(form.commission_rate) || 0,
      description: form.description || undefined,
      website: form.website || undefined,
    });
  };

  const field = (key: keyof OperatorForm, label: string, placeholder: string, type = "text") => (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}</label>
      <input
        required
        type={type}
        value={form[key]}
        onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">Register Operator</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 rounded-lg border border-border bg-secondary/40 p-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Wallet className="w-3.5 h-3.5" />
            <span>Wallet balance</span>
          </div>
          <div className="text-sm font-medium">
            {balanceLoading ? "Loading…" : `${balanceGen.toLocaleString(undefined, { maximumFractionDigits: 6 })} GEN`}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {txResult && (
          <div className="mb-4 p-3 rounded-lg border border-border bg-secondary/40 text-sm space-y-1">
            <div className="font-medium">On-chain status: {txResult.status || "pending"}</div>
            <div className="text-muted-foreground break-all">
              {txResult.tx_hash ? `Tx: ${txResult.tx_hash}` : "Transaction submitted without a hash."}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {field("name", "Operator Name", "e.g. Chorus One")}
          {field("address", "Wallet Address", "0x...")}

          <div>
            <label className="block text-sm font-medium mb-1.5">Network</label>
            <select
              required
              value={form.network}
              onChange={(e) => setForm((f) => ({ ...f, network: e.target.value }))}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-foreground/15 text-sm"
            >
              {NETWORKS.map((n) => (
                <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1)}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {field("total_stake", "Total Stake (GEN)", "e.g. 10000", "number")}
            {field("commission_rate", "Commission (%)", "e.g. 5", "number")}
          </div>

          {insufficientBalance && (
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm">
              Stake exceeds wallet balance. Add funds or lower the GEN amount before submitting.
            </div>
          )}

          {field("description", "Description *", "Brief description")}
          {field("website", "Website *", "https://")}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-border text-sm font-medium hover:bg-secondary transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending || insufficientBalance}
              className="flex-1 py-2.5 rounded-lg bg-foreground text-background disabled:opacity-50 hover:opacity-85 text-sm font-semibold transition-colors flex items-center justify-center gap-2"
            >
              {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {mutation.isPending ? "Registering…" : "Register On-Chain"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function OperatorsPage() {
  const [showModal, setShowModal] = useState(false);
  const [network, setNetwork] = useState("");
  const [page, setPage] = useState(1);
  const [selectedOperatorId, setSelectedOperatorId] = useState<string | null>(null);
  const [selectedOperatorRow, setSelectedOperatorRow] = useState<{
    id: string; name: string; address: string; network: string;
    status: string; total_stake: number; uptime_percentage: number; slash_count: number;
    commission_rate?: number; description?: string;
  } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["operators", CONTRACT_ADDRESS, network, page],
    queryFn: () => operatorsApi.list({ network: network || undefined, page, per_page: 20 }).then((r) => r.data),
    refetchInterval: 10_000,
  });

  const { data: selectedOperator } = useQuery({
    queryKey: ["operator-detail", CONTRACT_ADDRESS, selectedOperatorId],
    queryFn: () => operatorsApi.get(selectedOperatorId as string).then((r) => r.data),
    enabled: !!selectedOperatorId,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {showModal && <AddOperatorModal onClose={() => setShowModal(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Operators</h1>
          <p className="text-muted-foreground mt-1">Validators, AVSs, and node operators under monitoring</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-85 transition-opacity"
        >
          <Plus className="w-4 h-4" /> Add Operator
        </button>
      </div>

      {/* Network filter chips */}
      <div className="flex gap-2 flex-wrap">
        {["", ...NETWORKS].map((n) => (
          <button
            key={n || "all"}
            onClick={() => { setNetwork(n); setPage(1); }}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize",
              network === n
                ? "bg-foreground border-foreground text-background"
                : "border-border text-muted-foreground hover:border-foreground/30",
            )}
          >
            {n || "All networks"}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <Users className="w-4 h-4 text-muted-foreground" />
          <h2 className="font-semibold">All Operators</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Operator", "Network", "Status", "Stake", "Uptime", "Slashes", "Details"].map((h) => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading && (
                <tr><td colSpan={7} className="px-6 py-16 text-center text-muted-foreground">Loading…</td></tr>
              )}
              {data?.items?.map((op: {
                id: string; name: string; address: string; network: string;
                status: string; total_stake: number; uptime_percentage: number; slash_count: number;
              }) => (
                <tr
                  key={op.id}
                  className="hover:bg-secondary transition-colors cursor-pointer"
                  onClick={() => { setSelectedOperatorId(op.id); setSelectedOperatorRow(op); }}
                >
                  <td className="px-6 py-4">
                    <div className="font-medium">{op.name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{truncateAddress(op.address)}</div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground capitalize">{op.network}</td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(op.status))}>
                      {op.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono">{formatNumber(op.total_stake)} GEN</td>
                  <td className="px-6 py-4">
                    <span className={
                      op.uptime_percentage >= 99 ? "text-green-700"
                      : op.uptime_percentage >= 95 ? "text-amber-700"
                      : "text-red-700"
                    }>
                      {op.uptime_percentage.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={op.slash_count > 0 ? "text-red-700 font-medium" : "text-muted-foreground"}>
                      {op.slash_count}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setSelectedOperatorId(op.id); setSelectedOperatorRow(op); }}
                      className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
                    >
                      Details <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isLoading && !data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">
              No operators registered yet —{" "}
              <button onClick={() => setShowModal(true)} className="underline hover:text-foreground">
                add one
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
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-40 hover:bg-secondary/50"
              >
                Prev
              </button>
              <button
                disabled={page >= Math.ceil((data?.total ?? 0) / 20)}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded border border-border text-xs disabled:opacity-40 hover:bg-secondary/50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      <RecordDetailDrawer
        open={!!selectedOperatorId}
        onClose={() => setSelectedOperatorId(null)}
        title={selectedOperator?.name || selectedOperatorRow?.name || "Operator details"}
        subtitle={selectedOperator?.address ? truncateAddress(selectedOperator.address, 8) : selectedOperatorRow?.address ? truncateAddress(selectedOperatorRow.address, 8) : undefined}
        isLoading={selectedOperatorId !== null && !selectedOperator && !!selectedOperatorRow}
        sections={[
          { label: "Name", value: selectedOperator?.name ?? selectedOperatorRow?.name },
          { label: "Address", value: selectedOperator?.address ?? selectedOperatorRow?.address },
          { label: "Network", value: selectedOperator?.network ?? selectedOperatorRow?.network },
          { label: "Status", value: selectedOperator?.status ?? selectedOperatorRow?.status },
          { label: "Stake", value: selectedOperator?.total_stake != null ? `${formatNumber(selectedOperator.total_stake)} GEN` : selectedOperatorRow?.total_stake != null ? `${formatNumber(selectedOperatorRow.total_stake)} GEN` : "—" },
          { label: "Commission", value: selectedOperator?.commission_rate != null ? `${selectedOperator.commission_rate}%` : selectedOperatorRow?.commission_rate != null ? `${selectedOperatorRow.commission_rate}%` : "—" },
          { label: "Uptime", value: selectedOperator?.uptime_percentage != null ? `${Number(selectedOperator.uptime_percentage).toFixed(2)}%` : selectedOperatorRow?.uptime_percentage != null ? `${Number(selectedOperatorRow.uptime_percentage).toFixed(2)}%` : "—" },
          { label: "Slash count", value: selectedOperator?.slash_count ?? selectedOperatorRow?.slash_count ?? "—" },
          { label: "Website", value: selectedOperator?.website },
          { label: "Description", value: selectedOperator?.description ?? selectedOperatorRow?.description },
          { label: "Registered", value: selectedOperator?.created_at },
          { label: "Updated", value: selectedOperator?.updated_at },
        ]}
        raw={(selectedOperator ?? selectedOperatorRow) as Record<string, unknown> | null}
      />
    </div>
  );
}
