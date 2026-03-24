"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { ROLE_LABELS, formatDate } from "@/lib/utils";
import { Users, Plus, Shield } from "lucide-react";
import { useState } from "react";

interface Member {
  id: string;
  user_id: string;
  project_id: string;
  role: string;
  assigned_trade: string | null;
  user_email: string;
  user_full_name: string;
  user_company: string | null;
  created_at: string;
}

export default function MembersPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [showAdd, setShowAdd] = useState(false);
  const [newMember, setNewMember] = useState({ email: "", role: "subcontractor", assigned_trade: "" });

  const { data: members = [], refetch } = useQuery({
    queryKey: ["members", projectId],
    queryFn: () => api.get<Member[]>(`/projects/${projectId}/members`),
  });

  const addMember = useMutation({
    mutationFn: (data: typeof newMember) =>
      api.post(`/projects/${projectId}/members`, {
        ...data,
        assigned_trade: data.assigned_trade || null,
      }),
    onSuccess: () => {
      setShowAdd(false);
      setNewMember({ email: "", role: "subcontractor", assigned_trade: "" });
      refetch();
    },
  });

  const updateRole = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      api.patch(`/projects/${projectId}/members/${id}`, { role }),
    onSuccess: () => refetch(),
  });

  return (
    <div className="p-8">
      <div className="flex items-center gap-2 text-sm text-hard-concrete mb-6">
        <Link href={`/projects/${projectId}`} className="hover:text-hard-steel">Project</Link>
        <span>/</span>
        <span className="text-hard-beam font-medium">Members</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-hard-beam">Team Members</h1>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Add Member
        </button>
      </div>

      {showAdd && (
        <form
          onSubmit={(e) => { e.preventDefault(); addMember.mutate(newMember); }}
          className="card p-6 mb-6"
        >
          <h3 className="font-semibold text-hard-beam mb-4">Add Team Member</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <input
              placeholder="Email address"
              value={newMember.email}
              onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
              className="input-field"
              required
            />
            <select
              value={newMember.role}
              onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
              className="input-field"
            >
              {Object.entries(ROLE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <input
              placeholder="Assigned trade (optional)"
              value={newMember.assigned_trade}
              onChange={(e) => setNewMember({ ...newMember, assigned_trade: e.target.value })}
              className="input-field"
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Add</button>
            <button type="button" onClick={() => setShowAdd(false)} className="btn-ghost">Cancel</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-surface-muted border-b border-surface-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Name</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Email</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Company</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Role</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Trade</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-hard-concrete uppercase">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {members.map((m) => (
              <tr key={m.id} className="hover:bg-surface-muted/50">
                <td className="px-4 py-3 text-sm font-medium text-hard-beam">{m.user_full_name}</td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{m.user_email}</td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{m.user_company || "—"}</td>
                <td className="px-4 py-3">
                  <select
                    value={m.role}
                    onChange={(e) => updateRole.mutate({ id: m.id, role: e.target.value })}
                    className="text-sm border border-surface-border rounded px-2 py-1 bg-white"
                  >
                    {Object.entries(ROLE_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{m.assigned_trade || "—"}</td>
                <td className="px-4 py-3 text-sm text-hard-concrete">{formatDate(m.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
