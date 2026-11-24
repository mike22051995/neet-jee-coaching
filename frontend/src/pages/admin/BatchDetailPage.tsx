import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Calendar, AlertTriangle, CheckCircle } from 'lucide-react'
import { adminApi } from '@/services/api'
import { StatusBadge } from '@/components/common/StatusBadge'
import { format, addDays, startOfWeek } from 'date-fns'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export function BatchDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [saved, setSaved] = useState(false)
  const [scheduleDate, setScheduleDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [sessionForm, setSessionForm] = useState({
    subject: '', notice: '', is_cancelled: false,
  })

  const { data: batch, isLoading } = useQuery({
    queryKey: ['admin-batch', id],
    queryFn: () => adminApi.getBatch(id!),
    enabled: !!id,
  })

  const { data: sessions = [] } = useQuery({
    queryKey: ['admin-schedule', id],
    queryFn: () => adminApi.getSchedule(id!),
    enabled: !!id,
  })

  const [form, setForm] = useState<Record<string, any>>({})
  const f = (key: string) => (key in form ? form[key] : (batch as any)?.[key] ?? '')
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, any>) => adminApi.updateBatch(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-batch', id] })
      qc.invalidateQueries({ queryKey: ['admin-batches'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    },
  })

  const sessionMutation = useMutation({
    mutationFn: (data: any) => adminApi.upsertSession(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-schedule', id] })
      setSessionForm({ subject: '', notice: '', is_cancelled: false })
    },
  })

  const handleSave = () => {
    const data: Record<string, any> = { ...form }
    // coerce numeric fee
    if (data.fee_amount) data.fee_amount = parseFloat(data.fee_amount)
    if (data.total_seats) data.total_seats = parseInt(data.total_seats)
    updateMutation.mutate(data)
  }

  if (isLoading || !batch) return <div className="text-center py-10 text-gray-400">Loading batch...</div>

  const b = batch as any

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/admin/batches')} className="text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-xl font-display font-bold text-navy-900 flex items-center gap-2 flex-wrap">
          {b.name} <StatusBadge status={b.status} />
        </h1>
      </div>

      {/* Batch Edit Form */}
      <div className="card mb-6">
        <h2 className="font-semibold text-navy-900 mb-4 pb-2 border-b text-sm">Batch Details</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Batch Name">
            <input defaultValue={b.name} onBlur={set('name')} className="input-field" />
          </Field>
          <Field label="Academic Year">
            <input defaultValue={b.academic_year} onBlur={set('academic_year')} className="input-field" />
          </Field>
          <Field label="Exam Type">
            <select defaultValue={b.exam_type} onChange={set('exam_type')} className="input-field">
              <option value="neet">NEET</option>
              <option value="jee">JEE</option>
              <option value="both">Both</option>
            </select>
          </Field>
          <Field label="Fee Amount (₹)">
            <input type="number" defaultValue={b.fee_amount} onBlur={set('fee_amount')} className="input-field" />
          </Field>
          <Field label="Total Seats">
            <input type="number" defaultValue={b.total_seats} onBlur={set('total_seats')} className="input-field" />
          </Field>
          <Field label="Start Date">
            <input type="date" defaultValue={b.start_date?.slice(0, 10)} onChange={set('start_date')} className="input-field" />
          </Field>
          <Field label="End Date">
            <input type="date" defaultValue={b.end_date?.slice(0, 10)} onChange={set('end_date')} className="input-field" />
          </Field>
          <Field label="Enrollment Opens">
            <input type="date" defaultValue={b.enrollment_start_date?.slice(0, 10)} onChange={set('enrollment_start_date')} className="input-field" />
          </Field>
          <Field label="Enrollment Closes">
            <input type="date" defaultValue={b.enrollment_end_date?.slice(0, 10)} onChange={set('enrollment_end_date')} className="input-field" />
          </Field>
          <Field label="Class Start Time">
            <input type="time" defaultValue={b.class_start_time} onChange={set('class_start_time')} className="input-field" />
          </Field>
          <Field label="Class End Time">
            <input type="time" defaultValue={b.class_end_time} onChange={set('class_end_time')} className="input-field" />
          </Field>
          <Field label="Published">
            <select defaultValue={b.is_published ? '1' : '0'} onChange={e => setForm(p => ({ ...p, is_published: e.target.value === '1' }))} className="input-field">
              <option value="1">Yes — visible to students</option>
              <option value="0">No — hidden</option>
            </select>
          </Field>
        </div>
        <div className="mt-4">
          <Field label="Description">
            <textarea defaultValue={b.description} onBlur={set('description')} rows={3} className="input-field" />
          </Field>
        </div>
        <div className="mt-4">
          <Field label="Eligibility">
            <input defaultValue={b.eligibility} onBlur={set('eligibility')} className="input-field" />
          </Field>
        </div>

        <div className="flex gap-3 mt-4">
          <button onClick={handleSave} disabled={updateMutation.isPending} className="btn-primary text-sm flex items-center gap-2">
            <Save className="h-4 w-4" />
            {updateMutation.isPending ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}
          </button>
          {updateMutation.isError && (
            <span className="text-sm text-red-600 self-center">
              {(updateMutation.error as any)?.response?.data?.detail || 'Save failed'}
            </span>
          )}
        </div>
      </div>

      {/* Schedule Management */}
      <div className="card">
        <h2 className="font-semibold text-navy-900 mb-4 pb-2 border-b text-sm flex items-center gap-2">
          <Calendar className="h-4 w-4" /> Schedule Override
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          Use this to mark a specific class as cancelled or rescheduled, or add a notice.
          Leave the date blank for a regular class day.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <Field label="Session Date">
            <input
              type="date"
              value={scheduleDate}
              onChange={e => setScheduleDate(e.target.value)}
              className="input-field"
            />
          </Field>
          <Field label="Subject">
            <input
              value={sessionForm.subject}
              onChange={e => setSessionForm(p => ({ ...p, subject: e.target.value }))}
              className="input-field"
              placeholder="e.g. Physics"
            />
          </Field>
          <Field label="Status">
            <select
              value={sessionForm.is_cancelled ? 'cancelled' : 'regular'}
              onChange={e => setSessionForm(p => ({ ...p, is_cancelled: e.target.value === 'cancelled' }))}
              className="input-field"
            >
              <option value="regular">Regular</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </Field>
        </div>
        <div className="mb-3">
          <Field label="Notice / Announcement">
            <input
              value={sessionForm.notice}
              onChange={e => setSessionForm(p => ({ ...p, notice: e.target.value }))}
              className="input-field"
              placeholder="Optional notice shown to students"
            />
          </Field>
        </div>
        <button
          onClick={() => sessionMutation.mutate({ session_date: scheduleDate, ...sessionForm })}
          disabled={!scheduleDate || sessionMutation.isPending}
          className="btn-secondary text-sm flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          {sessionMutation.isPending ? 'Saving...' : 'Save Session Override'}
        </button>

        {/* Recent sessions */}
        {(sessions as any[]).length > 0 && (
          <div className="mt-6">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Session Overrides</h3>
            <div className="space-y-2">
              {(sessions as any[]).slice(0, 10).map((s: any) => (
                <div key={s.id} className="flex items-center gap-3 text-sm p-2 rounded-lg bg-gray-50">
                  {s.is_cancelled ? (
                    <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                  )}
                  <span className="font-medium">{format(new Date(s.session_date), 'd MMM yyyy')}</span>
                  {s.subject && <span className="text-gray-500">{s.subject}</span>}
                  {s.is_cancelled && <span className="badge badge-red text-xs">Cancelled</span>}
                  {s.notice && <span className="text-gray-400 text-xs truncate">{s.notice}</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
