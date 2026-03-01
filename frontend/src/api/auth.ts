import { api } from './client'

export async function login(email: string, password: string) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  return res.data as { access_token: string; token_type: string }
}

export async function register(email: string, password: string, full_name?: string) {
  const res = await api.post('/auth/register', { email, password, full_name })
  return res.data
}

export async function me() {
  const res = await api.get('/auth/me')
  return res.data
}
