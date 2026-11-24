/**
 * ExamPage — NEET-identical online exam interface.
 *
 * Layout matches the official NEET exam UI:
 *   - Left panel: question image + options image + A/B/C/D buttons
 *   - Right panel: candidate info + question palette (colour-coded) + navigation
 *   - Top bar: test title + countdown timer
 *
 * Palette colours (NEET convention):
 *   Gray    — not visited
 *   Red     — visited, not answered
 *   Green   — answered
 *   Purple  — marked for review (may or may not have an answer)
 *   Purple+Green — answered AND marked for review
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { studentApi } from '@/services/api'

type AnswerState = {
  selected_option: string | null
  is_marked_for_review: boolean
}

type Question = {
  id: string
  question_number: number
  question_image_path: string
  options_image_path: string
}

type ExamData = {
  attempt_id: string
  test_id: string
  test_title: string
  duration_minutes: number
  started_at: string
  time_remaining_seconds: number
  questions: Question[]
  answers: { question_id: string; selected_option: string | null; is_marked_for_review: boolean }[]
}

function paletteClass(
  questionId: string,
  currentIdx: number,
  questions: Question[],
  answers: Record<string, AnswerState>,
  visitedSet: Set<string>
): string {
  const q = questions[currentIdx]
  const isThis = q?.id === questionId
  const a = answers[questionId]
  const answered = a?.selected_option != null
  const review = a?.is_marked_for_review

  let bg = 'bg-gray-200 text-gray-700'
  if (answered && review) bg = 'bg-purple-700 text-white'
  else if (answered) bg = 'bg-green-600 text-white'
  else if (review) bg = 'bg-purple-500 text-white'
  else if (visitedSet.has(questionId)) bg = 'bg-red-500 text-white'

  return `w-9 h-9 rounded-full text-xs font-bold flex items-center justify-center cursor-pointer border-2 ${
    isThis ? 'border-blue-700 ring-2 ring-blue-400' : 'border-transparent'
  } ${bg}`
}

export function ExamPage() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()

  const [examData, setExamData] = useState<ExamData | null>(null)
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({})
  const [visited, setVisited] = useState<Set<string>>(new Set())
  const [timeLeft, setTimeLeft] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const saveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load exam data
  useEffect(() => {
    if (!attemptId) return
    studentApi.getAttempt(attemptId).then((data: ExamData) => {
      setExamData(data)
      setTimeLeft(data.time_remaining_seconds)
      const map: Record<string, AnswerState> = {}
      data.answers.forEach((a) => {
        map[a.question_id] = { selected_option: a.selected_option, is_marked_for_review: a.is_marked_for_review }
      })
      setAnswers(map)
      if (data.questions.length > 0) {
        setVisited(new Set([data.questions[0].id]))
      }
    })
  }, [attemptId])

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return
    const id = setInterval(() => setTimeLeft((t) => {
      if (t <= 1) {
        clearInterval(id)
        handleAutoSubmit()
        return 0
      }
      return t - 1
    }), 1000)
    return () => clearInterval(id)
  }, [timeLeft > 0])

  const handleAutoSubmit = useCallback(async () => {
    if (!attemptId || submitting) return
    setSubmitting(true)
    await studentApi.submitAttempt(attemptId, true)
    navigate(`/student/result/${attemptId}`)
  }, [attemptId, submitting, navigate])

  const saveAnswer = useCallback((questionId: string, option: string | null, markReview: boolean) => {
    if (!attemptId) return
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { selected_option: option, is_marked_for_review: markReview },
    }))
    // Debounce — save 400ms after the last action
    if (saveTimeout.current) clearTimeout(saveTimeout.current)
    saveTimeout.current = setTimeout(() => {
      studentApi.saveAnswer(attemptId, questionId, option, markReview)
    }, 400)
  }, [attemptId])

  const goTo = (idx: number) => {
    if (!examData) return
    setVisited((v) => new Set(v).add(examData.questions[idx].id))
    setCurrent(idx)
  }

  const handleSelectOption = (opt: string) => {
    if (!examData) return
    const qId = examData.questions[current].id
    const prev = answers[qId]
    const newOpt = prev?.selected_option === opt ? null : opt  // toggle off
    saveAnswer(qId, newOpt, prev?.is_marked_for_review ?? false)
  }

  const handleMarkReview = () => {
    if (!examData) return
    const qId = examData.questions[current].id
    const prev = answers[qId]
    saveAnswer(qId, prev?.selected_option ?? null, !(prev?.is_marked_for_review ?? false))
    if (current < examData.questions.length - 1) goTo(current + 1)
  }

  const handleClearResponse = () => {
    if (!examData) return
    const qId = examData.questions[current].id
    saveAnswer(qId, null, false)
  }

  const handleSubmit = async () => {
    if (!attemptId || submitting) return
    setSubmitting(true)
    setShowConfirm(false)
    await studentApi.submitAttempt(attemptId)
    navigate(`/student/result/${attemptId}`)
  }

  if (!examData) {
    return <div className="min-h-screen flex items-center justify-center">Loading exam…</div>
  }

  const question = examData.questions[current]
  const currentAnswer = answers[question?.id]
  const BASE = import.meta.env.VITE_API_URL || ''

  const mm = Math.floor(timeLeft / 60).toString().padStart(2, '0')
  const ss = (timeLeft % 60).toString().padStart(2, '0')
  const timerColor = timeLeft < 300 ? 'text-red-600' : 'text-gray-800'

  const totalQ = examData.questions.length
  const answered = Object.values(answers).filter((a) => a.selected_option).length
  const markedReview = Object.values(answers).filter((a) => a.is_marked_for_review).length
  const notVisited = totalQ - visited.size
  const notAnswered = visited.size - answered - markedReview

  return (
    <div className="flex flex-col h-screen bg-gray-100 overflow-hidden">
      {/* Top bar */}
      <header className="bg-blue-800 text-white px-4 py-2 flex items-center justify-between flex-shrink-0">
        <div className="font-semibold truncate max-w-xs">{examData.test_title}</div>
        <div className={`font-mono text-xl font-bold ${timerColor === 'text-red-600' ? 'text-red-300' : 'text-white'}`}>
          {mm}:{ss}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left — question area */}
        <div className="flex-1 flex flex-col overflow-y-auto bg-white border-r">
          {/* Question meta */}
          <div className="bg-blue-50 px-4 py-2 border-b text-sm text-gray-600 flex justify-between">
            <span>Question {current + 1} of {totalQ}</span>
            <span className="text-xs text-gray-400">+4 | -1 | 0 (unanswered)</span>
          </div>

          {/* Question image */}
          <div className="p-4">
            <img
              src={`${BASE}${question.question_image_path}`}
              alt={`Question ${question.question_number}`}
              className="max-w-full rounded border"
            />
          </div>

          {/* Options image + ABCD buttons */}
          <div className="px-4 pb-4">
            <img
              src={`${BASE}${question.options_image_path}`}
              alt="Options"
              className="max-w-full rounded border mb-4"
            />
            <div className="grid grid-cols-2 gap-3">
              {(['A', 'B', 'C', 'D'] as const).map((opt) => (
                <button
                  key={opt}
                  onClick={() => handleSelectOption(opt)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 font-semibold text-sm transition-colors ${
                    currentAnswer?.selected_option === opt
                      ? 'bg-blue-700 text-white border-blue-700'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                  }`}
                >
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    currentAnswer?.selected_option === opt
                      ? 'bg-white text-blue-700'
                      : 'bg-gray-200 text-gray-700'
                  }`}>
                    {opt}
                  </span>
                  Option {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Action buttons — NEET style */}
          <div className="px-4 pb-6 flex flex-wrap gap-2 mt-auto">
            <button
              onClick={handleMarkReview}
              className="px-4 py-2 bg-purple-600 text-white rounded text-sm font-medium hover:bg-purple-700"
            >
              Mark for Review & Next
            </button>
            <button
              onClick={handleClearResponse}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300"
            >
              Clear Response
            </button>
            <button
              onClick={() => { if (current < totalQ - 1) goTo(current + 1) }}
              disabled={current >= totalQ - 1}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-40 ml-auto"
            >
              Save & Next
            </button>
          </div>

          {/* Previous / Next nav */}
          <div className="px-4 pb-4 flex justify-between border-t pt-3">
            <button
              onClick={() => { if (current > 0) goTo(current - 1) }}
              disabled={current === 0}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm disabled:opacity-40 hover:bg-gray-300"
            >
              ← Previous
            </button>
            <button
              onClick={() => { if (current < totalQ - 1) goTo(current + 1) }}
              disabled={current >= totalQ - 1}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm disabled:opacity-40 hover:bg-gray-300"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Right — palette panel */}
        <div className="w-72 flex-shrink-0 flex flex-col overflow-y-auto bg-gray-50 border-l">
          {/* Legend */}
          <div className="p-3 border-b bg-white text-xs space-y-1">
            <div className="font-semibold text-gray-700 mb-2">Question Status</div>
            {[
              { color: 'bg-green-600', label: `Answered (${answered})` },
              { color: 'bg-red-500', label: `Not Answered (${notAnswered})` },
              { color: 'bg-gray-200', label: `Not Visited (${notVisited})` },
              { color: 'bg-purple-500', label: `Marked for Review (${markedReview})` },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full ${color}`} />
                <span className="text-gray-600">{label}</span>
              </div>
            ))}
          </div>

          {/* Palette grid */}
          <div className="p-3 flex-1">
            <div className="text-xs font-semibold text-gray-600 mb-2">Question Palette</div>
            <div className="flex flex-wrap gap-1">
              {examData.questions.map((q, idx) => (
                <button
                  key={q.id}
                  onClick={() => goTo(idx)}
                  className={paletteClass(q.id, current, examData.questions, answers, visited)}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <div className="p-3 border-t bg-white">
            <button
              onClick={() => setShowConfirm(true)}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg"
            >
              Submit Test
            </button>
          </div>
        </div>
      </div>

      {/* Confirm submit dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
            <h2 className="text-lg font-bold text-gray-800 mb-2">Submit Test?</h2>
            <div className="text-sm text-gray-600 mb-4 space-y-1">
              <p>Answered: <strong className="text-green-700">{answered}</strong></p>
              <p>Not answered: <strong className="text-red-600">{totalQ - answered}</strong></p>
              <p className="text-orange-600 font-medium mt-2">This action cannot be undone.</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 border rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
              >
                {submitting ? 'Submitting…' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
