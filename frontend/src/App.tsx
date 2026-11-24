import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { PublicLayout } from '@/components/layout/PublicLayout'
import { ProtectedRoute } from '@/components/admin/ProtectedRoute'
import { AdminLayout } from '@/components/admin/AdminLayout'

import { HomePage } from '@/pages/public/HomePage'
import { CoursesPage } from '@/pages/public/CoursesPage'
import { SchedulePage } from '@/pages/public/SchedulePage'
import { EnrollPage } from '@/pages/public/EnrollPage'
import { PaymentPage } from '@/pages/public/PaymentPage'

import { AdminLoginPage } from '@/pages/admin/AdminLoginPage'
import { DashboardPage } from '@/pages/admin/DashboardPage'
import { BatchesPage } from '@/pages/admin/BatchesPage'
import { BatchDetailPage } from '@/pages/admin/BatchDetailPage'
import { StudentsPage } from '@/pages/admin/StudentsPage'
import { PaymentsPage } from '@/pages/admin/PaymentsPage'
import { SettingsPage } from '@/pages/admin/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/enroll" element={<EnrollPage />} />
            <Route path="/payment" element={<PaymentPage />} />
          </Route>

          {/* Admin login — no layout wrapper */}
          <Route path="/admin/login" element={<AdminLoginPage />} />

          {/* Protected admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="batches" element={<BatchesPage />} />
            <Route path="batches/:id" element={<BatchDetailPage />} />
            <Route path="students" element={<StudentsPage />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
