import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import styles from './AnomalyAlert.module.css'

const DISMISS_MS = 5000

function Toast({ alert, onDismiss }) {
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    const t1 = setTimeout(() => setLeaving(true), DISMISS_MS - 300)
    const t2 = setTimeout(onDismiss, DISMISS_MS)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [onDismiss])

  const signals = alert.signals ?? []
  const sigStr  = signals.length ? signals.join(' · ') : 'no signals'

  return (
    <div className={`${styles.toast} ${leaving ? styles.leaving : ''}`}>
      <div className={styles.toastHeader}>
        <span className={styles.dot} />
        <span className={styles.title}>ANOMALY DETECTED</span>
        <button className={styles.close} onClick={onDismiss}>✕</button>
      </div>
      <div className={styles.body}>
        <span className={styles.field}>frame {alert.frame}</span>
        <span className={styles.sep}>·</span>
        <span className={styles.field}>{Number(alert.timestamp).toFixed(2)}s</span>
        <span className={styles.sep}>·</span>
        <span className={styles.score}>score {Number(alert.score).toFixed(3)}</span>
      </div>
      <div className={styles.signals}>{sigStr}</div>
      <div className={styles.progress}>
        <div className={styles.progressBar} />
      </div>
    </div>
  )
}

export default function AnomalyAlert({ lastAlert }) {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    if (!lastAlert) return
    setToasts(prev => [...prev, { ...lastAlert, _key: Date.now() + Math.random() }])
  }, [lastAlert])

  const dismiss = (key) => setToasts(prev => prev.filter(t => t._key !== key))

  return createPortal(
    <div className={styles.container}>
      {toasts.map(t => (
        <Toast key={t._key} alert={t} onDismiss={() => dismiss(t._key)} />
      ))}
    </div>,
    document.body
  )
}
