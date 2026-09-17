import React, { useState, useRef } from 'react'

export function DocumentViewer({
  document,
  imageUrl,
  ocrDetections = [],
  imageWidth = 1000,
  imageHeight = 1000,
  activeDetectionId = null,
  onSelectDetection = () => {},
  conflictingFields = [],
}) {
  const [zoom, setZoom] = useState(1.0)
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true)
  const [hoveredBox, setHoveredBox] = useState(null)
  const imageContainerRef = useRef(null)

  const handleZoomIn = () => setZoom((z) => Math.min(2.5, +(z + 0.25).toFixed(2)))
  const handleZoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))
  const handleZoomReset = () => setZoom(1.0)

  // Determine if a detection text contains an entity or conflicting field
  const getBoxStyle = (detection) => {
    const text = detection.text || ''
    const isConflicting =
      (conflictingFields.includes('amount') && (text.includes('$') || /\b\d+\.\d{2}\b/.test(text))) ||
      (conflictingFields.includes('date') && /\b\d{4}[-/.]\d{2}[-/.]\d{2}\b/.test(text)) ||
      (conflictingFields.includes('identifier') && /\b(?:INV|DOC|REF|#)[-A-Za-z0-9]+\b/i.test(text))

    const isEntity =
      /\b\d{4}[-/.]\d{2}[-/.]\d{2}\b/.test(text) ||
      /\$?\b\d+\.\d{2}\b/.test(text) ||
      /\b(?:INV|DOC|REF|#)[-A-Za-z0-9]+\b/i.test(text)

    if (isConflicting) return 'box-conflicting'
    if (isEntity) return 'box-entity'
    return 'box-regular'
  }

  return (
    <div className="layout-column document-viewer-card">
      <div className="column-header">
        <div>
          <span className="column-eyebrow">Left Layout · Input Evidence</span>
          <h3 className="column-title">Actual Uploaded Document</h3>
          <p className="column-subtitle">
            {document?.original_filename || 'Uploaded Document'} · {document?.file_extension?.toUpperCase() || ''}
          </p>
        </div>
        <div className="viewer-toolbar">
          <div className="zoom-controls">
            <button
              type="button"
              className="toolbar-btn"
              onClick={handleZoomOut}
              title="Zoom out"
              aria-label="Zoom out"
            >
              −
            </button>
            <button
              type="button"
              className="toolbar-btn zoom-level"
              onClick={handleZoomReset}
              title="Reset zoom"
            >
              {Math.round(zoom * 100)}%
            </button>
            <button
              type="button"
              className="toolbar-btn"
              onClick={handleZoomIn}
              title="Zoom in"
              aria-label="Zoom in"
            >
              +
            </button>
          </div>
          <button
            type="button"
            className={`toggle-btn ${showBoundingBoxes ? 'active' : ''}`}
            onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
            title="Toggle OCR detection overlays"
          >
            <span className="toggle-icon">⬚</span>
            {showBoundingBoxes ? 'Hide Overlays' : 'Show Overlays'}
          </button>
        </div>
      </div>

      <div className="document-viewport">
        <div
          ref={imageContainerRef}
          className="document-canvas"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
        >
          {imageUrl ? (
            <div className="image-wrapper">
              <img
                src={imageUrl}
                alt="Actual document preview"
                className="document-image"
                onError={(e) => {
                  // Fallback placeholder if image load fails
                  e.target.style.display = 'none'
                }}
              />
              {showBoundingBoxes && ocrDetections.length > 0 && (
                <div className="bounding-box-layer">
                  {ocrDetections.map((item, idx) => {
                    const [x1, y1, x2, y2] = item.bbox || [0, 0, 0, 0]
                    const left = `${(x1 / imageWidth) * 100}%`
                    const top = `${(y1 / imageHeight) * 100}%`
                    const width = `${Math.max(2, ((x2 - x1) / imageWidth) * 100)}%`
                    const height = `${Math.max(2, ((y2 - y1) / imageHeight) * 100)}%`
                    const boxType = getBoxStyle(item)
                    const isActive = activeDetectionId === item.reading_order || activeDetectionId === idx

                    return (
                      <div
                        key={item.reading_order || idx}
                        className={`ocr-bbox ${boxType} ${isActive ? 'bbox-active' : ''}`}
                        style={{ left, top, width, height }}
                        onMouseEnter={() => setHoveredBox(item)}
                        onMouseLeave={() => setHoveredBox(null)}
                        onClick={() => onSelectDetection(item.reading_order || idx, item)}
                        tabIndex={0}
                        role="button"
                        aria-label={`Detected text: ${item.text}`}
                      >
                        <span className="bbox-label">{item.reading_order || idx + 1}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="document-placeholder">
              <span className="placeholder-icon">▤</span>
              <p>Rendering document preview...</p>
            </div>
          )}

          {hoveredBox && (
            <div className="hover-tooltip" role="tooltip">
              <div className="tooltip-header">
                <span className="tooltip-order">#{hoveredBox.reading_order || 1}</span>
                <span className="tooltip-conf">
                  {Math.round((hoveredBox.confidence || 0.95) * 100)}% conf
                </span>
              </div>
              <div className="tooltip-text">{hoveredBox.text}</div>
            </div>
          )}
        </div>
      </div>

      <div className="document-meta-footer">
        <div className="meta-item">
          <span className="meta-label">SHA-256 Hash</span>
          <span className="meta-value mono">{document?.sha256 ? `${document.sha256.slice(0, 16)}...` : 'Pending'}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Dimensions</span>
          <span className="meta-value">{imageWidth} × {imageHeight} px</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Detections</span>
          <span className="meta-value">{ocrDetections.length} regions found</span>
        </div>
      </div>
    </div>
  )
}
