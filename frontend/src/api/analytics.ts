import { api } from './client'

export type Analytics = {
  rfi_aging: { status: string; count: number; avg_age_days: number }[]
  top_issues: { issue: string; count: number }[]
  trade_risk: { trade: string; open_rfis: number; risk_score: number }[]
}

export async function getAnalytics(projectId: string): Promise<Analytics> {
  const res = await api.get(`/projects/${projectId}/analytics`)
  return res.data
}
