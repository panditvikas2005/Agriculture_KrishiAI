// api.js — KrishiAI API client
import axios from 'axios'

const BASE = '/api'

const client = axios.create({ baseURL: BASE, timeout: 30000 })

// Attach JWT token to every request
client.interceptors.request.use(cfg => {
  const token = localStorage.getItem('krishi_jwt')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Normalise errors
client.interceptors.response.use(
  r => r.data,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

export const api = {
  // Auth
  register: d => client.post('/auth/register', d),
  login:    d => client.post('/auth/login', d),
  me:       () => client.get('/auth/me'),

  // Chat
  chat:        d => client.post('/chat', d),
  chatHistory: (limit=50) => client.get('/chat/history', { params: { limit } }),

  // Disease
  diseaseText:   d => client.post('/disease/text', d),
  diseasePhoto:  (formData) => client.post('/disease/photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000
  }),
  diseaseHistory:     (limit=20)    => client.get('/disease/history', { params: { limit } }),
  diseaseAlerts:      (district)    => client.get('/disease/nearby-alerts', { params: { district, limit: 5 } }),
  whatsappAlert:      d             => client.post('/alert/whatsapp', d),

  // Info
  weather: (lat, lon, district) => client.get('/weather', { params: { lat, lon, district } }),
  market:  (state)              => client.get('/market',  { params: { state } }),
  schemes: (language)           => client.get('/schemes', { params: { language } }),
  stats:   ()                   => client.get('/stats'),
  health:  ()                   => client.get('/health'),

  // Practical
  soil:       params => client.get('/soil/analyze',          { params }),
  irrigation: d      => client.post('/irrigation/recommend', d),
  fertilizer: d      => client.post('/planner/fertilizer',   d),
  marketPred: d      => client.post('/market/predict',       d),
  profit:     d      => client.post('/profit/calc',          d),
  cropRec:    d      => client.post('/recommend/crop',       d),
}

export default api
