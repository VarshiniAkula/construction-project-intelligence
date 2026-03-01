import { api } from './client'

export type RFI = {
  id: string
  rfi_number?: string
  title: string
  question: string
  status: string
  created_at: string
  phase_classification?: string
  issue_classification?: string
  trade_name?: string
  drawing_reference?: string
  spec_section?: string
  gridline_reference?: string
  room_number?: string
  cost_impact?: number
  schedule_impact_days?: number
}

export async function listRfis(projectId: string): Promise<RFI[]> {
  const res = await api.get(`/projects/${projectId}/rfis`)
  return res.data
}

export async function createRfi(projectId: string, payload: { rfi_number?: string; title: string; question: string; status?: string }): Promise<RFI> {
  const res = await api.post(`/projects/${projectId}/rfis`, payload)
  return res.data
}

export async function analyzeRfi(projectId: string, rfiId: string) {
  const res = await api.post(`/projects/${projectId}/rfis/${rfiId}/analyze`)
  return res.data
}

export async function importRfisCsv(projectId: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post(`/projects/${projectId}/rfis/import_csv`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}
