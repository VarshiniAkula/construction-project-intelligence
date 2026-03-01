import React, { useRef } from 'react'
import { Box, Button, Typography } from '@mui/material'

export default function FileDropzone({ onFile }: { onFile: (f: File) => void }) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  const handlePick = () => inputRef.current?.click()
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) onFile(f)
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f) onFile(f)
  }

  return (
    <Box
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      sx={{
        border: '2px dashed #aaa',
        borderRadius: 2,
        p: 2,
        textAlign: 'center'
      }}
    >
      <Typography variant="body1" sx={{ mb: 1 }}>
        Drag & drop a file here, or choose a file
      </Typography>
      <Button variant="contained" onClick={handlePick}>Choose file</Button>
      <input ref={inputRef} type="file" style={{ display: 'none' }} onChange={handleChange} />
      <Typography variant="caption" display="block" sx={{ mt: 1 }}>
        Tip: PDFs and DOCX extract best in this MVP.
      </Typography>
    </Box>
  )
}
