import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Box, Button, Card, CardContent, TextField, Typography } from '@mui/material'
import { login } from '../api/auth'

export default function Login() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState<string | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr(null)
    try {
      const res = await login(email, password)
      localStorage.setItem('cpi_token', res.access_token)
      nav('/projects')
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2 }}>Sign in</Typography>
          <Box component="form" onSubmit={submit}>
          <TextField fullWidth label="Email" value={email} onChange={(e) => setEmail(e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth type="password" label="Password" value={password} onChange={(e) => setPassword(e.target.value)} sx={{ mb: 2 }} />
          {err && <Typography color="error" sx={{ mb: 2 }}>{err}</Typography>}
          <Button type="submit" variant="contained" fullWidth>Login</Button>
          </Box>
          <Typography variant="body2" sx={{ mt: 2 }}>
            No account? <Link to="/register">Register</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
