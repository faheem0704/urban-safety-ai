import { useState } from 'react'
import './styles/globals.css'
import { useWebSocket }    from './hooks/useWebSocket'
import TopBar              from './components/TopBar'
import StatCards           from './components/StatCards'
import LiveFeed            from './components/LiveFeed'
import CameraGrid          from './components/CameraGrid'
import AlertTimeline       from './components/AlertTimeline'
import UploadPanel         from './components/UploadPanel'
import AnalyticsPanel      from './components/AnalyticsPanel'
import AnomalyAlert        from './components/AnomalyAlert'
import IncidentModal       from './components/IncidentModal'

export default function App() {
  const { alerts, isConnected, lastAlert } = useWebSocket()

  // Grid / single view toggle + selected camera
  const [gridView, setGridView]           = useState(false)
  const [selectedCamera, setSelectedCamera] = useState({ id: 'CAM-01', location: 'DOWNTOWN' })

  const handleCameraSelect = (cam) => {
    setSelectedCamera({ id: cam.id, location: cam.location })
    setGridView(false)
  }

  // Job state lifted from UploadPanel: {status, summary, jobId}
  const [liveJob, setLiveJob] = useState({ status: null, summary: null, jobId: null })

  // Incident modal
  const [selectedEvent, setSelectedEvent] = useState(null)

  // Last 20 WS events for LiveFeed mini bar chart
  const recent20 = alerts.slice(0, 20)

  const isProcessing  = liveJob.status === 'pending' || liveJob.status === 'processing'
  const statSummary   = liveJob.status === 'complete' ? liveJob.summary : null

  // Single object passed to AnalyticsPanel — null until a job completes
  const completedJob  = liveJob.status === 'complete'
    ? { jobId: liveJob.jobId, summary: liveJob.summary }
    : null

  // For CAM-04: derive live classification from last WS alert during processing
  const liveAlertCls = isProcessing && lastAlert
    ? (lastAlert.type === 'anomaly_alert' ? 'ANOMALY' : 'NORMAL')
    : null

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100vh', background: 'var(--bg-primary)',
    }}>
      <TopBar
        isConnected={isConnected}
        gridView={gridView}
        onToggleView={() => setGridView(v => !v)}
        camera={selectedCamera}
      />

      <div style={{
        flex: 1, overflow: 'auto', padding: '16px 20px',
        display: 'flex', flexDirection: 'column', gap: '16px',
      }}>
        {/* ── 2-col grid: feed (left) + timeline (right) ── */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 380px',
          gap: '16px', flex: '0 0 auto',
        }}>
          {/* Left: camera grid or single live feed */}
          {gridView ? (
            <CameraGrid
              isJobProcessing={isProcessing}
              lastAlertCls={liveAlertCls}
              onCameraSelect={handleCameraSelect}
            />
          ) : (
            <LiveFeed lastAlert={lastAlert} recentFrames={recent20} camera={selectedCamera} />
          )}

          {/* Right: alert timeline — clickable rows open incident modal */}
          <div style={{ height: '320px' }}>
            <AlertTimeline alerts={alerts} onEventClick={setSelectedEvent} />
          </div>
        </div>

        {/* ── Stat cards ── */}
        <StatCards summary={statSummary} isProcessing={isProcessing} />

        {/* ── Upload panel ── */}
        <div style={{
          minHeight: '200px',
          border: '2px dashed rgba(59,130,246,0.5)',
          borderRadius: '8px',
          overflow: 'hidden',
        }}>
          <UploadPanel onJobUpdate={setLiveJob} />
        </div>

        {/* ── Analytics panel — always renders; shows empty state until job completes ── */}
        <AnalyticsPanel job={completedJob} />
      </div>

      {/* Toast portal */}
      <AnomalyAlert lastAlert={lastAlert} />

      {/* Incident modal */}
      {selectedEvent && (
        <IncidentModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  )
}
