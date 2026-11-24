import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { adminTestApi } from '@/services/api'
import { AdminLayout } from '@/components/admin/AdminLayout'

export function TestsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', duration_minutes: 60, scheduled_at: '' })

  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['admin-tests'],
    queryFn: adminTestApi.listTests,
  })

  const createMutation = useMutation({
    mutationFn: adminTestApi.createTest,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-tests'] }); setCreating(false) },
  })

  const togglePublish = useMutation({
    mutationFn: ({ id, is_published }: { id: string; is_published: boolean }) =>
      adminTestApi.updateTest(id, { is_published }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-tests'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminTestApi.deleteTest(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-tests'] }),
  })

  return (
    <AdminLayout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Tests</h1>
          <button
            onClick={() => setCreating(true)}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800"
          >
            + New Test
          </button>
        </div>

        {/* Create form */}
        {creating && (
          <div className="bg-white rounded-xl shadow p-6 mb-6 border border-blue-200">
            <h2 className="font-semibold text-gray-700 mb-4">Create New Test</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Title *</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="e.g. NEET Weekly Test 1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  value={form.duration_minutes}
                  onChange={(e) => setForm((f) => ({ ...f, duration_minutes: Number(e.target.value) }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  min={5} max={360}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Description</label>
                <input
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Scheduled At (optional)</label>
                <input
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => createMutation.mutate({
                  ...form,
                  scheduled_at: form.scheduled_at || undefined,
                })}
                disabled={!form.title || createMutation.isPending}
                className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating…' : 'Create Test'}
              </button>
              <button onClick={() => setCreating(false)} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        )}

        {isLoading && <p className="text-gray-500">Loading…</p>}

        <div className="space-y-4">
          {tests.map((test: any) => (
            <div key={test.id} className="bg-white rounded-xl shadow p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-semibold text-gray-800">{test.title}</h2>
                  {test.description && <p className="text-sm text-gray-500 mt-1">{test.description}</p>}
                  <div className="flex gap-3 mt-2 text-xs text-gray-500">
                    <span>{test.question_count} questions</span>
                    <span>{test.duration_minutes} min</span>
                    {test.scheduled_at && <span>Scheduled: {new Date(test.scheduled_at).toLocaleString('en-IN')}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    test.is_published ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {test.is_published ? 'Published' : 'Draft'}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => navigate(`/admin/tests/${test.id}`)}
                  className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded text-xs font-medium hover:bg-blue-100"
                >
                  Manage Questions
                </button>
                <button
                  onClick={() => togglePublish.mutate({ id: test.id, is_published: !test.is_published })}
                  className={`px-3 py-1.5 rounded text-xs font-medium ${
                    test.is_published
                      ? 'bg-orange-50 text-orange-700 hover:bg-orange-100'
                      : 'bg-green-50 text-green-700 hover:bg-green-100'
                  }`}
                >
                  {test.is_published ? 'Unpublish' : 'Publish'}
                </button>
                <button
                  onClick={() => navigate(`/admin/tests/${test.id}/results`)}
                  className="px-3 py-1.5 bg-gray-50 text-gray-700 rounded text-xs font-medium hover:bg-gray-100"
                >
                  View Results
                </button>
                <button
                  onClick={() => { if (window.confirm('Delete this test?')) deleteMutation.mutate(test.id) }}
                  className="px-3 py-1.5 bg-red-50 text-red-600 rounded text-xs font-medium hover:bg-red-100 ml-auto"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AdminLayout>
  )
}
