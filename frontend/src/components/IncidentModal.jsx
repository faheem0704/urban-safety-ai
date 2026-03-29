import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import styles from './IncidentModal.module.css'

function exportReport(event) {
  const cls     = event.classification ?? (event.type === 'anomaly_alert' ? 'ANOMALY' : 'NORMAL')
  const score   = event.score   ?? event.anomaly_score   ?? 0
  const ts      = event.timestamp ?? event.timestamp_sec ?? 0
  const frame   = event.frame  ?? event.frame_number     ?? '—'
  const signals = event.signals ?? event.triggered_signals ?? []

  const lines = [
    'URBAN SAFETY AI — INCIDENT REPORT',
    '='.repeat(44),
    `Incident ID:       ${String(event.id ?? frame).padEnd(20)}`,
    `Timestamp:         ${Number(ts).toFixed(2)}s`,
    `Frame Number:      ${frame}`,
    `Classification:    ${cls}`,
    `Anomaly Score:     ${Number(score).toFixed(4)}`,
    `Triggered Signals: ${signals.length ? signals.join(', ') : 'none'}`,
    '',
    `Report Generated:  ${new Date().toISOString()}`,
    `System:            Urban Safety AI v1.0.0`,
    '='.repeat(44),
  ]

  const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `incident-frame${frame}-${cls.toLowerCase()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

export default function IncidentModal({ event, onClose }) {
  const [resolved, setResolved] = useState(false)
  const [leaving,  setLeaving]  = useState(false)

  const handleClose = useCallback(() => {
    setLeaving(true)
    setTimeout(onClose, 200)
  }, [onClose])

  // Reset state when a new event is shown
  useEffect(() => {
    setResolved(false)
    setLeaving(false)
  }, [event])

  // Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') handleClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [handleClose])

  if (!event) return null

  const cls     = event.classification ?? (event.type === 'anomaly_alert' ? 'ANOMALY' : 'NORMAL')
  const score   = event.score   ?? event.anomaly_score   ?? 0
  const ts      = event.timestamp ?? event.timestamp_sec ?? 0
  const frame   = event.frame  ?? event.frame_number     ?? '—'
  const signals = event.signals ?? event.triggered_signals ?? []
  const displayCls = resolved ? 'RESOLVED' : cls
  const badgeCls   = resolved ? styles.badgeRESOLVED : styles[`badge${cls}`]
  const scoreCls   = cls === 'ANOMALY' ? styles.scoreRed : cls === 'SUSPICIOUS' ? styles.scoreYellow : styles.scoreGreen

  return createPortal(
    <div
      className={`${styles.overlay} ${leaving ? styles.overlayLeaving : ''}`}
      onClick={handleClose}
    >
      <div className={styles.modal} onClick={e => e.stopPropagation()}>

        {/* ── Header ── */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.title}>INCIDENT REPORT</span>
            <span className={styles.incidentId}>
              #{String(event.id ?? frame).slice(-8).padStart(6, '0')}
            </span>
          </div>
          <button className={styles.closeBtn} onClick={handleClose}>✕</button>
        </div>

        {/* ── Simulated frame snapshot ── */}
        <div className={styles.snapshot}>
          <span className={`${styles.corner} ${styles.tl}`} />
          <span className={`${styles.corner} ${styles.tr}`} />
          <span className={`${styles.corner} ${styles.bl}`} />
          <span className={`${styles.corner} ${styles.br}`} />
          <div className={styles.snapshotContent}>
            <span className={styles.frameLabel}>FRAME {frame}</span>
            <span className={`${styles.snapBadge} ${badgeCls}`}>{displayCls}</span>
            <span className={styles.snapshotNote}>
              Frame snapshot available in production with RTSP feed
            </span>
          </div>
        </div>

        {/* ── Details ── */}
        <div className={styles.details}>
          <div className={styles.scoreRow}>
            <span className={styles.scoreLabel}>ANOMALY SCORE</span>
            <span className={`${styles.score} ${scoreCls}`}>
              {Number(score).toFixed(3)}
            </span>
          </div>

          <div className={styles.metaGrid}>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>TIMESTAMP</span>
              <span className={styles.metaValue}>{Number(ts).toFixed(2)}s</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>FRAME</span>
              <span className={styles.metaValue}>{frame}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>STATUS</span>
              <span className={`${styles.metaValue} ${resolved ? styles.resolvedText : ''}`}>
                {displayCls}
              </span>
            </div>
          </div>

          {signals.length > 0 && (
            <div className={styles.signalsSection}>
              <span className={styles.metaLabel}>TRIGGERED SIGNALS</span>
              <div className={styles.signals}>
                {signals.map((s, i) => (
                  <span key={i} className={styles.sig}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Actions ── */}
        <div className={styles.actions}>
          <button
            className={`${styles.btn} ${styles.btnGhost} ${resolved ? styles.btnResolved : ''}`}
            onClick={() => setResolved(r => !r)}
          >
            {resolved ? 'UNRESOLVE' : 'MARK RESOLVED'}
          </button>
          <button
            className={`${styles.btn} ${styles.btnBlue}`}
            onClick={() => exportReport(event)}
          >
            EXPORT REPORT
          </button>
          <button
            className={`${styles.btn} ${styles.btnGhost}`}
            onClick={handleClose}
          >
            CLOSE
          </button>
        </div>

      </div>
    </div>,
    document.body
  )
}
