import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts'
import axios from 'axios'
import { API_URL } from '../config'
import styles from './AnalyticsPanel.module.css'

const PIE_COLORS = ['#4ade80', '#fbbf24', '#f87171']

function buildSegments(events, totalDuration) {
  if (!events.length || !totalDuration) return []
  const sorted = [...events].sort((a, b) => a.frame_number - b.frame_number)
  const segs = []
  let cur = { cls: sorted[0].classification, start: sorted[0].timestamp_sec, end: sorted[0].timestamp_sec }
  for (let i = 1; i < sorted.length; i++) {
    const e = sorted[i]
    if (e.classification === cur.cls) { cur.end = e.timestamp_sec }
    else { segs.push({ ...cur }); cur = { cls: e.classification, start: e.timestamp_sec, end: e.timestamp_sec } }
  }
  segs.push({ ...cur, end: totalDuration })
  return segs.map(s => ({ ...s, dur: Math.max(s.end - s.start, 0.01) }))
}

function computeMetrics(events) {
  if (!events.length) return { peak: null, firstAnomalyAt: null, longestNormal: null }
  const peak = Math.max(...events.map(e => e.anomaly_score ?? 0))
  const anomalyEvents = events.filter(e => e.classification === 'ANOMALY')
  const firstAnomalyAt = anomalyEvents.length
    ? Math.min(...anomalyEvents.map(e => e.timestamp_sec))
    : null
  const sorted = [...events].sort((a, b) => a.frame_number - b.frame_number)
  let maxStreak = 0, streak = 0, streakStart = null, bestStart = null, bestEnd = null
  for (const e of sorted) {
    if (e.classification === 'NORMAL') {
      if (streak === 0) streakStart = e.timestamp_sec
      streak++
      if (streak > maxStreak) { maxStreak = streak; bestStart = streakStart; bestEnd = e.timestamp_sec }
    } else { streak = 0 }
  }
  return { peak, firstAnomalyAt, longestNormal: bestEnd !== null ? bestEnd - bestStart : null }
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div style={{ background: '#0d1220', border: '1px solid #1e2840', borderRadius: 6, padding: '6px 10px', fontSize: 11 }}>
      <span style={{ color: '#94a3b8' }}>{name}: </span>
      <span style={{ color: '#e2e8f0', fontWeight: 700 }}>{value} frames</span>
    </div>
  )
}

function renderPieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.04) return null
  const R = Math.PI / 180
  const r = innerRadius + (outerRadius - innerRadius) * 0.55
  const x = cx + r * Math.cos(-midAngle * R)
  const y = cy + r * Math.sin(-midAngle * R)
  return (
    <text x={x} y={y} fill="#e2e8f0" textAnchor="middle" dominantBaseline="central"
      fontSize={10} fontWeight={700} fontFamily="'JetBrains Mono', monospace">
      {`${(percent * 100).toFixed(1)}%`}
    </text>
  )
}

// Outer shell — always visible so the section is obvious on scroll
const SHELL = {
  width: '100%',
  padding: '2rem',
  borderTop: '1px solid #1e2840',
  background: '#0a0e1a',
}
const HEADING = {
  fontSize: '11px',
  letterSpacing: '0.1em',
  color: '#4a5568',
  marginBottom: '1.5rem',
  fontFamily: "'JetBrains Mono', monospace",
  fontWeight: 700,
}

export default function AnalyticsPanel({ job }) {
  const jobId   = job?.jobId   ?? null
  const summary = job?.summary ?? null

  const [events,  setEvents]  = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!jobId) { setEvents([]); return }
    setLoading(true)
    axios.get(`${API_URL}/api/jobs/${jobId}/events`)
      .then(r => setEvents(r.data))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false))
  }, [jobId])

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!job) {
    return (
      <div style={SHELL}>
        <div style={HEADING}>ANALYTICS</div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', padding: '24px 0' }}>
          <span style={{ fontSize: '28px', color: '#94a3b8', opacity: 0.5 }}>◈</span>
          <span style={{ fontSize: '12px', fontWeight: 700, color: '#94a3b8', letterSpacing: '1.5px', fontFamily: "'JetBrains Mono', monospace" }}>
            UPLOAD A VIDEO TO SEE ANALYTICS
          </span>
        </div>
      </div>
    )
  }

  // ── Loading state ────────────────────────────────────────────────────────
  if (loading && !events.length) {
    return (
      <div style={SHELL}>
        <div style={HEADING}>ANALYTICS</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 0' }}>
          <span style={{ fontSize: '12px', color: '#4a5568', letterSpacing: '1.5px' }}>LOADING…</span>
        </div>
      </div>
    )
  }

  // ── Charts ───────────────────────────────────────────────────────────────
  const total    = (summary?.normal_count ?? 0) + (summary?.suspicious_count ?? 0) + (summary?.anomaly_count ?? 0)
  const duration = summary?.duration_sec ?? 0

  const pieData = [
    { name: 'NORMAL',     value: summary?.normal_count     ?? 0 },
    { name: 'SUSPICIOUS', value: summary?.suspicious_count ?? 0 },
    { name: 'ANOMALY',    value: summary?.anomaly_count    ?? 0 },
  ].filter(d => d.value > 0)

  const segments    = buildSegments(events, duration)
  const totalSegDur = segments.reduce((s, seg) => s + seg.dur, 0) || 1
  const { peak, firstAnomalyAt, longestNormal } = computeMetrics(events)
  const axisTicks   = [0, 0.25, 0.5, 0.75, 1].map(f => `${(f * duration).toFixed(1)}s`)
  const segClass    = { NORMAL: styles.segNORMAL, SUSPICIOUS: styles.segSUSPICIOUS, ANOMALY: styles.segANOMALY }

  return (
    <div style={SHELL}>
      <div style={HEADING}>ANALYTICS</div>

      <div className={styles.charts}>

        {/* ── Donut chart — explicit height wrapper fixes Recharts -1px bug ── */}
        <div>
          <div style={{ width: '100%', minWidth: '300px', height: '280px', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={70} outerRadius={110}
                  dataKey="value"
                  label={renderPieLabel}
                  labelLine={false}
                  strokeWidth={0}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={PIE_COLORS[['NORMAL','SUSPICIOUS','ANOMALY'].indexOf(entry.name)]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Centre overlay — positioned over the SVG */}
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              pointerEvents: 'none',
            }}>
              <span style={{ fontSize: '24px', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", color: '#e2e8f0' }}>{total}</span>
              <span style={{ fontSize: '9px', letterSpacing: '1.5px', color: '#4a5568', marginTop: 2 }}>FRAMES</span>
            </div>
          </div>

          <div className={styles.donutLegend}>
            {[['NORMAL', '#4ade80'], ['SUSPICIOUS', '#fbbf24'], ['ANOMALY', '#f87171']].map(([name, color]) => (
              <div key={name} className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: color }} />
                {name}
              </div>
            ))}
          </div>
        </div>

        {/* ── Timeline bar ── */}
        <div className={styles.timelineWrap}>
          <span className={styles.timelineLabel}>CLASSIFICATION TIMELINE</span>
          <div className={styles.timelineBar}>
            {segments.map((seg, i) => (
              <div
                key={`${i}-${seg.cls}-${seg.start.toFixed(4)}`}
                className={`${styles.timelineSegment} ${segClass[seg.cls]}`}
                style={{ flex: seg.dur / totalSegDur }}
                title={`${seg.cls} · ${seg.start.toFixed(1)}s–${seg.end.toFixed(1)}s`}
              />
            ))}
          </div>
          <div className={styles.timelineAxis}>
            {axisTicks.map((t, i) => <span key={i}>{t}</span>)}
          </div>
        </div>
      </div>

      {/* ── Metric cards ── */}
      <div className={styles.metrics} style={{ marginTop: '20px' }}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>PEAK ANOMALY SCORE</div>
          <div className={styles.metricValue} style={{ color: '#f87171' }}>
            {peak !== null ? peak.toFixed(3) : '—'}
          </div>
          <div className={styles.metricSub}>highest single-frame score</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>LONGEST NORMAL STREAK</div>
          <div className={styles.metricValue} style={{ color: '#4ade80' }}>
            {longestNormal !== null ? `${longestNormal.toFixed(1)}s` : '—'}
          </div>
          <div className={styles.metricSub}>consecutive normal frames</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>FIRST ANOMALY AT</div>
          <div className={styles.metricValue} style={{ color: '#fbbf24' }}>
            {firstAnomalyAt !== null ? `${firstAnomalyAt.toFixed(2)}s` : '—'}
          </div>
          <div className={styles.metricSub}>into the recording</div>
        </div>
      </div>

    </div>
  )
}
