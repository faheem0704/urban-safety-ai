import styles from './TopBar.module.css'

export default function TopBar({ isConnected, gridView, onToggleView, camera = { id: 'CAM-01', location: 'DOWNTOWN' } }) {
  return (
    <header className={styles.bar}>
      {/* Logo */}
      <div className={styles.logo}>
        <span className={styles.logoUrban}>Urban</span>
        <span className={styles.logoSafety}>Safety</span>
        <span className={styles.logoDot}>.AI</span>
      </div>

      {/* Camera tag — changes label in grid view */}
      <div className={styles.camera}>
        {gridView ? (
          <>
            <span className={styles.camId}>GRID</span>
            <span className={styles.sep}>·</span>
            <span className={styles.location}>4 CAMERAS</span>
          </>
        ) : (
          <>
            <span className={styles.camId}>{camera.id}</span>
            <span className={styles.sep}>·</span>
            <span className={styles.location}>{camera.location}</span>
          </>
        )}
      </div>

      <div className={styles.right}>
        {/* View toggle */}
        <button className={styles.viewToggle} onClick={onToggleView}>
          {gridView ? 'SINGLE VIEW' : 'GRID VIEW'}
        </button>

        {/* WS status */}
        <div className={`${styles.pill} ${isConnected ? styles.pillGreen : styles.pillRed}`}>
          <span className={`${styles.dot} ${isConnected ? styles.dotGreen : styles.dotRed}`} />
          {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
        </div>
      </div>
    </header>
  )
}
