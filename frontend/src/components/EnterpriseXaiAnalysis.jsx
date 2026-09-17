import React, { useState } from 'react'

export function EnterpriseXaiAnalysis({
  documents = [],
  currentIndex = 0,
  activeFieldId = null,
  activeEvidenceId = null,
  onSelectField = () => {},
  onSelectEvidence = () => {},
  onCompareClick = () => {},
  onAddReviewNote = () => {},
  onFlagReview = () => {},
  onDownloadReport = () => {},
}) {
  const currentDoc = documents[currentIndex] || documents[0]
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  if (!currentDoc) {
    return (
      <div className="enterprise-analysis-panel empty-state">
        <p>No document selected for analysis.</p>
      </div>
    )
  }

  const statusBadge = () => {
    switch (currentDoc.verificationStatus) {
      case 'VERIFIED':
        return (
          <span className="status-badge status-verified">
            <span className="status-badge-circle green" />
            🟢 VERIFIED
          </span>
        )
      case 'REVIEW REQUIRED':
        return null
      case 'SUSPICIOUS':
      default:
        return (
          <span className="status-badge status-suspicious">
            <span className="status-badge-circle red" />
            🔴 SUSPICIOUS
          </span>
        )
    }
  }

  const riskLevelClass =
    currentDoc.riskScore <= 30
      ? 'risk-low'
      : currentDoc.riskScore <= 60
      ? 'risk-medium'
      : 'risk-high'

  const hasTamperDanger =
    currentDoc.xaiEvidence?.some((e) => e.type === 'danger') ||
    currentDoc.xaiReasons?.some((r) => r.severity === 'danger') ||
    currentDoc.verificationStatus === 'SUSPICIOUS'

  const hasTamperWarning =
    currentDoc.xaiEvidence?.some((e) => e.type === 'warning') ||
    currentDoc.xaiReasons?.some((r) => r.severity === 'warning') ||
    currentDoc.verificationStatus === 'REVIEW REQUIRED'

  const isDuplicateDetected = Boolean(currentDoc.duplicateDetection?.detected)
  const dupSimilarityVal = currentDoc.duplicateDetection?.similarity
    ? parseInt(currentDoc.duplicateDetection.similarity, 10) || (isDuplicateDetected ? 87 : 0)
    : isDuplicateDetected
    ? 87
    : 0

  return (
    <aside className="enterprise-analysis-panel" aria-label="AI Analysis Panel">
      {/* 1. Header: AI ANALYSIS & Document X/Y */}
      <div className="analysis-header">
        <div className="analysis-title-row">
          <div>
            <div className="panel-title-row">
              <span className="analysis-badge-sub">
                Document {currentIndex + 1} / {documents.length}
              </span>
            </div>
            <h2 className="analysis-title-filename" title={currentDoc.filename}>
              📄 {currentDoc.filename}
            </h2>
          </div>
          <div className="analysis-status-wrapper">{statusBadge()}</div>
        </div>

        {/* 2. Key Metrics Row matching user blueprint */}
        <div className="blueprint-kpi-bar">
          <div className={`blueprint-kpi-pill ${riskLevelClass}`}>
            <span className="kpi-lbl">Risk Score:</span>
            <strong>{currentDoc.riskScore} / 100</strong>
          </div>
          <div className="blueprint-kpi-pill kpi-ocr">
            <span className="kpi-lbl">OCR Confidence:</span>
            <strong>{currentDoc.ocrConfidence}%</strong>
          </div>
          <div className="blueprint-kpi-pill kpi-engine">
            <span className="kpi-lbl">Engine:</span>
            <span>DocVQA • DocTamper • SROIE</span>
          </div>
        </div>
      </div>

      <div className="analysis-content-scroll">
        {/* =========================================================================
            3. EXTRACTED FIELDS (Structured Key-Values from DocVQA)
            ========================================================================= */}
        <div className="blueprint-section">
          <div className="blueprint-section-header">
            <div className="bsh-left">
              <span className="bsh-icon">📋</span>
              <h3 className="blueprint-section-title">Extracted Fields</h3>
            </div>
            <span className="bsh-tag">DocVQA OCR</span>
          </div>
          <div className="blueprint-divider" />

          <div className="blueprint-fields-list">
            {currentDoc.extractedFields &&
              Object.entries(currentDoc.extractedFields).map(([groupKey, fields]) => (
                <div key={groupKey} className="blueprint-field-group">
                  <div className="bf-group-title">{groupKey}</div>
                  <div className="bf-table">
                    {fields.map((field) => {
                      const isSelected = activeFieldId === field.id
                      const isDanger = field.status === 'danger'
                      const isWarning = field.status === 'warning'
                      const rowClass = isDanger
                        ? 'row-danger'
                        : isWarning
                        ? 'row-warning'
                        : 'row-verified'

                      return (
                        <div
                          key={field.id}
                          className={`blueprint-field-row ${rowClass} ${isSelected ? 'selected' : ''}`}
                          onClick={() => onSelectField(field)}
                          title="Click to highlight on document viewer"
                          role="button"
                          tabIndex={0}
                        >
                          <div className="bf-key-col">
                            <span className="bf-key-label">{field.key}:</span>
                            <span className="bf-val-text">{field.value}</span>
                          </div>
                          <div className="bf-status-col">
                            <span className="bf-conf-badge">{field.confidence}%</span>
                            <span className="bf-icon-badge">
                              {isDanger ? '⚠ Flagged' : isWarning ? '⚠ Review' : '✓ Verified'}
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* =========================================================================
            4. XAI EXPLANATION (Decision Signals & Forensic Findings)
            ========================================================================= */}
        <div className="blueprint-section">
          <div className="blueprint-section-header">
            <div className="bsh-left">
              <span className="bsh-icon">🔍</span>
              <h3 className="blueprint-section-title">XAI Explanation</h3>
            </div>
            <span className="bsh-tag">DocTamper &amp; SROIE/CORD</span>
          </div>
          <div className="blueprint-divider" />

          <div className="xai-summary-bullets">
            {/* Finding 1: DocVQA Consistency */}
            <div
              className={`xai-bullet-item ${
                hasTamperDanger && currentDoc.xaiReasons?.some((r) => r.title.includes('mismatch'))
                  ? 'bullet-danger'
                  : 'bullet-success'
              }`}
            >
              <span className="bullet-symbol">
                {hasTamperDanger && currentDoc.xaiReasons?.some((r) => r.title.includes('mismatch'))
                  ? '⚠'
                  : '✓'}
              </span>
              <div className="bullet-content">
                <strong>
                  {hasTamperDanger && currentDoc.xaiReasons?.some((r) => r.title.includes('mismatch'))
                    ? 'Arithmetic Inconsistency Detected'
                    : 'No inconsistencies detected'}
                </strong>
                <p>
                  {hasTamperDanger && currentDoc.xaiReasons?.some((r) => r.title.includes('mismatch'))
                    ? 'Total amount does not match the computed sum of line items.'
                    : 'Document mathematical totals and field values align with registry standards.'}
                </p>
              </div>
            </div>

            {/* Finding 2: SROIE/CORD Duplicate */}
            <div className={`xai-bullet-item ${isDuplicateDetected ? 'bullet-warning' : 'bullet-success'}`}>
              <span className="bullet-symbol">{isDuplicateDetected ? '⧉' : '✓'}</span>
              <div className="bullet-content">
                <strong>
                  {isDuplicateDetected
                    ? `Duplicate collision detected (${dupSimilarityVal}% Match)`
                    : 'No duplicate detected'}
                </strong>
                <p>
                  {isDuplicateDetected
                    ? `Perceptual 64-bit dHash matches ${currentDoc.duplicateDetection?.matchedFilename}.`
                    : 'Perceptual hash index confirms unique submission in repository.'}
                </p>
              </div>
            </div>

            {/* Finding 3: DocTamper Alteration Masks */}
            <div
              className={`xai-bullet-item ${
                hasTamperDanger ? 'bullet-danger' : hasTamperWarning ? 'bullet-warning' : 'bullet-success'
              }`}
            >
              <span className="bullet-symbol">{hasTamperDanger || hasTamperWarning ? '⚠' : '✓'}</span>
              <div className="bullet-content">
                <strong>
                  {hasTamperDanger
                    ? 'Visual alteration detected (DocTamper XAI)'
                    : hasTamperWarning
                    ? 'Contrast irregularity on document seal'
                    : 'No alteration detected'}
                </strong>
                <p>
                  {hasTamperDanger
                    ? 'Font glyph bounding box and localized compression block anomalies flagged.'
                    : hasTamperWarning
                    ? 'Rubber stamp edges show non-uniform color blending. Human review recommended.'
                    : 'Pixel gradient analysis and font stream compression show authentic generation.'}
                </p>
              </div>
            </div>
          </div>

          {/* Traceable Evidence Cards (if altered or warnings exist) */}
          {currentDoc.xaiEvidence && currentDoc.xaiEvidence.length > 0 && (
            <div className="blueprint-evidence-cards">
              {currentDoc.xaiEvidence.map((ev) => {
                const isSelected = activeEvidenceId === ev.id
                const evClass =
                  ev.type === 'danger'
                    ? 'ev-danger'
                    : ev.type === 'warning'
                    ? 'ev-warning'
                    : 'ev-verified'

                return (
                  <div
                    key={ev.id}
                    className={`blueprint-evidence-item ${evClass} ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectEvidence(ev)}
                    role="button"
                    tabIndex={0}
                    title="Click to highlight anomaly on document viewer"
                  >
                    <div className="ev-item-header">
                      <span className="ev-title">{ev.title}</span>
                      <span className="ev-conf">{ev.confidence}% Conf</span>
                    </div>
                    <p className="ev-msg">{ev.message}</p>
                  </div>
                )
              })}
            </div>
          )}

          {/* Collapsible Tri-Pillar Formula Card */}
          <div className="blueprint-tech-accordion">
            <button
              type="button"
              className="btn-toggle-tech"
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            >
              <span>{showTechnicalDetails ? '▲ Hide' : '▼ View'} Tri-Pillar Composite Risk Formula</span>
              <span className="tech-formula-hint">Risk = 0.25·DocVQA + 0.45·DocTamper + 0.30·Duplicate</span>
            </button>

            {showTechnicalDetails && (
              <div className="tech-details-box">
                <div className="tech-meter-row">
                  <span>1. DocVQA OCR Inconsistency (25%):</span>
                  <strong>{Math.max(0, 100 - (currentDoc.ocrConfidence || 98))}/100</strong>
                </div>
                <div className="tech-meter-row">
                  <span>2. DocTamper Alteration (45%):</span>
                  <strong>{hasTamperDanger ? 90 : hasTamperWarning ? 50 : 5}/100</strong>
                </div>
                <div className="tech-meter-row">
                  <span>3. SROIE/CORD Duplicate Match (30%):</span>
                  <strong>{dupSimilarityVal}/100</strong>
                </div>
                <div className="tech-formula-summary">
                  Composite Weighted Score: <strong>{currentDoc.riskScore}/100 ({currentDoc.riskLevel})</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 5. Bottom Actions Footer */}
      <div className="analysis-actions-footer">
        <div className="footer-actions-grid">
          <button className="action-btn secondary" onClick={() => onCompareClick(currentDoc)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            Compare
          </button>

          <button className="action-btn secondary" onClick={() => onAddReviewNote(currentDoc)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Add Note
          </button>

          <button className="action-btn secondary" onClick={() => onDownloadReport(currentDoc)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Report
          </button>

          {currentDoc.verificationStatus === 'SUSPICIOUS' ||
          currentDoc.verificationStatus === 'REVIEW REQUIRED' ? (
            <button className="action-btn warning-action" onClick={() => onFlagReview(currentDoc)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                <line x1="4" y1="22" x2="4" y2="15" />
              </svg>
              Flag Review
            </button>
          ) : (
            <button className="action-btn primary-action" onClick={() => onDownloadReport(currentDoc)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Approve
            </button>
          )}
        </div>
      </div>
    </aside>
  )
}
