"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity, AlertTriangle, Users, FileText, Zap, TrendingUp,
  TrendingDown, Minus, ArrowRight, Shield, Globe
} from "lucide-react";
import Link from "next/link";
import { monitoringApi } from "@/lib/api";
import { cn, formatNumber, formatDateTime, severityColor, statusColor } from "@/lib/utils";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell,
} from "recharts";

const areaData = [
  { time: "00:00", incidents: 2, alerts: 5 },
  { time: "04:00", incidents: 1, alerts: 3 },
  { time: "08:00", incidents: 5, alerts: 12 },
  { time: "12:00", incidents: 8, alerts: 18 },
  { time: "16:00", incidents: 4, alerts: 9 },
  { time: "20:00", incidents: 6, alerts: 14 },
  { time: "Now", incidents: 3, alerts: 7 },
];

const networkData = [
  { name: "EigenLayer", value: 45, color: "#388bfd" },
  { name: "Symbiotic", value: 28, color: "#a855f7" },
  { name: "Babylon", value: 18, color: "#f59e0b" },
  { name: "Cosmos", value: 9, color: "#06b6d4" },
];

const recentIncidents = [
  { id: "1", title: "Validator downtime detected", network: "EigenLayer", severity: "high", time: "2 min ago" },
  { id: "2", title: "Oracle price deviation", network: "Symbiotic", severity: "critical", time: "8 min ago" },
  { id: "3", title: "Missed blocks threshold exceeded", network: "Cosmos", severity: "medium", time: "15 min ago" },
  { id: "4", title: "Unusual withdrawal pattern", network: "Babylon", severity: "low", time: "32 min ago" },
];

function StatCard({
  title, value, change, icon: Icon, color, href
}: {
  title: string; value: string | number; change?: number;
  icon: React.ElementType; color: string; href?: string;
}) {
  const TrendIcon = change === undefined ? Minus : change > 0 ? TrendingUp : TrendingDown;
  const trendColor = change === undefined ? "text-muted-foreground" : change > 0 ? "text-red-400" : "text-green-400";

  const content = (
    <div className="p-6 rounded-2xl border border-border bg-card/50 hover:border-blue-500/30 hover:shadow-card-hover transition-all duration-200 group">
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

  return href ? (
    <Link href={href} className="block">{content}</Link>
  ) : (
    content
  );
}

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => monitoringApi.dashboardStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Security Overview</h1>
        <p className="text-muted-foreground mt-1">
          Real-time monitoring across all networks — last updated just now
        </p>
      </div>

      {/* Live indicator */}
      <div className="flex items-center gap-2 text-sm text-green-400">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        Live monitoring active — all systems operational
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatCard
          title="Active Operators"
          value={stats?.active_operators ?? "—"}
          change={2.4}
          icon={Users}
          color="bg-blue-500/10 text-blue-400"
          href="/operators"
        />
        <StatCard
          title="Open Incidents"
          value={stats?.open_incidents ?? "—"}
          change={12}
          icon={AlertTriangle}
          color="bg-red-500/10 text-red-400"
          href="/incidents"
        />
        <StatCard
          title="Pending Slashing"
          value={stats?.pending_slashing_cases ?? "—"}
          change={-5}
          icon={Zap}
          color="bg-orange-500/10 text-orange-400"
          href="/slashing"
        />
        <StatCard
          title="Active Claims"
          value={stats?.active_insurance_claims ?? "—"}
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
          </div>
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
          <div className="flex items-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2"><span className="w-3 h-1 rounded bg-blue-400" /> Incidents</div>
            <div className="flex items-center gap-2"><span className="w-3 h-1 rounded bg-red-400" /> Alerts</div>
          </div>
        </div>

        {/* Network distribution */}
        <div className="p-6 rounded-2xl border border-border bg-card/50">
          <h3 className="font-semibold mb-2">Network Distribution</h3>
          <p className="text-sm text-muted-foreground mb-6">Active operators per network</p>
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
                <span className="text-muted-foreground">{n.value}%</span>
              </div>
            ))}
          </div>
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
          {recentIncidents.map((inc) => (
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
              <div className="text-xs text-muted-foreground">{inc.time}</div>
            </div>
          ))}
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
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total Operators", value: stats?.total_operators ?? "—" },
            { label: "Slashing Cases", value: "—" },
            { label: "Insurance Claims", value: "—" },
            { label: "Audit Entries", value: "—" },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-2xl font-bold gradient-text">{item.value}</div>
              <div className="text-xs text-muted-foreground mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
