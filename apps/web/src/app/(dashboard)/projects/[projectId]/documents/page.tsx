"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { DOC_TYPE_LABELS, VISIBILITY_LABELS, STATUS_COLORS, formatDate } from "@/lib/utils";
import { FileText, Upload, Search, Filter } from "lucide-react";
import { useState } from "react";

interface Document {
  id: string;
  file_name: string;
  doc_type: string;
  visibility_scope: string;
  trade_scope: string | null;
  revision: string | null;
  status: string;
  issue_date: string | null;
  uploaded_by_name: string;
  created_at: string;
  page_count: number | null;
}

export default function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [search, setSearch] = useState("");
  const [docTypeFilter, setDocTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", projectId, search, docTypeFilter, statusFilter],
    queryFn: () =>
      api.get<Document[]>(`/projects/${projectId}/documents`, {
        ...(search && { search }),
        ...(docTypeFilter && { doc_type: docTypeFilter }),
        ...(statusFilter && { status: statusFilter }),
      }),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2 text-sm text-hard-concrete">
          <Link href="/dashboard" className="hover:text-hard-steel">Projects</Link>
          <span>/</span>
          <Link href={`/projects/${projectId}`} className="hover:text-hard-steel">Project</Link>
          <span>/</span>
          <span className="text-hard-beam font-medium">Documents</span>
        </div>
        <Link href={`/projects/${projectId}/documents/upload`} className="btn-primary flex items-center gap-2">
          <Upload className="w-4 h-4" /> Upload
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-hard-beam mb-6">Documents Library</h1>

      {/* Filters */}
      <div className="card p-4 mb-6 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-hard-concrete" />
          <input
            type="text" placeholder="Search documents..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>
        <select value={docTypeFilter} onChange={(e) => setDocTypeFilter(e.target.value)} className="input-field w-auto">
          <option value="">All Types</option>
          {Object.entries(DOC_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input-field w-auto">
          <option value="">All Status</option>
          <option value="processing">Processing</option>
          <option value="ready">Ready</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-surface-muted border-b border-surface-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Document</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Type</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Visibility</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Revision</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Status</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Uploaded By</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-surface-muted/50 transition-colors">
                <td className="px-4 py-3">
                  <Link href={`/projects/${projectId}/documents/${doc.id}`} className="flex items-center gap-3 group">
                    <FileText className="w-5 h-5 text-hard-concrete flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-hard-beam group-hover:text-hard-hat transition-colors">
                        {doc.file_name}
                      </p>
                      {doc.trade_scope && <p className="text-xs text-hard-concrete">{doc.trade_scope}</p>}
                    </div>
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="badge bg-surface-muted text-hard-slate">{DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}</span>
                </td>
                <td className="px-4 py-3 text-sm text-hard-concrete">
                  {VISIBILITY_LABELS[doc.visibility_scope] || doc.visibility_scope}
                </td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{doc.revision || "—"}</td>
                <td className="px-4 py-3">
                  <span className={STATUS_COLORS[doc.status] || "badge"}>{doc.status}</span>
                </td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{doc.uploaded_by_name}</td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{formatDate(doc.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <div className="p-8 text-center text-hard-concrete">Loading documents...</div>}
        {!isLoading && documents.length === 0 && (
          <div className="p-12 text-center">
            <FileText className="w-10 h-10 text-hard-concrete mx-auto mb-3" />
            <p className="text-hard-concrete">No documents found</p>
          </div>
        )}
      </div>
    </div>
  );
}
