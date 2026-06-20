"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  Shield, AlertTriangle, BarChart3, Zap, Lock, Globe,
  ArrowRight, CheckCircle, ChevronRight, Activity, Database,
  Eye, TrendingUp, Award, FileText
} from "lucide-react";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

const HERO_BG = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=1600&q=80&auto=format";
const NETWORK_IMG = "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80&auto=format";
const SECURITY_IMG = "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80&auto=format";
const AI_IMG = "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&q=80&auto=format";
const TEAM_IMG = "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&q=80&auto=format";

const stats = [
  { label: "Operators Monitored", value: "2,400+", icon: Activity },
  { label: "Networks Covered", value: "12+", icon: Globe },
  { label: "Claims Adjudicated", value: "$48M+", icon: FileText },
  { label: "Slashing Events Detected", value: "1,800+", icon: AlertTriangle },
];

const features = [
  {
    icon: Eye,
    title: "Real-Time Monitoring",
    description:
      "Continuously ingest blockchain transactions, validator metrics, consensus reports, and security alerts across EigenLayer, Symbiotic, Babylon, and Cosmos ecosystems.",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    icon: AlertTriangle,
    title: "Violation Detection",
    description:
      "Instantly detect downtime, double-signing, oracle manipulation, consensus failures, censorship attacks, and coordinated malicious behavior.",
    color: "text-red-400",
    bg: "bg-red-400/10",
  },
  {
    icon: Database,
    title: "Evidence Engine",
    description:
      "Generate cryptographic evidence packages with Merkle-rooted on-chain proofs, historical behavior records, and tamper-proof audit trails.",
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
  {
    icon: Zap,
    title: "AI Judgment Layer",
    description:
      "GenLayer-powered AI evaluates fault probability, severity scores, and confidence levels — with validator consensus ensuring transparent, decentralized verdicts.",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
  },
  {
    icon: Shield,
    title: "Slashing Coordination",
    description:
      "Generate slashing eligibility, recommended percentages, and supporting rationale anchored on-chain for complete transparency and auditability.",
    color: "text-cyan-400",
    bg: "bg-cyan-400/10",
  },
  {
    icon: Award,
    title: "Insurance Adjudication",
    description:
      "AI-powered claim assessment determines coverage eligibility, damage amounts, and payout recommendations — automatically and impartially.",
    color: "text-green-400",
    bg: "bg-green-400/10",
  },
];

const networks = [
  { name: "EigenLayer", category: "Restaking", color: "border-blue-500/40" },
  { name: "Symbiotic", category: "Restaking", color: "border-purple-500/40" },
  { name: "Babylon", category: "BTC Staking", color: "border-orange-500/40" },
  { name: "Cosmos IBC", category: "Validators", color: "border-cyan-500/40" },
  { name: "AVS Operators", category: "EigenLayer", color: "border-blue-400/40" },
  { name: "Oracle Networks", category: "Data Layer", color: "border-green-500/40" },
  { name: "DePIN Networks", category: "Physical Infra", color: "border-pink-500/40" },
  { name: "Decentralized AI", category: "AI Layer", color: "border-yellow-500/40" },
];

const customers = [
  "Restaking Protocols",
  "AVS Operators",
  "Oracle Networks",
  "Validator Infrastructure",
  "DePIN Networks",
  "Insurance Protocols",
  "Institutional Node Ops",
  "Staking Platforms",
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background image */}
        <div className="absolute inset-0 z-0">
          <Image
            src={HERO_BG}
            alt="Decentralized network"
            fill
            className="object-cover opacity-10"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/60 via-background/40 to-background" />
          <div className="absolute inset-0 bg-hero-gradient" />
        </div>

        {/* Grid overlay */}
        <div className="absolute inset-0 grid-bg z-0 opacity-60" />

        {/* Animated orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl animate-pulse-glow delay-1000" />

        <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-blue-500/30 bg-blue-500/5 text-blue-400 text-sm font-medium mb-8">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Powered by GenLayer Intelligent Contracts
            </div>

            <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
              The AI-Powered{" "}
              <span className="gradient-text">Trust & Insurance</span>
              <br />
              Layer for Decentralized Networks
            </h1>

            <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed">
              SlashSure continuously monitors validators, operators, AVSs, and restaking
              ecosystems — detecting violations, adjudicating insurance claims, and
              coordinating slashing decisions with full AI transparency.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition-all duration-200 shadow-glow-blue hover:shadow-glow-blue/80"
              >
                Start Monitoring Free
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center gap-2 px-8 py-4 border border-border hover:border-blue-500/50 hover:bg-blue-500/5 rounded-lg font-semibold transition-all duration-200"
              >
                Read Documentation
                <ChevronRight className="w-5 h-5" />
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-24"
          >
            {stats.map((s) => (
              <div
                key={s.label}
                className="p-6 rounded-xl border border-border bg-card/50 backdrop-blur-sm"
              >
                <s.icon className="w-6 h-6 text-blue-400 mb-3 mx-auto" />
                <div className="text-3xl font-bold gradient-text">{s.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Networks ───────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-sm text-blue-400 font-semibold uppercase tracking-widest mb-4">
              Supported Networks
            </h2>
            <p className="text-3xl font-bold">
              Coverage across the entire decentralized stack
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {networks.map((n) => (
              <div
                key={n.name}
                className={`p-4 rounded-xl border ${n.color} bg-card/30 hover:bg-card/60 transition-all duration-200`}
              >
                <div className="text-sm text-muted-foreground mb-1">{n.category}</div>
                <div className="font-semibold">{n.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ───────────────────────────────────── */}
      <section id="features" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-sm text-blue-400 font-semibold uppercase tracking-widest mb-4">
              Core Platform
            </h2>
            <h3 className="text-4xl font-bold mb-6">
              Every layer of decentralized trust — covered
            </h3>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              From detection to payout, SlashSure handles the complete lifecycle of
              slashing and insurance events on-chain.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="p-6 rounded-2xl border border-border bg-card/50 hover:border-blue-500/30 hover:shadow-card-hover transition-all duration-300 group"
              >
                <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
                  <f.icon className={`w-6 h-6 ${f.color}`} />
                </div>
                <h4 className="text-lg font-semibold mb-3">{f.title}</h4>
                <p className="text-muted-foreground leading-relaxed">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────── */}
      <section className="py-32 px-6 bg-card/20 border-y border-border">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-sm text-blue-400 font-semibold uppercase tracking-widest mb-4">
                How It Works
              </h2>
              <h3 className="text-4xl font-bold mb-8">
                AI-native from detection to payout
              </h3>
              <div className="space-y-6">
                {[
                  {
                    step: "01",
                    title: "Monitor",
                    desc: "Ingest real-time blockchain data, validator metrics, and network events across all supported chains.",
                    color: "text-blue-400",
                  },
                  {
                    step: "02",
                    title: "Detect & Evidence",
                    desc: "Detect violations automatically. Build cryptographic evidence packages with Merkle-rooted proofs anchored on GenLayer.",
                    color: "text-purple-400",
                  },
                  {
                    step: "03",
                    title: "AI Analysis",
                    desc: "GenLayer LLMs analyze fault probability, severity, and confidence — reaching decentralized validator consensus.",
                    color: "text-yellow-400",
                  },
                  {
                    step: "04",
                    title: "Slash & Insure",
                    desc: "Slashing recommendations and insurance adjudications are recorded on-chain with full audit trails.",
                    color: "text-green-400",
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-6">
                    <div className={`text-4xl font-bold ${item.color} opacity-30 w-12 shrink-0`}>
                      {item.step}
                    </div>
                    <div>
                      <div className="font-semibold text-lg mb-1">{item.title}</div>
                      <div className="text-muted-foreground">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500/5 rounded-3xl blur-3xl" />
              <Image
                src={AI_IMG}
                alt="AI analysis"
                width={600}
                height={400}
                className="rounded-2xl border border-border relative z-10 object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── GenLayer Section ──────────────────────────── */}
      <section className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="relative">
              <div className="absolute inset-0 bg-purple-500/5 rounded-3xl blur-3xl" />
              <Image
                src={NETWORK_IMG}
                alt="GenLayer network"
                width={600}
                height={400}
                className="rounded-2xl border border-border relative z-10 object-cover"
              />
            </div>
            <div>
              <h2 className="text-sm text-purple-400 font-semibold uppercase tracking-widest mb-4">
                GenLayer Intelligent Contracts
              </h2>
              <h3 className="text-4xl font-bold mb-6">
                AI verdicts with decentralized consensus
              </h3>
              <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
                SlashSure&apos;s core logic runs on GenLayer Intelligent Contracts — combining
                LLM reasoning with blockchain-grade consensus. Every AI verdict, slashing
                recommendation, and insurance decision is validated by multiple GenLayer
                nodes before being finalized on StudioNet.
              </p>
              <div className="space-y-4">
                {[
                  "Non-deterministic LLM calls with fuzzy consensus equality",
                  "All evidence hashes anchored immutably on-chain",
                  "GEN token-denominated payouts and operations",
                  "Full audit trail preserved on GenLayer StudioNet",
                  "Governance and appeal system built into the contract",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-purple-400 mt-0.5 shrink-0" />
                    <span className="text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Security ──────────────────────────────────── */}
      <section className="py-32 px-6 bg-card/20 border-y border-border">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-sm text-red-400 font-semibold uppercase tracking-widest mb-4">
                Enterprise Security
              </h2>
              <h3 className="text-4xl font-bold mb-6">
                Built for institutional-grade protection
              </h3>
              <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
                SlashSure is architected with OWASP best practices, end-to-end encryption,
                RBAC, and complete audit logging. Your operators, data, and keys are
                protected at every layer.
              </p>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "OWASP Compliant", icon: Shield },
                  { label: "End-to-End Encryption", icon: Lock },
                  { label: "RBAC Permissions", icon: Award },
                  { label: "Complete Audit Trail", icon: FileText },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 p-4 rounded-xl border border-border bg-card/50">
                    <item.icon className="w-5 h-5 text-red-400" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-red-500/5 rounded-3xl blur-3xl" />
              <Image
                src={SECURITY_IMG}
                alt="Security infrastructure"
                width={600}
                height={400}
                className="rounded-2xl border border-border relative z-10 object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── Customers ─────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-sm text-blue-400 font-semibold uppercase tracking-widest mb-4">
            Built For
          </h2>
          <h3 className="text-4xl font-bold mb-16">
            Trusted by every layer of the decentralized stack
          </h3>
          <div className="flex flex-wrap justify-center gap-4">
            {customers.map((c) => (
              <div
                key={c}
                className="px-6 py-3 rounded-full border border-border bg-card/50 text-sm font-medium hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-200"
              >
                {c}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────── */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="p-12 rounded-3xl border border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 relative overflow-hidden">
            <div className="absolute inset-0 bg-hero-gradient opacity-50" />
            <div className="relative z-10">
              <h2 className="text-4xl font-bold mb-6">
                Start protecting your network today
              </h2>
              <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
                Join operators, AVSs, and protocols using SlashSure to monitor, protect,
                and automate trust in decentralized infrastructure.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition-all duration-200 shadow-glow-blue"
                >
                  Get Started Free
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="/contact"
                  className="inline-flex items-center gap-2 px-8 py-4 border border-border hover:border-blue-500/50 rounded-lg font-semibold transition-all duration-200"
                >
                  Contact Sales
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
