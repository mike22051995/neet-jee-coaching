import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit, Calendar, ChevronDown } from 'lucide-react'
import { adminApi, Batch } from '@/services/api'
import { StatusBadge } from '@/components/common/StatusBadge'

const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['upcoming', 'archived'],
  upcoming: ['enrollment_open', 'archived'],
  enrollment_open: ['running', 'archived'],
  running: ['completed', 'archived'],
  completed: ['archived'],
}

function BatchCard({ batch, onStatusChange }: { batch: Batch; onStatusChange: (id: string, status: string) => void }) {
  const transitions = STATUS_TRANSITIONS[batch.status] || []

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-display font-semibold text-navy-900">{batch.name}</h3>
            <StatusBadge status={batch.status} />
            {batch.is_published && <span className="badge badge-green">Published</span>}
          </div>
          <p className="text-sm text-gray-500">AY: {batch.academic_year} · {batch.exam_type.toUpperCase()}</p>
          {batch.fee_amount && (
            <p className="text-sm font-medium text-navy-700 mt-1">
              ₹{batch.fee_amount.toLocaleString('en-IN')}
            </p>
          )}
          {batch.start_date && (
            <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Starts {new Date(batch.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            </p>
          )}
          <p className="text-xs text-gray-500 mt-1">{batch.confirmed_enrollment_count} confirmed enrollments</p>
        </div>
        <div className="flex flex-col gap-2 items-end">
          {transitions.length > 0 && (
            <select
              className="text-xs border rounded px-2 py-1 text-gray-600"
              value=""
              onChange={e => { if (e.target.value) onStatusChange(batch.id, e.target.value) }}
            >
              <option value="">Change status…</option>
              {transitions.map(s => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          )}
          <button
            className="text-xs text-navy-600 hover:underline flex items-center gap-1"
            onClick={() => window.location.href = `/admin/batches/${batch.id}`}
          >
            <Edit className="h-3 w-3" /> Edit
          </button>
        </div>
      </div>
    </div>
  )
}

export function BatchesPage() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', exam_type: 'neet', academic_year: '', fee_amount: '' })

  const { data: batches = [], isLoading } = useQuery({
    queryKey: ['admin-batches'],
    queryFn: adminApi.listBatches,
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => adminApi.createBatch({
      ...data,
      fee_amount: data.fee_amount ? parseFloat(data.fee_amount) : undefined,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-batches'] }); setShowForm(false) },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminApi.updateBatch(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-batches'] }),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-bold text-navy-900">Batches</h1>
        <button onClick={() => setShowForm(o => !o)} className="btn-primary text-sm px-4 py-2">
          <Plus className="h-4 w-4" /> New Batch
        </button>
      </div>

      {showForm && (
        <div className="card mb-6 border-navy-200">
          <h2 className="font-semibold text-navy-900 mb-4">Create New Batch</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Batch Name</label>
              <input value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} className="input-field" placeholder="e.g. NEET 2027 Batch" />
            </div>
            <div>
              <label className="label">Exam Type</label>
              <select value={form.exam_type} onChange={e => setForm(f => ({...f, exam_type: e.target.value}))} className="input-field">
                <option value="neet">NEET</option>
                <option value="jee">JEE</option>
                <option value="both">Both</option>
              </select>
            </div>
            <div>
              <label className="label">Academic Year</label>
              <input value={form.academic_year} onChange={e => setForm(f => ({...f, academic_year: e.target.value}))} className="input-field" placeholder="e.g. 2026-27" />
            </div>
            <div>
              <label className="label">Fee Amount (₹)</label>
              <input value={form.fee_amount} onChange={e => setForm(f => ({...f, fee_amount: e.target.value}))} type="number" className="input-field" placeholder="e.g. 25000" />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={() => createMutation.mutate(form)} disabled={!form.name || createMutation.isPending} className="btn-primary text-sm">
              {createMutation.isPending ? 'Creating...' : 'Create Batch'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-outline text-sm">Cancel</button>
          </div>
        </div>
      )}

      {isLoading && <div className="text-center py-10 text-gray-400">Loading batches...</div>}

      {!isLoading && batches.length === 0 && (
        <div className="card text-center py-10 text-gray-500">
          No batches yet. Create your first batch above.
        </div>
      )}

      <div className="space-y-4">
        {(batches as Batch[]).map(batch => (
          <BatchCard
            key={batch.id}
            batch={batch}
            onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
          />
        ))}
      </div>
    </div>
  )
}
