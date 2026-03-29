import { useEffect, useState } from 'react'
import styles from './StatCards.module.css'

function AnimatedNumber({ value, suffix = '' }) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    if (value === null || value === undefined) return
    const target = parseFloat(value)
    const duration = 800
    const start = performance.now()
    let raf

    const step = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)   // ease-out cubic
      setDisplayed(Math.round(target * eased * 10) / 10)
      if (t < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [value])

  if (value === null || value === undefined) return <span className={styles.numEmpty}>—</span>
  return <span>{typeof value === 'number' && !Number.isInteger(value) ? displayed.toFixed(1) : Math.round(displayed)}{suffix}</span>
}

// Shown while a job is processing — avoids misleading mid-job percentages
function PendingDash() {
  return <span className={styles.pending}>—</span>
}

export default function StatCards({ summary, isProcessing = false }) {
  // total_frames is not in AnalysisSummary schema — derive from the three counts
  const total = summary
    ? (summary.normal_count + summary.suspicious_count + summary.anomaly_count)
    : null

  const pct = (count) =>
    total > 0 ? parseFloat(((count / total) * 100).toFixed(1)) : null

  const normalPct = summary ? pct(summary.normal_count)     : null
  const suspPct   = summary ? pct(summary.suspicious_count) : null
  const anomPct   = summary ? pct(summary.anomaly_count)    : null

  // Only glow when we have a definitive final anomaly rate above 15%
  const anomalyGlow = !isProcessing && anomPct !== null && anomPct > 15

  return (
    <div className={styles.grid}>
      <div className={styles.card}>
        <div className={styles.label}>TOTAL FRAMES</div>
        <div className={styles.value}><AnimatedNumber value={total} /></div>
        <div className={styles.sub}>frames processed</div>
      </div>

      <div className={styles.card}>
        <div className={styles.label}>NORMAL</div>
        <div className={`${styles.value} ${styles.green}`}>
          {isProcessing ? <PendingDash /> : <AnimatedNumber value={normalPct} suffix="%" />}
        </div>
        <div className={styles.sub}>{(!isProcessing && summary) ? summary.normal_count : '—'} frames</div>
      </div>

      <div className={styles.card}>
        <div className={styles.label}>SUSPICIOUS</div>
        <div className={`${styles.value} ${styles.yellow}`}>
          {isProcessing ? <PendingDash /> : <AnimatedNumber value={suspPct} suffix="%" />}
        </div>
        <div className={styles.sub}>{(!isProcessing && summary) ? summary.suspicious_count : '—'} frames</div>
      </div>

      <div className={`${styles.card} ${anomalyGlow ? styles.cardGlow : ''}`}>
        <div className={styles.label}>ANOMALY</div>
        <div className={`${styles.value} ${styles.red}`}>
          {isProcessing ? <PendingDash /> : <AnimatedNumber value={anomPct} suffix="%" />}
        </div>
        <div className={styles.sub}>{(!isProcessing && summary) ? summary.anomaly_count : '—'} frames</div>
      </div>
    </div>
  )
}
