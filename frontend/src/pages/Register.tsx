import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Box, Button, Card, CardContent, TextField, Typography } from '@mui/material'
import { register } from '../api/auth'

export default function Register() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState<string | null>(null)

  const submit = async () => {
    setErr(null)
    try {
      await register(email, password, fullName || undefined)
      nav('/login')
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
      <Card sx={{ width: 420 }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2 }}>Create account</Typography>
          <TextField fullWidth label="Email" value={email} onChange={(e) => setEmail(e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth label="Full name (optional)" value={fullName} onChange={(e) => setFullName(e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth type="password" label="Password (min 8 chars)" value={password} onChange={(e) => setPassword(e.target.value)} sx={{ mb: 2 }} />
          {err && <Typography color="error" sx={{ mb: 2 }}>{err}</Typography>}
          <Button variant="contained" fullWidth onClick={submit}>Register</Button>
          <Typography variant="body2" sx={{ mt: 2 }}>
            Already have an account? <Link to="/login">Login</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
