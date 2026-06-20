"use client";

import { Bell, Search, Wallet } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { truncateAddress } from "@/lib/utils";

export function TopBar() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="h-16 border-b border-border bg-card/30 flex items-center justify-between px-6">
      {/* Search */}
      <div className="relative w-72">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search operators, incidents..."
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-input text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-blue-500/50"
        />
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        {/* Wallet */}
        {user?.wallet_address && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-card/50 text-sm">
            <Wallet className="w-3.5 h-3.5 text-blue-400" />
            <code className="text-muted-foreground text-xs">
              {truncateAddress(user.wallet_address)}
            </code>
          </div>
        )}

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-secondary transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-500/30 flex items-center justify-center text-sm font-medium text-blue-400">
          {user?.email?.[0]?.toUpperCase() || "U"}
        </div>
      </div>
    </header>
  );
}
