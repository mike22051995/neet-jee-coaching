import { Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/services/api'

interface Props {
  children: React.ReactNode
}

/**
 * Guards admin routes by verifying the session with the backend.
 *
 * Because the JWT is in an httpOnly cookie (not localStorage), we cannot
 * check auth state client-side. Instead, we call /api/auth/me; if it returns
 * 401 the cookie is absent or expired and we redirect to login.
 *
 * staleTime: 60s — React Query won't re-fetch on every navigation within that
 * window, so the check runs at most once per minute rather than on each click.
 */
export function ProtectedRoute({ children }: Props) {
  const { isLoading, isError } = useQuery({
    queryKey: ['auth-check'],
    queryFn: adminApi.me,
    retry: false,
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-navy-950">
        <p className="text-gray-400 text-sm">Authenticating…</p>
      </div>
    )
  }

  if (isError) return <Navigate to="/admin/login" replace />
  return <>{children}</>
}
