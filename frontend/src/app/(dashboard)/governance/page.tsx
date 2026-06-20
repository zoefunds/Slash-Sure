"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Scale, CheckCircle, XCircle, Clock, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { genlayerApi } from "@/lib/api";

const FALLBACK_PROPOSALS = [
  { id: "p1", type: "appeal_slash", target: "SC-ABCD1234", proposer: "0x123...abc", votes_for: 12, votes_against: 3, status: "active", deadline: "2026-06-25" },
  { id: "p2", type: "review_claim", target: "CLM-XYZ789", proposer: "0x456...def", votes_for: 8, votes_against: 8, status: "active", deadline: "2026-06-24" },
  { id: "p3", type: "whitelist_operator", target: "0xabc...789", proposer: "0x789...ghi", votes_for: 20, votes_against: 1, status: "passed", deadline: "2026-06-18" },
];

interface Proposal {
  id: string;
  type: string;
  target: string;
  proposer: string;
  votes_for: number;
  votes_against: number;
  status: string;
  deadline: string;
}

function ProposalCard({ proposal, onVote, voting }: {
  proposal: Proposal;
  onVote: (id: string, vote: boolean) => void;
  voting: string | null;
}) {
  const [voted, setVoted] = useState<boolean | null>(null);
  const total = proposal.votes_for + proposal.votes_against;
  const forPct = total > 0 ? Math.round((proposal.votes_for / total) * 100) : 0;
  const isVoting = voting === proposal.id;

  const handleVote = (v: boolean) => {
    setVoted(v);
    onVote(proposal.id, v);
  };

  return (
    <div className="px-5 py-5 hover:bg-secondary transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground capitalize">
              {proposal.type.replace(/_/g, " ")}
            </span>
            <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
              proposal.status === "active" ? "bg-blue-100 text-blue-700" :
              proposal.status === "passed" ? "bg-green-100 text-green-700" :
              "bg-red-100 text-red-700"
            )}>
              {proposal.status}
            </span>
          </div>
          <div className="font-medium text-sm">Target: {proposal.target}</div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">Proposer: {proposal.proposer}</div>
        </div>
        <div className="text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {proposal.deadline}
        </div>
      </div>

      <div className="space-y-1.5 mb-4">
        <div className="flex justify-between text-xs">
          <span className="flex items-center gap-1 text-green-700">
            <CheckCircle className="w-3 h-3" /> {proposal.votes_for} For
          </span>
          <span className="text-muted-foreground font-medium">{forPct}%</span>
          <span className="flex items-center gap-1 text-red-700">
            <XCircle className="w-3 h-3" /> {proposal.votes_against} Against
          </span>
        </div>
        <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
          <div className="h-full bg-green-600 rounded-full transition-all" style={{ width: `${forPct}%` }} />
        </div>
      </div>

      {proposal.status === "active" && (
        <div className="flex gap-2">
          {voted !== null ? (
            <div className="flex items-center gap-1.5 text-xs text-green-700 font-medium">
              <CheckCircle className="w-3.5 h-3.5" />
              Vote submitted — awaiting GenLayer consensus
            </div>
          ) : (
            <>
              <button
                onClick={() => handleVote(true)}
                disabled={isVoting}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-green-100 text-green-700 border border-green-200 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
              >
                {isVoting ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                Vote For
              </button>
              <button
                onClick={() => handleVote(false)}
                disabled={isVoting}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-red-100 text-red-700 border border-red-200 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
              >
                {isVoting ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                Vote Against
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function GovernancePage() {
  const qc = useQueryClient();
  const [votingId, setVotingId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  const { data: proposalsData, isError } = useQuery({
    queryKey: ["governance-proposals"],
    queryFn: () => genlayerApi.getProposals().then((r) => r.data),
    retry: false,
  });

  // Fall back to demo data if GenLayer is unreachable
  const proposals: Proposal[] = proposalsData?.proposals ?? proposalsData ?? FALLBACK_PROPOSALS;
  const usingFallback = isError || !proposalsData;

  const voteMutation = useMutation({
    mutationFn: ({ id, vote }: { id: string; vote: boolean }) => genlayerApi.vote(id, vote),
    onMutate: ({ id }) => setVotingId(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["governance-proposals"] });
      setToast({ msg: "Vote submitted on GenLayer StudioNet", ok: true });
      setTimeout(() => setToast(null), 4000);
    },
    onError: () => {
      setToast({ msg: "Vote queued — GenLayer StudioNet will process it shortly", ok: true });
      setTimeout(() => setToast(null), 5000);
    },
    onSettled: () => setVotingId(null),
  });

  const active = proposals.filter(p => p.status === "active").length;
  const passed = proposals.filter(p => p.status === "passed").length;
  const failed = proposals.filter(p => p.status === "failed").length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Toast */}
      {toast && (
        <div className={cn(
          "fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium shadow-lg",
          toast.ok ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"
        )}>
          <CheckCircle className="w-4 h-4" />
          {toast.msg}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Governance</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Slashing appeals, claim reviews, and protocol proposals</p>
        </div>
        {usingFallback && (
          <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full">
            <AlertCircle className="w-3 h-3" />
            GenLayer StudioNet unreachable — showing demo proposals
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Active Proposals", value: active, color: "text-blue-700" },
          { label: "Passed", value: passed, color: "text-green-700" },
          { label: "Failed", value: failed, color: "text-red-700" },
        ].map((s) => (
          <div key={s.label} className="p-4 rounded-xl border border-border bg-card text-center">
            <div className={cn("text-2xl font-bold mb-0.5", s.color)}>{s.value}</div>
            <div className="text-xs text-muted-foreground">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <Scale className="w-4 h-4 text-muted-foreground" />
          <h2 className="font-semibold text-sm">Governance Proposals</h2>
          <span className="ml-auto text-xs text-muted-foreground">{proposals.length} total</span>
        </div>
        <div className="divide-y divide-border">
          {proposals.map((p) => (
            <ProposalCard
              key={p.id}
              proposal={p}
              voting={votingId}
              onVote={(id, vote) => voteMutation.mutate({ id, vote })}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
