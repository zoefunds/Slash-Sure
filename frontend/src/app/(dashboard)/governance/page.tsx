"use client";
import { Scale, CheckCircle, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const mockProposals = [
  { id: "p1", type: "appeal_slash", target: "SC-ABCD1234", proposer: "0x123...abc", votesFor: 12, votesAgainst: 3, status: "active", deadline: "2026-06-22" },
  { id: "p2", type: "review_claim", target: "CLM-XYZ789", proposer: "0x456...def", votesFor: 8, votesAgainst: 8, status: "active", deadline: "2026-06-21" },
  { id: "p3", type: "whitelist_operator", target: "0xabc...789", proposer: "0x789...ghi", votesFor: 20, votesAgainst: 1, status: "passed", deadline: "2026-06-18" },
];

export default function GovernancePage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Governance</h1>
        <p className="text-muted-foreground mt-1">Slashing appeals, claim reviews, and protocol proposals</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Active Proposals", value: 2, color: "text-blue-400" },
          { label: "Passed", value: 1, color: "text-green-400" },
          { label: "Failed", value: 0, color: "text-red-400" },
        ].map((s) => (
          <div key={s.label} className="p-5 rounded-2xl border border-border bg-card/50 text-center">
            <div className={cn("text-3xl font-bold mb-1", s.color)}>{s.value}</div>
            <div className="text-sm text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <Scale className="w-4 h-4 text-cyan-400" />
          <h2 className="font-semibold">Governance Proposals</h2>
        </div>
        <div className="divide-y divide-border">
          {mockProposals.map((p) => {
            const total = p.votesFor + p.votesAgainst;
            const forPct = total > 0 ? Math.round((p.votesFor / total) * 100) : 0;
            return (
              <div key={p.id} className="px-6 py-5 hover:bg-secondary/20 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground capitalize">
                        {p.type.replace(/_/g, " ")}
                      </span>
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                        p.status === "active" ? "bg-blue-500/10 text-blue-400" :
                        p.status === "passed" ? "bg-green-500/10 text-green-400" :
                        "bg-red-500/10 text-red-400"
                      )}>
                        {p.status}
                      </span>
                    </div>
                    <div className="font-medium">Target: {p.target}</div>
                    <div className="text-xs text-muted-foreground font-mono mt-0.5">Proposer: {p.proposer}</div>
                  </div>
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Deadline: {p.deadline}
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1 text-green-400"><CheckCircle className="w-3 h-3" /> {p.votesFor} For</span>
                    <span>{forPct}%</span>
                    <span className="flex items-center gap-1 text-red-400"><XCircle className="w-3 h-3" /> {p.votesAgainst} Against</span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-green-400 rounded-full transition-all" style={{ width: `${forPct}%` }} />
                  </div>
                </div>
                {p.status === "active" && (
                  <div className="flex gap-3 mt-4">
                    <button className="px-4 py-2 text-xs bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-colors">
                      Vote For
                    </button>
                    <button className="px-4 py-2 text-xs bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-colors">
                      Vote Against
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
