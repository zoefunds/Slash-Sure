"use client";
import { useState } from "react";
import { Settings, Wallet, Bell, Shield, Key, Copy, Check } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { truncateAddress } from "@/lib/utils";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const [exportPw, setExportPw] = useState("");
  const [exportedKey, setExportedKey] = useState("");
  const [exportError, setExportError] = useState("");
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExportKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setExporting(true);
    setExportError("");
    try {
      const { data } = await authApi.exportKey(exportPw);
      setExportedKey(data.private_key);
    } catch {
      setExportError("Invalid password");
    } finally {
      setExporting(false);
    }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(exportedKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account, wallet, and notification preferences</p>
      </div>

      {/* Account */}
      <div className="rounded-2xl border border-border bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold">Account Information</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground">Email</label>
            <div className="mt-1 font-medium">{user?.email}</div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">Full Name</label>
            <div className="mt-1 font-medium">{user?.full_name || "—"}</div>
          </div>
        </div>
      </div>

      {/* Wallet */}
      <div className="rounded-2xl border border-border bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Wallet className="w-5 h-5 text-purple-400" />
          <h2 className="font-semibold">Blockchain Wallet</h2>
        </div>
        <div className="mb-6">
          <label className="text-sm text-muted-foreground">Wallet Address</label>
          <div className="mt-1 font-mono text-sm bg-secondary/50 px-4 py-3 rounded-lg">
            {user?.wallet_address || "—"}
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="font-medium mb-2 flex items-center gap-2">
            <Key className="w-4 h-4 text-yellow-400" />
            Export Private Key
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Enter your account password to decrypt and export your private key.
            Store it securely — anyone with this key controls your wallet.
          </p>

          {exportedKey ? (
            <div className="space-y-3">
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-yellow-400 font-medium">PRIVATE KEY — KEEP SECRET</span>
                  <button onClick={copyKey} className="text-xs flex items-center gap-1 text-muted-foreground hover:text-foreground">
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <code className="text-xs break-all text-yellow-300">{exportedKey}</code>
              </div>
              <button onClick={() => setExportedKey("")} className="text-sm text-muted-foreground hover:text-foreground">
                Clear
              </button>
            </div>
          ) : (
            <form onSubmit={handleExportKey} className="flex gap-3">
              <input
                type="password"
                value={exportPw}
                onChange={(e) => setExportPw(e.target.value)}
                placeholder="Enter your password"
                className="flex-1 px-4 py-2.5 rounded-lg border border-border bg-input text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                required
              />
              <button
                type="submit"
                disabled={exporting}
                className="px-4 py-2.5 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg text-sm font-medium hover:bg-yellow-500/20 transition-colors disabled:opacity-50"
              >
                {exporting ? "Decrypting..." : "Export"}
              </button>
            </form>
          )}
          {exportError && <p className="text-red-400 text-sm mt-2">{exportError}</p>}
        </div>
      </div>

      {/* Notifications */}
      <div className="rounded-2xl border border-border bg-card/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="w-5 h-5 text-green-400" />
          <h2 className="font-semibold">Notification Preferences</h2>
        </div>
        <div className="space-y-4">
          {[
            { label: "Critical slashing events", desc: "Get notified immediately for critical severity" },
            { label: "Insurance claim updates", desc: "Status changes on submitted claims" },
            { label: "Operator status changes", desc: "When operators are jailed or slashed" },
            { label: "Weekly risk digest", desc: "Weekly summary of risk scores and trends" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between py-3 border-b border-border last:border-0">
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-muted-foreground">{item.desc}</div>
              </div>
              <div className="w-10 h-6 bg-blue-600 rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
