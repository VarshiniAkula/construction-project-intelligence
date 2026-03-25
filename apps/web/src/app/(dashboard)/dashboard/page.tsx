"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import { FolderOpen, FileText, Users, MapPin, Plus, Building2, ArrowRight } from "lucide-react";
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
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const { data: projects = [], isLoading, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/projects"),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError("");
    try {
      await api.post("/projects", newProject);
      setShowCreate(false);
      setNewProject({ name: "", code: "", location: "", description: "" });
      refetch();
    } catch (err: any) {
      setCreateError(err.message || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  // Auto-generate code from name
  const handleNameChange = (name: string) => {
    const code = name
      .toUpperCase()
      .replace(/[^A-Z0-9\s]/g, "")
      .split(/\s+/)
      .filter(Boolean)
      .map((w) => w.slice(0, 4))
      .join("-")
      .slice(0, 20);
    setNewProject({ ...newProject, name, code: newProject.code || code });
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

      {/* Create Project Form */}
      {showCreate && (
        <form onSubmit={handleCreate} className="card p-6 mb-8 border-2 border-hard-hat/20">
          <h3 className="font-semibold text-hard-beam mb-1">Create New Construction Site Workspace</h3>
          <p className="text-sm text-hard-concrete mb-4">
            Set up an isolated workspace for your project. You can add team members after creation.
          </p>

          {createError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
              {createError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-hard-slate mb-1">Project Name *</label>
              <input
                placeholder="e.g. Riverside Commercial Complex"
                value={newProject.name}
                onChange={(e) => handleNameChange(e.target.value)}
                className="input-field"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-hard-slate mb-1">Project Code *</label>
              <input
                placeholder="e.g. RVSD-COMM"
                value={newProject.code}
                onChange={(e) => setNewProject({ ...newProject, code: e.target.value.toUpperCase() })}
                className="input-field"
                required
              />
              <p className="text-xs text-hard-concrete mt-1">Unique short code for this project</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-hard-slate mb-1">Location</label>
              <input
                placeholder="e.g. Austin, TX"
                value={newProject.location}
                onChange={(e) => setNewProject({ ...newProject, location: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-hard-slate mb-1">Description</label>
              <input
                placeholder="Brief description of the project"
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                className="input-field"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={creating} className="btn-primary flex items-center gap-2">
              {creating ? "Creating..." : "Create Workspace"}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="btn-ghost">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Loading skeleton */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-5 bg-surface-muted rounded w-3/4 mb-3" />
              <div className="h-4 bg-surface-muted rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : projects.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="card p-6 hover:shadow-md transition-shadow group"
            >
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
      ) : (
        /* Empty state for new users */
        <div className="text-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-hard-hat/10 flex items-center justify-center mx-auto mb-5">
            <Building2 className="w-8 h-8 text-hard-hat" />
          </div>
          <h3 className="text-xl font-semibold text-hard-beam">Create your first workspace</h3>
          <p className="text-hard-concrete mt-2 max-w-md mx-auto">
            A workspace is an isolated space for a construction project. Upload documents, invite team
            members, and use the AI assistant to get cited answers.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Create Your First Workspace
          </button>
        </div>
      )}
    </div>
  );
}
