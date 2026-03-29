import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { API_URL } from '../config'

const POLL_INTERVAL = 2000
const TERMINAL = new Set(['complete', 'failed'])

export function useJobPoller(jobId) {
  const [job, setJob]           = useState(null)
  const [summary, setSummary]   = useState(null)
  const [isPolling, setPolling] = useState(false)
  const [error, setError]       = useState(null)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    let active = true
    setPolling(true)
    setError(null)

    const poll = async () => {
      if (!active) return
      try {
        const { data } = await axios.get(`${API_URL}/api/jobs/${jobId}`)
        if (!active) return
        setJob(data.job)
        setSummary(data.summary)
        if (TERMINAL.has(data.job?.status)) {
          setPolling(false)
          // One final re-fetch 500ms later — ensures the backend has finished
          // writing all events before we lock in the definitive summary numbers
          if (data.job.status === 'complete') {
            setTimeout(async () => {
              if (!active) return
              try {
                const { data: fin } = await axios.get(`${API_URL}/api/jobs/${jobId}`)
                if (active) { setJob(fin.job); setSummary(fin.summary) }
              } catch { /* best-effort, ignore */ }
            }, 500)
          }
          return
        }
      } catch (err) {
        if (!active) return
        setError(err.message)
      }
      timerRef.current = setTimeout(poll, POLL_INTERVAL)
    }

    poll()

    return () => {
      active = false
      clearTimeout(timerRef.current)
      setPolling(false)
    }
  }, [jobId])

  return { job, summary, isPolling, error }
}
