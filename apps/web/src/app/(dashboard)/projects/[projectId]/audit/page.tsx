"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { formatDateTime } from "@/lib/utils";
import { Shield, Filter } from "lucide-react";
import { useState } from "react";

interface AuditEntry {
  id: string;
  user_email: string;
  user_name: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details_json: Record<string, unknown> | null;
  created_at: string;
}

const ACTION_LABELS: Record<string, string> = {
  "auth.login": "Signed In",
  "document.upload": "Uploaded Document",
  "document.view": "Viewed Document",
  "chat.query": "Asked Question",
  "member.add": "Added Member",
  "member.update": "Updated Member",
  "project.create": "Created Project",
};

export default function AuditPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [actionFilter, setActionFilter] = useState("");

  const { data: logs = [] } = useQuery({
    queryKey: ["audit", projectId, actionFilter],
    queryFn: () =>
      api.get<AuditEntry[]>(`/projects/${projectId}/audit`, {
        ...(actionFilter && { action: actionFilter }),
        limit: "100",
      }),
  });

  return (
    <div className="p-8">
      <div className="flex items-center gap-2 text-sm text-hard-concrete mb-6">
        <Link href={`/projects/${projectId}`} className="hover:text-hard-steel">Project</Link>
        <span>/</span>
        <span className="text-hard-beam font-medium">Audit Log</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-hard-beam flex items-center gap-2">
          <Shield className="w-6 h-6 text-hard-hat" /> Audit Log
        </h1>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="input-field w-auto"
        >
          <option value="">All Actions</option>
          {Object.entries(ACTION_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-surface-muted border-b border-surface-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Time</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">User</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Action</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Entity</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-surface-muted/50">
                <td className="px-4 py-3 text-sm text-hard-concrete whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-hard-beam">{log.user_name}</p>
                  <p className="text-xs text-hard-concrete">{log.user_email}</p>
                </td>
                <td className="px-4 py-3">
                  <span className="badge bg-surface-muted text-hard-slate">
                    {ACTION_LABELS[log.action] || log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-hard-concrete">
                  {log.entity_type && <span>{log.entity_type}</span>}
                </td>
                <td className="px-4 py-3 text-xs text-hard-concrete max-w-xs truncate">
                  {log.details_json ? JSON.stringify(log.details_json) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && (
          <div className="p-12 text-center text-hard-concrete">No audit logs found</div>
        )}
      </div>
    </div>
  );
}
