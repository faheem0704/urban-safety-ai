export const API_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost'
    ? 'http://localhost:8080'
    : 'https://urban-safety-ai-production.up.railway.app')

export const WS_URL = import.meta.env.VITE_WS_URL ||
  (window.location.hostname === 'localhost'
    ? 'ws://localhost:8080/ws/live'
    : 'wss://urban-safety-ai-production.up.railway.app/ws/live')
