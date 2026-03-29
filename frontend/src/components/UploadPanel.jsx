import { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { useJobPoller } from '../hooks/useJobPoller'
import styles from './UploadPanel.module.css'

// Explicit MIME types per extension — Windows can report different MIME types
// than the wildcard 'video/*' catches, causing silent rejection in react-dropzone v14+
const ACCEPT = {
  'video/mp4':        ['.mp4'],
  'video/quicktime':  ['.mov'],
  'video/avi':        ['.avi'],
  'video/x-msvideo':  ['.avi'],
  'video/msvideo':    ['.avi'],
  'video/x-matroska': ['.mkv'],
  'video/*':          ['.mp4', '.avi', '.mov', '.mkv'],
}

function SummaryGrid({ summary }) {
  if (!summary) return null
  const dur = summary.duration_sec?.toFixed(1) ?? '—'
  const ts  = summary.anomaly_timestamps ?? []

  return (
    <div className={styles.summaryGrid}>
      <div className={styles.sumCard}>
        <div className={styles.sumLabel}>DURATION</div>
        <div className={styles.sumValue}>{dur}s</div>
      </div>
      <div className={styles.sumCard}>
        <div className={styles.sumLabel}>NORMAL</div>
        <div className={`${styles.sumValue} ${styles.green}`}>{summary.normal_count}</div>
      </div>
      <div className={styles.sumCard}>
        <div className={styles.sumLabel}>SUSPICIOUS</div>
        <div className={`${styles.sumValue} ${styles.yellow}`}>{summary.suspicious_count}</div>
      </div>
      <div className={styles.sumCard}>
        <div className={styles.sumLabel}>ANOMALY</div>
        <div className={`${styles.sumValue} ${styles.red}`}>{summary.anomaly_count} ({summary.anomaly_percentage}%)</div>
      </div>
      {ts.length > 0 && (
        <div className={`${styles.sumCard} ${styles.sumCardWide}`}>
          <div className={styles.sumLabel}>ANOMALY WINDOWS</div>
          <div className={styles.sumValue}>
            {ts.map((t, i) => (
              <span key={i} className={styles.tsRange}>{t.start.toFixed(1)}s–{t.end.toFixed(1)}s</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Pure display — receives job/summary/isPolling as props (state lives in UploadPanel)
function JobStatus({ jobId, job, summary, isPolling }) {
  const status = job?.status ?? 'pending'

  return (
    <div className={styles.jobStatus}>
      <div className={styles.jobHeader}>
        <span className={styles.jobId}>JOB #{jobId}</span>
        <span className={`${styles.badge} ${styles[`badge_${status}`]}`}>
          {status.toUpperCase()}
        </span>
      </div>

      {isPolling && status !== 'complete' && (
        <div className={styles.processing}>
          <span className={styles.spinner} />
          <span>Analysing frames&hellip;</span>
          {job && <span className={styles.frameCount}>{job.total_frames ? `${job.total_frames} frames` : ''}</span>}
        </div>
      )}

      {status === 'complete' && <SummaryGrid summary={summary} />}
      {status === 'failed'   && <div className={styles.failed}>Pipeline failed. Check server logs.</div>}
    </div>
  )
}

export default function UploadPanel({ onJobUpdate }) {
  const [jobId,    setJobId]    = useState(null)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [uploadErr, setUploadErr] = useState(null)

  // useJobPoller lives here so App can receive status/summary via onJobUpdate
  const { job, summary, isPolling } = useJobPoller(jobId)

  useEffect(() => {
    if (!onJobUpdate) return
    onJobUpdate({ status: job?.status ?? null, summary, jobId })
  }, [job?.status, summary, jobId, onJobUpdate])

  const onDrop = useCallback(async (acceptedFiles) => {
    console.log('onDrop fired', acceptedFiles)
    if (!acceptedFiles.length) return
    const file = acceptedFiles[0]

    setUploading(true)
    setUploadErr(null)
    setProgress(0)
    setJobId(null)

    const form = new FormData()
    form.append('file', file)

    try {
      console.log('uploading file:', file.name)
      const { data } = await axios.post('/api/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          setProgress(Math.round((e.loaded / e.total) * 100))
        },
      })
      console.log('job created:', data)
      setJobId(data.job_id)
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message
      console.error('upload error:', err.response?.status, msg)
      setUploadErr(msg)
    } finally {
      setUploading(false)
    }
  }, [])

  const onDropRejected = useCallback((rejections) => {
    console.warn('files rejected by dropzone:', rejections.map(r => ({
      name: r.file.name,
      type: r.file.type,
      errors: r.errors.map(e => e.code),
    })))
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, onDropRejected, accept: ACCEPT, multiple: false, disabled: uploading,
  })

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>VIDEO UPLOAD</span>
        <span className={styles.panelSub}>Drop an MP4, AVI or MOV to analyse</span>
      </div>

      <div className={styles.body}>
        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`${styles.drop} ${isDragActive ? styles.dropActive : ''} ${uploading ? styles.dropDisabled : ''}`}
        >
          <input {...getInputProps()} />
          <div className={styles.dropIcon}>⬆</div>
          {isDragActive
            ? <p className={styles.dropText}>Release to upload…</p>
            : <p className={styles.dropText}>Drag &amp; drop a video file here, or <span className={styles.link}>browse</span></p>
          }
          <p className={styles.dropHint}>.mp4 · .avi · .mov</p>
        </div>

        {/* Upload progress */}
        {uploading && (
          <div className={styles.progressWrap}>
            <div className={styles.progressBar} style={{ width: `${progress}%` }} />
            <span className={styles.progressLabel}>{progress}%</span>
          </div>
        )}

        {uploadErr && <div className={styles.error}>{uploadErr}</div>}

        {/* Job polling */}
        {jobId && <JobStatus jobId={jobId} job={job} summary={summary} isPolling={isPolling} />}
      </div>
    </div>
  )
}
