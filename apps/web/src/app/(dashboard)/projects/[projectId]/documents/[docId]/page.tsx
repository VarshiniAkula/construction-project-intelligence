"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { DOC_TYPE_LABELS, VISIBILITY_LABELS, STATUS_COLORS, formatDate } from "@/lib/utils";
import { FileText, Download, ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DocumentDetailPage() {
  const { projectId, docId } = useParams<{ projectId: string; docId: string }>();
  const searchParams = useSearchParams();
  const highlightPage = searchParams.get("page");
  const [currentPage, setCurrentPage] = useState(1);

  const { data: doc } = useQuery({
    queryKey: ["document", projectId, docId],
    queryFn: () => api.get<any>(`/projects/${projectId}/documents/${docId}`),
    refetchInterval: (query) => {
      const d = query.state.data;
      return d && d.status === "processing" ? 3000 : false;
    },
  });

  useEffect(() => {
    if (highlightPage) setCurrentPage(parseInt(highlightPage));
  }, [highlightPage]);

  if (!doc) return <div className="p-8 animate-pulse">Loading document...</div>;

  const totalPages = doc.page_count || doc.pages?.length || 0;

  return (
    <div className="p-8">
      <div className="flex items-center gap-2 text-sm text-hard-concrete mb-6">
        <Link href={`/projects/${projectId}/documents`} className="hover:text-hard-steel">Documents</Link>
        <span>/</span>
        <span className="text-hard-beam font-medium truncate max-w-[300px]">{doc.file_name}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Viewer */}
        <div className="lg:col-span-2">
          <div className="card overflow-hidden">
            {/* Page navigation */}
            <div className="flex items-center justify-between px-4 py-2 bg-surface-muted border-b border-surface-border">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage <= 1}
                className="btn-ghost p-1"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm text-hard-slate">
                Page {currentPage} of {totalPages || "?"}
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage >= totalPages}
                className="btn-ghost p-1"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Page content */}
            <div className="bg-gray-100 min-h-[600px] flex items-center justify-center">
              {(doc.status === "ready" || doc.pages?.length > 0) && doc.file_type === "pdf" ? (
                <img
                  src={`${API_URL}/api/projects/${projectId}/documents/${docId}/pages/${currentPage}/image`}
                  alt={`Page ${currentPage}`}
                  className="max-w-full h-auto"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              ) : (doc.status === "ready" || doc.pages?.length > 0) && ["docx", "xlsx", "csv"].includes(doc.file_type) ? (
                <div className="w-full p-6 text-sm font-mono whitespace-pre-wrap overflow-auto max-h-[700px]">
                  {doc.pages?.[currentPage - 1]?.page_summary || "Content extracted. View in document library."}
                </div>
              ) : (
                <div className="text-center p-8">
                  <FileText className="w-16 h-16 text-hard-concrete mx-auto mb-4" />
                  <p className="text-hard-concrete">
                    {doc.status === "processing" ? "Document is being processed..." : "Preview not available"}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Page thumbnails */}
          {doc.pages && doc.pages.length > 0 && (
            <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
              {doc.pages.map((page: any) => (
                <button
                  key={page.page_number}
                  onClick={() => setCurrentPage(page.page_number)}
                  className={`flex-shrink-0 w-16 h-20 rounded border-2 flex items-center justify-center text-xs transition-colors ${
                    currentPage === page.page_number
                      ? "border-hard-hat bg-hard-hat/5 text-hard-hat"
                      : "border-surface-border hover:border-hard-steel"
                  }`}
                >
                  {page.page_number}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Metadata panel */}
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="font-semibold text-hard-beam mb-4">Document Info</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-hard-concrete">Status</dt>
                <dd><span className={STATUS_COLORS[doc.status] || "badge"}>{doc.status}</span></dd>
              </div>
              {doc.processing_error && (
                <div>
                  <dt className="text-hard-concrete">Error</dt>
                  <dd className="text-status-rejected text-xs">{doc.processing_error}</dd>
                </div>
              )}
              <div>
                <dt className="text-hard-concrete">Type</dt>
                <dd className="text-hard-beam">{DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}</dd>
              </div>
              <div>
                <dt className="text-hard-concrete">Visibility</dt>
                <dd className="text-hard-beam">{VISIBILITY_LABELS[doc.visibility_scope] || doc.visibility_scope}</dd>
              </div>
              {doc.trade_scope && (
                <div>
                  <dt className="text-hard-concrete">Trade</dt>
                  <dd className="text-hard-beam">{doc.trade_scope}</dd>
                </div>
              )}
              {doc.revision && (
                <div>
                  <dt className="text-hard-concrete">Revision</dt>
                  <dd className="text-hard-beam">{doc.revision}</dd>
                </div>
              )}
              <div>
                <dt className="text-hard-concrete">Pages</dt>
                <dd className="text-hard-beam">{totalPages}</dd>
              </div>
              <div>
                <dt className="text-hard-concrete">Uploaded By</dt>
                <dd className="text-hard-beam">{doc.uploaded_by_name}</dd>
              </div>
              <div>
                <dt className="text-hard-concrete">Upload Date</dt>
                <dd className="text-hard-beam">{formatDate(doc.created_at)}</dd>
              </div>
            </dl>
          </div>

          <a
            href={`${API_URL}/api/projects/${projectId}/documents/${docId}/download`}
            className="btn-secondary w-full flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" /> Download Original
          </a>

          {/* Page summaries */}
          {doc.pages?.some((p: any) => p.page_summary) && (
            <div className="card p-5">
              <h3 className="font-semibold text-hard-beam mb-3">Page Summaries</h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {doc.pages.filter((p: any) => p.page_summary).map((page: any) => (
                  <button
                    key={page.page_number}
                    onClick={() => setCurrentPage(page.page_number)}
                    className="block w-full text-left p-3 rounded-lg hover:bg-surface-muted transition-colors"
                  >
                    <span className="text-xs font-medium text-hard-hat">Page {page.page_number}</span>
                    <p className="text-xs text-hard-concrete mt-1 line-clamp-3">{page.page_summary}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
