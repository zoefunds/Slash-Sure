"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { authApi, operatorsApi, incidentsApi, adminApi } from "@/lib/api";
import { Shield, Users, AlertTriangle, Activity, BarChart3, UserCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AdminPage() {
  const user = useAuthStore((s) => s.user);
  const router = useRouter();

  // Fetch current user to get fresh is_superadmin flag
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me().then((r) => r.data),
  });

  useEffect(() => {
    if (me && !me.is_superadmin) {
      router.replace("/dashboard");
    }
  }, [me, router]);

  const { data: operators } = useQuery({
    queryKey: ["operators"],
    queryFn: () => operatorsApi.list({ per_page: 100 }).then((r) => r.data),
  });

  const { data: incidents } = useQuery({
    queryKey: ["incidents"],
    queryFn: () => incidentsApi.list().then((r) => r.data),
  });

  const isSuperadmin = me?.is_superadmin;

  const { data: usersData } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminApi.listUsers({ per_page: 100 }).then((r) => r.data),
    enabled: !!isSuperadmin,
  });
  if (!isSuperadmin) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground text-sm">Checking permissions…</p>
      </div>
    );
  }

  const userList = usersData?.items ?? [];
  const operatorList = operators?.items ?? [];
  const incidentList = incidents?.items ?? [];

  const stats = [
    { label: "Total Users", value: usersData?.total ?? 0, icon: UserCheck, color: "text-indigo-700" },
    { label: "Total Operators", value: operators?.total ?? 0, icon: Users, color: "text-blue-700" },
    { label: "Total Incidents", value: incidents?.total ?? 0, icon: AlertTriangle, color: "text-red-700" },
    { label: "AI Reviews", value: incidentList.filter((i: { status: string }) => i.status === "ai_review").length, icon: BarChart3, color: "text-purple-700" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Shield className="w-5 h-5 text-foreground" />
        <div>
          <h1 className="text-xl font-bold">Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">System overview — superadmin access</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="p-5 rounded-xl border border-border bg-card">
            <s.icon className={cn("w-4 h-4 mb-3", s.color)} />
            <div className="text-2xl font-bold mb-0.5">{s.value}</div>
            <div className="text-xs text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Users table */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <UserCheck className="w-4 h-4 text-indigo-600" />
          <h2 className="font-semibold text-sm">All Users</h2>
          <span className="ml-auto text-xs text-muted-foreground">{userList.length} registered</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Name", "Email", "Verified", "Superadmin", "Joined", "Last Login"].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {userList.map((u: {
                id: string; full_name?: string; email: string;
                is_verified: boolean; is_superadmin: boolean;
                created_at: string; last_login_at?: string;
              }) => (
                <tr key={u.id} className="hover:bg-secondary/50 transition-colors">
                  <td className="px-5 py-3.5 font-medium">{u.full_name || "—"}</td>
                  <td className="px-5 py-3.5 text-muted-foreground">{u.email}</td>
                  <td className="px-5 py-3.5">
                    <span className={cn("px-2 py-0.5 rounded text-xs font-medium",
                      u.is_verified ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                    )}>{u.is_verified ? "Verified" : "Unverified"}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    {u.is_superadmin && (
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">Admin</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-muted-foreground text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="px-5 py-3.5 text-muted-foreground text-xs">{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
              {userList.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground text-sm">No users found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Operators table */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <Users className="w-4 h-4 text-muted-foreground" />
          <h2 className="font-semibold text-sm">All Operators</h2>
          <span className="ml-auto text-xs text-muted-foreground">{operatorList.length} registered</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Address", "Network", "Status", "Stake", "Uptime", "Slash Count"].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {operatorList.map((op: {
                id: string; address: string; network: string; status: string;
                total_stake: number; uptime_percentage: number; slash_count: number;
              }) => (
                <tr key={op.id} className="hover:bg-secondary/50 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-xs">{op.address.slice(0, 10)}…{op.address.slice(-6)}</td>
                  <td className="px-5 py-3.5 capitalize text-muted-foreground">{op.network}</td>
                  <td className="px-5 py-3.5">
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">{op.status}</span>
                  </td>
                  <td className="px-5 py-3.5 tabular-nums">{op.total_stake.toLocaleString()} GEN</td>
                  <td className="px-5 py-3.5 tabular-nums">{op.uptime_percentage}%</td>
                  <td className="px-5 py-3.5 tabular-nums">{op.slash_count}</td>
                </tr>
              ))}
              {operatorList.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground text-sm">No operators registered</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent incidents */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <h2 className="font-semibold text-sm">All Incidents</h2>
          <span className="ml-auto text-xs text-muted-foreground">{incidentList.length} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-secondary">
              <tr>
                {["Title", "Network", "Severity", "Status", "AI Score", "Detected"].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {incidentList.map((i: {
                id: string; title: string; network: string; severity: string;
                status: string; ai_fault_probability?: number; detected_at: string;
              }) => (
                <tr key={i.id} className="hover:bg-secondary/50 transition-colors">
                  <td className="px-5 py-3.5 font-medium">{i.title}</td>
                  <td className="px-5 py-3.5 text-muted-foreground capitalize">{i.network}</td>
                  <td className="px-5 py-3.5">
                    <span className={cn("px-2 py-0.5 rounded text-xs font-medium",
                      i.severity === "critical" ? "bg-red-100 text-red-800" :
                      i.severity === "high" ? "bg-orange-100 text-orange-800" :
                      "bg-yellow-100 text-yellow-800"
                    )}>{i.severity}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="px-2 py-0.5 rounded text-xs bg-secondary text-muted-foreground">{i.status}</span>
                  </td>
                  <td className="px-5 py-3.5 tabular-nums">{i.ai_fault_probability != null ? `${i.ai_fault_probability}%` : "—"}</td>
                  <td className="px-5 py-3.5 text-muted-foreground text-xs">{new Date(i.detected_at).toLocaleString()}</td>
                </tr>
              ))}
              {incidentList.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground text-sm">No incidents recorded</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
