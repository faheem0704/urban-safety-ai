import { useEffect, useRef, useState, useCallback } from 'react'

// Use window.location.host so this works on any Vite port (5173, 5174, etc.)
// Vite's /ws proxy forwards this to ws://localhost:8080/ws/live
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const WS_URL = `${protocol}//${window.location.host}/ws/live`
const MAX_ALERTS = 50
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const [alerts, setAlerts]           = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [lastAlert, setLastAlert]     = useState(null)
  const wsRef      = useRef(null)
  const timerRef   = useRef(null)
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) return
      setIsConnected(true)
      clearTimeout(timerRef.current)
    }

    ws.onmessage = (e) => {
      if (!mountedRef.current) return
      try {
        const msg = JSON.parse(e.data)
        const alert = { ...msg, id: Date.now() + Math.random(), receivedAt: new Date() }
        setLastAlert(alert)
        setAlerts(prev => [alert, ...prev].slice(0, MAX_ALERTS))
      } catch { /* ignore malformed */ }
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      setIsConnected(false)
      // Auto-reconnect after delay
      timerRef.current = setTimeout(connect, RECONNECT_DELAY)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimeout(timerRef.current)
      if (wsRef.current && wsRef.current.readyState !== WebSocket.CONNECTING) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { alerts, isConnected, lastAlert }
}
