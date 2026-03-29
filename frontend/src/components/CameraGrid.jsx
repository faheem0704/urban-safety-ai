import { useEffect, useState } from 'react'
import styles from './CameraGrid.module.css'

const CAMERAS = [
  { id: 'CAM-01', location: 'DOWNTOWN',      interval: 8000, weights: [0.70, 0.20, 0.10] },
  { id: 'CAM-02', location: 'METRO STATION', interval: 5000, weights: [0.20, 0.60, 0.20] },
  { id: 'CAM-03', location: 'CITY PARK',     interval: 6000, weights: [0.40, 0.35, 0.25] },
  // CAM-04 is controlled externally via liveJobStatus / lastAlertCls
  { id: 'CAM-04', location: 'CENTRAL MALL',  interval: null, weights: null },
]

const CLASSES = ['NORMAL', 'SUSPICIOUS', 'ANOMALY']

function pickClass(weights) {
  const r = Math.random()
  if (r < weights[0]) return 'NORMAL'
  if (r < weights[0] + weights[1]) return 'SUSPICIOUS'
  return 'ANOMALY'
}

function CameraTile({ camera, classification, isActive, onClick }) {
  const isAnomaly = classification === 'ANOMALY'
  return (
    <div
      className={`${styles.tile} ${isActive ? styles.tileActive : ''} ${isAnomaly ? styles.tileAnomaly : ''}`}
      onClick={onClick}
    >
      <span className={`${styles.corner} ${styles.tl}`} />
      <span className={`${styles.corner} ${styles.tr}`} />
      <span className={`${styles.corner} ${styles.bl}`} />
      <span className={`${styles.corner} ${styles.br}`} />
      <div className={styles.scanline} />
      {isAnomaly && <span className={styles.alertDot} />}
      <span className={`${styles.badge} ${styles[`badge${classification}`]}`}>
        {classification}
      </span>
      <div className={styles.camLabel}>
        <span className={styles.camId}>{camera.id}</span>
        <span className={styles.camLocation}>{camera.location}</span>
      </div>
    </div>
  )
}

export default function CameraGrid({ isJobProcessing, lastAlertCls, onCameraSelect }) {
  const [active, setActive] = useState('CAM-01')
  const [states, setStates] = useState({
    'CAM-01': 'NORMAL',
    'CAM-02': 'SUSPICIOUS',
    'CAM-03': 'NORMAL',
    'CAM-04': 'NORMAL',
  })

  // Independent timers for CAM-01, CAM-02, CAM-03
  useEffect(() => {
    const timers = CAMERAS.slice(0, 3).map(cam =>
      setInterval(() => {
        setStates(prev => ({ ...prev, [cam.id]: pickClass(cam.weights) }))
      }, cam.interval)
    )
    return () => timers.forEach(clearInterval)
  }, [])

  // CAM-04 mirrors live job: SUSPICIOUS while processing, reflects WS anomaly alerts
  useEffect(() => {
    if (!isJobProcessing) {
      setStates(prev => ({ ...prev, 'CAM-04': 'NORMAL' }))
      return
    }
    if (lastAlertCls) {
      setStates(prev => ({ ...prev, 'CAM-04': lastAlertCls }))
      // After 2s, revert to SUSPICIOUS (job still running)
      const t = setTimeout(() => {
        setStates(prev => ({ ...prev, 'CAM-04': 'SUSPICIOUS' }))
      }, 2000)
      return () => clearTimeout(t)
    } else {
      setStates(prev => ({ ...prev, 'CAM-04': 'SUSPICIOUS' }))
    }
  }, [isJobProcessing, lastAlertCls])

  // Show the blue glow for 300ms before switching to single view
  const handleTileClick = (cam) => {
    setActive(cam.id)
    if (onCameraSelect) {
      setTimeout(() => onCameraSelect(cam), 300)
    }
  }

  return (
    <div className={styles.grid}>
      {CAMERAS.map(cam => (
        <CameraTile
          key={cam.id}
          camera={cam}
          classification={states[cam.id]}
          isActive={active === cam.id}
          onClick={() => handleTileClick(cam)}
        />
      ))}
    </div>
  )
}
