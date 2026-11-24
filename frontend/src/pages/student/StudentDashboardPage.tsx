import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { studentApi } from '@/services/api'
import { StudentLayout } from '@/components/student/StudentLayout'

export function StudentDashboardPage() {
  const navigate = useNavigate()
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['student-tests'],
    queryFn: studentApi.listTests,
  })

  const handleStart = async (test: any) => {
    if (test.is_started && !test.is_submitted) {
      navigate(`/student/exam/${test.attempt_id}`)
    } else if (!test.is_started) {
      const attempt = await studentApi.startTest(test.id)
      navigate(`/student/exam/${attempt.id}`)
    } else {
      navigate(`/student/result/${test.attempt_id}`)
    }
  }

  return (
    <StudentLayout>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Available Tests</h1>

        {isLoading && <p className="text-gray-500">Loading tests…</p>}

        {!isLoading && tests.length === 0 && (
          <div className="bg-white rounded-xl shadow p-8 text-center text-gray-500">
            No tests available yet. Check back soon!
          </div>
        )}

        <div className="space-y-4">
          {tests.map((test: any) => (
            <div key={test.id} className="bg-white rounded-xl shadow p-6 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">{test.title}</h2>
                {test.description && <p className="text-gray-500 text-sm mt-1">{test.description}</p>}
                <div className="flex gap-4 mt-2 text-sm text-gray-600">
                  <span>{test.question_count} questions</span>
                  <span>{test.duration_minutes} minutes</span>
                  {test.scheduled_at && (
                    <span>Scheduled: {new Date(test.scheduled_at).toLocaleDateString('en-IN')}</span>
                  )}
                </div>
              </div>

              <div className="ml-4 flex-shrink-0">
                {test.is_submitted ? (
                  <button
                    onClick={() => navigate(`/student/result/${test.attempt_id}`)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
                  >
                    View Result
                  </button>
                ) : test.is_started ? (
                  <button
                    onClick={() => handleStart(test)}
                    className="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600"
                  >
                    Continue
                  </button>
                ) : (
                  <button
                    onClick={() => handleStart(test)}
                    className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800"
                  >
                    Start Test
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </StudentLayout>
  )
}
