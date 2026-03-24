"use client";

import Link from "next/link";
import { FileText, Shield, MessageSquare, Search, Users, HardHat } from "lucide-react";

const features = [
  {
    icon: FileText,
    title: "Smart Document Ingestion",
    desc: "Upload drawings, specs, RFIs, submittals, and more. Our AI extracts, indexes, and understands every page.",
  },
  {
    icon: MessageSquare,
    title: "Ask Your Documents",
    desc: "Chat with your project documents in plain language. Every answer is grounded in your actual project data with citations.",
  },
  {
    icon: Shield,
    title: "Role-Aware Access",
    desc: "Subcontractors see only their trade docs. Owners see only what you share. Access control is enforced at every layer.",
  },
  {
    icon: Search,
    title: "Hybrid AI Retrieval",
    desc: "Dense embeddings plus keyword search with reranking. Find the right information even in thousands of pages.",
  },
  {
    icon: Users,
    title: "Built for Teams",
    desc: "PMs, superintendents, subcontractors, and owners each get the right view of the right documents.",
  },
  {
    icon: HardHat,
    title: "Construction-Native",
    desc: "Understands title blocks, spec sections, RFI workflows, daily reports, and construction-specific document types.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-hard-beam">
      {/* Nav */}
      <nav className="border-b border-white/10 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-hard-hat rounded-lg flex items-center justify-center">
            <HardHat className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">BuildDocs AI</span>
        </div>
        <Link href="/login" className="btn-primary text-sm">
          Sign In
        </Link>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-hard-hat/10 border border-hard-hat/30 rounded-full px-4 py-1.5 mb-6">
          <span className="text-hard-hat text-sm font-medium">Construction Document Intelligence</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
          Ask your project docs.<br />
          <span className="text-hard-hat">Get cited answers.</span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-10">
          BuildDocs AI lets construction teams upload project documents, then chat with them.
          Role-based access ensures every team member sees only what they should.
          Every answer cites the exact document and page.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login" className="btn-primary text-lg px-8 py-3">
            Get Started
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="bg-white/5 border border-white/10 rounded-xl p-6">
              <f.icon className="w-10 h-10 text-hard-hat mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 text-center text-gray-500 text-sm">
        BuildDocs AI &mdash; Construction Document Intelligence Platform
      </footer>
    </div>
  );
}
