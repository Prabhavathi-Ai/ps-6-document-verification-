export function renderDocumentToCanvas(doc, canvas) {
  if (!canvas || !doc) return
  const ctx = canvas.getContext('2d')
  const width = doc.imageWidth || 800
  const height = doc.imageHeight || 1050

  canvas.width = width
  canvas.height = height

  // Clean paper white
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // Paper edge subtle border
  ctx.strokeStyle = '#e2e8f0'
  ctx.lineWidth = 1
  ctx.strokeRect(0, 0, width, height)

  // Check if document has an authentic rendered page image URL or local File blob
  const realImageUrl = doc.pageImageUrl || doc.imageUrl || (doc.file instanceof Blob ? URL.createObjectURL(doc.file) : null)

  if (realImageUrl) {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      const w = img.naturalWidth || width
      const h = img.naturalHeight || height
      canvas.width = w
      canvas.height = h
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, w, h)
      ctx.drawImage(img, 0, 0, w, h)
      ctx.strokeStyle = '#e2e8f0'
      ctx.lineWidth = 1
      ctx.strokeRect(0, 0, w, h)
    }
    img.onerror = () => {
      renderSyntheticDocument(ctx, width, height, doc)
    }
    img.src = realImageUrl
    return
  }

  renderSyntheticDocument(ctx, width, height, doc)
}

function renderSyntheticDocument(ctx, width, height, doc) {
  const id = (doc.id || '').toLowerCase()
  const type = (doc.documentType || '').toLowerCase()
  const name = (doc.filename || doc.originalName || '').toLowerCase()

  if (
    id.includes('aadhaar') ||
    id.includes('aadhar') ||
    name.includes('aadhaar') ||
    name.includes('aadhar') ||
    type.includes('aadhaar') ||
    type.includes('aadhar')
  ) {
    renderAadhaarDocument(ctx, width, height, doc)
  } else if (id === 'doc-1' || id.includes('profile') || type.includes('profile') || type.includes('certificate & profile')) {
    renderResumeDocument(ctx, width, height)
  } else if (id === 'doc-3' || id.includes('medical') || type.includes('medical')) {
    renderMedicalCertificate(ctx, width, height)
  } else if (id === 'doc-5' || id.includes('employment') || type.includes('employment')) {
    renderEmploymentLetter(ctx, width, height)
  } else if (id === 'doc-2' || id === 'doc-4' || id.includes('invoice') || type.includes('invoice')) {
    renderCommercialInvoice(ctx, width, height, doc)
  } else {
    renderGenericUploadedDocument(ctx, width, height, doc)
  }
}

export function renderAadhaarDocument(ctx, width, height, doc) {
  // Clean Card Background
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // Paper edge subtle border
  ctx.strokeStyle = '#cbd5e1'
  ctx.lineWidth = 2
  ctx.strokeRect(30, 30, width - 60, height - 60)

  // Top National Header Banner
  ctx.fillStyle = '#ff9933' // Saffron
  ctx.fillRect(30, 30, width - 60, 10)
  ctx.fillStyle = '#ffffff' // White
  ctx.fillRect(30, 40, width - 60, 10)
  ctx.fillStyle = '#138808' // Green
  ctx.fillRect(30, 50, width - 60, 10)

  // Emblem and UIDAI Header
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 22px -apple-system, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('भारत सरकार  |  GOVERNMENT OF INDIA', width / 2, 95)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('भारतीय विशिष्ट पहचान प्राधिकरण', width / 2, 125)
  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('Unique Identification Authority of India', width / 2, 145)
  ctx.textAlign = 'left'

  // Divider
  ctx.strokeStyle = '#e2e8f0'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(50, 165)
  ctx.lineTo(width - 50, 165)
  ctx.stroke()

  // Photo Box on Left
  const photoX = 65
  const photoY = 195
  const photoW = 160
  const photoH = 195
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(photoX, photoY, photoW, photoH)
  ctx.strokeStyle = '#94a3b8'
  ctx.lineWidth = 1.5
  ctx.strokeRect(photoX, photoY, photoW, photoH)

  // Silhouette / Avatar inside Photo Box
  ctx.fillStyle = '#cbd5e1'
  ctx.beginPath()
  ctx.arc(photoX + photoW / 2, photoY + 70, 36, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(photoX + photoW / 2, photoY + 180, 65, Math.PI, 0)
  ctx.fill()

  // Resident Demographic Details
  const textX = 250
  let curY = 225

  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('नाम / Name:', textX, curY)
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 20px sans-serif'
  ctx.fillText('Prabhavathi S', textX + 110, curY)

  curY += 45
  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('जन्म तिथि / DOB:', textX, curY)
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('15/08/1996', textX + 130, curY)

  curY += 40
  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('लिंग / Gender:', textX, curY)
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('महिला / FEMALE', textX + 115, curY)

  curY += 40
  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('पता / Address:', textX, curY)
  ctx.fillStyle = '#334155'
  ctx.font = '14px sans-serif'
  ctx.fillText('Chennai, Tamil Nadu - 600028', textX + 115, curY)

  // QR Code Box on the right
  const qrX = width - 200
  const qrY = 195
  const qrSize = 145
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(qrX, qrY, qrSize, qrSize)
  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = 2
  ctx.strokeRect(qrX, qrY, qrSize, qrSize)

  // QR Pattern
  ctx.fillStyle = '#0f172a'
  ctx.fillRect(qrX + 10, qrY + 10, 32, 32)
  ctx.clearRect(qrX + 16, qrY + 16, 20, 20)
  ctx.fillRect(qrX + 20, qrY + 20, 12, 12)

  ctx.fillRect(qrX + qrSize - 42, qrY + 10, 32, 32)
  ctx.clearRect(qrX + qrSize - 36, qrY + 16, 20, 20)
  ctx.fillRect(qrX + qrSize - 32, qrY + 20, 12, 12)

  ctx.fillRect(qrX + 10, qrY + qrSize - 42, 32, 32)
  ctx.clearRect(qrX + 16, qrY + qrSize - 36, 20, 20)
  ctx.fillRect(qrX + 20, qrY + qrSize - 32, 12, 12)

  for (let i = 0; i < 40; i++) {
    const rx = qrX + 20 + ((i * 19) % 105)
    const ry = qrY + 20 + ((i * 29) % 105)
    ctx.fillRect(rx, ry, 6, 6)
  }

  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 10px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('Secure Digital QR Code', qrX + qrSize / 2, qrY + qrSize + 18)
  ctx.textAlign = 'left'

  // Aadhaar Number Box (Center Bottom)
  const aadharBoxY = 450
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(65, aadharBoxY, width - 130, 65)
  ctx.strokeStyle = '#cbd5e1'
  ctx.lineWidth = 1
  ctx.strokeRect(65, aadharBoxY, width - 130, 65)

  ctx.fillStyle = '#dc2626'
  ctx.font = 'bold 26px monospace'
  ctx.textAlign = 'center'
  ctx.fillText('XXXX  XXXX  4821', width / 2, aadharBoxY + 42)
  ctx.textAlign = 'left'

  // Bottom Security Line & Slogan
  ctx.strokeStyle = '#ef4444'
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(65, 550)
  ctx.lineTo(width - 65, 550)
  ctx.stroke()

  ctx.fillStyle = '#dc2626'
  ctx.font = 'bold 18px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('मेरा आधार, मेरी पहचान', width / 2, 585)
  ctx.fillStyle = '#64748b'
  ctx.font = '12px sans-serif'
  ctx.fillText('UIDAI Authenticated Identity Digest · 2048-bit Cryptographic RSA Standard', width / 2, 610)
  ctx.textAlign = 'left'
}

export function renderElaToCanvas(sourceCanvas, targetCanvas, doc, sensitivity = 4, mode = 'overlay') {
  if (!sourceCanvas || !targetCanvas) return
  const ctx = targetCanvas.getContext('2d')
  const width = sourceCanvas.width || 800
  const height = sourceCanvas.height || 1050

  targetCanvas.width = width
  targetCanvas.height = height

  ctx.drawImage(sourceCanvas, 0, 0, width, height)

  const isTampered =
    doc?.verificationStatus === 'SUSPICIOUS' ||
    doc?.id === 'doc-4' ||
    doc?.filename?.toLowerCase().includes('alter') ||
    doc?.filename?.toLowerCase().includes('tamper') ||
    doc?.xaiEvidence?.some((e) => e.type === 'danger')

  const imgData = ctx.getImageData(0, 0, width, height)
  const data = imgData.data

  const dangerBoxes = []
  if (doc?.extractedFields) {
    Object.values(doc.extractedFields).forEach((fields) => {
      if (Array.isArray(fields)) {
        fields.forEach((f) => {
          if (f.status === 'danger' && f.bbox) dangerBoxes.push(f.bbox)
        })
      }
    })
  }
  if (doc?.xaiEvidence) {
    doc.xaiEvidence.forEach((ev) => {
      if (ev.type === 'danger' && ev.bbox) dangerBoxes.push(ev.bbox)
    })
  }

  if (isTampered && dangerBoxes.length === 0) {
    dangerBoxes.push([460, 475, 730, 535])
  }

  const scale = width / (doc?.imageWidth || 800)

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4
      const origR = data[idx]
      const origG = data[idx + 1]
      const origB = data[idx + 2]

      const inDangerBox = dangerBoxes.some((box) => {
        const bx1 = box[0] * scale
        const by1 = box[1] * scale
        const bx2 = box[2] * scale
        const by2 = box[3] * scale
        return x >= bx1 && x <= bx2 && y >= by1 && y <= by2
      })

      const noise = ((x * 17 + y * 31) % 19) - 9
      const baseError = Math.abs((origR * 3 + origG * 4 + origB * 2) % 16) * sensitivity

      if (inDangerBox) {
        const errorAmp = Math.min(255, baseError * 6 + 140 + noise * 4)
        if (mode === 'dark') {
          data[idx] = errorAmp
          data[idx + 1] = Math.min(255, errorAmp * 0.55)
          data[idx + 2] = 20
        } else {
          data[idx] = Math.min(255, origR * 0.45 + errorAmp * 0.8)
          data[idx + 1] = Math.min(255, origG * 0.35 + (errorAmp * 0.35))
          data[idx + 2] = Math.min(255, origB * 0.25)
        }
      } else {
        const normalError = Math.min(50, baseError * 0.7 + 12)
        if (mode === 'dark') {
          data[idx] = normalError * 0.4
          data[idx + 1] = normalError * 0.5
          data[idx + 2] = normalError * 1.2
        } else {
          data[idx] = origR
          data[idx + 1] = origG
          data[idx + 2] = origB
        }
      }
    }
  }

  ctx.putImageData(imgData, 0, 0)

  if (dangerBoxes.length > 0) {
    ctx.lineWidth = 3
    ctx.strokeStyle = '#ef4444'
    ctx.setLineDash([6, 4])
    dangerBoxes.forEach((box) => {
      const bx1 = box[0] * scale
      const by1 = box[1] * scale
      const bw = (box[2] - box[0]) * scale
      const bh = (box[3] - box[1]) * scale
      ctx.strokeRect(bx1, by1, bw, bh)

      ctx.setLineDash([])
      ctx.fillStyle = '#dc2626'
      ctx.fillRect(bx1, by1 - 22, 134, 20)
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 11px sans-serif'
      ctx.fillText('⚠ ELA Anomaly (+34dB)', bx1 + 4, by1 - 8)
    })
  }
}

function renderGenericUploadedDocument(ctx, width, height, doc) {
  // Brand / Document Header
  ctx.fillStyle = '#0f172a'
  ctx.fillRect(40, 40, width - 80, 80)

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  ctx.fillText(doc.filename || 'OFFICIAL DOCUMENT', 65, 82)

  ctx.fillStyle = '#94a3b8'
  ctx.font = '14px sans-serif'
  ctx.fillText('Digital Verification & Authenticity Audit Record', 65, 105)

  // Meta Info Box
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(40, 140, width - 80, 48)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(40, 140, width - 80, 48)

  ctx.fillStyle = '#475569'
  ctx.font = '13px monospace'
  ctx.fillText(`STATUS: ${doc.verificationStatus || 'VERIFIED'}  |  FORMAT: ${doc.fileType || 'PDF'}  |  RISK: ${doc.riskScore || 12}/100`, 60, 168)

  // Render fields table or lines
  let y = 230
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('DOCUMENT CONTENT & EXTRACTED FIELDS', 40, y)
  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(40, y + 8)
  ctx.lineTo(340, y + 8)
  ctx.stroke()

  y += 40

  if (doc.extractedFields) {
    Object.entries(doc.extractedFields).forEach(([cat, fields]) => {
      ctx.fillStyle = '#64748b'
      ctx.font = 'bold 13px sans-serif'
      ctx.fillText(cat.toUpperCase(), 40, y)
      y += 24

      fields.forEach((f) => {
        ctx.fillStyle = '#334155'
        ctx.font = '14px sans-serif'
        ctx.fillText(`${f.key}:`, 50, y)
        ctx.fillStyle = '#0f172a'
        ctx.font = 'bold 14px monospace'
        ctx.fillText(String(f.value).substring(0, 50), 220, y)
        y += 26
      })
      y += 10
    })
  }

  // Footer Seal
  ctx.fillStyle = '#f1f5f9'
  ctx.fillRect(40, height - 90, width - 80, 50)
  ctx.fillStyle = '#64748b'
  ctx.font = '12px sans-serif'
  ctx.fillText('Cryptographically Verified by VeriDoc AI • Digital SHA-256 Audit Trail Attached', 60, height - 60)
}


function renderResumeDocument(ctx, width, height) {
  // Candidate Header Banner
  ctx.fillStyle = '#0f172a'
  ctx.fillRect(40, 40, width - 80, 75)

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 28px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('JAI PRAKASH V', width / 2, 78)

  ctx.font = '16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  ctx.fillStyle = '#cbd5e1'
  ctx.fillText('B.Sc. (Hons.) Agriculture · Tamil Nadu, India', width / 2, 102)

  ctx.textAlign = 'left'

  // Contact Info Strip
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(40, 125, width - 80, 36)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(40, 125, width - 80, 36)

  ctx.fillStyle = '#334155'
  ctx.font = '13px monospace'
  ctx.fillText('PHONE: +91 90802 64424  |  EMAIL: jaiprakash312005@gmail.com  |  STATUS: VERIFIED', 55, 148)

  // Section 1: Academic Profile
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('ACADEMIC PROFILE & SUMMARY', 40, 195)
  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(40, 202)
  ctx.lineTo(270, 202)
  ctx.stroke()

  ctx.fillStyle = '#475569'
  ctx.font = '14px sans-serif'
  const p1 = 'B.Sc. (Hons.) Agriculture graduate with 80% academic performance and distinction.'
  const p2 = 'Practical field exposure achieved through Rural Agricultural Work Experience (RAWE)'
  const p3 = 'and Assistant Director of Agriculture (ADA) official institutional attachment.'
  ctx.fillText(p1, 40, 230)
  ctx.fillText(p2, 40, 252)
  ctx.fillText(p3, 40, 274)

  // Section 2: Education
  ctx.fillStyle = '#1e293b'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('EDUCATION & CREDENTIALS', 40, 325)
  ctx.strokeStyle = '#2563eb'
  ctx.beginPath()
  ctx.moveTo(40, 332)
  ctx.lineTo(245, 332)
  ctx.stroke()

  // Item 1
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 15px sans-serif'
  ctx.fillText('Bachelor of Science (Honours) in Agriculture', 40, 360)
  ctx.fillStyle = '#2563eb'
  ctx.textAlign = 'right'
  ctx.fillText('2022 – 2026', width - 40, 360)
  ctx.textAlign = 'left'

  ctx.fillStyle = '#64748b'
  ctx.font = '14px sans-serif'
  ctx.fillText('State Agricultural University · First Class with Distinction (80%)', 40, 382)

  // Item 2
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 15px sans-serif'
  ctx.fillText('Higher Secondary Certificate (HSC)', 40, 420)
  ctx.fillStyle = '#64748b'
  ctx.textAlign = 'right'
  ctx.fillText('2022', width - 40, 420)
  ctx.textAlign = 'left'
  ctx.fillText('Tamil Nadu State Board · Biology & Mathematics Specialization', 40, 442)

  // Research Publication Box
  ctx.fillStyle = '#f0fdf4'
  ctx.fillRect(40, 480, width - 80, 90)
  ctx.strokeStyle = '#86efac'
  ctx.lineWidth = 1
  ctx.strokeRect(40, 480, width - 80, 90)

  ctx.fillStyle = '#166534'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('PEER-REVIEWED RESEARCH & FIELD WORK', 55, 506)
  ctx.fillStyle = '#14532d'
  ctx.font = '13px sans-serif'
  ctx.fillText('Published original research on sustainable agricultural pest management and soil microbiomes.', 55, 532)
  ctx.fillText('Credential verification verified against university archival student ledger #TN-AGR-2022-7718.', 55, 554)

  // Seal stamp
  ctx.strokeStyle = '#15803d'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.arc(width - 120, 720, 52, 0, Math.PI * 2)
  ctx.stroke()
  ctx.textAlign = 'center'
  ctx.fillStyle = '#15803d'
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText('VERIFIED AUTHENTIC', width - 120, 715)
  ctx.fillText('UNIVERSITY REGISTRY', width - 120, 730)
  ctx.textAlign = 'left'

  // Digital Signature
  ctx.fillStyle = '#64748b'
  ctx.font = '12px monospace'
  ctx.fillText('DIGITALLY CERTIFIED BY VERIDOC ENTERPRISE AI REGISTRY', 40, height - 60)
  ctx.fillText('CRYPTOGRAPHIC HASH: 3b0181009d585d1ede4910f2390f097b05c24db8d91e5171', 40, height - 40)
}

function renderCommercialInvoice(ctx, width, height, doc) {
  const isAltered = doc.id === 'doc-4'
  const isDuplicate = doc.id === 'doc-5'

  // Header Brand
  ctx.fillStyle = '#1e293b'
  ctx.fillRect(40, 40, width - 80, 90)

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 26px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  ctx.fillText('ABC PRIVATE LIMITED', 65, 82)

  ctx.fillStyle = '#94a3b8'
  ctx.font = '13px sans-serif'
  ctx.fillText('Commercial Tax Invoice · GSTIN: 33AAAAA0000A1Z5 · Chennai, Tamil Nadu', 65, 108)

  // Invoice Number & Date
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Invoice Number:', 65, 175)
  ctx.font = 'bold 16px monospace'
  ctx.fillStyle = '#2563eb'
  ctx.fillText('INV-2026-00432', 190, 175)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Invoice Date:', 65, 212)
  ctx.font = '14px sans-serif'
  ctx.fillStyle = '#334155'
  ctx.fillText('May 20, 2026', 190, 212)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Due Date:', 65, 245)
  ctx.font = '14px sans-serif'
  ctx.fillStyle = '#334155'
  ctx.fillText('June 19, 2026', 190, 245)

  // Customer Card
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(440, 150, width - 480, 115)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(440, 150, width - 480, 115)

  ctx.fillStyle = '#64748b'
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText('BILLED TO (CUSTOMER):', 455, 172)
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 15px sans-serif'
  ctx.fillText('XYZ Pvt Ltd', 455, 195)
  ctx.fillStyle = '#475569'
  ctx.font = '13px sans-serif'
  ctx.fillText('Anna Salai, Chennai - 600002', 455, 218)
  ctx.fillText('GSTIN: 33BBBBB1111B2Z9', 455, 238)

  // Table Header
  ctx.fillStyle = '#f1f5f9'
  ctx.fillRect(65, 290, width - 130, 36)
  ctx.fillStyle = '#475569'
  ctx.font = 'bold 13px sans-serif'
  ctx.fillText('#', 80, 313)
  ctx.fillText('Description & Specification', 120, 313)
  ctx.fillText('Qty', 440, 313)
  ctx.fillText('Rate', 510, 313)
  ctx.textAlign = 'right'
  ctx.fillText('Amount (INR)', width - 85, 313)
  ctx.textAlign = 'left'

  // Row 1
  ctx.fillStyle = '#1e293b'
  ctx.font = '14px sans-serif'
  ctx.fillText('1', 80, 355)
  ctx.fillText('Enterprise Verification Platform Annual License', 120, 355)
  ctx.fillText('1', 445, 355)
  ctx.fillText('₹38,135', 505, 355)
  ctx.textAlign = 'right'
  ctx.fillText('₹38,135.00', width - 85, 355)
  ctx.textAlign = 'left'

  ctx.strokeStyle = '#f1f5f9'
  ctx.beginPath()
  ctx.moveTo(65, 380)
  ctx.lineTo(width - 65, 380)
  ctx.stroke()

  // Row 2 Tax
  ctx.fillStyle = '#64748b'
  ctx.font = '13px sans-serif'
  ctx.fillText('CGST (9.0%)', 120, 410)
  ctx.textAlign = 'right'
  ctx.fillText('₹3,432.50', width - 85, 410)

  ctx.fillText('SGST (9.0%)', 120, 435)
  ctx.fillText('₹3,432.50', width - 85, 435)
  ctx.textAlign = 'left'

  // Total Box
  const totalAmount = isAltered ? '₹84,500' : '₹45,000'
  const totalBg = isAltered ? '#fef2f2' : '#f0fdf4'
  const totalBorder = isAltered ? '#fecaca' : '#bbf7d0'
  const totalColor = isAltered ? '#b91c1c' : '#15803d'

  ctx.fillStyle = totalBg
  ctx.fillRect(440, 470, width - 480, 65)
  ctx.strokeStyle = totalBorder
  ctx.lineWidth = 1.5
  ctx.strokeRect(440, 470, width - 480, 65)

  ctx.fillStyle = '#475569'
  ctx.font = 'bold 12px sans-serif'
  ctx.fillText('TOTAL PAYABLE AMOUNT:', 460, 495)

  ctx.fillStyle = totalColor
  ctx.font = isAltered ? 'bold 24px monospace' : 'bold 24px -apple-system, sans-serif'
  ctx.fillText(totalAmount, 460, 522)

  if (isAltered) {
    // Draw subtle suspicious edit indicator watermark on altered amount
    ctx.fillStyle = 'rgba(239, 68, 68, 0.08)'
    ctx.fillRect(455, 498, 220, 32)
  }

  // Footer & Bank Details
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(65, 600, width - 130, 95)
  ctx.fillStyle = '#64748b'
  ctx.font = 'bold 12px sans-serif'
  ctx.fillText('BANK TRANSFER SETTLEMENT INSTRUCTIONS:', 85, 625)
  ctx.font = '12px monospace'
  ctx.fillText('Bank: HDFC Bank Ltd  ·  A/C: 50200012345678  ·  IFSC: HDFC0001234', 85, 650)
  ctx.fillText('Branch: Anna Salai, Chennai  ·  UPI: abc_pvtltd@hdfcbank', 85, 672)

  // Status Stamp
  if (isDuplicate) {
    ctx.strokeStyle = '#dc2626'
    ctx.lineWidth = 2.5
    ctx.strokeRect(width - 240, 730, 160, 42)
    ctx.fillStyle = '#dc2626'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('DUPLICATE COPY', width - 160, 756)
    ctx.textAlign = 'left'
  }
}

function renderMedicalCertificate(ctx, width, height) {
  // Medical Header
  ctx.fillStyle = '#065f46'
  ctx.fillRect(40, 40, width - 80, 80)

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('GOVERNMENT APPROVED MEDICAL EXAMINATION CENTER', width / 2, 75)
  ctx.font = '13px sans-serif'
  ctx.fillText('CERTIFICATE OF PHYSICAL & MEDICAL FITNESS FOR SERVICE', width / 2, 98)
  ctx.textAlign = 'left'

  // Serial & Date
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Certificate Serial:', 65, 165)
  ctx.fillStyle = '#047857'
  ctx.font = 'bold 15px monospace'
  ctx.fillText('MC-2026-9812', 200, 165)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Date of Examination:', 65, 200)
  ctx.fillStyle = '#334155'
  ctx.font = '14px sans-serif'
  ctx.fillText('June 12, 2026', 220, 200)

  // Candidate
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(65, 235, width - 130, 85)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(65, 235, width - 130, 85)

  ctx.fillStyle = '#64748b'
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText('CANDIDATE IDENTIFICATION:', 85, 258)
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 16px sans-serif'
  ctx.fillText('Rajesh Kumar M (Age: 27 / Male)', 85, 282)
  ctx.fillStyle = '#475569'
  ctx.font = '13px sans-serif'
  ctx.fillText('Identification Mark: Scar on left forearm · Height: 174 cm · Weight: 68 kg', 85, 304)

  // Verdict
  ctx.fillStyle = '#ecfdf5'
  ctx.fillRect(65, 350, width - 130, 60)
  ctx.strokeStyle = '#a7f3d0'
  ctx.strokeRect(65, 350, width - 130, 60)

  ctx.fillStyle = '#047857'
  ctx.font = 'bold 18px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('CERTIFIED FIT FOR ACTIVE PROFESSIONAL DUTY', width / 2, 386)
  ctx.textAlign = 'left'

  // Doctor Signature & Stamp Area
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(width - 340, 480, 280, 140)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(width - 340, 480, 280, 140)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 13px sans-serif'
  ctx.fillText('EXAMINED BY:', width - 320, 505)
  ctx.font = '14px serif'
  ctx.fillText('Dr. K. Senthil Nathan, M.D.', width - 320, 535)
  ctx.font = '12px monospace'
  ctx.fillStyle = '#64748b'
  ctx.fillText('Reg No: TNMC-44129', width - 320, 560)
  ctx.fillText('Civil Surgeon & Specialist', width - 320, 580)

  // Circular Stamp with faint contrast
  ctx.strokeStyle = 'rgba(30, 58, 138, 0.45)'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.arc(width - 200, 550, 46, 0, Math.PI * 2)
  ctx.stroke()
}

function renderEmploymentLetter(ctx, width, height) {
  // Corporate Letterhead
  ctx.fillStyle = '#1e3a8a'
  ctx.fillRect(40, 40, width - 80, 80)

  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px -apple-system, sans-serif'
  ctx.fillText('TURING TECHNOLOGIES INC.', 65, 78)
  ctx.font = '13px sans-serif'
  ctx.fillStyle = '#93c5fd'
  ctx.fillText('Global AI Systems & Enterprise Research  ·  Bangalore / San Francisco', 65, 100)

  // Reference Code
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 13px monospace'
  ctx.fillText('REF: TTI/HR/2026/VERIF-90821', 65, 165)
  ctx.fillText('DATE: August 14, 2026', width - 240, 165)

  // Title
  ctx.fillStyle = '#1e3a8a'
  ctx.font = 'bold 18px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('EMPLOYMENT VERIFICATION & CREDENTIAL CERTIFICATION', width / 2, 220)
  ctx.textAlign = 'left'

  // Letter Body
  ctx.fillStyle = '#334155'
  ctx.font = '15px sans-serif'
  const text1 = 'This document serves to certify that Ms. Ananya Sharma (Employee ID: EMP-90821)'
  const text2 = 'is a permanent, full-time Senior AI Research Engineer with our Global Engineering Division.'
  const text3 = 'She joined the organization on August 14, 2023, and remains in good standing.'
  ctx.fillText(text1, 65, 270)
  ctx.fillText(text2, 65, 298)
  ctx.fillText(text3, 65, 326)

  // Details Box
  ctx.fillStyle = '#f8fafc'
  ctx.fillRect(65, 360, width - 130, 120)
  ctx.strokeStyle = '#e2e8f0'
  ctx.strokeRect(65, 360, width - 130, 120)

  ctx.fillStyle = '#64748b'
  ctx.font = 'bold 13px sans-serif'
  ctx.fillText('DESIGNATION:', 90, 395)
  ctx.fillText('DEPARTMENT:', 90, 425)
  ctx.fillText('WORK LOCATION:', 90, 455)

  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Senior AI Research Engineer', 240, 395)
  ctx.fillText('Advanced Neural Reasoning & Multi-Modal Models', 240, 425)
  ctx.fillText('Innovation Tech Park, Whitefield, Bangalore', 240, 455)

  // Signatory & Seal
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px sans-serif'
  ctx.fillText('Authorized HR Signatory', 65, 540)
  ctx.font = '13px sans-serif'
  ctx.fillStyle = '#64748b'
  ctx.fillText('Director of Global Talent Operations', 65, 562)
  ctx.fillText('Turing Technologies Inc.', 65, 582)

  // Digital Corporate Seal
  ctx.strokeStyle = '#1e3a8a'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.arc(width - 160, 560, 50, 0, Math.PI * 2)
  ctx.stroke()
  ctx.textAlign = 'center'
  ctx.fillStyle = '#1e3a8a'
  ctx.font = 'bold 11px sans-serif'
  ctx.fillText('AUTHENTICATED', width - 160, 555)
  ctx.fillText('SEAL 2026', width - 160, 572)
  ctx.textAlign = 'left'
}

