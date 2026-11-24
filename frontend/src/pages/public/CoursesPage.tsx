import { Link } from 'react-router-dom'
import { Calendar, Clock, BookOpen, Users, ArrowRight } from 'lucide-react'
import { useSiteSettings, useActiveBatch } from '@/hooks/usePublicData'
import { StatusBadge } from '@/components/common/StatusBadge'

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export function CoursesPage() {
  const { data: settings } = useSiteSettings()
  const { data: batchData, isLoading } = useActiveBatch()
  const batch = batchData?.batch

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-navy-900 text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-display font-bold mb-3">Our Courses</h1>
          <p className="text-gray-300 text-lg">Comprehensive preparation for NEET & JEE examinations</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-12">
        {isLoading && (
          <div className="text-center py-16 text-gray-500">Loading batch details...</div>
        )}

        {!isLoading && !batch && (
          <div className="card text-center py-12">
            <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No Active Batch</h2>
            <p className="text-gray-500">There are no active batches at the moment. Please check back soon or contact us.</p>
            {settings?.contact_phone && (
              <a href={`tel:${settings.contact_phone}`} className="btn-primary mt-6 inline-flex">
                Contact Us
              </a>
            )}
          </div>
        )}

        {batch && (
          <div className="space-y-6">
            {/* Main batch card */}
            <div className="card">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-2xl font-display font-bold text-navy-900">{batch.name}</h2>
                    <StatusBadge status={batch.status} />
                  </div>
                  <p className="text-gray-500">Academic Year: {batch.academic_year}</p>
                </div>
                {batch.fee_amount && (
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-1">Total Fee</p>
                    <p className="text-3xl font-display font-bold text-navy-900">{formatCurrency(batch.fee_amount)}</p>
                  </div>
                )}
              </div>

              {batch.description && (
                <p className="text-gray-600 mb-6 leading-relaxed">{batch.description}</p>
              )}

              {/* Details grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {batch.start_date && (
                  <div className="bg-navy-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-navy-600 mb-1">
                      <Calendar className="h-4 w-4" />
                      <span className="text-xs font-medium">Start Date</span>
                    </div>
                    <p className="font-semibold text-navy-900 text-sm">
                      {new Date(batch.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </p>
                  </div>
                )}
                {batch.class_start_time && (
                  <div className="bg-navy-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-navy-600 mb-1">
                      <Clock className="h-4 w-4" />
                      <span className="text-xs font-medium">Class Time (IST)</span>
                    </div>
                    <p className="font-semibold text-navy-900 text-sm">
                      {batch.class_start_time} – {batch.class_end_time}
                    </p>
                  </div>
                )}
                {batch.class_days && (
                  <div className="bg-navy-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-navy-600 mb-1">
                      <BookOpen className="h-4 w-4" />
                      <span className="text-xs font-medium">Class Days</span>
                    </div>
                    <p className="font-semibold text-navy-900 text-sm capitalize">
                      {batch.class_days.map(d => d.slice(0,3)).join(', ')}
                    </p>
                  </div>
                )}
                {batch.total_seats != null && (
                  <div className="bg-navy-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-navy-600 mb-1">
                      <Users className="h-4 w-4" />
                      <span className="text-xs font-medium">Seats</span>
                    </div>
                    <p className="font-semibold text-navy-900 text-sm">
                      {batch.available_seats ?? (batch.total_seats - batch.confirmed_enrollment_count)} remaining
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Subjects */}
            {batch.subjects && batch.subjects.length > 0 && (
              <div className="card">
                <h3 className="font-display font-semibold text-navy-900 text-lg mb-4">Subjects Covered</h3>
                <div className="flex flex-wrap gap-2">
                  {batch.subjects.map(s => (
                    <span key={s} className="px-4 py-2 bg-navy-100 text-navy-800 rounded-lg font-medium text-sm">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Syllabus */}
            {batch.syllabus && (
              <div className="card">
                <h3 className="font-display font-semibold text-navy-900 text-lg mb-4">Course Syllabus</h3>
                <div className="prose prose-sm max-w-none text-gray-600">
                  <p className="whitespace-pre-line leading-relaxed">{batch.syllabus}</p>
                </div>
              </div>
            )}

            {/* Eligibility */}
            {batch.eligibility && (
              <div className="card">
                <h3 className="font-display font-semibold text-navy-900 text-lg mb-3">Eligibility</h3>
                <p className="text-gray-600 leading-relaxed">{batch.eligibility}</p>
              </div>
            )}

            {/* Enrollment window */}
            {(batch.enrollment_opens_at || batch.enrollment_closes_at) && (
              <div className="card bg-gold-50 border-gold-200">
                <h3 className="font-display font-semibold text-navy-900 text-lg mb-3">Enrollment Window</h3>
                <div className="flex gap-8 text-sm">
                  {batch.enrollment_opens_at && (
                    <div>
                      <p className="text-gray-500">Opens</p>
                      <p className="font-semibold">{new Date(batch.enrollment_opens_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                    </div>
                  )}
                  {batch.enrollment_closes_at && (
                    <div>
                      <p className="text-gray-500">Closes</p>
                      <p className="font-semibold">{new Date(batch.enrollment_closes_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CTA */}
            {batch.status === 'enrollment_open' && (
              <div className="text-center py-6">
                <Link to="/enroll" className="btn-primary text-base px-10 py-4 shadow-lg">
                  Enroll in This Batch <ArrowRight className="h-5 w-5" />
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
