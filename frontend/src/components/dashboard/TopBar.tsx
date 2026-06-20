"use client";

import { Bell, Search, Wallet } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { truncateAddress } from "@/lib/utils";

export function TopBar() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="h-[60px] border-b border-border bg-background flex items-center justify-between px-6">
      <div className="relative w-64">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search operators, incidents..."
          className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-card text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground/20 transition-all"
        />
      </div>

      <div className="flex items-center gap-3">
        {user?.wallet_address && (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card text-sm">
            <Wallet className="w-3 h-3 text-muted-foreground" />
            <code className="text-muted-foreground text-xs">
              {truncateAddress(user.wallet_address)}
            </code>
          </div>
        )}

        <button className="relative p-2 rounded-lg hover:bg-secondary transition-colors">
          <Bell className="w-4 h-4 text-muted-foreground" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-600 rounded-full" />
        </button>

        <div className="w-7 h-7 rounded-full bg-foreground flex items-center justify-center text-xs font-semibold text-background">
          {user?.email?.[0]?.toUpperCase() || "U"}
        </div>
      </div>
    </header>
  );
}
