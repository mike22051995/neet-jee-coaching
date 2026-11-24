import { useQuery } from '@tanstack/react-query'
import { Users, CheckCircle, Clock, CreditCard, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { adminApi } from '@/services/api'

function StatCard({ icon: Icon, label, value, color }: { icon: typeof Users; label: string; value: number; color: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-display font-bold text-navy-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: adminApi.getDashboardStats,
    refetchInterval: 30_000,
  })

  return (
    <div>
      <h1 className="text-2xl font-display font-bold text-navy-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Users}        label="Total Enrollments"   value={stats?.total_enrollments   ?? 0} color="bg-navy-600" />
        <StatCard icon={CheckCircle}  label="Confirmed"           value={stats?.confirmed_enrollments ?? 0} color="bg-green-500" />
        <StatCard icon={Clock}        label="Pending Payment"     value={stats?.pending_payment      ?? 0} color="bg-amber-500" />
        <StatCard icon={CreditCard}   label="Awaiting Verification" value={stats?.pending_verification ?? 0} color="bg-purple-500" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-navy-900">Pending Payment Reviews</h2>
            <Link to="/admin/payments" className="text-sm text-navy-600 hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          {stats?.pending_verification === 0 ? (
            <p className="text-sm text-gray-400">No payments awaiting review.</p>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-amber-800 font-semibold">{stats?.pending_verification} payment{stats?.pending_verification !== 1 ? 's' : ''} need review</p>
              <p className="text-amber-600 text-sm mt-1">Review and verify student payments to confirm their enrollments.</p>
              <Link to="/admin/payments" className="btn-primary text-sm mt-3 inline-flex">
                Review Now
              </Link>
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-navy-900">Quick Actions</h2>
          </div>
          <div className="space-y-2">
            <Link to="/admin/batches" className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors text-sm">
              <div className="w-8 h-8 bg-navy-100 rounded-lg flex items-center justify-center">
                <span className="text-navy-700 font-bold text-xs">B</span>
              </div>
              <span className="text-gray-700">Manage Batches & Schedule</span>
              <ArrowRight className="h-4 w-4 text-gray-400 ml-auto" />
            </Link>
            <Link to="/admin/students" className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors text-sm">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <Users className="h-4 w-4 text-green-700" />
              </div>
              <span className="text-gray-700">View Student Enrollments</span>
              <ArrowRight className="h-4 w-4 text-gray-400 ml-auto" />
            </Link>
            <Link to="/admin/settings" className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors text-sm">
              <div className="w-8 h-8 bg-gold-100 rounded-lg flex items-center justify-center">
                <span className="text-gold-700 font-bold text-xs">S</span>
              </div>
              <span className="text-gray-700">Update Website Settings</span>
              <ArrowRight className="h-4 w-4 text-gray-400 ml-auto" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
