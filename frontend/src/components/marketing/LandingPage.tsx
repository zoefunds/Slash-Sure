"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Shield, AlertTriangle, BarChart3, Zap, Lock,
  ArrowRight, CheckCircle, Activity, Database,
  Eye, FileText
} from "lucide-react";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

const stats = [
  { label: "Operators Monitored", value: "2,400+" },
  { label: "Networks Covered", value: "12+" },
  { label: "Claims Adjudicated", value: "$48M+" },
  { label: "Slashing Events", value: "1,800+" },
];

const features = [
  {
    icon: Eye,
    title: "Real-Time Monitoring",
    description: "Continuously ingest blockchain transactions, validator metrics, and security alerts across EigenLayer, Symbiotic, Babylon, and Cosmos ecosystems.",
  },
  {
    icon: AlertTriangle,
    title: "Violation Detection",
    description: "Instantly detect downtime, double-signing, oracle manipulation, consensus failures, and coordinated malicious behavior.",
  },
  {
    icon: Database,
    title: "Evidence Engine",
    description: "Generate cryptographic evidence packages with Merkle-rooted on-chain proofs, historical behavior records, and tamper-proof audit trails.",
  },
  {
    icon: Zap,
    title: "AI Judgment Layer",
    description: "GenLayer-powered AI evaluates fault probability and severity — with validator consensus ensuring transparent, decentralized verdicts.",
  },
  {
    icon: Shield,
    title: "Slashing Coordination",
    description: "Generate slashing eligibility, recommended percentages, and supporting rationale anchored on-chain for complete auditability.",
  },
  {
    icon: FileText,
    title: "Insurance Adjudication",
    description: "AI-powered claim assessment determines coverage eligibility, damage amounts, and payout recommendations — automatically and impartially.",
  },
];

const networks = [
  { name: "EigenLayer", category: "Restaking" },
  { name: "Symbiotic", category: "Restaking" },
  { name: "Babylon", category: "BTC Staking" },
  { name: "Cosmos IBC", category: "Validators" },
  { name: "AVS Operators", category: "EigenLayer" },
  { name: "Oracle Networks", category: "Data Layer" },
  { name: "DePIN Networks", category: "Physical Infra" },
  { name: "Decentralized AI", category: "AI Layer" },
];

const steps = [
  {
    n: "01",
    title: "Monitor",
    desc: "Ingest real-time blockchain data, validator metrics, and network events across all supported chains.",
  },
  {
    n: "02",
    title: "Detect & Evidence",
    desc: "Detect violations automatically. Build cryptographic evidence packages with Merkle-rooted proofs anchored on GenLayer.",
  },
  {
    n: "03",
    title: "AI Analysis",
    desc: "GenLayer LLMs analyze fault probability, severity, and confidence — reaching decentralized validator consensus.",
  },
  {
    n: "04",
    title: "Slash & Insure",
    desc: "Slashing recommendations and insurance adjudications are recorded on-chain with full audit trails.",
  },
];

const genlayerPoints = [
  "Non-deterministic LLM calls with fuzzy consensus equality",
  "All evidence hashes anchored immutably on-chain",
  "GEN token-denominated payouts and operations",
  "Full audit trail preserved on GenLayer StudioNet",
  "Governance and appeal system built into the contract",
];

const securityItems = [
  { label: "OWASP Compliant", icon: Shield },
  { label: "End-to-End Encryption", icon: Lock },
  { label: "RBAC Permissions", icon: BarChart3 },
  { label: "Complete Audit Trail", icon: FileText },
];

const customers = [
  "Restaking Protocols", "AVS Operators", "Oracle Networks",
  "Validator Infrastructure", "DePIN Networks", "Insurance Protocols",
  "Institutional Node Ops", "Staking Platforms",
];

const fade = { initial: { opacity: 0, y: 18 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true } };

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 px-6 grid-bg overflow-hidden">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-border bg-card text-xs font-medium text-muted-foreground mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-green-600" />
              Powered by GenLayer Intelligent Contracts
            </div>

            <h1 className="text-5xl md:text-7xl font-bold leading-[1.06] tracking-tight mb-6 text-foreground">
              The AI-Powered{" "}
              <span className="gradient-text">Trust & Insurance</span>
              <br />
              Layer for Decentralized Networks
            </h1>

            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              SlashSure continuously monitors validators, operators, AVSs, and restaking
              ecosystems — detecting violations, adjudicating insurance claims, and
              coordinating slashing decisions with full AI transparency.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-foreground text-background rounded-lg font-semibold text-sm hover:opacity-85 transition-opacity"
              >
                Start Monitoring Free
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/#how-it-works"
                className="inline-flex items-center gap-2 px-7 py-3.5 border border-border bg-card hover:bg-secondary rounded-lg font-semibold text-sm transition-colors"
              >
                See How It Works
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20"
          >
            {stats.map((s) => (
              <div key={s.label} className="p-5 rounded-xl border border-border bg-card text-left">
                <div className="text-2xl font-bold tracking-tight text-foreground">{s.value}</div>
                <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Networks ─────────────────────────────────────── */}
      <section id="networks" className="py-20 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">Supported Networks</p>
            <h2 className="text-3xl font-bold">Coverage across the entire stack</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {networks.map((n) => (
              <div key={n.name} className="p-4 rounded-xl border border-border bg-card hover:bg-secondary transition-colors">
                <p className="text-xs text-muted-foreground mb-1">{n.category}</p>
                <p className="font-medium text-sm">{n.name}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section id="features" className="py-24 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">Core Platform</p>
            <h2 className="text-4xl font-bold mb-4">Every layer of decentralized trust — covered</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              From detection to payout, SlashSure handles the complete lifecycle of slashing and insurance events on-chain.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                {...fade}
                transition={{ duration: 0.4, delay: i * 0.07 }}
                className="p-6 rounded-2xl border border-border bg-card hover:border-foreground/20 transition-colors group"
              >
                <div className="w-9 h-9 rounded-lg border border-border bg-background flex items-center justify-center mb-4">
                  <f.icon className="w-4 h-4 text-foreground" />
                </div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6 border-t border-border bg-card">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">How It Works</p>
              <h2 className="text-4xl font-bold mb-10">AI-native from detection to payout</h2>
              <div className="space-y-8">
                {steps.map((s, i) => (
                  <motion.div key={s.n} {...fade} transition={{ delay: i * 0.1 }} className="flex gap-5">
                    <span className="text-3xl font-bold text-border w-10 shrink-0 leading-none pt-0.5">{s.n}</span>
                    <div>
                      <p className="font-semibold mb-1">{s.title}</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">{s.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
            {/* Visual panel */}
            <div className="rounded-2xl border border-border bg-background p-8 space-y-4">
              <div className="flex items-center gap-3 mb-6">
                <Activity className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium">Live monitoring active</span>
                <span className="ml-auto text-xs text-muted-foreground">StudioNet</span>
              </div>
              {[
                { label: "Operators monitored", val: "2,400+", color: "bg-blue-100 text-blue-800" },
                { label: "Incidents this week", val: "0 detected", color: "bg-green-100 text-green-800" },
                { label: "Avg response time", val: "< 3s", color: "bg-amber-100 text-amber-800" },
                { label: "AI verdict accuracy", val: "99.2%", color: "bg-purple-100 text-purple-800" },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <span className="text-sm text-muted-foreground">{row.label}</span>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${row.color}`}>{row.val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── GenLayer Section ─────────────────────────────── */}
      <section className="py-24 px-6 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="rounded-2xl border border-border bg-card p-8">
              <div className="text-xs font-mono text-muted-foreground mb-4">GenLayer Intelligent Contract</div>
              <div className="space-y-3">
                {[
                  ["Contract type", "Intelligent Contract"],
                  ["Consensus", "Non-deterministic LLM"],
                  ["Network", "StudioNet"],
                  ["Validator nodes", "Multiple"],
                  ["Verdict finality", "On-chain"],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center py-2 border-b border-border last:border-0">
                    <span className="text-sm text-muted-foreground">{k}</span>
                    <span className="text-sm font-medium font-mono">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">GenLayer Intelligent Contracts</p>
              <h2 className="text-4xl font-bold mb-5">AI verdicts with decentralized consensus</h2>
              <p className="text-muted-foreground mb-7 leading-relaxed">
                SlashSure&apos;s core logic runs on GenLayer Intelligent Contracts — combining
                LLM reasoning with blockchain-grade consensus. Every AI verdict is validated
                by multiple GenLayer nodes before being finalized on StudioNet.
              </p>
              <div className="space-y-3">
                {genlayerPoints.map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                    <span className="text-sm text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Security ─────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-border bg-card">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">Enterprise Security</p>
              <h2 className="text-4xl font-bold mb-5">Built for institutional-grade protection</h2>
              <p className="text-muted-foreground mb-8 leading-relaxed">
                SlashSure is architected with OWASP best practices, end-to-end encryption,
                RBAC, and complete audit logging. Your operators, data, and keys are
                protected at every layer.
              </p>
              <div className="grid grid-cols-2 gap-3">
                {securityItems.map((item) => (
                  <div key={item.label} className="flex items-center gap-3 p-4 rounded-xl border border-border bg-background">
                    <item.icon className="w-4 h-4 text-foreground shrink-0" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-background p-8">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-5">Built For</p>
              <div className="flex flex-wrap gap-2">
                {customers.map((c) => (
                  <span key={c} className="px-3 py-1.5 rounded-full border border-border bg-card text-xs font-medium text-foreground">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-border">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Start protecting your network today</h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto leading-relaxed">
            Join operators, AVSs, and protocols using SlashSure to monitor, protect,
            and automate trust in decentralized infrastructure.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-foreground text-background rounded-lg font-semibold text-sm hover:opacity-85 transition-opacity"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-7 py-3.5 border border-border bg-card hover:bg-secondary rounded-lg font-semibold text-sm transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
