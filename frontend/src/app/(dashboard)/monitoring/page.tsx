"use client";
import { useQuery } from "@tanstack/react-query";
import { monitoringApi } from "@/lib/api";
import { cn, formatDateTime, severityColor } from "@/lib/utils";
import { Activity, Bell, CheckCheck } from "lucide-react";

export default function MonitoringPage() {
  const { data: events } = useQuery({
    queryKey: ["monitoring-events"],
    queryFn: () => monitoringApi.events().then((r) => r.data),
    refetchInterval: 10_000,
  });
  const { data: alerts, refetch: refetchAlerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => monitoringApi.alerts({ acknowledged: false }).then((r) => r.data),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Live Monitoring</h1>
        <p className="text-muted-foreground mt-1">Real-time blockchain events and security alerts</p>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
          <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
            <Activity className="w-4 h-4 text-blue-400" />
            <h2 className="font-semibold">Network Events</h2>
            <span className="ml-auto text-xs text-muted-foreground">{events?.total ?? 0} total</span>
          </div>
          <div className="divide-y divide-border max-h-96 overflow-y-auto">
            {events?.items?.length ? events.items.map((e: { id: string; event_type: string; network: string; severity: string; summary: string; occurred_at: string }) => (
              <div key={e.id} className="px-6 py-3 hover:bg-secondary/20 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("px-1.5 py-0.5 rounded text-xs font-medium border", severityColor(e.severity))}>
                        {e.severity}
                      </span>
                      <span className="text-xs text-muted-foreground">{e.network}</span>
                    </div>
                    <div className="text-sm">{e.event_type.replace(/_/g, " ")}</div>
                  </div>
                  <div className="text-xs text-muted-foreground whitespace-nowrap">
                    {e.occurred_at ? formatDateTime(e.occurred_at) : "—"}
                  </div>
                </div>
              </div>
            )) : (
              <div className="px-6 py-12 text-center text-muted-foreground text-sm">No events yet</div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
          <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
            <Bell className="w-4 h-4 text-yellow-400" />
            <h2 className="font-semibold">Active Alerts</h2>
            <span className="ml-auto text-xs text-muted-foreground">{alerts?.total ?? 0} unacknowledged</span>
          </div>
          <div className="divide-y divide-border max-h-96 overflow-y-auto">
            {alerts?.items?.length ? alerts.items.map((a: { id: string; title: string; message: string; severity: string; created_at: string }) => (
              <div key={a.id} className="px-6 py-3 hover:bg-secondary/20 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("px-1.5 py-0.5 rounded text-xs font-medium border", severityColor(a.severity))}>
                        {a.severity}
                      </span>
                    </div>
                    <div className="text-sm font-medium">{a.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{a.message}</div>
                  </div>
                  <button onClick={async () => { await monitoringApi.acknowledgeAlert(a.id); refetchAlerts(); }}
                    className="text-xs text-muted-foreground hover:text-green-400 flex items-center gap-1 transition-colors shrink-0">
                    <CheckCheck className="w-3.5 h-3.5" /> Ack
                  </button>
                </div>
              </div>
            )) : (
              <div className="px-6 py-12 text-center text-muted-foreground text-sm">No active alerts</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
