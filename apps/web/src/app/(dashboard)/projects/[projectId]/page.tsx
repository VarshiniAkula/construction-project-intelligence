"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { ROLE_LABELS, formatDate } from "@/lib/utils";
import { FileText, MessageSquare, Users, Shield, Upload, FolderOpen } from "lucide-react";

export default function ProjectOverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<any>(`/projects/${projectId}`),
  });

  if (!project) {
    return <div className="p-8 animate-pulse">Loading project...</div>;
  }

  const links = [
    { href: `/projects/${projectId}/documents`, icon: FileText, label: "Documents", desc: "Browse and manage project documents", color: "bg-hard-hat/10 text-hard-hat" },
    { href: `/projects/${projectId}/documents/upload`, icon: Upload, label: "Upload Documents", desc: "Upload new drawings, specs, RFIs, and more", color: "bg-green-50 text-status-approved" },
    { href: `/projects/${projectId}/chat`, icon: MessageSquare, label: "Chat", desc: "Ask questions about your project documents", color: "bg-blue-50 text-hard-steel" },
    { href: `/projects/${projectId}/members`, icon: Users, label: "Team Members", desc: "Manage project roles and access", color: "bg-purple-50 text-purple-600" },
    { href: `/projects/${projectId}/audit`, icon: Shield, label: "Audit Log", desc: "View activity history", color: "bg-amber-50 text-amber-600" },
  ];

  return (
    <div className="p-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-hard-concrete mb-6">
        <Link href="/dashboard" className="hover:text-hard-steel">Projects</Link>
        <span>/</span>
        <span className="text-hard-beam font-medium">{project.name}</span>
      </div>

      {/* Header */}
      <div className="card p-6 mb-8">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-hard-hat/10 rounded-xl flex items-center justify-center">
                <FolderOpen className="w-6 h-6 text-hard-hat" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-hard-beam">{project.name}</h1>
                <p className="text-hard-concrete">{project.code} {project.location && `• ${project.location}`}</p>
              </div>
            </div>
            {project.description && <p className="text-sm text-hard-concrete mt-3">{project.description}</p>}
          </div>
          {project.my_role && (
            <span className="badge bg-hard-steel/10 text-hard-steel text-sm px-3 py-1">
              {ROLE_LABELS[project.my_role] || project.my_role}
            </span>
          )}
        </div>
        <div className="flex items-center gap-6 mt-6 pt-4 border-t border-surface-border text-sm text-hard-concrete">
          <span>{project.document_count} documents</span>
          <span>{project.member_count} members</span>
          <span>Created {formatDate(project.created_at)}</span>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {links.map((link) => (
          <Link key={link.href} href={link.href} className="card p-5 hover:shadow-md transition-shadow group">
            <div className={`w-10 h-10 rounded-lg ${link.color} flex items-center justify-center mb-3`}>
              <link.icon className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-hard-beam group-hover:text-hard-hat transition-colors">
              {link.label}
            </h3>
            <p className="text-sm text-hard-concrete mt-1">{link.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
