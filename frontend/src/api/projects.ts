import { api } from './client'

export type Project = {
  id: string
  name: string
  description?: string
  location?: string
  contract_type?: string
  created_at: string
}

export async function listProjects(): Promise<Project[]> {
  const res = await api.get('/projects')
  return res.data
}

export async function createProject(payload: { name: string; description?: string; location?: string; contract_type?: string }): Promise<Project> {
  const res = await api.post('/projects', payload)
  return res.data
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await api.get(`/projects/${projectId}`)
  return res.data
}
