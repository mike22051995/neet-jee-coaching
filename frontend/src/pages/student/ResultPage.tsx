import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { studentApi } from '@/services/api'
import { StudentLayout } from '@/components/student/StudentLayout'

export function ResultPage() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()
  const BASE = import.meta.env.VITE_API_URL || ''

  const { data: result, isLoading, isError } = useQuery({
    queryKey: ['result', attemptId],
    queryFn: () => studentApi.getResult(attemptId!),
    enabled: !!attemptId,
  })

  if (isLoading) return <StudentLayout><div className="p-8 text-center text-gray-500">Loading result…</div></StudentLayout>
  if (isError || !result) return <StudentLayout><div className="p-8 text-center text-red-500">Could not load result.</div></StudentLayout>

  const maxMarks = result.total_questions * 4
  const percentage = Math.round((result.score / maxMarks) * 100)

  return (
    <StudentLayout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Score summary */}
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-1">{result.test_title}</h1>
          <p className="text-gray-500 text-sm mb-6">Result</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-blue-700">{result.score}</div>
              <div className="text-sm text-gray-500 mt-1">Total Score</div>
              <div className="text-xs text-gray-400">out of {maxMarks}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-green-700">{result.correct_count}</div>
              <div className="text-sm text-gray-500 mt-1">Correct</div>
              <div className="text-xs text-gray-400">+4 each</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-red-600">{result.wrong_count}</div>
              <div className="text-sm text-gray-500 mt-1">Wrong</div>
              <div className="text-xs text-gray-400">-1 each</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-gray-500">{result.unanswered_count}</div>
              <div className="text-sm text-gray-500 mt-1">Unanswered</div>
              <div className="text-xs text-gray-400">0 marks</div>
            </div>
          </div>

          <div className="mt-4 text-center text-gray-600 text-sm">
            Accuracy: <strong>{percentage}%</strong> ({result.correct_count} / {result.total_questions} questions)
          </div>
        </div>

        {/* Question-by-question breakdown */}
        <h2 className="text-lg font-bold text-gray-700 mb-4">Question Review</h2>
        <div className="space-y-6">
          {result.questions.map((q: any, idx: number) => {
            const isCorrect = q.student_option === q.correct_option
            const isWrong = q.student_option && !isCorrect
            const isUnanswered = !q.student_option

            return (
              <div key={idx} className={`bg-white rounded-xl shadow p-4 border-l-4 ${
                isCorrect ? 'border-green-500' : isWrong ? 'border-red-500' : 'border-gray-300'
              }`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-gray-700">Q{q.question_number}</span>
                  <span className={`text-sm font-bold px-2 py-1 rounded ${
                    isCorrect ? 'bg-green-100 text-green-700' :
                    isWrong ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-500'
                  }`}>
                    {q.marks > 0 ? `+${q.marks}` : q.marks} marks
                  </span>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Question</p>
                    <img src={`${BASE}${q.question_image_path}`} alt={`Q${q.question_number}`} className="max-w-full rounded border" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Options</p>
                    <img src={`${BASE}${q.options_image_path}`} alt="Options" className="max-w-full rounded border" />
                  </div>
                </div>

                <div className="mt-3 flex gap-4 text-sm">
                  <span>
                    Your answer:{' '}
                    <strong className={isCorrect ? 'text-green-700' : isWrong ? 'text-red-600' : 'text-gray-500'}>
                      {q.student_option || '—'}
                    </strong>
                  </span>
                  <span>
                    Correct answer:{' '}
                    <strong className="text-green-700">{q.correct_option}</strong>
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/student/dashboard')}
            className="px-6 py-3 bg-blue-700 text-white rounded-lg font-semibold hover:bg-blue-800"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </StudentLayout>
  )
}
