import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState('Checking...')
  const [backendDetails, setBackendDetails] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()
        setBackendDetails(data)
        setStatus('Backend Connected')
        setError('')
      } catch (err) {
        setStatus('Backend Unavailable')
        setError(err.message || 'Unable to reach the backend')
        setBackendDetails(null)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">V</div>
          <div>
            <p className="eyebrow">AI document verification</p>
            <h1>VeriDoc AI</h1>
          </div>
        </div>
        <nav className="nav" aria-label="Main navigation">
          <a href="#overview">Overview</a>
          <a href="#status">Status</a>
          <a href="#foundation">Foundation</a>
        </nav>
      </header>

      <main className="main-content">
        <section className="hero-panel" id="overview">
          <div>
            <p className="section-label">Phase 1 foundation</p>
            <h2>Application foundation is live.</h2>
            <p className="description">
              This project establishes a responsive React frontend and FastAPI backend foundation
              for future document verification workflows.
            </p>
          </div>

          <div className="status-card" id="status">
            <span className="status-label">Backend status</span>
            <strong className="status-value">{status}</strong>
            {error ? <p className="error-text">{error}</p> : null}
            {backendDetails ? (
              <dl className="status-meta">
                <div>
                  <dt>Service</dt>
                  <dd>{backendDetails.service}</dd>
                </div>
                <div>
                  <dt>Environment</dt>
                  <dd>{backendDetails.environment}</dd>
                </div>
                <div>
                  <dt>Version</dt>
                  <dd>{backendDetails.version}</dd>
                </div>
              </dl>
            ) : null}
          </div>
        </section>

        <section className="foundation-grid" id="foundation">
          <article className="feature-card">
            <h3>Frontend</h3>
            <p>React shell, responsive layout, navigation foundation, and health-check integration.</p>
          </article>
          <article className="feature-card">
            <h3>Backend</h3>
            <p>FastAPI app, configuration, logging, CORS, and health endpoints for future services.</p>
          </article>
          <article className="feature-card">
            <h3>Future</h3>
            <p>OCR, validation, duplicate detection, forensic analysis, and scoring will be added later.</p>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App
