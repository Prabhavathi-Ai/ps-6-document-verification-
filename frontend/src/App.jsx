import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const MAX_FILE_SIZE = 20 * 1024 * 1024
const ACCEPTED_TYPES = ['application/pdf', 'image/png', 'image/jpeg']
const ACCEPTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']
const UPLOAD_ERROR_MESSAGES = {
  EMPTY_FILE: 'Choose a document that contains data.',
  FILE_TOO_LARGE: 'File is too large.',
  INVALID_FILE_CONTENT: 'The file content could not be validated.',
  INVALID_FILENAME: 'Choose a file with a valid name.',
  MIME_TYPE_MISMATCH: 'The file type does not match its contents.',
  STORAGE_ERROR: 'The document could not be saved. Please try again.',
  DATABASE_ERROR: 'The document could not be saved. Please try again.',
  UNSUPPORTED_FILE_TYPE: 'This file type is not supported.',
}

function App() {
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadState, setUploadState] = useState('idle')
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadedDocument, setUploadedDocument] = useState(null)
  const [documents, setDocuments] = useState([])

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/health`).catch(() => undefined)
    fetch(`${API_BASE_URL}/api/v1/documents?page=1&page_size=20`)
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error('Unable to load documents'))))
      .then((data) => setDocuments(data.documents))
      .catch(() => setDocuments([]))
  }, [])

  const chooseFile = () => fileInputRef.current?.click()

  const handleFileSelected = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const extension = `.${file.name.split('.').pop()?.toLowerCase()}`
    if (!ACCEPTED_EXTENSIONS.includes(extension) || !ACCEPTED_TYPES.includes(file.type)) {
      setSelectedFile(null)
      setUploadState('error')
      setUploadMessage('Choose a PDF, PNG, JPG, or JPEG document.')
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null)
      setUploadState('error')
      setUploadMessage('The selected document is larger than 20 MB.')
      return
    }
    setSelectedFile(file)
    setUploadedDocument(null)
    setUploadState('ready')
    setUploadMessage('')
  }

  const uploadDocument = async () => {
    if (!selectedFile) return
    setUploadState('uploading')
    setUploadMessage('')
    const formData = new FormData()
    formData.append('file', selectedFile)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents`, { method: 'POST', body: formData })
      const data = await response.json()
      if (!response.ok) {
        const code = data.error?.code
        throw new Error(UPLOAD_ERROR_MESSAGES[code] || 'The document could not be uploaded.')
      }
      setUploadedDocument(data)
      setDocuments((current) => [data, ...current])
      setUploadState('success')
      setUploadMessage('Document uploaded successfully')
    } catch (error) {
      setUploadState('error')
      setUploadMessage(error.message || 'The document could not be uploaded.')
    }
  }

  const formatBytes = (bytes) => `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  const formatDate = (value) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block"><div className="brand-mark">V</div><div><h1>VeriDoc AI</h1><p className="brand-tagline">Intelligent Document Verification &amp; Fraud Detection</p></div></div>
        <nav className="desktop-nav" aria-label="Main navigation"><a className="active" href="#dashboard">Dashboard</a><a href="#verify">Verify Document</a><a href="#documents">Documents</a><a href="#history">Verification History</a><a href="#profile">Profile</a><a href="#settings">Settings</a></nav>
        <button className="avatar-button" type="button" aria-label="Open profile">JD</button>
      </header>
      <main className="main-content" id="dashboard">
        <div className="content-heading"><div><p className="eyebrow">Overview</p><h2>Welcome to VeriDoc AI</h2><p className="description">Verify documents, detect inconsistencies, and identify potential tampering with AI-powered analysis.</p></div><button className="profile-chip" type="button" id="profile"><span className="profile-avatar">JD</span><span>Jordan Davis</span><span className="chevron">⌄</span></button></div>
        <section className="welcome-grid" id="verify">
          <div className="welcome-copy"><span className="spark-icon" aria-hidden="true">✦</span><p className="section-label">Your verification workspace</p><h3>Confidence in every document.</h3><p>Start with a document and let VeriDoc AI help you review what matters.</p><button className="primary-action" type="button" onClick={chooseFile} disabled={uploadState === 'uploading'}><span aria-hidden="true">＋</span> Upload Document</button><input ref={fileInputRef} className="visually-hidden" aria-label="Choose a document to upload" type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileSelected} /><span className="file-note">PDF, JPG, JPEG, or PNG · Up to 20 MB</span>{selectedFile ? <div className="selected-file"><div><strong>{selectedFile.name}</strong><span>{formatBytes(selectedFile.size)}</span></div>{uploadState === 'ready' ? <button type="button" onClick={uploadDocument}>Upload now</button> : null}{uploadState === 'uploading' ? <span className="uploading" role="status">Uploading...</span> : null}{uploadState === 'success' && uploadedDocument ? <div className="success-message" role="status" aria-live="polite"><strong>{uploadMessage}</strong><span>Reference: {uploadedDocument.document_id.slice(0, 8)} · Status: Uploaded</span></div> : null}</div> : null}{uploadState === 'error' ? <p className="upload-error" role="alert" aria-live="assertive">{uploadMessage}</p> : null}</div>
          <div className="document-art" aria-hidden="true"><div className="scan-line" /><div className="document-sheet"><span className="sheet-top" /><span className="sheet-line long" /><span className="sheet-line" /><span className="sheet-line short" /><span className="sheet-seal">✓</span></div><div className="shield">✓</div></div>
        </section>
        <section className="recent-section" id="history"><div className="section-heading"><div><p className="eyebrow">Activity</p><h3>Recent Verifications</h3></div><a href="#documents">View all <span aria-hidden="true">→</span></a></div>{documents.length === 0 ? <div className="empty-state" id="documents"><div className="empty-icon" aria-hidden="true">▤</div><h4>No documents uploaded yet.</h4><p>Your stored documents will appear here once you upload one.</p><button className="secondary-action" type="button" onClick={chooseFile}>Upload your first document</button></div> : <div className="document-list" id="documents">{documents.map((document) => <article className="document-row" key={document.document_id}><div className="document-type" aria-hidden="true">{document.file_extension.replace('.', '').toUpperCase()}</div><div className="document-info"><strong>{document.original_filename}</strong><span>{formatDate(document.created_at)} · {formatBytes(document.file_size)}</span></div><span className="document-status">Uploaded</span></article>)}</div>}</section>
      </main>
      <nav className="mobile-nav" aria-label="Mobile navigation"><a className="active" href="#dashboard"><span aria-hidden="true">⌂</span>Home</a><a href="#verify"><span aria-hidden="true">＋</span>Verify</a><a href="#documents"><span aria-hidden="true">▤</span>Documents</a><a href="#history"><span aria-hidden="true">◷</span>History</a><a href="#profile"><span aria-hidden="true">○</span>Profile</a></nav>
    </div>
  )
}

export default App
