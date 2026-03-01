import React from 'react'
import { Box, Card, CardContent, Divider, Typography } from '@mui/material'

export default function Help() {
  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>Help / How to use</Typography>

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">What this app does (MVP)</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            This is a local-run Construction Project Intelligence workspace. Each project acts like a private folder
            for documents + RFIs + analytics. The Assistant can answer questions by searching your uploaded documents
            and citing relevant snippets.
          </Typography>
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">Typical workflow</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            1) Create a Project<br/>
            2) Upload Documents (PDF/DOCX work best in this MVP)<br/>
            3) Ask the Assistant questions (it will cite sources)<br/>
            4) Import or create RFIs, then click Analyze for classification + entity extraction<br/>
            5) Review Analytics to spot recurring issues and risks
          </Typography>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6">Troubleshooting</Typography>
          <Divider sx={{ my: 1 }} />
          <Typography variant="subtitle2">Document shows “No extractable text found”</Typography>
          <Typography variant="body2" color="text.secondary">
            Many drawings are scanned PDFs. This MVP does not enable OCR. Convert to searchable PDF or upload specs/RFI logs/meeting minutes for best results.
          </Typography>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>Assistant says it is in “fallback” mode</Typography>
          <Typography variant="body2" color="text.secondary">
            That means no OpenAI API key is configured. The assistant still retrieves relevant snippets, but does not call a large language model.
            To enable LLM answers, set OPENAI_API_KEY in your .env and restart the app.
          </Typography>

          <Typography variant="subtitle2" sx={{ mt: 2 }}>I want true RFI NLP models</Typography>
          <Typography variant="body2" color="text.secondary">
            The backend includes a placeholder heuristic classifier + entity extraction.
            You can replace it with a fine-tuned transformer classifier and spaCy NER while keeping the same API endpoints.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
