import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminTestApi } from '@/services/api'
import { AdminLayout } from '@/components/admin/AdminLayout'

export function ExamStudentsPage() {
  const qc = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: '', username: '', password: '' })
  const [createError, setCreateError] = useState('')

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['exam-students'],
    queryFn: adminTestApi.listStudents,
  })

  const createMutation = useMutation({
    mutationFn: adminTestApi.createStudent,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exam-students'] })
      setCreating(false)
      setForm({ name: '', username: '', password: '' })
      setCreateError('')
    },
    onError: (e: any) => setCreateError(e?.response?.data?.detail || 'Error creating student'),
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminTestApi.updateStudent(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exam-students'] }),
  })

  return (
    <AdminLayout>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Exam Students</h1>
          <button
            onClick={() => setCreating(true)}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800"
          >
            + Add Student
          </button>
        </div>

        {creating && (
          <div className="bg-white rounded-xl shadow p-6 mb-6 border border-blue-200">
            <h2 className="font-semibold text-gray-700 mb-4">Add Exam Student</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Full Name *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Student name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Username *</label>
                <input
                  value={form.username}
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="e.g. student001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Password *</label>
                <input
                  type="text"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Set their initial password"
                />
              </div>
            </div>
            {createError && <p className="text-red-500 text-sm mt-2">{createError}</p>}
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => createMutation.mutate(form)}
                disabled={!form.name || !form.username || !form.password || createMutation.isPending}
                className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Adding…' : 'Add Student'}
              </button>
              <button onClick={() => setCreating(false)} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        )}

        {isLoading && <p className="text-gray-500">Loading…</p>}

        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Username</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Added</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {students.map((s: any) => (
                <tr key={s.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{s.name}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono">{s.username}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      s.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                    }`}>
                      {s.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(s.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleActive.mutate({ id: s.id, is_active: !s.is_active })}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      {s.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">No exam students yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  )
}
