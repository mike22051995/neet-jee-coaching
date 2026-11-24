import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import { adminApi, Enrollment } from '@/services/api'
import { StatusBadge } from '@/components/common/StatusBadge'

export function StudentsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(0)
  const limit = 20
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-enrollments', search, statusFilter, page],
    queryFn: () => adminApi.listEnrollments({
      search: search || undefined,
      status: statusFilter || undefined,
      limit,
      offset: page * limit,
    }),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminApi.updateEnrollmentStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-enrollments'] }),
  })

  const exportCSV = () => {
    const url = `/api/admin/enrollments/export/csv${statusFilter ? `?status=${statusFilter}` : ''}`
    window.open(url, '_blank')
  }

  const items: Enrollment[] = data?.items || []
  const total: number = data?.total || 0
  const pages = Math.ceil(total / limit)

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-display font-bold text-navy-900">Students</h1>
        <button onClick={exportCSV} className="btn-outline text-sm px-4 py-2 flex items-center gap-2">
          <Download className="h-4 w-4" /> Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
            placeholder="Search by name, email, or reference..."
            className="input-field pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(0) }}
          className="input-field sm:w-48"
        >
          <option value="">All Statuses</option>
          <option value="pending_payment">Pending Payment</option>
          <option value="confirmed">Confirmed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {isLoading && <div className="text-center py-10 text-gray-400">Loading...</div>}

      {!isLoading && (
        <>
          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    {['Reference', 'Student', 'Email', 'Phone', 'Grade', 'Exam', 'Status', 'Date', 'Action'].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.length === 0 ? (
                    <tr><td colSpan={9} className="text-center py-8 text-gray-400">No enrollments found</td></tr>
                  ) : items.map((e) => (
                    <tr key={e.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs">{e.reference}</td>
                      <td className="px-4 py-3 font-medium whitespace-nowrap">{e.student_name}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate">{e.email}</td>
                      <td className="px-4 py-3 text-gray-600">{e.phone}</td>
                      <td className="px-4 py-3">{e.grade}</td>
                      <td className="px-4 py-3 uppercase text-xs">{e.exam_preference}</td>
                      <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                        {new Date(e.created_at).toLocaleDateString('en-IN')}
                      </td>
                      <td className="px-4 py-3">
                        {e.status === 'pending_payment' && (
                          <button
                            onClick={() => statusMutation.mutate({ id: e.id, status: 'confirmed' })}
                            className="text-xs text-green-700 hover:underline"
                          >
                            Confirm
                          </button>
                        )}
                        {e.status === 'confirmed' && (
                          <button
                            onClick={() => statusMutation.mutate({ id: e.id, status: 'cancelled' })}
                            className="text-xs text-red-600 hover:underline"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
              <span>Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total}</span>
              <div className="flex gap-2">
                <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="p-1 disabled:opacity-40">
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button disabled={page >= pages - 1} onClick={() => setPage(p => p + 1)} className="p-1 disabled:opacity-40">
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
