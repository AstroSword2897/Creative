import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Temporarily removed StrictMode to fix Three.js double-mount issue
// Will re-enable with proper guards later
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)

