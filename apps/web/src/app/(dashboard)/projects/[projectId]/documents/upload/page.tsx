"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useDropzone } from "react-dropzone";
import { api } from "@/lib/api-client";
import { DOC_TYPE_LABELS, VISIBILITY_LABELS } from "@/lib/utils";
import { Upload, FileText, CheckCircle, XCircle } from "lucide-react";

export default function UploadPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [docType, setDocType] = useState("general");
  const [visibility, setVisibility] = useState("project_full");
  const [tradeScope, setTradeScope] = useState("");
  const [revision, setRevision] = useState("");
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<Array<{ name: string; ok: boolean; error?: string }>>([]);

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/csv": [".csv"],
    },
    maxSize: 100 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    const uploadResults: typeof results = [];

    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("doc_type", docType);
      formData.append("visibility_scope", visibility);
      if (tradeScope) formData.append("trade_scope", tradeScope);
      if (revision) formData.append("revision", revision);

      try {
        await api.upload(`/projects/${projectId}/documents/upload`, formData);
        uploadResults.push({ name: file.name, ok: true });
      } catch (err: any) {
        uploadResults.push({ name: file.name, ok: false, error: err.message });
      }
    }

    setResults(uploadResults);
    setUploading(false);
    setFiles([]);
  };

  return (
    <div className="p-8 max-w-3xl">
      <div className="flex items-center gap-2 text-sm text-hard-concrete mb-6">
        <Link href="/dashboard" className="hover:text-hard-steel">Projects</Link>
        <span>/</span>
        <Link href={`/projects/${projectId}`} className="hover:text-hard-steel">Project</Link>
        <span>/</span>
        <Link href={`/projects/${projectId}/documents`} className="hover:text-hard-steel">Documents</Link>
        <span>/</span>
        <span className="text-hard-beam font-medium">Upload</span>
      </div>

      <h1 className="text-2xl font-bold text-hard-beam mb-6">Upload Documents</h1>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`card p-12 text-center cursor-pointer border-2 border-dashed transition-colors mb-6 ${
          isDragActive ? "border-hard-hat bg-hard-hat/5" : "border-surface-border hover:border-hard-steel"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-10 h-10 text-hard-concrete mx-auto mb-3" />
        <p className="text-hard-beam font-medium">Drop files here or click to browse</p>
        <p className="text-sm text-hard-concrete mt-1">PDF, DOCX, XLSX, CSV, PNG, JPG up to 100MB</p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="card p-4 mb-6 space-y-2">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-surface-muted rounded-lg">
              <FileText className="w-4 h-4 text-hard-concrete" />
              <span className="text-sm text-hard-beam flex-1">{f.name}</span>
              <span className="text-xs text-hard-concrete">{(f.size / 1024 / 1024).toFixed(1)} MB</span>
              <button onClick={() => setFiles(files.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600 text-xs">
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Metadata */}
      <div className="card p-6 mb-6 space-y-4">
        <h3 className="font-semibold text-hard-beam">Document Properties</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-hard-slate mb-1">Document Type</label>
            <select value={docType} onChange={(e) => setDocType(e.target.value)} className="input-field">
              {Object.entries(DOC_TYPE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-hard-slate mb-1">Visibility</label>
            <select value={visibility} onChange={(e) => setVisibility(e.target.value)} className="input-field">
              {Object.entries(VISIBILITY_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-hard-slate mb-1">Trade Scope</label>
            <input value={tradeScope} onChange={(e) => setTradeScope(e.target.value)} className="input-field" placeholder="e.g. electrical, concrete" />
          </div>
          <div>
            <label className="block text-sm font-medium text-hard-slate mb-1">Revision</label>
            <input value={revision} onChange={(e) => setRevision(e.target.value)} className="input-field" placeholder="e.g. Rev A, v2" />
          </div>
        </div>
      </div>

      <button onClick={handleUpload} disabled={files.length === 0 || uploading} className="btn-primary w-full py-3">
        {uploading ? "Uploading..." : `Upload ${files.length} file${files.length !== 1 ? "s" : ""}`}
      </button>

      {/* Results */}
      {results.length > 0 && (
        <div className="card p-4 mt-6 space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex items-center gap-3 p-2">
              {r.ok ? <CheckCircle className="w-5 h-5 text-status-approved" /> : <XCircle className="w-5 h-5 text-status-rejected" />}
              <span className="text-sm">{r.name}</span>
              {r.error && <span className="text-xs text-status-rejected">{r.error}</span>}
            </div>
          ))}
          <button
            onClick={() => router.push(`/projects/${projectId}/documents`)}
            className="btn-secondary mt-2"
          >
            View Documents
          </button>
        </div>
      )}
    </div>
  );
}
