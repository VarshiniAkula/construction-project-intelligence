import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Card, CardContent, Grid, TextField, Typography } from '@mui/material'
import { createProject, listProjects, Project } from '../api/projects'

export default function Projects() {
  const nav = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [contractType, setContractType] = useState('')
  const [err, setErr] = useState<string | null>(null)

  const refresh = async () => {
    const ps = await listProjects()
    setProjects(ps)
  }

  useEffect(() => {
    refresh().catch((e) => setErr(e?.message || 'Failed to load projects'))
  }, [])

  const submit = async () => {
    setErr(null)
    try {
      const p = await createProject({ name, description: description || undefined, location: location || undefined, contract_type: contractType || undefined })
      setName('')
      setDescription('')
      setLocation('')
      setContractType('')
      await refresh()
      nav(`/projects/${p.id}`)
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Create project failed')
    }
  }

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>Projects</Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Create a new project</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField fullWidth label="Project name" value={name} onChange={(e) => setName(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField fullWidth label="Location (optional)" value={location} onChange={(e) => setLocation(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField fullWidth label="Contract type (optional)" value={contractType} onChange={(e) => setContractType(e.target.value)} placeholder="Design-bid-build, Design-build, etc." />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} multiline minRows={2} />
            </Grid>
          </Grid>
          {err && <Typography color="error" sx={{ mt: 2 }}>{err}</Typography>}
          <Button sx={{ mt: 2 }} variant="contained" onClick={submit} disabled={!name.trim()}>
            Create project
          </Button>
        </CardContent>
      </Card>

      <Typography variant="h6" sx={{ mb: 1 }}>Your projects</Typography>
      <Grid container spacing={2}>
        {projects.map((p) => (
          <Grid item xs={12} md={6} lg={4} key={p.id}>
            <Card variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => nav(`/projects/${p.id}`)}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{p.name}</Typography>
                <Typography variant="body2" color="text.secondary">{p.location || 'No location set'}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>{p.description || 'No description'}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
        {projects.length === 0 && (
          <Grid item xs={12}>
            <Typography variant="body2" color="text.secondary">No projects yet. Create one above.</Typography>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}
