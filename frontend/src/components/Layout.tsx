import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AppBar, Toolbar, Typography, Drawer, List, ListItemButton, ListItemText, Box, Button } from '@mui/material'

const drawerWidth = 240

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()

  const logout = () => {
    localStorage.removeItem('cpi_token')
    navigate('/login')
  }

  const items = [
    { label: 'Projects', path: '/projects' },
    { label: 'Help / How to use', path: '/help' }
  ]

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      <AppBar position="fixed" sx={{ zIndex: 1201 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Construction Project Intelligence
          </Typography>
          <Button color="inherit" onClick={logout}>Logout</Button>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box', marginTop: '64px' }
        }}
      >
        <List>
          {items.map((it) => (
            <ListItemButton
              key={it.path}
              selected={location.pathname === it.path}
              onClick={() => navigate(it.path)}
            >
              <ListItemText primary={it.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, marginTop: '64px' }}>
        {children}
      </Box>
    </Box>
  )
}
