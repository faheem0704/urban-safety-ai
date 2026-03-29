import styles from './LiveFeed.module.css'

const CLS_COLOR = { NORMAL: 'green', SUSPICIOUS: 'yellow', ANOMALY: 'red' }
const CLS_LABEL = { NORMAL: 'NORMAL', SUSPICIOUS: 'SUSPICIOUS', ANOMALY: '⚠ ANOMALY' }

export default function LiveFeed({ lastAlert, recentFrames = [], camera = { id: 'CAM-01', location: 'DOWNTOWN' } }) {
  const cls   = lastAlert?.type === 'anomaly_alert' ? 'ANOMALY'
              : null   // no frame data outside anomalies — default to NORMAL for display
  const frame = lastAlert?.frame ?? null
  const ts    = lastAlert?.timestamp ?? null

  // Build 20-bar mini-chart from recentFrames (most recent alerts)
  const bars = Array.from({ length: 20 }, (_, i) => recentFrames[i] ?? null)

  return (
    <div className={styles.wrapper}>
      {/* Main screen */}
      <div className={styles.screen}>
        {/* Corner brackets */}
        <span className={`${styles.corner} ${styles.tl}`} />
        <span className={`${styles.corner} ${styles.tr}`} />
        <span className={`${styles.corner} ${styles.bl}`} />
        <span className={`${styles.corner} ${styles.br}`} />

        {/* Scanline overlay */}
        <div className={styles.scanline} />

        {/* Camera info overlay */}
        <div className={styles.camInfo}>{camera.id} · {camera.location} · 4K</div>

        {/* Classification badge */}
        {cls && (
          <div className={`${styles.badge} ${styles[`badge${cls}`]}`}>
            {CLS_LABEL[cls]}
          </div>
        )}
        {!cls && (
          <div className={`${styles.badge} ${styles.badgeNORMAL}`}>STANDBY</div>
        )}

        {/* Frame / timestamp */}
        <div className={styles.frameInfo}>
          {frame !== null ? (
            <>
              <span className={styles.frameNum}>FRAME {String(frame).padStart(6, '0')}</span>
              <span className={styles.frameSep}>·</span>
              <span className={styles.frameTs}>{ts?.toFixed(2)}s</span>
            </>
          ) : (
            <span className={styles.frameEmpty}>AWAITING FEED</span>
          )}
        </div>
      </div>

      {/* Mini bar chart — last 20 classifications */}
      <div className={styles.chart}>
        <div className={styles.chartLabel}>LAST 20 EVENTS</div>
        <div className={styles.bars}>
          {bars.map((item, i) => (
            <div
              key={i}
              className={`${styles.bar} ${item ? styles[`bar${item.type === 'anomaly_alert' ? 'ANOMALY' : 'NORMAL'}`] : styles.barEmpty}`}
              title={item ? `Frame ${item.frame}` : 'no data'}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
