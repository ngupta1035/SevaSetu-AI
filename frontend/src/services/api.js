import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Turn FastAPI error payloads into a readable string.
export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (!d) return err?.message || 'Something went wrong'
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => `${(e.loc || []).slice(-1)[0]}: ${e.msg}`).join('; ')
  return 'Request failed'
}

export const authApi = {
  register: (data) => api.post('/auth/register', data).then((r) => r.data),
  login: (email, password) =>
    api
      .post('/auth/login', new URLSearchParams({ username: email, password }))
      .then((r) => r.data),
}

export const issuesApi = {
  create: (formData) => api.post('/issues', formData).then((r) => r.data),
  mine: () => api.get('/issues/my').then((r) => r.data),
  get: (id) => api.get(`/issues/${id}`).then((r) => r.data),
}

export const adminApi = {
  departments: () => api.get('/admin/departments').then((r) => r.data),
  map: (params) => api.get('/admin/map', { params }).then((r) => r.data),
  analytics: (days = 14) => api.get('/admin/analytics', { params: { days } }).then((r) => r.data),
  resolve: (id, { notes, file }) => {
    const fd = new FormData()
    if (notes) fd.append('notes', notes)
    if (file) fd.append('after_image', file)
    return api.post(`/admin/issues/${id}/resolve`, fd).then((r) => r.data)
  },
  verify: (id, approved, comment) => api.post(`/admin/issues/${id}/verify`, { approved, comment: comment || null }).then((r) => r.data),
  dashboard: () => api.get('/admin/dashboard').then((r) => r.data),
  issues: (params) => api.get('/admin/issues', { params }).then((r) => r.data),
  assign: (id, body) => api.patch(`/admin/issues/${id}/assign`, body).then((r) => r.data),
  setStatus: (id, body) => api.patch(`/admin/issues/${id}/status`, body).then((r) => r.data),
  reviewDuplicate: (id, action) => api.post(`/admin/duplicates/${id}/${action}`).then((r) => r.data),
}

export const aiApi = {
  status: () => api.get('/ai/status').then((r) => r.data),
  analyze: (file) => {
    const fd = new FormData()
    fd.append('image', file)
    return api.post('/ai/analyze', fd).then((r) => r.data)
  },
}

export default api
