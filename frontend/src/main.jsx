import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import MetricsPreview from './MetricsPreview.jsx'
import LiveInvestigation1 from './LiveInvestigation1.jsx'

const q = window.location.search
const Page = q.includes('live') ? LiveInvestigation1 : q.includes('preview') ? MetricsPreview : App

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)