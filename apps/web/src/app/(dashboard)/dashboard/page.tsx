"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import { FolderOpen, FileText, Users, MapPin, Plus } from "lucide-react";
import { ROLE_LABELS, formatDate } from "@/lib/utils";
import { useState } from "react";

interface Project {
  id: string;
  name: string;
  code: string;
  location: string | null;
  description: string | null;
  created_at: string;
  member_count: number;
  document_count: number;
  my_role: string | null;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", code: "", location: "", description: "" });

  const { data: projects = [], isLoading, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/projects"),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post("/projects", newProject);
    setShowCreate(false);
    setNewProject({ name: "", code: "", location: "", description: "" });
    refetch();
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-hard-beam">Projects</h1>
          <p className="text-hard-concrete mt-1">Welcome back, {user?.full_name}</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="card p-6 mb-8">
          <h3 className="font-semibold text-hard-beam mb-4">Create New Project</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <input placeholder="Project Name" value={newProject.name} onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} className="input-field" required />
            <input placeholder="Project Code" value={newProject.code} onChange={(e) => setNewProject({ ...newProject, code: e.target.value })} className="input-field" required />
            <input placeholder="Location" value={newProject.location} onChange={(e) => setNewProject({ ...newProject, location: e.target.value })} className="input-field" />
            <input placeholder="Description" value={newProject.description} onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} className="input-field" />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Create</button>
            <button type="button" onClick={() => setShowCreate(false)} className="btn-ghost">Cancel</button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-5 bg-surface-muted rounded w-3/4 mb-3" />
              <div className="h-4 bg-surface-muted rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="card p-6 hover:shadow-md transition-shadow group">
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-hard-hat/10 flex items-center justify-center">
                  <FolderOpen className="w-5 h-5 text-hard-hat" />
                </div>
                {project.my_role && (
                  <span className="badge bg-hard-steel/10 text-hard-steel">
                    {ROLE_LABELS[project.my_role] || project.my_role}
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-hard-beam group-hover:text-hard-hat transition-colors">
                {project.name}
              </h3>
              <p className="text-sm text-hard-concrete mt-1">{project.code}</p>
              {project.location && (
                <p className="text-xs text-hard-concrete mt-2 flex items-center gap-1">
                  <MapPin className="w-3 h-3" /> {project.location}
                </p>
              )}
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-surface-border text-xs text-hard-concrete">
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" /> {project.document_count} docs
                </span>
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" /> {project.member_count} members
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!isLoading && projects.length === 0 && (
        <div className="text-center py-20">
          <FolderOpen className="w-12 h-12 text-hard-concrete mx-auto mb-4" />
          <h3 className="text-lg font-medium text-hard-slate">No projects yet</h3>
          <p className="text-hard-concrete mt-1">Create your first project to get started.</p>
        </div>
      )}
    </div>
  );
}
