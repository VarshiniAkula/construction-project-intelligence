import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Button, Card, CardContent, Divider, Grid, Tab, Tabs, TextField, Typography } from '@mui/material'
import { getProject, Project } from '../api/projects'
import { listDocuments, uploadDocument, downloadUrl, Doc } from '../api/documents'
import FileDropzone from '../components/FileDropzone'
import Chat from '../components/Chat'
import { createRfi, listRfis, analyzeRfi, importRfisCsv, RFI } from '../api/rfi'
import { getAnalytics, Analytics } from '../api/analytics'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'

export default function ProjectDetail() {
  const { projectId } = useParams()
  const pid = projectId || ''

  const [tab, setTab] = useState(0)
  const [project, setProject] = useState<Project | null>(null)
  const [docs, setDocs] = useState<Doc[]>([])
  const [rfis, setRfis] = useState<RFI[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)

  const [rfiTitle, setRfiTitle] = useState('')
  const [rfiNumber, setRfiNumber] = useState('')
  const [rfiQuestion, setRfiQuestion] = useState('')

  const refreshDocs = async () => setDocs(await listDocuments(pid))
  const refreshRfis = async () => setRfis(await listRfis(pid))
  const refreshAnalytics = async () => setAnalytics(await getAnalytics(pid))

  useEffect(() => {
    getProject(pid).then(setProject)
    refreshDocs()
    refreshRfis()
    refreshAnalytics()
  }, [pid])

  const upload = async (f: File) => {
    await uploadDocument(pid, f)
    await refreshDocs()
  }

  const createOneRfi = async () => {
    await createRfi(pid, { rfi_number: rfiNumber || undefined, title: rfiTitle, question: rfiQuestion, status: 'Open' })
    setRfiTitle('')
    setRfiNumber('')
    setRfiQuestion('')
    await refreshRfis()
    await refreshAnalytics()
  }

  const analyzeOne = async (id: string) => {
    await analyzeRfi(pid, id)
    await refreshRfis()
    await refreshAnalytics()
  }

  const importCsv = async (f: File) => {
    await importRfisCsv(pid, f)
    await refreshRfis()
    await refreshAnalytics()
  }

  const docsByStatus = useMemo(() => {
    const m: Record<string, number> = {}
    docs.forEach(d => { m[d.status] = (m[d.status] || 0) + 1 })
    return Object.entries(m).map(([status, count]) => ({ status, count }))
  }, [docs])

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{project?.name || 'Project'}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {project?.location || 'No location'} • {project?.contract_type || 'No contract type'}
      </Typography>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Overview" />
        <Tab label="Documents" />
        <Tab label="Assistant" />
        <Tab label="RFIs" />
        <Tab label="Analytics" />
      </Tabs>

      {tab === 0 && (
        <Grid container spacing={2}>
          <Grid item xs={12} md={7}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">How to use this project workspace</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  1) Upload drawings, specs, RFIs, meeting notes, submittals (PDF/DOCX work best).<br/>
                  2) Go to <strong>Assistant</strong> and ask questions. The assistant uses retrieval so it will cite snippets.<br/>
                  3) Import or create RFIs, then click <strong>Analyze</strong> to classify phase/issue and extract entities.<br/>
                  4) Review <strong>Analytics</strong> to spot recurring issues and trade risk.
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2">Document processing status</Typography>
                <Box sx={{ height: 220, mt: 1 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={docsByStatus}>
                      <XAxis dataKey="status" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={5}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">Quick prompts</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Try asking:
                </Typography>
                <ul>
                  <li>“What are the key scope risks for MEP rough-in based on the documents?”</li>
                  <li>“Find any conflicts between reflected ceiling plan and sections.”</li>
                  <li>“What is the spec section for gypsum board finishing?”</li>
                  <li>“Summarize open RFIs and likely schedule impact.”</li>
                </ul>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tab === 1 && (
        <Box>
          <Grid container spacing={2}>
            <Grid item xs={12} md={5}>
              <Typography variant="h6" sx={{ mb: 1 }}>Upload documents</Typography>
              <FileDropzone onFile={upload} />
            </Grid>

            <Grid item xs={12} md={7}>
              <Typography variant="h6" sx={{ mb: 1 }}>Document library</Typography>
              {docs.length === 0 && (
                <Typography variant="body2" color="text.secondary">No documents yet.</Typography>
              )}
              {docs.map((d) => (
                <Card key={d.id} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {d.original_filename} <Typography component="span" color="text.secondary">(v{d.version})</Typography>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Status: {d.status} • Extracted chars: {d.extracted_text_chars}
                      </Typography>
                      {d.error && <Typography variant="body2" color="error">{d.error}</Typography>}
                    </Box>
                    <Box>
                      <Button variant="outlined" href={downloadUrl(pid, d.id)} target="_blank">Download</Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Grid>
          </Grid>
        </Box>
      )}

      {tab === 2 && (
        <Chat projectId={pid} />
      )}

      {tab === 3 && (
        <Box>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6">Create RFI</Typography>
                  <TextField fullWidth label="RFI number (optional)" value={rfiNumber} onChange={(e) => setRfiNumber(e.target.value)} sx={{ mt: 2 }} />
                  <TextField fullWidth label="Title" value={rfiTitle} onChange={(e) => setRfiTitle(e.target.value)} sx={{ mt: 2 }} />
                  <TextField fullWidth label="Question / Description" value={rfiQuestion} onChange={(e) => setRfiQuestion(e.target.value)} sx={{ mt: 2 }} multiline minRows={3} />
                  <Button sx={{ mt: 2 }} variant="contained" onClick={createOneRfi} disabled={!rfiTitle.trim() || !rfiQuestion.trim()}>
                    Create
                  </Button>
                </CardContent>
              </Card>

              <Card variant="outlined" sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6">Import RFIs from CSV</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Expected columns: rfi_number, title, question, status
                  </Typography>
                  <FileDropzone onFile={importCsv} />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="h6" sx={{ mb: 1 }}>RFI list</Typography>
              {rfis.length === 0 && <Typography variant="body2" color="text.secondary">No RFIs yet.</Typography>}

              {rfis.map((r) => (
                <Card key={r.id} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {r.rfi_number ? `${r.rfi_number}: ` : ''}{r.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Status: {r.status}</Typography>
                      </Box>
                      <Button variant="contained" onClick={() => analyzeOne(r.id)}>Analyze</Button>
                    </Box>

                    <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>{r.question}</Typography>

                    {(r.phase_classification || r.issue_classification || r.trade_name) && (
                      <Box sx={{ mt: 1 }}>
                        <Divider sx={{ mb: 1 }} />
                        <Typography variant="caption" color="text.secondary">Analysis</Typography>
                        <Typography variant="body2">
                          Phase: <strong>{r.phase_classification || '—'}</strong> • Issue: <strong>{r.issue_classification || '—'}</strong>
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Trade: {r.trade_name || '—'} • Drawing: {r.drawing_reference || '—'} • Spec: {r.spec_section || '—'}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Grid>
          </Grid>
        </Box>
      )}

      {tab === 4 && (
        <Box>
          {!analytics && <Typography variant="body2" color="text.secondary">Loading analytics...</Typography>}
          {analytics && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">RFI aging</Typography>
                    <Box sx={{ height: 280, mt: 1 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analytics.rfi_aging}>
                          <XAxis dataKey="status" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="avg_age_days" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">Top recurring issues</Typography>
                    <Box sx={{ height: 280, mt: 1 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analytics.top_issues}>
                          <XAxis dataKey="issue" hide />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Hover bars to see issue labels.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">Trade risk indicators (starter)</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Risk score is a simple function of open RFIs, schedule impact days, and cost impact. Replace with a true predictive model later.
                    </Typography>
                    <Box sx={{ height: 280, mt: 1 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={analytics.trade_risk}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="trade" />
                          <YAxis />
                          <Tooltip />
                          <Line type="monotone" dataKey="risk_score" />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}
    </Box>
  )
}
