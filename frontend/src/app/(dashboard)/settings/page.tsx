"use client";
import { useState } from "react";
import { Settings, Wallet, Bell, Key, Copy, Check, Save, Pencil, X } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState(user?.full_name || "");
  const [nameSaving, setNameSaving] = useState(false);
  const [nameError, setNameError] = useState("");
  const [exportPw, setExportPw] = useState("");
  const [exportedKey, setExportedKey] = useState("");
  const [exportError, setExportError] = useState("");
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [notifs, setNotifs] = useState({
    critical_slashing: true,
    claim_updates: true,
    operator_status: true,
    weekly_digest: false,
  });
  const [savedNotifs, setSavedNotifs] = useState(false);

  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameSaving(true);
    setNameError("");
    try {
      const { data } = await authApi.updateProfile({ full_name: nameInput.trim() });
      setUser({ ...user!, full_name: data.full_name });
      setEditingName(false);
    } catch {
      setNameError("Failed to update name");
    } finally {
      setNameSaving(false);
    }
  };

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
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-5 h-5 text-muted-foreground" />
          <h2 className="font-semibold">Account Information</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground">Email</label>
            <div className="mt-1 font-medium">{user?.email}</div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">Full Name</label>
            {editingName ? (
              <form onSubmit={handleSaveName} className="mt-1 flex items-center gap-2">
                <input
                  autoFocus
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-foreground/15"
                  placeholder="Your full name"
                />
                <button type="submit" disabled={nameSaving} className="px-3 py-1.5 text-sm bg-foreground text-background rounded-lg disabled:opacity-50">
                  {nameSaving ? "Saving…" : "Save"}
                </button>
                <button type="button" onClick={() => { setEditingName(false); setNameInput(user?.full_name || ""); }} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
                {nameError && <span className="text-red-600 text-xs">{nameError}</span>}
              </form>
            ) : (
              <div className="mt-1 flex items-center gap-2">
                <span className="font-medium">{user?.full_name || "—"}</span>
                <button onClick={() => { setEditingName(true); setNameInput(user?.full_name || ""); }} className="text-muted-foreground hover:text-foreground">
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Wallet */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Wallet className="w-5 h-5 text-muted-foreground" />
          <h2 className="font-semibold">Blockchain Wallet</h2>
        </div>
        <div className="mb-6">
          <label className="text-sm text-muted-foreground">Wallet Address</label>
          <div className="mt-1 font-mono text-sm bg-secondary px-4 py-3 rounded-lg">
            {user?.wallet_address || "—"}
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="font-medium mb-2 flex items-center gap-2">
            <Key className="w-4 h-4 text-amber-700" />
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
                  <span className="text-xs text-amber-700 font-medium">PRIVATE KEY — KEEP SECRET</span>
                  <button onClick={copyKey} className="text-xs flex items-center gap-1 text-muted-foreground hover:text-foreground">
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <code className="text-xs break-all text-amber-800">{exportedKey}</code>
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
                className="flex-1 px-4 py-2.5 rounded-lg border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-foreground/15"
                required
              />
              <button
                type="submit"
                disabled={exporting}
                className="px-4 py-2.5 bg-amber-100 text-amber-800 border border-amber-200 rounded-lg text-sm font-medium hover:bg-amber-200 transition-colors disabled:opacity-50"
              >
                {exporting ? "Decrypting..." : "Export"}
              </button>
            </form>
          )}
          {exportError && <p className="text-red-700 text-sm mt-2">{exportError}</p>}
        </div>
      </div>

      {/* Notifications */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="w-5 h-5" />
          <h2 className="font-semibold">Notification Preferences</h2>
        </div>
        <div className="space-y-1">
          {([
            { key: "critical_slashing", label: "Critical slashing events", desc: "Get notified immediately for critical severity" },
            { key: "claim_updates", label: "Insurance claim updates", desc: "Status changes on submitted claims" },
            { key: "operator_status", label: "Operator status changes", desc: "When operators are jailed or slashed" },
            { key: "weekly_digest", label: "Weekly risk digest", desc: "Weekly summary of risk scores and trends" },
          ] as const).map((item) => (
            <div key={item.key} className="flex items-center justify-between py-3.5 border-b border-border last:border-0">
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{item.desc}</div>
              </div>
              <button
                type="button"
                onClick={() => setNotifs(n => ({ ...n, [item.key]: !n[item.key] }))}
                className={cn(
                  "w-10 h-6 rounded-full relative transition-colors",
                  notifs[item.key] ? "bg-foreground" : "bg-border"
                )}
              >
                <div className={cn(
                  "absolute top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm",
                  notifs[item.key] ? "right-1" : "left-1"
                )} />
              </button>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={() => { setSavedNotifs(true); setTimeout(() => setSavedNotifs(false), 2500); }}
            className="flex items-center gap-2 px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-85 transition-opacity"
          >
            {savedNotifs ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {savedNotifs ? "Saved!" : "Save Preferences"}
          </button>
        </div>
      </div>
    </div>
  );
}
