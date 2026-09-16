import { useEffect, useRef } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/health`).catch(() => undefined)
  }, [])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">V</div>
          <div>
            <h1>VeriDoc AI</h1>
            <p className="brand-tagline">Intelligent Document Verification &amp; Fraud Detection</p>
          </div>
        </div>
        <nav className="desktop-nav" aria-label="Main navigation">
          <a className="active" href="#dashboard">Dashboard</a>
          <a href="#verify">Verify Document</a>
          <a href="#documents">Documents</a>
          <a href="#history">Verification History</a>
          <a href="#profile">Profile</a>
          <a href="#settings">Settings</a>
        </nav>
        <button className="avatar-button" type="button" aria-label="Open profile">JD</button>
      </header>

      <main className="main-content" id="dashboard">
        <div className="content-heading">
          <div>
            <p className="eyebrow">Overview</p>
            <h2>Welcome to VeriDoc AI</h2>
            <p className="description">
              Verify documents, detect inconsistencies, and identify potential tampering with AI-powered analysis.
            </p>
          </div>
          <button className="profile-chip" type="button" id="profile">
            <span className="profile-avatar">JD</span>
            <span>Jordan Davis</span>
            <span className="chevron">⌄</span>
          </button>
        </div>

        <section className="welcome-grid" id="verify">
          <div className="welcome-copy">
            <span className="spark-icon" aria-hidden="true">✦</span>
            <p className="section-label">Your verification workspace</p>
            <h3>Confidence in every document.</h3>
            <p>Start with a document and let VeriDoc AI help you review what matters.</p>
            <button className="primary-action" type="button" onClick={() => fileInputRef.current?.click()}>
              <span aria-hidden="true">＋</span> Upload Document
            </button>
            <input ref={fileInputRef} className="visually-hidden" type="file" accept=".pdf,.jpg,.jpeg,.png" />
            <span className="file-note">PDF, JPG, JPEG, or PNG</span>
          </div>
          <div className="document-art" aria-hidden="true">
            <div className="scan-line" />
            <div className="document-sheet">
              <span className="sheet-top" />
              <span className="sheet-line long" />
              <span className="sheet-line" />
              <span className="sheet-line short" />
              <span className="sheet-seal">✓</span>
            </div>
            <div className="shield">✓</div>
          </div>
        </section>

        <section className="recent-section" id="history">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Activity</p>
              <h3>Recent Verifications</h3>
            </div>
            <a href="#documents">View all <span aria-hidden="true">→</span></a>
          </div>
          <div className="empty-state" id="documents">
            <div className="empty-icon" aria-hidden="true">▤</div>
            <h4>No documents verified yet.</h4>
            <p>Your verified documents will appear here once you begin.</p>
            <button className="secondary-action" type="button" onClick={() => fileInputRef.current?.click()}>
              Upload your first document
            </button>
          </div>
        </section>
      </main>

      <nav className="mobile-nav" aria-label="Mobile navigation">
        <a className="active" href="#dashboard"><span aria-hidden="true">⌂</span>Home</a>
        <a href="#verify"><span aria-hidden="true">＋</span>Verify</a>
        <a href="#documents"><span aria-hidden="true">▤</span>Documents</a>
        <a href="#history"><span aria-hidden="true">◷</span>History</a>
        <a href="#profile"><span aria-hidden="true">○</span>Profile</a>
      </nav>
    </div>
  )
}

export default App
