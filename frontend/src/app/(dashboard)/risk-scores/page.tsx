"use client";
import { BarChart3, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn, scoreColor } from "@/lib/utils";

const mockScores = [
  { name: "EigenLayer Validator A", address: "0x1234...abcd", network: "EigenLayer", reliability: 98, security: 95, slashRisk: 5, overall: 97, trend: "stable" },
  { name: "Symbiotic Node B", address: "0x5678...efgh", network: "Symbiotic", reliability: 72, security: 68, slashRisk: 42, overall: 70, trend: "degrading" },
  { name: "Cosmos Validator C", address: "0x9abc...ijkl", network: "Cosmos", reliability: 99, security: 97, slashRisk: 2, overall: 99, trend: "improving" },
  { name: "Babylon Staker D", address: "0xdef0...mnop", network: "Babylon", reliability: 85, security: 80, slashRisk: 25, overall: 82, trend: "stable" },
];

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs font-mono w-8 text-right">{value}</span>
    </div>
  );
}

export default function RiskScoresPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Risk Intelligence</h1>
        <p className="text-muted-foreground mt-1">AI-computed reputation and risk scores for all operators</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "High Risk Operators", value: 2, color: "text-red-400" },
          { label: "Medium Risk", value: 5, color: "text-yellow-400" },
          { label: "Low Risk / Safe", value: 18, color: "text-green-400" },
        ].map((s) => (
          <div key={s.label} className="p-5 rounded-2xl border border-border bg-card/50 text-center">
            <div className={cn("text-3xl font-bold mb-1", s.color)}>{s.value}</div>
            <div className="text-sm text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card/50 overflow-hidden">
        <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <h2 className="font-semibold">Operator Risk Scores</h2>
        </div>
        <div className="divide-y divide-border">
          {mockScores.map((op) => {
            const TrendIcon = op.trend === "improving" ? TrendingUp : op.trend === "degrading" ? TrendingDown : Minus;
            const trendColor = op.trend === "improving" ? "text-green-400" : op.trend === "degrading" ? "text-red-400" : "text-muted-foreground";
            return (
              <div key={op.address} className="px-6 py-5 hover:bg-secondary/20 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="font-semibold">{op.name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{op.address} · {op.network}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={cn("text-2xl font-bold", scoreColor(op.overall))}>{op.overall}</div>
                    <TrendIcon className={cn("w-4 h-4", trendColor)} />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div>
                    <div className="text-muted-foreground mb-1.5">Reliability</div>
                    <ScoreBar value={op.reliability} color="bg-blue-400" />
                  </div>
                  <div>
                    <div className="text-muted-foreground mb-1.5">Security</div>
                    <ScoreBar value={op.security} color="bg-purple-400" />
                  </div>
                  <div>
                    <div className="text-muted-foreground mb-1.5">Slash Risk</div>
                    <ScoreBar value={op.slashRisk} color={op.slashRisk > 50 ? "bg-red-400" : op.slashRisk > 25 ? "bg-yellow-400" : "bg-green-400"} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
