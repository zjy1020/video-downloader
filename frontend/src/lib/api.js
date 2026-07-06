const isTauri = typeof window !== 'undefined' && window.__TAURI_INTERNALS__
export const API_BASE = isTauri ? 'http://127.0.0.1:8000' : '/api'
