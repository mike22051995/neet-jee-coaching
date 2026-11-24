/**
 * Authentication hook — login, logout, and loading state.
 *
 * The JWT is stored in an httpOnly cookie set by the backend, so this hook
 * never touches localStorage. Auth state is verified by calling /api/auth/me
 * (see ProtectedRoute), not by checking a local value.
 */
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '@/services/api'

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)
    try {
      // The backend sets the httpOnly cookie; nothing to store client-side.
      await adminApi.login(email, password)
      navigate('/admin/dashboard')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail || 'Login failed. Please try again.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [navigate])

  const logout = useCallback(async () => {
    try {
      // Tell the backend to clear the httpOnly cookie.
      await adminApi.logout()
    } catch {
      // Best-effort — navigate to login even if the request fails.
    }
    navigate('/admin/login')
  }, [navigate])

  return { login, logout, isLoading, error }
}
