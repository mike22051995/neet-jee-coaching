import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { studentApi } from '@/services/api'

export function useStudentAuth() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      studentApi.login(username, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-auth'] })
      navigate('/student/dashboard')
    },
  })

  const logoutMutation = useMutation({
    mutationFn: studentApi.logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/student/login')
    },
  })

  return {
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
  }
}
