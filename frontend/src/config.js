const isProd = window.location.hostname !== 'localhost'

export const API_URL = isProd
  ? 'https://urban-safety-ai-production.up.railway.app'
  : 'http://localhost:8080'

export const WS_URL = isProd
  ? 'wss://urban-safety-ai-production.up.railway.app/ws/live'
  : 'ws://localhost:8080/ws/live'
