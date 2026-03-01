import { api } from './client'

export type SourceSnippet = {
  document_id: string
  filename: string
  version: number
  snippet: string
}

export type ChatResponse = {
  answer: string
  sources: SourceSnippet[]
  mode: string
}

export async function chat(projectId: string, message: string, top_k?: number): Promise<ChatResponse> {
  const res = await api.post(`/projects/${projectId}/assistant/chat`, { message, top_k })
  return res.data
}
