import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { adminTestApi } from '@/services/api'
import { AdminLayout } from '@/components/admin/AdminLayout'

export function TestDetailPage() {
  const { testId } = useParams<{ testId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [uploading, setUploading] = useState(false)
  const [qNum, setQNum] = useState(1)
  const [correct, setCorrect] = useState('A')
  const [qFile, setQFile] = useState<File | null>(null)
  const [oFile, setOFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState('')

  const { data: test, isLoading } = useQuery({
    queryKey: ['admin-test', testId],
    queryFn: () => adminTestApi.getTest(testId!),
    enabled: !!testId,
  })

  const uploadMutation = useMutation({
    mutationFn: (fd: FormData) => adminTestApi.uploadQuestion(testId!, fd),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-test', testId] })
      setQFile(null)
      setOFile(null)
      setUploadError('')
    },
    onError: (e: any) => setUploadError(e?.response?.data?.detail || 'Upload failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (questionId: string) => adminTestApi.deleteQuestion(testId!, questionId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-test', testId] }),
  })

  const handleUpload = () => {
    if (!qFile || !oFile) { setUploadError('Select both images'); return }
    const fd = new FormData()
    fd.append('question_number', String(qNum))
    fd.append('correct_option', correct)
    fd.append('question_image', qFile)
    fd.append('options_image', oFile)
    uploadMutation.mutate(fd)
  }

  if (isLoading) return <AdminLayout><div className="p-8 text-gray-500">Loading…</div></AdminLayout>
  if (!test) return <AdminLayout><div className="p-8 text-red-500">Test not found.</div></AdminLayout>

  const BASE = import.meta.env.VITE_API_URL || ''

  return (
    <AdminLayout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate('/admin/tests')} className="text-blue-600 text-sm hover:underline">
            ← Tests
          </button>
          <span className="text-gray-400">/</span>
          <h1 className="text-xl font-bold text-gray-800">{test.title}</h1>
          <span className={`ml-2 text-xs px-2 py-1 rounded-full font-medium ${
            test.is_published ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {test.is_published ? 'Published' : 'Draft'} · {test.question_count} questions
          </span>
        </div>

        {/* Upload form */}
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          <h2 className="font-semibold text-gray-700 mb-4">Upload / Replace Question</h2>
          <div className="grid md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Question #</label>
              <input
                type="number"
                min={1} max={45}
                value={qNum}
                onChange={(e) => setQNum(Number(e.target.value))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Correct Answer</label>
              <select
                value={correct}
                onChange={(e) => setCorrect(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {['A', 'B', 'C', 'D'].map((o) => <option key={o}>{o}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Question Image</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setQFile(e.target.files?.[0] || null)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Options Image (A/B/C/D)</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setOFile(e.target.files?.[0] || null)}
                className="w-full text-sm"
              />
            </div>
          </div>
          {uploadError && <p className="text-red-500 text-sm mt-2">{uploadError}</p>}
          <button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="mt-4 px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
          >
            {uploadMutation.isPending ? 'Uploading…' : 'Upload Question'}
          </button>
        </div>

        {/* Questions list */}
        <h2 className="font-semibold text-gray-700 mb-3">Questions ({test.questions?.length ?? 0})</h2>
        {(!test.questions || test.questions.length === 0) && (
          <p className="text-gray-400 text-sm">No questions uploaded yet.</p>
        )}
        <div className="grid md:grid-cols-2 gap-4">
          {(test.questions || []).map((q: any) => (
            <div key={q.id} className="bg-white rounded-xl shadow p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-700">Q{q.question_number}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-medium">
                    Ans: {q.correct_option}
                  </span>
                  <button
                    onClick={() => { if (window.confirm(`Delete Q${q.question_number}?`)) deleteMutation.mutate(q.id) }}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
              <img src={`${BASE}${q.question_image_path}`} alt={`Q${q.question_number}`} className="w-full rounded border mb-2 max-h-40 object-contain" />
              <img src={`${BASE}${q.options_image_path}`} alt="Options" className="w-full rounded border max-h-32 object-contain" />
            </div>
          ))}
        </div>
      </div>
    </AdminLayout>
  )
}
