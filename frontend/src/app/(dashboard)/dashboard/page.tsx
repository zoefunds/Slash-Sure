"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity, AlertTriangle, Users, FileText, Zap,
  TrendingUp, TrendingDown, Minus, ArrowRight, Shield,
} from "lucide-react";
import Link from "next/link";
import { monitoringApi, genlayerApi, incidentsApi } from "@/lib/api";
import { cn, formatNumber, formatDateTime, severityColor } from "@/lib/utils";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

const NETWORK_COLORS: Record<string, string> = {
  eigenlayer: "#388bfd",
  symbiotic: "#a855f7",
  babylon: "#f59e0b",
  cosmos: "#06b6d4",
};
const FALLBACK_COLORS = ["#388bfd", "#a855f7", "#f59e0b", "#06b6d4", "#22c55e"];

function StatCard({
  title, value, change, icon: Icon, color, href,
}: {
  title: string; value: string | number; change?: number;
  icon: React.ElementType; color: string; href?: string;
}) {
  const TrendIcon = change === undefined ? Minus : change > 0 ? TrendingUp : TrendingDown;
  const trendColor = change === undefined ? "text-muted-foreground" : change > 0 ? "text-red-400" : "text-green-400";
  const content = (
    <div className="p-6 rounded-2xl border border-border bg-card/50 hover:border-blue-500/30 hover:shadow-card-hover transition-all duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", color)}>
          <Icon className="w-5 h-5" />
        </div>
        {change !== undefined && (
          <div className={cn("flex items-center gap-1 text-xs font-medium", trendColor)}>
            <TrendIcon className="w-3.5 h-3.5" />
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{title}</div>
    </div>
  );
  return href ? <Link href={href} className="block">{content}</Link> : content;
}

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => monitoringApi.dashboardStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: contractStats } = useQuery({
    queryKey: ["genlayer-contract-stats"],
    queryFn: () => genlayerApi.getContractStats().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const { data: recentData } = useQuery({
    queryKey: ["recent-incidents"],
    queryFn: () => incidentsApi.list({ per_page: 5 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  // Build area chart from hourly_stats if available, else empty
  const areaData: { time: string; incidents: number; alerts: number }[] =
    stats?.hourly_stats?.map((h: { hour: string; incidents: number; alerts: number }) => ({
      time: h.hour,
      incidents: h.incidents,
      alerts: h.alerts,
    })) ?? [];

  // Build pie chart from network distribution
  const networkData: { name: string; value: number; color: string }[] =
    stats?.network_distribution
      ? Object.entries(stats.network_distribution).map(([name, value], i) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          value: value as number,
          color: NETWORK_COLORS[name.toLowerCase()] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length],
        }))
      : [];

  const recentIncidents = recentData?.items ?? [];

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Security Overview</h1>
        <p className="text-muted-foreground mt-1">
          Real-time monitoring across all networks
        </p>
      </div>

      <div className="flex items-center gap-2 text-sm text-green-400">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        Live monitoring active
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatCard
          title="Active Operators"
          value={formatNumber(stats?.active_operators ?? 0)}
          icon={Users}
          color="bg-blue-500/10 text-blue-400"
          href="/operators"
        />
        <StatCard
          title="Open Incidents"
          value={formatNumber(stats?.open_incidents ?? 0)}
          icon={AlertTriangle}
          color="bg-red-500/10 text-red-400"
          href="/incidents"
        />
        <StatCard
          title="Pending Slashing"
          value={formatNumber(stats?.pending_slashing_cases ?? 0)}
          icon={Zap}
          color="bg-orange-500/10 text-orange-400"
          href="/slashing"
        />
        <StatCard
          title="Active Claims"
          value={formatNumber(stats?.active_insurance_claims ?? 0)}
          icon={FileText}
          color="bg-purple-500/10 text-purple-400"
          href="/insurance"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incidents over time */}
        <div className="lg:col-span-2 p-6 rounded-2xl border border-border bg-card/50">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold">Incident Activity</h3>
              <p className="text-sm text-muted-foreground">Last 24 hours</p>
            </div>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </div>
          {areaData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={areaData}>
                <defs>
                  <linearGradient id="incidentGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#388bfd" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#388bfd" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time" stroke="#555" tick={{ fontSize: 11 }} />
                <YAxis stroke="#555" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#0d1526", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                />
                <Area type="monotone" dataKey="incidents" stroke="#388bfd" fill="url(#incidentGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="alerts" stroke="#ef4444" fill="url(#alertGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm">
              No activity data yet — monitoring worker will populate this
            </div>
          )}
          <div className="flex items-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2"><span className="w-3 h-1 rounded bg-blue-400" /> Incidents</div>
            <div className="flex items-center gap-2"><span className="w-3 h-1 rounded bg-red-400" /> Alerts</div>
          </div>
        </div>

        {/* Network distribution */}
        <div className="p-6 rounded-2xl border border-border bg-card/50">
          <h3 className="font-semibold mb-2">Network Distribution</h3>
          <p className="text-sm text-muted-foreground mb-6">Active operators per network</p>
          {networkData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={networkData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                    {networkData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "#0d1526", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {networkData.map((n) => (
                  <div key={n.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: n.color }} />
                      {n.name}
                    </div>
                    <span className="text-muted-foreground">{n.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm text-center">
              Register operators to see network distribution
            </div>
          )}
        </div>
      </div>

      {/* Recent incidents */}
      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="font-semibold">Recent Incidents</h3>
          <Link href="/incidents" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        <div className="divide-y divide-border">
          {recentIncidents.length > 0 ? recentIncidents.map((inc: {
            id: string; title: string; network: string; severity: string; created_at: string;
          }) => (
            <div key={inc.id} className="flex items-center justify-between px-6 py-4 hover:bg-secondary/30 transition-colors">
              <div className="flex items-center gap-4">
                <div className={cn("px-2 py-1 rounded text-xs font-medium border", severityColor(inc.severity))}>
                  {inc.severity}
                </div>
                <div>
                  <div className="text-sm font-medium">{inc.title}</div>
                  <div className="text-xs text-muted-foreground">{inc.network}</div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">{formatDateTime(inc.created_at)}</div>
            </div>
          )) : (
            <div className="px-6 py-10 text-center text-muted-foreground text-sm">
              No incidents detected yet — monitoring worker is watching
            </div>
          )}
        </div>
      </div>

      {/* GenLayer contract stats */}
      <div className="p-6 rounded-2xl border border-border bg-gradient-to-r from-blue-500/5 to-purple-500/5">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold">GenLayer Contract</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
            StudioNet Live
          </span>
          <a
            href={`https://studio.genlayer.com/contracts/${process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS}`}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto text-xs text-muted-foreground hover:text-blue-400 transition-colors font-mono truncate max-w-[240px]"
          >
            {process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS}
          </a>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Operators", value: contractStats?.total_operators ?? "—" },
            { label: "Slashing Cases", value: contractStats?.total_cases ?? "—" },
            { label: "Insurance Claims", value: contractStats?.total_claims ?? "—" },
            { label: "Audit Entries", value: contractStats?.audit_count ?? "—" },
          ].map((item) => (
            <div key={item.label} className="text-center p-3 rounded-xl bg-card/50 border border-border/50">
              <div className="text-2xl font-bold gradient-text">{item.value}</div>
              <div className="text-xs text-muted-foreground mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
