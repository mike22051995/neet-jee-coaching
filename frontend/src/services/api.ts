/**
 * API client — all HTTP calls go through this module.
 * React Query hooks import from here, never from components directly.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  // withCredentials sends the httpOnly admin_token cookie on every request.
  // The JWT lives in the cookie only — never in localStorage — so JavaScript
  // cannot read or steal it via XSS.
  withCredentials: true,
})

// On 401 from admin routes, redirect to login (cookie is gone or expired).
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname.startsWith('/admin')) {
      window.location.href = '/admin/login'
    }
    return Promise.reject(error)
  }
)

// ── Public API ─────────────────────────────────────────────────────────────

export const publicApi = {
  getSettings: () => api.get('/api/public/settings').then(r => r.data),
  getActiveBatch: () => api.get('/api/public/batch/active').then(r => r.data),
  getSchedule: (batchId: string, fromDate?: string, toDate?: string) => {
    const params = new URLSearchParams()
    if (fromDate) params.set('from_date', fromDate)
    if (toDate) params.set('to_date', toDate)
    return api.get(`/api/public/schedule/${batchId}?${params}`).then(r => r.data)
  },
}

// ── Enrollment API ──────────────────────────────────────────────────────────

export const enrollmentApi = {
  createEnrollment: (data: EnrollmentCreateData) =>
    api.post('/api/enrollment/', data).then(r => r.data),

  checkStatus: (reference: string) =>
    api.get(`/api/enrollment/check/${reference}`).then(r => r.data),

  submitPayment: (formData: FormData) =>
    api.post('/api/enrollment/payment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data),
}

// ── Admin API ───────────────────────────────────────────────────────────────

export const adminApi = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }).then(r => r.data),

  logout: () => api.post('/api/auth/logout').then(r => r.data),

  me: () => api.get('/api/auth/me').then(r => r.data),

  getDashboardStats: () => api.get('/api/admin/dashboard/stats').then(r => r.data),

  // Batches
  listBatches: () => api.get('/api/admin/batches').then(r => r.data),
  createBatch: (data: unknown) => api.post('/api/admin/batches', data).then(r => r.data),
  updateBatch: (id: string, data: unknown) => api.patch(`/api/admin/batches/${id}`, data).then(r => r.data),
  getBatch: (id: string) => api.get(`/api/admin/batches/${id}`).then(r => r.data),

  // Schedule
  getSchedule: (batchId: string) => api.get(`/api/admin/batches/${batchId}/schedule`).then(r => r.data),
  upsertSession: (batchId: string, data: unknown) =>
    api.post(`/api/admin/batches/${batchId}/schedule`, data).then(r => r.data),

  // Enrollments
  listEnrollments: (params?: Record<string, string | number>) =>
    api.get('/api/admin/enrollments', { params }).then(r => r.data),
  updateEnrollmentStatus: (id: string, status: string, notes?: string) =>
    api.patch(`/api/admin/enrollments/${id}/status`, null, {
      params: { new_status: status, admin_notes: notes },
    }).then(r => r.data),

  // Payments
  listPendingPayments: () => api.get('/api/admin/payments/pending').then(r => r.data),
  reviewPayment: (id: string, action: 'verify' | 'reject', rejectionReason?: string) =>
    api.post(`/api/admin/payments/${id}/review`, { action, rejection_reason: rejectionReason }).then(r => r.data),

  // Settings
  getSettings: () => api.get('/api/admin/settings').then(r => r.data),
  updateSettings: (data: unknown) => api.patch('/api/admin/settings', data).then(r => r.data),
  uploadLogo: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/api/admin/settings/logo', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
  },
  uploadQR: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/api/admin/settings/qr', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
  },
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface EnrollmentCreateData {
  batch_id: string
  student_name: string
  email: string
  phone: string
  grade: string
  exam_preference: 'neet' | 'jee'
  guardian_name?: string
  guardian_phone?: string
  privacy_acknowledged: boolean
}

export interface SiteSettings {
  institute_name: string
  tagline?: string
  contact_email?: string
  contact_phone?: string
  contact_address?: string
  hero_heading?: string
  hero_subheading?: string
  about_text?: string
  why_choose_us_json?: string
  faculty_json?: string
  faq_json?: string
  enrollment_instructions?: string
  upi_id?: string
  upi_name?: string
  upi_qr_path?: string
  payment_instructions?: string
  logo_path?: string
  social_whatsapp?: string
  social_telegram?: string
  social_youtube?: string
}

export interface Batch {
  id: string
  name: string
  exam_type: string
  academic_year: string
  description?: string
  start_date?: string
  end_date?: string
  enrollment_opens_at?: string
  enrollment_closes_at?: string
  class_days?: string[]
  class_start_time?: string
  class_end_time?: string
  classes_per_week?: number
  subjects?: string[]
  syllabus?: string
  eligibility?: string
  fee_amount?: number
  total_seats?: number
  status: string
  is_published: boolean
  platform?: string
  confirmed_enrollment_count: number
  available_seats?: number
}

export interface Enrollment {
  id: string
  reference: string
  student_name: string
  email: string
  phone: string
  grade: string
  exam_preference: string
  batch_id: string
  status: string
  created_at: string
  guardian_name?: string
  guardian_phone?: string
  admin_notes?: string
}

export interface PaymentSubmission {
  id: string
  enrollment_id: string
  transaction_ref: string
  payment_date?: string
  amount_claimed?: number
  status: string
  reviewed_at?: string
  rejection_reason?: string
  created_at: string
}
