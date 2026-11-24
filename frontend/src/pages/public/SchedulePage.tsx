import { useState } from 'react'
import { Calendar, Clock, BookOpen, AlertCircle, CheckCircle } from 'lucide-react'
import { useActiveBatch, useSchedule } from '@/hooks/usePublicData'
import { addDays, format, parseISO } from 'date-fns'

interface ScheduleSession {
  id: string
  session_date: string
  start_time?: string
  end_time?: string
  subject?: string
  is_cancelled: boolean
  is_rescheduled: boolean
  notice?: string
}

function SessionCard({ session }: { session: ScheduleSession }) {
  const dateObj = parseISO(session.session_date)
  const dateStr = format(dateObj, 'EEE, d MMM yyyy')

  return (
    <div className={`card flex items-start gap-4 ${session.is_cancelled ? 'opacity-60 border-red-200' : ''}`}>
      <div className="text-center min-w-[52px]">
        <p className="text-xs font-medium text-gray-500 uppercase">{format(dateObj, 'EEE')}</p>
        <p className="text-2xl font-display font-bold text-navy-900">{format(dateObj, 'd')}</p>
        <p className="text-xs text-gray-500">{format(dateObj, 'MMM')}</p>
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          {session.is_cancelled ? (
            <span className="badge badge-red">Cancelled</span>
          ) : session.is_rescheduled ? (
            <span className="badge badge-yellow">Rescheduled</span>
          ) : (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
          {session.subject && (
            <span className="text-sm font-medium text-navy-800">{session.subject}</span>
          )}
        </div>
        {session.start_time && !session.is_cancelled && (
          <div className="flex items-center gap-1.5 text-sm text-gray-600 mt-1">
            <Clock className="h-3.5 w-3.5" />
            {session.start_time} – {session.end_time} IST
          </div>
        )}
        {session.notice && (
          <div className="flex items-start gap-1.5 mt-2 text-sm text-amber-700 bg-amber-50 rounded px-2 py-1">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            {session.notice}
          </div>
        )}
      </div>
    </div>
  )
}

export function SchedulePage() {
  const { data: batchData } = useActiveBatch()
  const batch = batchData?.batch
  const today = new Date()
  const fromDate = format(today, 'yyyy-MM-dd')
  const toDate = format(addDays(today, 60), 'yyyy-MM-dd')

  const { data: sessions = [], isLoading } = useSchedule(batch?.id, fromDate, toDate)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-navy-900 text-white py-14 px-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-display font-bold mb-2">Class Schedule</h1>
          <p className="text-gray-300">All times are in Indian Standard Time (IST / UTC+5:30)</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-10">
        {/* Weekly pattern */}
        {batch?.class_days && (
          <div className="card mb-8">
            <h2 className="font-display font-semibold text-navy-900 text-lg mb-4">Weekly Schedule</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {batch.class_days.map(day => (
                <div key={day} className="bg-navy-50 rounded-lg p-3 text-center">
                  <p className="font-semibold text-navy-800 capitalize">{day}</p>
                  {batch.class_start_time && (
                    <p className="text-sm text-gray-600 mt-1">{batch.class_start_time} IST</p>
                  )}
                </div>
              ))}
            </div>
            {batch.subjects && (
              <div className="mt-4 flex flex-wrap gap-2">
                {batch.subjects.map(s => (
                  <span key={s} className="text-xs px-3 py-1 bg-gold-100 text-gold-800 rounded-full font-medium">{s}</span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Upcoming sessions with exceptions */}
        <div>
          <h2 className="font-display font-semibold text-navy-900 text-xl mb-4">
            Upcoming Classes & Notices
          </h2>

          {isLoading && (
            <div className="text-center py-10 text-gray-400">Loading schedule...</div>
          )}

          {!isLoading && !batch && (
            <div className="card text-center py-10">
              <Calendar className="h-10 w-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No active batch found. Check back soon.</p>
            </div>
          )}

          {!isLoading && batch && sessions.length === 0 && (
            <div className="card text-center py-10">
              <BookOpen className="h-10 w-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No special notices for the next 60 days. Regular schedule applies.</p>
            </div>
          )}

          {sessions.length > 0 && (
            <div className="space-y-3">
              {(sessions as ScheduleSession[]).map(s => (
                <SessionCard key={s.id} session={s} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
