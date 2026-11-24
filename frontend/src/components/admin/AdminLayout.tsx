import React from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, BookOpen, Users, CreditCard, Settings, LogOut, Menu, X, FileText, GraduationCap } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { adminApi } from '@/services/api'

const navItems = [
  { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/admin/batches', icon: BookOpen, label: 'Batches' },
  { to: '/admin/students', icon: Users, label: 'Students' },
  { to: '/admin/payments', icon: CreditCard, label: 'Payments' },
  { to: '/admin/tests', icon: FileText, label: 'Tests' },
  { to: '/admin/exam-students', icon: GraduationCap, label: 'Exam Students' },
  { to: '/admin/settings', icon: Settings, label: 'Settings' },
]

interface AdminLayoutProps {
  children?: React.ReactNode
}

export function AdminLayout({ children }: AdminLayoutProps = {}) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const navigate = useNavigate()

  const logout = async () => {
    try {
      await adminApi.logout()
    } catch {
      // best-effort
    }
    navigate('/admin/login')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-navy-800">
        <div className="flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-gold-400" />
          <span className="font-display font-bold text-white text-sm">Admin Dashboard</span>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-navy-700 text-white'
                : 'text-gray-400 hover:text-white hover:bg-navy-800'
            )}
            onClick={() => setSidebarOpen(false)}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-navy-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-3 py-2.5 text-sm text-gray-400 hover:text-white hover:bg-navy-800 rounded-lg transition-colors"
        >
          <LogOut className="h-5 w-5" />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-56 bg-navy-950 flex-col fixed inset-y-0 left-0 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <aside className="relative w-56 bg-navy-950 h-full">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 md:ml-56 flex flex-col">
        {/* Mobile topbar */}
        <div className="md:hidden bg-navy-950 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-gold-400" />
            <span className="font-bold text-white text-sm">Admin</span>
          </div>
          <button onClick={() => setSidebarOpen(o => !o)} className="text-gray-300">
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Page content */}
        <main className="flex-1 p-4 md:p-6 overflow-auto">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}
