import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { adminTestApi } from '@/services/api'
import { AdminLayout } from '@/components/admin/AdminLayout'

export function TestResultsPage() {
  const { testId } = useParams<{ testId: string }>()
  const navigate = useNavigate()

  const { data: results = [], isLoading } = useQuery({
    queryKey: ['test-results', testId],
    queryFn: () => adminTestApi.getTestResults(testId!),
    enabled: !!testId,
  })

  const { data: test } = useQuery({
    queryKey: ['admin-test-meta', testId],
    queryFn: () => adminTestApi.getTest(testId!),
    enabled: !!testId,
  })

  return (
    <AdminLayout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/admin/tests')} className="text-blue-600 text-sm hover:underline">
            ← Tests
          </button>
          <span className="text-gray-400">/</span>
          <h1 className="text-xl font-bold text-gray-800">{test?.title ?? 'Results'}</h1>
        </div>

        {isLoading && <p className="text-gray-500">Loading…</p>}

        {!isLoading && results.length === 0 && (
          <p className="text-gray-400">No attempts yet.</p>
        )}

        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Student</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Score</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Correct</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Wrong</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Unanswered</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Submitted</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r: any) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800">{r.student_name}</div>
                    <div className="text-xs text-gray-400 font-mono">{r.student_username}</div>
                  </td>
                  <td className="px-4 py-3 font-bold text-blue-700">{r.score ?? '—'}</td>
                  <td className="px-4 py-3 text-green-700">{r.correct_count ?? '—'}</td>
                  <td className="px-4 py-3 text-red-600">{r.wrong_count ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{r.unanswered_count ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {r.submitted_at ? new Date(r.submitted_at).toLocaleString('en-IN') : 'In progress'}
                  </td>
                  <td className="px-4 py-3">
                    {r.submitted_at ? (
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        r.is_timed_out ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {r.is_timed_out ? 'Timed out' : 'Submitted'}
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 font-medium">Live</span>
                    )}
                  </td>
                </tr>
              ))}
              {results.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-6 text-center text-gray-400">No attempts yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  )
}
