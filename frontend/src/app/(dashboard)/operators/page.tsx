"use client";
import { useQuery } from "@tanstack/react-query";
import { operatorsApi } from "@/lib/api";
import { cn, formatNumber, statusColor, truncateAddress } from "@/lib/utils";
import { Users, Plus } from "lucide-react";

export default function OperatorsPage() {
  const { data } = useQuery({
    queryKey: ["operators"],
    queryFn: () => operatorsApi.list().then((r) => r.data),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Operators</h1>
          <p className="text-muted-foreground mt-1">Validators, AVSs, and node operators under monitoring</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Add Operator
        </button>
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <Users className="w-4 h-4 text-blue-400" />
          <h2 className="font-semibold">All Operators</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/30">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Operator</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Network</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Stake</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Uptime</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Slashes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.items?.map((op: { id: string; name: string; address: string; network: string; status: string; total_stake: number; uptime_percentage: number; slash_count: number }) => (
                <tr key={op.id} className="hover:bg-secondary/20 transition-colors cursor-pointer">
                  <td className="px-6 py-4">
                    <div className="font-medium">{op.name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{truncateAddress(op.address)}</div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">{op.network}</td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(op.status))}>
                      {op.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono">{formatNumber(op.total_stake)}</td>
                  <td className="px-6 py-4">
                    <span className={op.uptime_percentage >= 99 ? "text-green-400" : op.uptime_percentage >= 95 ? "text-yellow-400" : "text-red-400"}>
                      {op.uptime_percentage.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={op.slash_count > 0 ? "text-red-400 font-medium" : "text-muted-foreground"}>
                      {op.slash_count}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">No operators registered yet</div>
          )}
        </div>
      </div>
    </div>
  );
}
