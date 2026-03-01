import { api } from './client'

export type Doc = {
  id: string
  original_filename: string
  version: number
  status: string
  created_at: string
  extracted_text_chars: number
  error?: string
}

export async function listDocuments(projectId: string): Promise<Doc[]> {
  const res = await api.get(`/projects/${projectId}/documents`)
  return res.data
}

export async function uploadDocument(projectId: string, file: File): Promise<Doc> {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post(`/projects/${projectId}/documents`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export function downloadUrl(projectId: string, docId: string) {
  const base = api.defaults.baseURL || ''
  return `${base}/projects/${projectId}/documents/${docId}/download`
}
