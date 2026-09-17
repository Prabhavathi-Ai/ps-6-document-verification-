import React, { useState } from 'react'

export function UserProfileSettings({
  onBackToDashboard = () => {},
  onBackToVerify = () => {},
  onSaveNotification = () => {},
}) {
  const [activeTab, setActiveTab] = useState('profile') // 'profile' | 'engine' | 'security' | 'notifications'

  // Profile Form State
  const [profile, setProfile] = useState({
    fullName: 'Jordan Davis',
    email: 'jordan.davis@veridoc.ai',
    phone: '+1 (555) 019-2834',
    title: 'Lead Document Forensic Auditor & System Administrator',
    department: 'Anti-Fraud & Compliance Examination Unit',
    employeeId: 'VD-AUDITOR-0492',
    timezone: 'UTC-05:00 Eastern Time (US & Canada)',
    language: 'English (United States)',
    theme: 'Enterprise Light',
  })

  // Verification Engine Settings (Merged from Settings)
  const [engineSettings, setEngineSettings] = useState({
    docVqaConfidenceFloor: 85,
    docTamperSensitivity: 'high', // 'high' | 'medium' | 'strict'
    duplicateSimilarityFloor: 80,
    hashAlgorithm: 'dhash_64_embeddings', // 'dhash_64_embeddings' | 'phash_hamming'
    autoApproveLowRisk: true,
    autoQuarantineTampered: true,
    requireReviewNotes: true,
    maxConcurrentBatchUploads: 50,
  })

  // Security & API Settings (Merged from Settings)
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorEnabled: true,
    apiKey: 'vd_live_89f4b912c019fa5e8c381d',
    showApiKey: false,
    sessionTimeout: '4 hours',
    auditLogging: 'Full Forensic Trail (SHA-256 Digest)',
  })

  // Notification & Webhook Settings (Merged from Settings)
  const [notifications, setNotifications] = useState({
    emailOnSuspicious: true,
    emailOnDuplicate: true,
    dailyDigest: false,
    slackWebhook: true,
    webhookUrl: 'https://api.enterprise.corp/v1/fraud-webhooks/veridoc',
  })

  const [copiedKey, setCopiedKey] = useState(false)

  const handleCopyApiKey = () => {
    navigator.clipboard?.writeText(securitySettings.apiKey)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2500)
    onSaveNotification('✓ API Key copied to clipboard')
  }

  const handleSave = (e) => {
    e?.preventDefault()
    onSaveNotification('✓ Profile & Enterprise Settings saved successfully')
  }

  const handleReset = () => {
    setEngineSettings({
      docVqaConfidenceFloor: 85,
      docTamperSensitivity: 'high',
      duplicateSimilarityFloor: 80,
      hashAlgorithm: 'dhash_64_embeddings',
      autoApproveLowRisk: true,
      autoQuarantineTampered: true,
      requireReviewNotes: true,
      maxConcurrentBatchUploads: 50,
    })
    onSaveNotification('↺ Settings restored to factory defaults')
  }

  return (
    <main className="main-content profile-page-content" id="profile-page">
      {/* Top Header Row with Unified 1.35rem Heading */}
      <div className="profile-page-header">
        <div className="profile-header-title-block">
          <p className="eyebrow">Account &amp; System Administration</p>
          <div className="profile-headline-row">
            <h2>Profile &amp; Settings</h2>
            <span className="profile-role-badge">Enterprise Administrator</span>
          </div>
        </div>

        <div className="profile-heading-actions">
          <button
            type="button"
            className="secondary-action"
            style={{ margin: 0, padding: '8px 16px' }}
            onClick={onBackToDashboard}
          >
            ← Back to Dashboard
          </button>
          <button
            type="button"
            className="primary-action"
            style={{ margin: 0, padding: '8px 18px' }}
            onClick={onBackToVerify}
          >
            Verify Document ↗
          </button>
        </div>
      </div>

      {/* User Hero Overview Card */}
      <div className="profile-hero-card">
        <div className="hero-avatar-wrap">
          <div className="hero-avatar-large">JD</div>
          <span className="hero-online-dot" title="Active Auditor Online" />
        </div>

        <div className="hero-info-col">
          <div className="hero-name-row">
            <h3>{profile.fullName}</h3>
            <span className="hero-badge-verified">✓ Verified Auditor</span>
          </div>
          <p className="hero-title-text">{profile.title}</p>
          <div className="hero-meta-chips">
            <span className="hero-chip">🏢 {profile.department}</span>
            <span className="hero-chip">🆔 {profile.employeeId}</span>
            <span className="hero-chip">✉ {profile.email}</span>
            <span className="hero-chip">🌐 {profile.timezone.split(' ')[0]}</span>
          </div>
        </div>

        <div className="hero-stats-strip">
          <div className="hero-stat-item">
            <span className="h-stat-num">1,284</span>
            <span className="h-stat-lbl">Documents Verified</span>
          </div>
          <div className="hero-stat-item">
            <span className="h-stat-num stat-flagged">63</span>
            <span className="h-stat-lbl">Tamper Cases Flagged</span>
          </div>
          <div className="hero-stat-item">
            <span className="h-stat-num stat-dup">142</span>
            <span className="h-stat-lbl">Duplicates Intercepted</span>
          </div>
          <div className="hero-stat-item">
            <span className="h-stat-num stat-pass">99.8%</span>
            <span className="h-stat-lbl">Compliance Precision</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation for Combined Profile & Settings */}
      <nav className="profile-tabs-nav" aria-label="Profile and Settings Sections">
        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          <span aria-hidden="true">👤</span> Personal Details
        </button>
        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'engine' ? 'active' : ''}`}
          onClick={() => setActiveTab('engine')}
        >
          <span aria-hidden="true">⚙</span> Verification Engine Rules
        </button>
        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          <span aria-hidden="true">🔒</span> Security &amp; API Keys
        </button>
        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          <span aria-hidden="true">🔔</span> Notifications &amp; Webhooks
        </button>
      </nav>

      {/* Tab 1: Personal Details */}
      {activeTab === 'profile' && (
        <form className="profile-form-grid" onSubmit={handleSave}>
          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Personal &amp; Contact Information</h4>
              <p>Manage your account credentials and verification auditor identity.</p>
            </div>

            <div className="form-fields-two-col">
              <div className="form-group">
                <label htmlFor="p-fullName">Full Name</label>
                <input
                  id="p-fullName"
                  type="text"
                  value={profile.fullName}
                  onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                  className="profile-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="p-email">Work Email</label>
                <input
                  id="p-email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="profile-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="p-phone">Phone Number</label>
                <input
                  id="p-phone"
                  type="tel"
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  className="profile-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="p-empId">Auditor Staff ID</label>
                <input
                  id="p-empId"
                  type="text"
                  value={profile.employeeId}
                  disabled
                  className="profile-input disabled"
                />
              </div>
            </div>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Departmental Organization &amp; Regional Localization</h4>
              <p>Your institutional division assignment and timezone formatting.</p>
            </div>

            <div className="form-fields-two-col">
              <div className="form-group">
                <label htmlFor="p-dept">Department / Division</label>
                <input
                  id="p-dept"
                  type="text"
                  value={profile.department}
                  onChange={(e) => setProfile({ ...profile, department: e.target.value })}
                  className="profile-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="p-tz">Timezone</label>
                <select
                  id="p-tz"
                  value={profile.timezone}
                  onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                  className="profile-input"
                >
                  <option>UTC-05:00 Eastern Time (US &amp; Canada)</option>
                  <option>UTC+00:00 Greenwich Mean Time</option>
                  <option>UTC+05:30 Chennai, Kolkata, Mumbai, New Delhi</option>
                  <option>UTC+08:00 Singapore, Hong Kong</option>
                  <option>UTC-08:00 Pacific Time (US &amp; Canada)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="p-lang">Platform Language</label>
                <select
                  id="p-lang"
                  value={profile.language}
                  onChange={(e) => setProfile({ ...profile, language: e.target.value })}
                  className="profile-input"
                >
                  <option>English (United States)</option>
                  <option>English (United Kingdom)</option>
                  <option>Tamil (தமிழ்)</option>
                  <option>French (Français)</option>
                  <option>German (Deutsch)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="p-theme">Workspace Theme</label>
                <select
                  id="p-theme"
                  value={profile.theme}
                  onChange={(e) => setProfile({ ...profile, theme: e.target.value })}
                  className="profile-input"
                >
                  <option>Enterprise Light (Standard)</option>
                  <option>High Contrast Accessibility</option>
                  <option>Dark Mode (Beta)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-actions-bar">
            <button type="button" className="btn-secondary-plain" onClick={handleReset}>
              Reset Defaults
            </button>
            <button type="submit" className="primary-action" style={{ margin: 0, padding: '10px 24px' }}>
              Save Profile Changes
            </button>
          </div>
        </form>
      )}

      {/* Tab 2: Verification Engine & Fraud Settings (Incorporated from Settings) */}
      {activeTab === 'engine' && (
        <form className="profile-form-grid" onSubmit={handleSave}>
          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Pillar 1: DocVQA OCR Entity Confidence Floor</h4>
              <p>Minimum character &amp; key-value parsing confidence before flagging a field warning.</p>
            </div>

            <div className="range-slider-row">
              <div className="range-info">
                <span>Confidence Floor: <strong>{engineSettings.docVqaConfidenceFloor}%</strong></span>
                <span className="range-hint">(Default recommended: 85%)</span>
              </div>
              <input
                type="range"
                min="50"
                max="99"
                value={engineSettings.docVqaConfidenceFloor}
                onChange={(e) =>
                  setEngineSettings({ ...engineSettings, docVqaConfidenceFloor: Number(e.target.value) })
                }
                className="profile-slider"
              />
            </div>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Pillar 2: DocTamper Alteration &amp; XAI Sensitivity</h4>
              <p>Forensic mask trigger threshold for pixel compression divergences and font glyph splices.</p>
            </div>

            <div className="radio-pill-group">
              <label
                className={`radio-pill-item ${engineSettings.docTamperSensitivity === 'medium' ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="tamperSensitivity"
                  value="medium"
                  checked={engineSettings.docTamperSensitivity === 'medium'}
                  onChange={() => setEngineSettings({ ...engineSettings, docTamperSensitivity: 'medium' })}
                />
                <strong>Medium</strong>
                <span>Tolerates minor scan distortion</span>
              </label>

              <label
                className={`radio-pill-item ${engineSettings.docTamperSensitivity === 'high' ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="tamperSensitivity"
                  value="high"
                  checked={engineSettings.docTamperSensitivity === 'high'}
                  onChange={() => setEngineSettings({ ...engineSettings, docTamperSensitivity: 'high' })}
                />
                <strong>High (Recommended)</strong>
                <span>Flags numeric alterations &gt; 12% pixel divergence</span>
              </label>

              <label
                className={`radio-pill-item ${engineSettings.docTamperSensitivity === 'strict' ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="tamperSensitivity"
                  value="strict"
                  checked={engineSettings.docTamperSensitivity === 'strict'}
                  onChange={() => setEngineSettings({ ...engineSettings, docTamperSensitivity: 'strict' })}
                />
                <strong>Strict Forensic</strong>
                <span>Zero-tolerance on font artifacts</span>
              </label>
            </div>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Pillar 3: SROIE/CORD Duplicate Detection &amp; Perceptual Hashing</h4>
              <p>Perceptual 64-bit dHash index and cosine embedding match threshold for duplicate submission alerts.</p>
            </div>

            <div className="range-slider-row">
              <div className="range-info">
                <span>Duplicate Collision Floor: <strong>{engineSettings.duplicateSimilarityFloor}%</strong></span>
                <span className="range-hint">Documents with similarity ≥ {engineSettings.duplicateSimilarityFloor}% will trigger collision alert</span>
              </div>
              <input
                type="range"
                min="60"
                max="95"
                value={engineSettings.duplicateSimilarityFloor}
                onChange={(e) =>
                  setEngineSettings({ ...engineSettings, duplicateSimilarityFloor: Number(e.target.value) })
                }
                className="profile-slider"
              />
            </div>

            <div className="toggle-setting-row" style={{ marginTop: '16px' }}>
              <div>
                <strong>Auto-Quarantine Altered &amp; Tampered Documents</strong>
                <p>Instantly flag suspicious files to prevent downstream ledger ingestion.</p>
              </div>
              <input
                type="checkbox"
                checked={engineSettings.autoQuarantineTampered}
                onChange={(e) =>
                  setEngineSettings({ ...engineSettings, autoQuarantineTampered: e.target.checked })
                }
                className="profile-toggle"
              />
            </div>
          </div>

          <div className="form-actions-bar">
            <button type="button" className="btn-secondary-plain" onClick={handleReset}>
              Reset Defaults
            </button>
            <button type="submit" className="primary-action" style={{ margin: 0, padding: '10px 24px' }}>
              Save Engine Settings
            </button>
          </div>
        </form>
      )}

      {/* Tab 3: Security & API Keys (Incorporated from Settings) */}
      {activeTab === 'security' && (
        <div className="profile-form-grid">
          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Two-Factor Authentication (2FA)</h4>
              <p>Mandatory security compliance for enterprise document verification operators.</p>
            </div>

            <div className="security-status-row">
              <div className="security-badge-state pass">
                <span className="sec-dot green" />
                <span>2FA Activated via Authenticator (TOTP)</span>
              </div>
              <button
                type="button"
                className="secondary-action"
                style={{ margin: 0, padding: '6px 14px' }}
                onClick={() => onSaveNotification('✓ 2FA security configuration is active and verified')}
              >
                Reconfigure 2FA
              </button>
            </div>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Enterprise API Keys</h4>
              <p>Authenticate programmatic batch uploads and automated REST endpoint verification.</p>
            </div>

            <div className="api-key-box">
              <div className="api-key-code-wrap">
                <span className="api-key-label">Production API Key:</span>
                <code className="api-key-val">
                  {securitySettings.showApiKey
                    ? securitySettings.apiKey
                    : 'vd_live_••••••••••••••••••••••••381d'}
                </code>
              </div>
              <div className="api-key-btns">
                <button
                  type="button"
                  className="secondary-action"
                  style={{ margin: 0, padding: '6px 12px' }}
                  onClick={() =>
                    setSecuritySettings({ ...securitySettings, showApiKey: !securitySettings.showApiKey })
                  }
                >
                  {securitySettings.showApiKey ? 'Hide' : 'Reveal'}
                </button>
                <button
                  type="button"
                  className="primary-action"
                  style={{ margin: 0, padding: '6px 14px' }}
                  onClick={handleCopyApiKey}
                >
                  {copiedKey ? '✓ Copied' : 'Copy Key'}
                </button>
              </div>
            </div>
            <p className="api-key-hint">
              Created on Sep 12, 2026 • Last used: 2 minutes ago by DocVQA ingestion pipeline.
            </p>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Cryptographic Audit Signature</h4>
              <p>Deterministic SHA-256 certificate for legal audit trails and tamper-proof verification records.</p>
            </div>

            <div className="audit-hash-chip">
              <span className="audit-hash-title">Institution Master Key Hash:</span>
              <code className="audit-hash-val">
                SHA-256: 0xa4f298c77b1029e84d7e819b2c01fa5e0984a1d9bc77a1029e84d7e819b2c01f
              </code>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Notifications & Webhooks (Incorporated from Settings) */}
      {activeTab === 'notifications' && (
        <form className="profile-form-grid" onSubmit={handleSave}>
          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Automated Alert Dispatch Preferences</h4>
              <p>Configure real-time security alerts sent to your email and team notification channels.</p>
            </div>

            <div className="toggle-list">
              <div className="toggle-setting-row">
                <div>
                  <strong>Critical Tamper Alteration Alerts</strong>
                  <p>Trigger instant high-priority email when DocTamper spots an altered number or stamp.</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.emailOnSuspicious}
                  onChange={(e) => setNotifications({ ...notifications, emailOnSuspicious: e.target.checked })}
                  className="profile-toggle"
                />
              </div>

              <div className="toggle-setting-row">
                <div>
                  <strong>Duplicate Submission Conflict Alerts</strong>
                  <p>Notify when SROIE/CORD perceptual hash detects duplicate repository uploads.</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.emailOnDuplicate}
                  onChange={(e) => setNotifications({ ...notifications, emailOnDuplicate: e.target.checked })}
                  className="profile-toggle"
                />
              </div>

              <div className="toggle-setting-row">
                <div>
                  <strong>Daily Verification Digest</strong>
                  <p>Receive a daily summary of total verifications, risk distribution, and flagged cases.</p>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.dailyDigest}
                  onChange={(e) => setNotifications({ ...notifications, dailyDigest: e.target.checked })}
                  className="profile-toggle"
                />
              </div>
            </div>
          </div>

          <div className="profile-section-card">
            <div className="card-top-title">
              <h4>Enterprise Fraud Webhook Integration</h4>
              <p>Forward verified JSON payloads and suspicious tamper logs to your ERP / compliance endpoints.</p>
            </div>

            <div className="form-group">
              <label htmlFor="webhook-url">Payload Webhook URL</label>
              <div className="webhook-input-row">
                <input
                  id="webhook-url"
                  type="url"
                  value={notifications.webhookUrl}
                  onChange={(e) => setNotifications({ ...notifications, webhookUrl: e.target.value })}
                  className="profile-input"
                  placeholder="https://your-domain.com/webhook/endpoint"
                />
                <button
                  type="button"
                  className="secondary-action"
                  style={{ margin: 0, padding: '8px 16px', whiteSpace: 'nowrap' }}
                  onClick={() => onSaveNotification('✓ Test Webhook event pinged successfully (Status 200 OK)')}
                >
                  Test Webhook
                </button>
              </div>
            </div>
          </div>

          <div className="form-actions-bar">
            <button type="button" className="btn-secondary-plain" onClick={handleReset}>
              Reset Defaults
            </button>
            <button type="submit" className="primary-action" style={{ margin: 0, padding: '10px 24px' }}>
              Save Notification Settings
            </button>
          </div>
        </form>
      )}
    </main>
  )
}
