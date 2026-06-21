"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Activity, AlertTriangle,
  Users, BarChart3, FileText, Zap, Scale, Settings, LogOut, ChevronLeft, Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { LogoIcon } from "@/components/ui/Logo";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/lib/api";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/monitoring", icon: Activity, label: "Monitoring" },
  { href: "/operators", icon: Users, label: "Operators" },
  { href: "/incidents", icon: AlertTriangle, label: "Incidents" },
  { href: "/risk-scores", icon: BarChart3, label: "Risk Scores" },
  { href: "/slashing", icon: Zap, label: "Slashing" },
  { href: "/insurance", icon: FileText, label: "Insurance" },
  { href: "/governance", icon: Scale, label: "Governance" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me().then((r) => r.data),
    staleTime: 60_000,
  });
  const isSuperadmin = me?.is_superadmin ?? false;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-card transition-all duration-300",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="h-[60px] flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2 font-bold text-sm">
            <LogoIcon className="w-6 h-6 shrink-0" />
            <span>SlashSure</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/" className="mx-auto">
            <LogoIcon className="w-6 h-6" />
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-muted-foreground hover:text-foreground transition-colors ml-auto"
        >
          <ChevronLeft className={cn("w-3.5 h-3.5 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-100",
                active
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              <item.icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
        {isSuperadmin && (
          <Link
            href="/admin"
            className={cn(
              "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-100",
              pathname === "/admin" || pathname.startsWith("/admin/")
                ? "bg-foreground text-background"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            )}
          >
            <Shield className="w-4 h-4 shrink-0" />
            {!collapsed && <span>Admin</span>}
          </Link>
        )}
      </nav>

      {/* Logout */}
      <div className="px-2 pb-3 border-t border-border pt-3">
        <button
          onClick={handleLogout}
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary w-full transition-all"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
