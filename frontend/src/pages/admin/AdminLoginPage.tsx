import { BookOpen } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/hooks/useAuth'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type FormData = z.infer<typeof schema>

export function AdminLoginPage() {
  const { login, isLoading, error } = useAuth()
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <BookOpen className="h-10 w-10 text-gold-400 mx-auto mb-3" />
          <h1 className="text-2xl font-display font-bold text-white">Admin Login</h1>
          <p className="text-gray-400 text-sm mt-1">Coaching Institute Dashboard</p>
        </div>

        <form
          onSubmit={handleSubmit(d => login(d.email, d.password))}
          className="bg-navy-900 rounded-xl p-6 shadow-xl border border-navy-800 space-y-4"
        >
          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-300 text-sm rounded-lg p-3">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              className="w-full px-4 py-3 bg-navy-800 border border-navy-700 text-white rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500 outline-none transition-colors placeholder-gray-500"
              placeholder="admin@coaching.in"
            />
            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input
              {...register('password')}
              type="password"
              autoComplete="current-password"
              className="w-full px-4 py-3 bg-navy-800 border border-navy-700 text-white rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500 outline-none transition-colors"
            />
            {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-gold-500 hover:bg-gold-400 text-navy-900 font-semibold rounded-lg transition-colors disabled:opacity-60"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-600 mt-6">
          Protected area — authorised personnel only
        </p>
      </div>
    </div>
  )
}
