"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { incidentsApi } from "@/lib/api";
import { cn, formatDateTime, severityColor, statusColor } from "@/lib/utils";
import { AlertTriangle, Plus } from "lucide-react";

export default function IncidentsPage() {
  const { data } = useQuery({
    queryKey: ["incidents"],
    queryFn: () => incidentsApi.list().then((r) => r.data),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Incidents</h1>
          <p className="text-muted-foreground mt-1">All detected protocol violations and security events</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" /> Report Incident
        </button>
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <h2 className="font-semibold">All Incidents</h2>
          <span className="ml-auto text-xs text-muted-foreground">{data?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary/30">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Title</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Network</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Severity</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">AI Score</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-muted-foreground uppercase">Detected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.items?.map((i: { id: string; title: string; network: string; severity: string; status: string; ai_fault_probability?: number; ai_confidence_score?: number; detected_at: string }) => (
                <tr key={i.id} className="hover:bg-secondary/20 transition-colors cursor-pointer">
                  <td className="px-6 py-4 font-medium">{i.title}</td>
                  <td className="px-6 py-4 text-muted-foreground">{i.network}</td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium border", severityColor(i.severity))}>
                      {i.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2 py-1 rounded text-xs font-medium", statusColor(i.status))}>
                      {i.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {i.ai_fault_probability !== undefined ? (
                      <span className="font-mono">{i.ai_fault_probability}%</span>
                    ) : <span className="text-muted-foreground">Pending</span>}
                  </td>
                  <td className="px-6 py-4 text-muted-foreground text-xs">
                    {formatDateTime(i.detected_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data?.items?.length && (
            <div className="px-6 py-16 text-center text-muted-foreground">No incidents recorded</div>
          )}
        </div>
      </div>
    </div>
  );
}
