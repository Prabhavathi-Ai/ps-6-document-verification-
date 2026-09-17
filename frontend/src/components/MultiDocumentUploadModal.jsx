import React, { useState, useRef } from 'react'

export function MultiDocumentUploadModal({
  isOpen,
  onClose,
  documents = [],
  onAddDocuments = () => {},
  onStartVerification = () => {},
  isVerifyingAll = false,
}) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedQueue, setSelectedQueue] = useState([])
  const [processingProgress, setProcessingProgress] = useState({})
  const [batchActive, setBatchActive] = useState(false)

  const fileInputRef = useRef(null)
  const folderInputRef = useRef(null)

  if (!isOpen) return null

  const handleFiles = (filesList) => {
    const files = Array.from(filesList)
    if (!files.length) return

    const newDocs = files.map((file, idx) => {
      const ext = file.name.split('.').pop().toUpperCase()
      const sizeKB = Math.round(file.size / 1024) + ' KB'
      return {
        id: 'upload-' + Date.now() + '-' + idx,
        filename: file.name,
        originalName: file.name,
        fileType: ext || 'PDF',
        fileSize: sizeKB,
        fileBlob: file,
        uploadStatus: 'Uploaded',
        verificationStatus: 'Pending',
        progress: 100,
        riskScore: Math.floor(Math.random() * 25) + 5,
        riskLevel: 'Low Risk',
        ocrConfidence: 96,
        documentType: ext === 'PDF' ? 'Official Document' : 'Document Image',
        extractedFields: {
          DOCUMENT: [
            { key: 'Filename', value: file.name, confidence: 99, status: 'verified', id: 'f-u1' },
            { key: 'Format', value: ext, confidence: 100, status: 'verified', id: 'f-u2' },
            { key: 'File Size', value: sizeKB, confidence: 100, status: 'verified', id: 'f-u3' },
          ],
        },
        xaiReasons: [
          {
            severity: 'success',
            title: 'File structure valid',
            explanation: 'Clean digital formatting detected with zero binary tampering.',
            confidence: '98%',
            evidenceSource: 'File Header Parser',
            impact: '-10',
          },
        ],
        consistencyChecks: [
          { label: 'File integrity checksum matches', status: 'pass' },
          { label: 'Standard format compliant', status: 'pass' },
        ],
        duplicateDetection: {
          detected: false,
          similarity: '0%',
          matchedFilename: 'None (Unique Submission)',
          reasons: ['No matching duplicate entries in verification ledger.'],
        },
        documentIntegrity: [
          { name: 'OCR consistency', status: 'pass', note: 'File is ready for full extraction' },
          { name: 'Image manipulation signals', status: 'pass', note: 'No anomaly' },
        ],
      }
    })

    setSelectedQueue((prev) => [...prev, ...newDocs])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const runBatchProcessing = () => {
    if (!selectedQueue.length) return
    setBatchActive(true)

    // Simulate asynchronous batch processing document by document
    selectedQueue.forEach((doc, index) => {
      // Step 1: Processing
      setTimeout(() => {
        setSelectedQueue((current) =>
          current.map((item) =>
            item.id === doc.id
              ? { ...item, uploadStatus: 'Processing', verificationStatus: 'Processing', progress: 45 }
              : item
          )
        )
      }, index * 800)

      // Step 2: Completed
      setTimeout(() => {
        const finalStatus =
          doc.filename.toLowerCase().includes('altered') || doc.filename.toLowerCase().includes('suspicious')
            ? 'SUSPICIOUS'
            : doc.filename.toLowerCase().includes('review')
            ? 'REVIEW REQUIRED'
            : 'VERIFIED'

        setSelectedQueue((current) =>
          current.map((item) =>
            item.id === doc.id
              ? {
                  ...item,
                  uploadStatus: finalStatus === 'VERIFIED' ? 'Verified' : finalStatus,
                  verificationStatus: finalStatus,
                  progress: 100,
                }
              : item
          )
        )

        // If this is the last document, notify parent
        if (index === selectedQueue.length - 1) {
          setTimeout(() => {
            setBatchActive(false)
            onAddDocuments(selectedQueue)
            onClose()
          }, 600)
        }
      }, index * 800 + 1200)
    })
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="upload-modal-window" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Upload Multiple Documents</h3>
            <p className="modal-subtitle">
              Drag and drop files here or select multiple documents for automated AI batch verification.
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Dropzone Area */}
        <div
          className={`modal-dropzone ${dragOver ? 'drag-active' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="dropzone-icon-circle">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h4 className="dropzone-heading">Drag and drop files here or select multiple documents</h4>
          <p className="dropzone-formats">Supported formats: PDF, JPG, JPEG, PNG • Maximum 50 MB per file</p>

          <div className="dropzone-actions">
            <button
              className="btn-select-docs"
              onClick={() => fileInputRef.current?.click()}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
              Select Documents
            </button>

            <button
              className="btn-upload-folder"
              onClick={() => folderInputRef.current?.click()}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
              Upload Folder
            </button>

            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(e.target.files)}
            />
            <input
              type="file"
              ref={folderInputRef}
              // @ts-ignore
              webkitdirectory="true"
              directory="true"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        </div>

        {/* Horizontal Document Queue with Thumbnails */}
        {selectedQueue.length > 0 && (
          <div className="upload-queue-section">
            <div className="queue-header">
              <span className="queue-title">Selected Document Queue ({selectedQueue.length})</span>
              <button
                className="btn-clear-queue"
                onClick={() => setSelectedQueue([])}
                disabled={batchActive}
              >
                Clear Queue
              </button>
            </div>

            <div className="queue-cards-row">
              {selectedQueue.map((doc, idx) => {
                const isSuspicious = doc.verificationStatus === 'SUSPICIOUS'
                const isReview = doc.verificationStatus === 'REVIEW REQUIRED'
                const isVerified = doc.verificationStatus === 'VERIFIED'
                const isProcessing = doc.verificationStatus === 'Processing'

                return (
                  <div key={doc.id} className="queue-doc-card">
                    <div className="queue-thumb-preview">
                      <div className="queue-thumb-badge">{doc.fileType}</div>
                      <div className="queue-thumb-sheet">
                        <div className="sheet-line line-1" />
                        <div className="sheet-line line-2" />
                        <div className="sheet-line line-3" />
                      </div>
                      {isProcessing && (
                        <div className="thumb-processing-overlay">
                          <span className="spinner-mini" />
                        </div>
                      )}
                    </div>

                    <div className="queue-doc-info">
                      <div className="queue-doc-name" title={doc.filename}>
                        {doc.filename}
                      </div>
                      <div className="queue-doc-meta">
                        <span>{doc.fileSize}</span>
                        <span className="dot-sep">•</span>
                        <span>{doc.fileType}</span>
                      </div>

                      {/* Progress bar */}
                      <div className="queue-progress-bar">
                        <div
                          className={`queue-progress-fill ${isProcessing ? 'anim-stripes' : ''}`}
                          style={{ width: `${doc.progress}%` }}
                        />
                      </div>

                      {/* Status Tag */}
                      <div className="queue-status-tag-row">
                        <span
                          className={`queue-status-pill ${
                            isVerified
                              ? 'pill-verified'
                              : isReview
                              ? 'pill-review'
                              : isSuspicious
                              ? 'pill-suspicious'
                              : isProcessing
                              ? 'pill-processing'
                              : 'pill-uploaded'
                          }`}
                        >
                          {doc.uploadStatus}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="modal-footer">
          <div className="footer-left-info">
            {selectedQueue.length > 0 ? (
              <span>{selectedQueue.length} documents ready to batch verify</span>
            ) : (
              <span>Select documents to populate batch queue</span>
            )}
          </div>
          <div className="footer-right-actions">
            <button className="btn-cancel" onClick={onClose} disabled={batchActive}>
              Cancel
            </button>
            <button
              className="btn-verify-batch"
              disabled={!selectedQueue.length || batchActive}
              onClick={runBatchProcessing}
            >
              {batchActive ? (
                <>
                  <span className="spinner-mini" />
                  Verifying Batch Automatically...
                </>
              ) : (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Verify All Automatically ({selectedQueue.length})
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
