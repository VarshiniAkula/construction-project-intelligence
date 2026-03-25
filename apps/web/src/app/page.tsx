"use client";

import Link from "next/link";
import {
  FileText,
  Shield,
  MessageSquare,
  FolderKanban,
  BarChart3,
  DollarSign,
  CalendarClock,
  ClipboardList,
  HardHat,
  Building2,
  Lock,
  Quote,
  ChevronRight,
  ArrowRight,
  UserCheck,
  Briefcase,
  Ruler,
  Wrench,
  Eye,
  SearchCheck,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */

const features = [
  {
    icon: FolderKanban,
    title: "Project Workspaces",
    desc: "Fully isolated workspaces per project. Documents, conversations, and analytics stay separate so nothing leaks between jobs.",
  },
  {
    icon: FileText,
    title: "Document Library",
    desc: "Upload PDFs, DOCX, and TXT files. Every page is extracted, chunked, and indexed so your AI assistant can find answers fast.",
  },
  {
    icon: MessageSquare,
    title: "AI Assistant with Citations",
    desc: "Ask questions in plain language and get answers grounded in your actual project documents — with exact page and source citations.",
  },
  {
    icon: ClipboardList,
    title: "RFI Intelligence",
    desc: "Manage RFIs inside the platform. AI analyzes incoming requests and surfaces relevant specs, drawings, and prior answers automatically.",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    desc: "See document activity, query trends, team usage, and project health at a glance with a purpose-built analytics view.",
  },
  {
    icon: DollarSign,
    title: "Budget & Schedule Tracking",
    desc: "Monitor budgets and schedules alongside your documents. Keep cost and timeline data in the same workspace as your project intelligence.",
  },
];

const roles = [
  { icon: Briefcase, label: "Project Manager" },
  { icon: Building2, label: "Architect" },
  { icon: Ruler, label: "Engineer" },
  { icon: Wrench, label: "Subcontractor" },
  { icon: Eye, label: "Owner" },
  { icon: SearchCheck, label: "Inspector" },
];

const pillars = [
  {
    icon: Lock,
    title: "Project Isolation",
    desc: "Every workspace is a sealed environment. Documents, members, and AI context never cross project boundaries.",
  },
  {
    icon: Quote,
    title: "Cited Answers",
    desc: "No hallucinations. Every AI response links back to the exact document, page, and passage it drew from.",
  },
  {
    icon: Shield,
    title: "Role-Based Security",
    desc: "Access control is enforced at every layer — from document visibility to AI retrieval — based on each member's role.",
  },
  {
    icon: UserCheck,
    title: "Role-Aware Access",
    desc: "Subcontractors see only their trade. Owners see only what you share. Everyone gets the right view automatically.",
  },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-hard-beam text-white">
      {/* ── Navigation ─────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-hard-beam/80 border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 bg-hard-hat rounded-lg flex items-center justify-center shadow-lg shadow-hard-hat/20 group-hover:shadow-hard-hat/40 transition-shadow">
              <HardHat className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              Construction<span className="text-hard-hat">RAG</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-gray-400 hover:text-white transition-colors px-3 py-2"
            >
              Sign In
            </Link>
            <Link href="/register" className="btn-primary text-sm flex items-center gap-1.5">
              Get Started <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Gradient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-hard-hat/[0.07] rounded-full blur-[120px] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 pt-24 pb-20 lg:pt-32 lg:pb-28 text-center">
          <div className="inline-flex items-center gap-2 bg-hard-hat/10 border border-hard-hat/20 rounded-full px-4 py-1.5 mb-8">
            <Building2 className="w-4 h-4 text-hard-hat" />
            <span className="text-hard-hat text-sm font-medium">
              Construction Project Intelligence
            </span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.08] tracking-tight mb-6">
            Your project docs,
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-hard-hat to-amber-400">
              answered with proof.
            </span>
          </h1>

          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            CPI is the intelligence layer for construction teams. Upload project
            documents, ask questions in plain language, and get answers cited to
            the exact page — all secured with role-based access.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="btn-primary text-base px-8 py-3.5 flex items-center justify-center gap-2 shadow-lg shadow-hard-hat/25"
            >
              Create Your Workspace <ChevronRight className="w-5 h-5" />
            </Link>
            <Link
              href="/login"
              className="btn-ghost text-base px-8 py-3.5 border border-white/10 text-gray-300 hover:text-white hover:border-white/20"
            >
              Sign In
            </Link>
          </div>

          {/* Trust strip */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-gray-500">
            <span className="flex items-center gap-1.5">
              <Lock className="w-4 h-4" /> End-to-end project isolation
            </span>
            <span className="hidden sm:inline text-gray-700">|</span>
            <span className="flex items-center gap-1.5">
              <Quote className="w-4 h-4" /> Every answer cites its source
            </span>
            <span className="hidden sm:inline text-gray-700">|</span>
            <span className="flex items-center gap-1.5">
              <Shield className="w-4 h-4" /> Role-based access control
            </span>
          </div>
        </div>
      </section>

      {/* ── Feature Cards ──────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Everything your project needs, in one place
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto">
            From document ingestion to AI-powered Q&amp;A to budget tracking —
            CPI covers the full project lifecycle.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="group relative bg-white/[0.03] border border-white/[0.06] rounded-2xl p-7 hover:bg-white/[0.06] hover:border-hard-hat/20 transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-hard-hat/10 flex items-center justify-center mb-5 group-hover:bg-hard-hat/20 transition-colors">
                <f.icon className="w-6 h-6 text-hard-hat" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────────── */}
      <section className="border-y border-white/[0.06] bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              From upload to insight in minutes
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Three steps to unlock the knowledge buried in your project files.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Create a workspace",
                desc: "Set up an isolated project workspace. Invite team members and assign roles — PM, architect, subcontractor, or owner.",
              },
              {
                step: "02",
                title: "Upload your documents",
                desc: "Drop in PDFs, Word docs, or text files. CPI extracts every page, indexes the content, and makes it searchable in seconds.",
              },
              {
                step: "03",
                title: "Ask anything",
                desc: "Use the AI assistant to ask questions about your documents. Get answers with citations pointing to the exact source and page.",
              },
            ].map((s) => (
              <div key={s.step} className="relative">
                <span className="text-6xl font-black text-hard-hat/10 leading-none">
                  {s.step}
                </span>
                <h3 className="text-xl font-semibold mt-2 mb-3">{s.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Security Pillars ───────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Built for how construction actually works
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto">
            Construction projects demand strict document control. CPI enforces
            it at every layer.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {pillars.map((p) => (
            <div
              key={p.title}
              className="text-center p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]"
            >
              <div className="w-14 h-14 rounded-full bg-hard-steel/10 flex items-center justify-center mx-auto mb-4">
                <p.icon className="w-6 h-6 text-hard-steel" />
              </div>
              <h3 className="font-semibold mb-2">{p.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Roles ──────────────────────────────────────────────────── */}
      <section className="border-y border-white/[0.06] bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              One platform, every seat at the table
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              CPI supports the full project team with role-specific access and views.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-4 md:gap-6">
            {roles.map((r) => (
              <div
                key={r.label}
                className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.08] rounded-full pl-4 pr-6 py-3 hover:border-hard-hat/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-hard-hat/10 flex items-center justify-center">
                  <r.icon className="w-5 h-5 text-hard-hat" />
                </div>
                <span className="font-medium text-sm">{r.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-hard-hat/20 via-hard-beam to-hard-steel/20 border border-white/[0.08] p-12 md:p-16 text-center">
          {/* Decorative glow */}
          <div className="absolute inset-0 bg-gradient-to-t from-hard-beam/80 to-transparent pointer-events-none" />

          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to make your documents work for you?
            </h2>
            <p className="text-gray-400 max-w-lg mx-auto mb-8">
              Create a free workspace, upload your first project files, and ask
              your first question — in under five minutes.
            </p>
            <Link
              href="/register"
              className="btn-primary text-base px-10 py-4 inline-flex items-center gap-2 shadow-lg shadow-hard-hat/25"
            >
              Get Started Free <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.06] py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-hard-hat rounded-md flex items-center justify-center">
              <HardHat className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-sm">
              Construction<span className="text-hard-hat">RAG</span>
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            Construction Project Intelligence &mdash; Secure, cited, role-aware.
          </p>
        </div>
      </footer>
    </div>
  );
}
