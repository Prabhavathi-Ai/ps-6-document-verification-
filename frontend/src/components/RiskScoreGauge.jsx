import React from 'react'

export function RiskScoreGauge({ score = 95, riskLevel = 'low', category = 'genuine' }) {
  // Score is 0-100 (higher = safer / more genuine, lower = higher risk)
  const radius = 48
  const strokeWidth = 8
  const normalizedRadius = radius - strokeWidth / 2
  const circumference = normalizedRadius * 2 * Math.PI
  const strokeDashoffset = circumference - (score / 100) * circumference

  let color = '#249b69' // green
  let statusText = 'Low Risk'
  let description = 'Genuine & Verified'

  if (score < 50 || category === 'tampered') {
    color = '#d94f64' // red
    statusText = 'High Risk'
    description = category === 'tampered' ? 'Potential Tampering' : 'High Risk Submission'
  } else if (score < 80 || category === 'duplicate' || category === 'near_duplicate' || category === 'mixed') {
    color = '#e68a00' // amber
    statusText = 'Medium Risk'
    description = category === 'duplicate' ? 'Duplicate Submission' : 'Verification Warning'
  }

  return (
    <div className="risk-gauge-container">
      <div className="risk-gauge-graphic">
        <svg height={radius * 2} width={radius * 2} className="gauge-svg">
          <circle
            stroke="#e9eef6"
            fill="transparent"
            strokeWidth={strokeWidth}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.8s ease' }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            transform={`rotate(-90 ${radius} ${radius})`}
          />
        </svg>
        <div className="gauge-center-text">
          <span className="gauge-number" style={{ color }}>{score}</span>
          <span className="gauge-max">/100</span>
        </div>
      </div>
      <div className="risk-gauge-meta">
        <div className="risk-badge" style={{ backgroundColor: `${color}18`, color }}>
          <span className="badge-dot" style={{ backgroundColor: color }} />
          {statusText}
        </div>
        <h4 className="risk-description">{description}</h4>
        <p className="risk-category-label">
          Category: <strong className="capitalize">{category.replace('_', ' ')}</strong>
        </p>
      </div>
    </div>
  )
}
