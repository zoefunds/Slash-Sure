"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, TrendingUp, TrendingDown, Minus, RefreshCw } from "lucide-react";
import { cn, scoreColor, truncateAddress } from "@/lib/utils";
import { operatorsApi, riskApi } from "@/lib/api";

function ScoreBar({ value, colorClass }: { value: number; colorClass: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", colorClass)} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs font-mono w-7 text-right tabular-nums">{value}</span>
    </div>
  );
}

export default function RiskScoresPage() {
  const { data: operatorsData } = useQuery({
    queryKey: ["operators"],
    queryFn: () => operatorsApi.list({ per_page: 50 }).then((r) => r.data),
  });

  const operators = operatorsData?.items ?? [];

  // Fetch reputation score for each operator
  const { data: scoresData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["risk-scores", operators.map((o: { address: string }) => o.address)],
    queryFn: async () => {
      const results = await Promise.allSettled(
        operators.map((op: { address: string }) =>
          riskApi.getOperatorRisk(op.address).then((r) => ({ address: op.address, ...r.data }))
        )
      );
      return results
        .filter((r): r is PromiseFulfilledResult<Record<string, unknown>> => r.status === "fulfilled")
        .map((r) => r.value);
    },
    enabled: operators.length > 0,
    retry: false,
  });

  type EnrichedOp = {
    id: string; name: string; address: string; network: string; status: string;
    reliability: number | null; security: number | null; slashRisk: number | null;
    overall: number | null; trend: string;
  };

  // Merge operator info with risk scores
  const enriched: EnrichedOp[] = operators.map((op: {
    id: string; name: string; address: string; network: string; status: string;
  }) => {
    const score = scoresData?.find((s) => s.address === op.address);
    return {
      ...op,
      reliability: score?.reliability_score ?? score?.overall_score ?? null,
      security: score?.security_score ?? null,
      slashRisk: score?.slashing_risk_score ?? null,
      overall: score?.overall_score ?? null,
      trend: score?.risk_trend ?? "stable",
    };
  });

  const highRisk = enriched.filter((o) => o.overall !== null && (o.overall as number) < 60).length;
  const medRisk = enriched.filter((o) => o.overall !== null && (o.overall as number) >= 60 && (o.overall as number) < 80).length;
  const lowRisk = enriched.filter((o) => o.overall !== null && (o.overall as number) >= 80).length;
  const noData = enriched.filter((o) => o.overall === null).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Risk Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-0.5">AI-computed reputation and risk scores for all operators</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-secondary transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isFetching && "animate-spin")} />
          Refresh Scores
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "High Risk", value: highRisk, color: "text-red-700" },
          { label: "Medium Risk", value: medRisk, color: "text-amber-700" },
          { label: "Low Risk / Safe", value: lowRisk, color: "text-green-700" },
          { label: "Score Pending", value: noData, color: "text-muted-foreground" },
        ].map((s) => (
          <div key={s.label} className="p-4 rounded-xl border border-border bg-card text-center">
            <div className={cn("text-2xl font-bold mb-0.5", s.color)}>{s.value}</div>
            <div className="text-xs text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <BarChart3 className="w-4 h-4 text-muted-foreground" />
          <h2 className="font-semibold text-sm">Operator Risk Scores</h2>
          <span className="ml-auto text-xs text-muted-foreground">{operators.length} operators</span>
        </div>

        {isLoading || operators.length === 0 ? (
          <div className="px-5 py-16 text-center text-muted-foreground text-sm">
            {operators.length === 0 ? "No operators registered yet" : "Computing risk scores…"}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {enriched.map((op) => {
              const trend = op.trend as string;
              const TrendIcon = trend === "improving" ? TrendingUp : trend === "degrading" ? TrendingDown : Minus;
              const trendColor = trend === "improving" ? "text-green-700" : trend === "degrading" ? "text-red-700" : "text-muted-foreground";
              const overall = op.overall as number | null;

              return (
                <div key={op.address} className="px-5 py-5 hover:bg-secondary/50 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="font-semibold text-sm">{op.name}</div>
                      <div className="text-xs text-muted-foreground font-mono mt-0.5">
                        {truncateAddress(op.address)} · <span className="capitalize">{op.network}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {overall !== null ? (
                        <>
                          <div className={cn("text-2xl font-bold tabular-nums", scoreColor(overall))}>{overall}</div>
                          <TrendIcon className={cn("w-4 h-4", trendColor)} />
                        </>
                      ) : (
                        <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
                          {isFetching ? "Computing…" : "No data"}
                        </span>
                      )}
                    </div>
                  </div>
                  {overall !== null ? (
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      <div>
                        <div className="text-muted-foreground mb-1.5">Reliability</div>
                        <ScoreBar value={(op.reliability as number) ?? 0} colorClass="bg-blue-700" />
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1.5">Security</div>
                        <ScoreBar value={(op.security as number) ?? 0} colorClass="bg-purple-600" />
                      </div>
                      <div>
                        <div className="text-muted-foreground mb-1.5">Slash Risk</div>
                        <ScoreBar
                          value={(op.slashRisk as number) ?? 0}
                          colorClass={(op.slashRisk as number) > 50 ? "bg-red-600" : (op.slashRisk as number) > 25 ? "bg-amber-600" : "bg-green-600"}
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Risk score not yet computed — click Refresh Scores to trigger AI analysis.
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
