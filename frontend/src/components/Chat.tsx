import React, { useState } from 'react'
import { Box, Button, Paper, TextField, Typography, Divider, Chip } from '@mui/material'
import { chat, SourceSnippet } from '../api/assistant'

type Msg = { role: 'user' | 'assistant'; text: string; sources?: SourceSnippet[]; mode?: string }

export default function Chat({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    const q = input.trim()
    if (!q) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await chat(projectId, q)
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, sources: res.sources, mode: res.mode }])
    } catch (e: any) {
      setMessages((m) => [...m, { role: 'assistant', text: `Error: ${e?.message || 'Request failed'}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 1 }}>Project Assistant</Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        Ask questions like: <em>"What spec section covers gypsum board finishing?"</em>, or <em>"Any conflicts in ceiling heights?"</em>
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, height: 420, overflow: 'auto' }}>
        {messages.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No messages yet. Upload documents, then ask your first question.
          </Typography>
        )}

        {messages.map((m, idx) => (
          <Box key={idx} sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
              {m.role === 'user' ? 'You' : 'Assistant'} {m.mode ? <Chip size="small" label={m.mode} sx={{ ml: 1 }} /> : null}
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{m.text}</Typography>

            {m.sources && m.sources.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Divider sx={{ mb: 1 }} />
                <Typography variant="caption" color="text.secondary">Sources</Typography>
                {m.sources.map((s, i) => (
                  <Box key={i} sx={{ mt: 0.5 }}>
                    <Typography variant="caption"><strong>{s.filename}</strong> (v{s.version})</Typography>
                    <Typography variant="caption" display="block" color="text.secondary">{s.snippet}</Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        ))}
      </Paper>

      <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
        <TextField
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this project..."
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          multiline
          minRows={2}
        />
        <Button variant="contained" onClick={send} disabled={loading}>
          {loading ? 'Thinking...' : 'Send'}
        </Button>
      </Box>
    </Box>
  )
}
