import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import MetricsPreview from './MetricsPreview.jsx'

const Page = window.location.search.includes('preview') ? MetricsPreview : App

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)