import React, { useState, useEffect, useRef } from 'react'
import { renderDocumentToCanvas } from '../utils/documentRenderer'

export function EnterpriseDocumentViewer({
  documents = [],
  currentIndex = 0,
  onSelectIndex = () => {},
  activeFieldId = null,
  activeEvidenceId = null,
  onSelectField = () => {},
  onAddClick = () => {},
  onUploadFiles = () => {},
}) {
  const currentDoc = documents[currentIndex] || documents[0]
  const [zoom, setZoom] = useState(1.0)
  const [showOverlays, setShowOverlays] = useState(true)
  const [hoveredBox, setHoveredBox] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStartX, setDragStartX] = useState(0)
  const [dragOverViewer, setDragOverViewer] = useState(false)

  const canvasRef = useRef(null)

  // Render document canvas when active document changes
  useEffect(() => {
    if (canvasRef.current && currentDoc) {
      renderDocumentToCanvas(currentDoc, canvasRef.current)
    }
  }, [currentDoc])

  // Keyboard arrow navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        onSelectIndex(Math.max(0, currentIndex - 1))
      } else if (e.key === 'ArrowRight') {
        onSelectIndex(Math.min(documents.length - 1, currentIndex + 1))
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, documents.length, onSelectIndex])

  // Swipe / Drag handling
  const handleMouseDown = (e) => {
    setIsDragging(true)
    setDragStartX(e.clientX)
  }

  const handleMouseUp = (e) => {
    if (!isDragging) return
    setIsDragging(false)
    const diff = e.clientX - dragStartX
    if (diff > 80 && currentIndex > 0) {
      onSelectIndex(currentIndex - 1)
    } else if (diff < -80 && currentIndex < documents.length - 1) {
      onSelectIndex(currentIndex + 1)
    }
  }

  const handleTouchStart = (e) => {
    setDragStartX(e.touches[0].clientX)
  }

  const handleTouchEnd = (e) => {
    const diff = e.changedTouches[0].clientX - dragStartX
    if (diff > 60 && currentIndex > 0) {
      onSelectIndex(currentIndex - 1)
    } else if (diff < -60 && currentIndex < documents.length - 1) {
      onSelectIndex(currentIndex + 1)
    }
  }

  const [overlayFilter, setOverlayFilter] = useState('all') // 'all', 'docvqa', 'doctamper'

  const handleZoomIn = () => setZoom((z) => Math.min(2.0, +(z + 0.15).toFixed(2)))
  const handleZoomOut = () => setZoom((z) => Math.max(0.6, +(z - 0.15).toFixed(2)))
  const handleZoomFit = () => setZoom(1.0)

  // Collect all visual bounding boxes from fields (DocVQA) & XAI evidence (DocTamper)
  const allBoxes = []
  if (currentDoc?.extractedFields) {
    Object.entries(currentDoc.extractedFields).forEach(([groupKey, fields]) => {
      fields.forEach((f) => {
        allBoxes.push({
          ...f,
          engine: 'DocVQA',
          group: groupKey,
          boxType: f.status === 'danger' ? 'red' : f.status === 'warning' ? 'yellow' : 'blue',
        })
      })
    })
  }

  if (currentDoc?.xaiEvidence) {
    currentDoc.xaiEvidence.forEach((ev) => {
      allBoxes.push({
        id: ev.id,
        key: ev.title,
        value: ev.message,
        confidence: ev.confidence,
        status: ev.type,
        bbox: ev.bbox,
        engine: 'DocTamper',
        isEvidence: true,
        boxType: ev.type === 'danger' ? 'red' : ev.type === 'warning' ? 'yellow' : 'green',
      })
    })
  }

  const displayedBoxes = allBoxes.filter((b) => {
    if (overlayFilter === 'docvqa') return b.engine === 'DocVQA'
    if (overlayFilter === 'doctamper') return b.engine === 'DocTamper'
    return true
  })

  const imageWidth = currentDoc?.imageWidth || 800
  const imageHeight = currentDoc?.imageHeight || 1050

  return (
    <div className="enterprise-viewer-panel">
      {/* Viewer Header matching user blueprint */}
      <div className="viewer-top-meta">
        <div className="doc-identity">
          <div className="panel-title-row">
            <span className="panel-super-label">DOCUMENTS</span>
            <span className="doc-type-pill">{currentDoc?.documentType || 'Enterprise Document'}</span>
          </div>
        </div>

        <div className="doc-top-info-tag">
          <h3 className="doc-active-filename" title={currentDoc?.filename}>
            📄 {currentDoc?.filename}
          </h3>
        </div>
      </div>

      {/* Dark Document Viewer Toolbar (Inspired by InvoiceOps reference) */}
      <div className="dark-viewer-toolbar">
        <div className="toolbar-left-group">
          <button
            type="button"
            className="dark-tool-btn"
            disabled={currentIndex === 0}
            onClick={() => onSelectIndex(currentIndex - 1)}
            title="Previous Document"
          >
            ←
          </button>
          <span className="dark-page-count">Document {currentIndex + 1} / {documents.length}</span>
          <button
            type="button"
            className="dark-tool-btn"
            disabled={currentIndex === documents.length - 1}
            onClick={() => onSelectIndex(currentIndex + 1)}
            title="Next Document"
          >
            →
          </button>
          <span className="toolbar-divider" />
          <button
            type="button"
            className={`dark-overlay-toggle ${showOverlays ? 'active' : ''}`}
            onClick={() => setShowOverlays(!showOverlays)}
            title="Toggle XAI Bounding Boxes"
          >
            <span className="toggle-dot" />
            {showOverlays ? 'Overlays On' : 'Hidden'}
          </button>
          {showOverlays && (
            <div className="dark-filter-pills-group">
              <button
                type="button"
                className={`dark-filter-pill ${overlayFilter === 'all' ? 'pill-active' : ''}`}
                onClick={() => setOverlayFilter('all')}
                title="Show all overlays"
              >
                All
              </button>
              <button
                type="button"
                className={`dark-filter-pill ${overlayFilter === 'docvqa' ? 'pill-active' : ''}`}
                onClick={() => setOverlayFilter('docvqa')}
                title="Show DocVQA structured fields only"
              >
                DocVQA
              </button>
              <button
                type="button"
                className={`dark-filter-pill ${overlayFilter === 'doctamper' ? 'pill-active' : ''}`}
                onClick={() => setOverlayFilter('doctamper')}
                title="Show DocTamper XAI anomaly masks only"
              >
                DocTamper
              </button>
            </div>
          )}
        </div>

        <div className="toolbar-center-group">
          <button type="button" className="dark-tool-btn" onClick={handleZoomOut} title="Zoom Out">−</button>
          <span className="dark-zoom-val">{Math.round(zoom * 100)}%</span>
          <button type="button" className="dark-tool-btn" onClick={handleZoomIn} title="Zoom In">+</button>
          <button type="button" className="dark-tool-btn" onClick={handleZoomFit} title="Fit to Screen">⤢</button>
        </div>

        <div className="toolbar-right-group">
          <span className="file-format-tag">{currentDoc?.fileType}</span>
          <button
            type="button"
            className="dark-tool-btn"
            title="Download Document"
            onClick={() => alert(`Downloading ${currentDoc?.filename}`)}
          >
            ↓
          </button>
        </div>
      </div>

      {/* Document Viewport with Dynamic Overlays */}
      <div
        className={`document-main-viewport ${dragOverViewer ? 'viewer-drag-active' : ''}`}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOverViewer(true)
        }}
        onDragLeave={() => setDragOverViewer(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOverViewer(false)
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onUploadFiles(e.dataTransfer.files)
          }
        }}
      >
        {dragOverViewer && (
          <div className="viewer-drop-overlay">
            <div className="drop-overlay-card">
              <span className="drop-overlay-icon">📁</span>
              <h4>Drop file to verify</h4>
              <p>Supports PDF, PNG, JPG, JPEG</p>
            </div>
          </div>
        )}
        <div
          className="document-zoom-wrap"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
        >
          <div className="canvas-shadow-card">
            <canvas ref={canvasRef} className="document-canvas-element" />

            {showOverlays && (
              <div className="xai-bbox-layer">
                {displayedBoxes.map((box, idx) => {
                  const [x1, y1, x2, y2] = box.bbox || [0, 0, 0, 0]
                  const left = `${(x1 / imageWidth) * 100}%`
                  const top = `${(y1 / imageHeight) * 100}%`
                  const width = `${Math.max(2, ((x2 - x1) / imageWidth) * 100)}%`
                  const height = `${Math.max(2, ((y2 - y1) / imageHeight) * 100)}%`

                  const isActive = activeFieldId === box.id || activeEvidenceId === box.id

                  return (
                    <div
                      key={box.id || idx}
                      className={`enterprise-bbox box-${box.boxType} ${isActive ? 'bbox-highlight-active' : ''}`}
                      style={{ left, top, width, height }}
                      onMouseEnter={() => setHoveredBox(box)}
                      onMouseLeave={() => setHoveredBox(null)}
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectField(box.id)
                      }}
                      tabIndex={0}
                      role="button"
                      aria-label={`${box.key}: ${box.value}`}
                    >
                      {isActive && <span className="active-pulse-ring" />}
                      <span className="bbox-mini-pill">{box.confidence}%</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {hoveredBox && (
            <div className="floating-xai-tooltip" role="tooltip">
              <div className="tooltip-tag-row">
                <span className="tooltip-engine-badge">
                  {hoveredBox.engine === 'DocTamper' ? 'DocTamper • Mask' : 'DocVQA • Entity'}
                </span>
                <span className={`status-pill pill-${hoveredBox.boxType}`}>
                  {hoveredBox.status?.toUpperCase() || 'EXTRACTED'}
                </span>
                <span className="tooltip-confidence">{hoveredBox.confidence}% Conf</span>
              </div>
              <strong className="tooltip-key">{hoveredBox.key}</strong>
              <div className="tooltip-val">{hoveredBox.value}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
