import React from 'react'
import { Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { studentApi } from '@/services/api'
import { useStudentAuth } from '@/hooks/useStudentAuth'

interface Props {
  children: React.ReactNode
}

export function StudentLayout({ children }: Props) {
  const { isLoading, isError, data: student } = useQuery({
    queryKey: ['student-auth'],
    queryFn: studentApi.me,
    retry: false,
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-500">Loading…</div>
      </div>
    )
  }

  if (isError) return <Navigate to="/student/login" replace />

  return (
    <div className="min-h-screen bg-gray-50">
      <StudentNav studentName={student?.name} />
      <main>{children}</main>
    </div>
  )
}

function StudentNav({ studentName }: { studentName?: string }) {
  const { logout } = useStudentAuth()

  return (
    <nav className="bg-blue-700 text-white px-4 py-3 flex items-center justify-between">
      <span className="font-semibold text-lg">Exam Portal</span>
      <div className="flex items-center gap-4 text-sm">
        <span>{studentName}</span>
        <button
          onClick={() => logout()}
          className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded"
        >
          Logout
        </button>
      </div>
    </nav>
  )
}
