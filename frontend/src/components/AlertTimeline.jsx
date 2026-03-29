import { useEffect, useRef } from 'react'
import styles from './AlertTimeline.module.css'

const CLS_DOT = { NORMAL: styles.dotGreen, SUSPICIOUS: styles.dotYellow, ANOMALY: styles.dotRed }

function AlertItem({ alert, onClick }) {
  const isAnomaly = alert.classification === 'ANOMALY' || alert.type === 'anomaly_alert'
  const cls       = alert.classification ?? (alert.type === 'anomaly_alert' ? 'ANOMALY' : 'NORMAL')
  const signals   = alert.signals ?? alert.triggered_signals ?? []
  const score     = alert.score   ?? alert.anomaly_score     ?? 0
  const ts        = alert.timestamp ?? alert.timestamp_sec   ?? 0
  const frame     = alert.frame   ?? alert.frame_number      ?? '—'
  const time      = alert.receivedAt instanceof Date
    ? alert.receivedAt.toLocaleTimeString()
    : new Date().toLocaleTimeString()

  return (
    <div
      className={`${styles.item} ${isAnomaly ? styles.itemAnomaly : ''}`}
      onClick={() => onClick(alert)}
      style={{ cursor: 'pointer' }}
    >
      <span className={`${styles.dot} ${CLS_DOT[cls] ?? styles.dotGreen}`} />
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={`${styles.cls} ${isAnomaly ? styles.clsRed : cls === 'SUSPICIOUS' ? styles.clsYellow : styles.clsGreen}`}>
            {cls}
          </span>
          <span className={styles.meta}>frame {frame} · {Number(ts).toFixed(2)}s · score {Number(score).toFixed(3)}</span>
          <span className={styles.time}>{time}</span>
        </div>
        {signals.length > 0 && (
          <div className={styles.signals}>
            {signals.map((s, i) => <span key={i} className={styles.sig}>{s}</span>)}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AlertTimeline({ alerts, onEventClick }) {
  const listRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }, [alerts.length])

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>ALERT TIMELINE</span>
        <span className={styles.count}>{alerts.length} events</span>
      </div>

      <div className={styles.list} ref={listRef}>
        {alerts.length === 0 ? (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>◎</span>
            <span>No alerts yet</span>
            <span className={styles.emptySub}>Alerts will appear here when anomalies are detected</span>
          </div>
        ) : (
          alerts.map(a => (
            <AlertItem key={a.id} alert={a} onClick={onEventClick ?? (() => {})} />
          ))
        )}
      </div>
    </div>
  )
}
