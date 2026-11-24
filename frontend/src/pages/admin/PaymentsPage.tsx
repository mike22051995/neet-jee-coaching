import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, ExternalLink, AlertTriangle } from 'lucide-react'
import { adminApi, PaymentSubmission } from '@/services/api'
import { StatusBadge } from '@/components/common/StatusBadge'

function ReviewModal({
  submission,
  onClose,
}: {
  submission: PaymentSubmission
  onClose: () => void
}) {
  const [action, setAction] = useState<'verify' | 'reject' | null>(null)
  const [reason, setReason] = useState('')
  const qc = useQueryClient()

  const reviewMutation = useMutation({
    mutationFn: () =>
      adminApi.reviewPayment(submission.id, {
        action: action!,
        rejection_reason: action === 'reject' ? reason : undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-payments'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-navy-900 mb-4">Review Payment Submission</h2>

          <div className="space-y-3 text-sm mb-6">
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              <div className="text-gray-500">Transaction Ref</div>
              <div className="font-mono font-medium">{submission.transaction_ref}</div>
              <div className="text-gray-500">Payment Date</div>
              <div>{submission.payment_date ? new Date(submission.payment_date).toLocaleDateString('en-IN') : '—'}</div>
              <div className="text-gray-500">Amount Claimed</div>
              <div className="font-medium">
                {submission.amount_claimed ? `₹${Number(submission.amount_claimed).toLocaleString('en-IN')}` : '—'}
              </div>
              <div className="text-gray-500">Receipt</div>
              <div>
                {submission.receipt_path ? (
                  <a
                    href={`/api/admin/payments/${submission.id}/receipt`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-navy-600 hover:underline inline-flex items-center gap-1"
                  >
                    View receipt <ExternalLink className="h-3 w-3" />
                  </a>
                ) : '—'}
              </div>
            </div>
          </div>

          {/* Important notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6 flex gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800">
              Verify this payment by checking your actual bank/UPI statement.
              Do <strong>not</strong> verify based solely on the submitted screenshot.
            </p>
          </div>

          <div className="flex gap-3 mb-4">
            <button
              onClick={() => setAction('verify')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border text-sm font-medium transition-colors ${
                action === 'verify'
                  ? 'bg-green-600 text-white border-green-600'
                  : 'border-green-300 text-green-700 hover:bg-green-50'
              }`}
            >
              <CheckCircle className="h-4 w-4" /> Verify Payment
            </button>
            <button
              onClick={() => setAction('reject')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border text-sm font-medium transition-colors ${
                action === 'reject'
                  ? 'bg-red-600 text-white border-red-600'
                  : 'border-red-300 text-red-700 hover:bg-red-50'
              }`}
            >
              <XCircle className="h-4 w-4" /> Reject
            </button>
          </div>

          {action === 'reject' && (
            <div className="mb-4">
              <label className="label">Rejection Reason <span className="text-red-500">*</span></label>
              <textarea
                value={reason}
                onChange={e => setReason(e.target.value)}
                rows={3}
                placeholder="Explain why this payment is being rejected (visible to admin only)"
                className="input-field"
              />
            </div>
          )}

          {reviewMutation.isError && (
            <p className="text-sm text-red-600 mb-3">
              {(reviewMutation.error as any)?.response?.data?.detail || 'An error occurred'}
            </p>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => reviewMutation.mutate()}
              disabled={!action || (action === 'reject' && !reason.trim()) || reviewMutation.isPending}
              className="btn-primary text-sm flex-1"
            >
              {reviewMutation.isPending ? 'Submitting...' : 'Confirm Decision'}
            </button>
            <button onClick={onClose} className="btn-outline text-sm">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function PaymentsPage() {
  const [selected, setSelected] = useState<PaymentSubmission | null>(null)

  const { data: payments = [], isLoading } = useQuery({
    queryKey: ['pending-payments'],
    queryFn: adminApi.listPendingPayments,
    refetchInterval: 60_000,
  })

  return (
    <div>
      <h1 className="text-2xl font-display font-bold text-navy-900 mb-2">Payment Reviews</h1>
      <p className="text-sm text-gray-500 mb-6">
        Verify each payment against your bank/UPI statement before confirming enrollment.
      </p>

      {isLoading && <div className="text-center py-10 text-gray-400">Loading...</div>}

      {!isLoading && (payments as PaymentSubmission[]).length === 0 && (
        <div className="card text-center py-10">
          <CheckCircle className="h-10 w-10 text-green-400 mx-auto mb-2" />
          <p className="text-gray-500">No pending payments — all caught up!</p>
        </div>
      )}

      <div className="space-y-3">
        {(payments as PaymentSubmission[]).map(p => (
          <div key={p.id} className="card flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="font-mono text-sm font-medium">{p.transaction_ref}</span>
                <StatusBadge status={p.status} />
              </div>
              <div className="text-sm text-gray-500 space-x-4">
                {p.amount_claimed && (
                  <span>₹{Number(p.amount_claimed).toLocaleString('en-IN')}</span>
                )}
                {p.payment_date && (
                  <span>{new Date(p.payment_date).toLocaleDateString('en-IN')}</span>
                )}
                <span className="text-xs text-gray-400">
                  Submitted {new Date(p.created_at).toLocaleDateString('en-IN')}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelected(p)}
              className="btn-primary text-sm px-4 py-2 shrink-0"
            >
              Review
            </button>
          </div>
        ))}
      </div>

      {selected && <ReviewModal submission={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
