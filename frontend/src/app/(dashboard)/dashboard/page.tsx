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
  eigenlayer: "#1d4ed8",
  symbiotic: "#7c3aed",
  babylon: "#b45309",
  cosmos: "#0e7490",
};
const FALLBACK_COLORS = ["#1d4ed8", "#7c3aed", "#b45309", "#0e7490", "#15803d"];

function StatCard({
  title, value, change, icon: Icon, colorClass, href,
}: {
  title: string; value: string | number; change?: number;
  icon: React.ElementType; colorClass: string; href?: string;
}) {
  const TrendIcon = change === undefined ? Minus : change > 0 ? TrendingUp : TrendingDown;
  const trendColor = change === undefined ? "text-muted-foreground" : change > 0 ? "text-red-600" : "text-green-600";
  const content = (
    <div className="p-5 rounded-2xl border border-border bg-card hover:bg-secondary transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", colorClass)}>
          <Icon className="w-4 h-4" />
        </div>
        {change !== undefined && (
          <div className={cn("flex items-center gap-1 text-xs font-medium", trendColor)}>
            <TrendIcon className="w-3 h-3" />
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold tracking-tight mb-0.5">{value}</div>
      <div className="text-xs text-muted-foreground">{title}</div>
    </div>
  );
  return href ? <Link href={href} className="block">{content}</Link> : content;
}

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => monitoringApi.dashboardStats().then((r) => r.data),
    refetchInterval: 10_000,
  });

  const { data: contractStats, isError: contractError } = useQuery({
    queryKey: ["genlayer-contract-stats"],
    queryFn: () => genlayerApi.getContractStats().then((r) => r.data),
    refetchInterval: 10_000,
    retry: 1,
  });

  const { data: recentData } = useQuery({
    queryKey: ["recent-incidents"],
    queryFn: () => incidentsApi.list({ per_page: 5 }).then((r) => r.data),
    refetchInterval: 10_000,
  });

  const areaData: { time: string; incidents: number; alerts: number }[] =
    stats?.hourly_stats?.map((h: { hour: string; incidents: number; alerts: number }) => ({
      time: h.hour, incidents: h.incidents, alerts: h.alerts,
    })) ?? [];

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
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Security Overview</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Real-time monitoring across all networks</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-green-700 font-medium bg-green-50 border border-green-200 px-3 py-1.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-green-600" />
          Live monitoring active
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Active Operators" value={formatNumber(stats?.active_operators ?? 0)}
          icon={Users} colorClass="bg-blue-100 text-blue-700" href="/operators" />
        <StatCard title="Open Incidents" value={formatNumber(stats?.open_incidents ?? 0)}
          icon={AlertTriangle} colorClass="bg-red-100 text-red-700" href="/incidents" />
        <StatCard title="Pending Slashing" value={formatNumber(stats?.pending_slashing_cases ?? 0)}
          icon={Zap} colorClass="bg-amber-100 text-amber-700" href="/slashing" />
        <StatCard title="Active Claims" value={formatNumber(stats?.active_insurance_claims ?? 0)}
          icon={FileText} colorClass="bg-purple-100 text-purple-700" href="/insurance" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 p-5 rounded-2xl border border-border bg-card">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-semibold text-sm">Incident Activity</h3>
              <p className="text-xs text-muted-foreground">Last 24 hours</p>
            </div>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </div>
          {areaData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={areaData}>
                <defs>
                  <linearGradient id="incidentGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1d4ed8" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="#1d4ed8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#b91c1c" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="#b91c1c" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis dataKey="time" stroke="#a09080" tick={{ fontSize: 11 }} />
                <YAxis stroke="#a09080" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#f5f2ec", border: "1px solid #d4cfc5", borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="incidents" stroke="#1d4ed8" fill="url(#incidentGrad)" strokeWidth={1.5} />
                <Area type="monotone" dataKey="alerts" stroke="#b91c1c" fill="url(#alertGrad)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
              No activity data yet — monitoring worker will populate this
            </div>
          )}
          <div className="flex items-center gap-5 mt-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 rounded bg-blue-700 inline-block" /> Incidents</div>
            <div className="flex items-center gap-1.5"><span className="w-3 h-0.5 rounded bg-red-700 inline-block" /> Alerts</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-border bg-card">
          <h3 className="font-semibold text-sm mb-1">Network Distribution</h3>
          <p className="text-xs text-muted-foreground mb-5">Active operators per network</p>
          {networkData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={networkData} cx="50%" cy="50%" innerRadius={38} outerRadius={58} paddingAngle={3} dataKey="value">
                    {networkData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#f5f2ec", border: "1px solid #d4cfc5", borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-3">
                {networkData.map((n) => (
                  <div key={n.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: n.color }} />
                      <span className="text-muted-foreground">{n.name}</span>
                    </div>
                    <span className="font-medium">{n.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[180px] flex items-center justify-center text-muted-foreground text-xs text-center px-4">
              Register operators to see network distribution
            </div>
          )}
        </div>
      </div>

      {/* Recent incidents */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="font-semibold text-sm">Recent Incidents</h3>
          <Link href="/incidents" className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="divide-y divide-border">
          {recentIncidents.length > 0 ? recentIncidents.map((inc: {
            id: string; title: string; network: string; severity: string; created_at: string;
          }) => (
            <div key={inc.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-secondary transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn("px-2 py-0.5 rounded text-xs font-medium border", severityColor(inc.severity))}>
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
            <div className="px-5 py-10 text-center text-muted-foreground text-sm">
              No incidents detected yet — monitoring worker is watching
            </div>
          )}
        </div>
      </div>

      {/* GenLayer contract stats */}
      <div className="p-5 rounded-2xl border border-border bg-card">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-4 h-4 text-muted-foreground" />
          <h3 className="font-semibold text-sm">GenLayer Contract</h3>
          <span className={cn(
            "text-xs px-2 py-0.5 rounded-full font-medium border",
            contractError
              ? "bg-amber-100 text-amber-700 border-amber-200"
              : "bg-green-100 text-green-700 border-green-200"
          )}>
            {contractError ? "StudioNet Unreachable" : "StudioNet Live"}
          </span>
          <a
            href={`https://explorer-studio.genlayer.com/contracts/${process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS}`}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto text-xs text-muted-foreground hover:text-foreground transition-colors font-mono truncate max-w-[220px]"
          >
            {process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS}
          </a>
        </div>
        {contractError ? (
          <p className="text-xs text-muted-foreground py-2">
            GenLayer StudioNet is not responding. On-chain stats will appear once the network is reachable.
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Total Operators", value: contractStats?.total_operators ?? "—" },
              { label: "Slashing Cases", value: contractStats?.total_cases ?? "—" },
              { label: "Insurance Claims", value: contractStats?.total_claims ?? "—" },
              { label: "Audit Entries", value: contractStats?.audit_count ?? "—" },
            ].map((item) => (
              <div key={item.label} className="text-center p-3 rounded-xl bg-background border border-border">
                <div className="text-xl font-bold tracking-tight">{item.value}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{item.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
