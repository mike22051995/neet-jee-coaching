import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Copy, CheckCircle, AlertCircle, Upload, QrCode } from 'lucide-react'
import { useSiteSettings } from '@/hooks/usePublicData'
import { enrollmentApi, publicApi } from '@/services/api'

const schema = z.object({
  transaction_ref: z.string().min(5, 'Enter your UPI transaction reference number'),
  payment_date: z.string().optional(),
  amount_claimed: z.number().positive('Enter the amount you paid').optional(),
})
type FormData = z.infer<typeof schema>

export function PaymentPage() {
  const [params] = useSearchParams()
  const enrollmentId = params.get('id') || ''
  const reference = params.get('ref') || ''
  const { data: settings } = useSiteSettings()
  const [copied, setCopied] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [receiptFile, setReceiptFile] = useState<File | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const copyUPI = () => {
    if (settings?.upi_id) {
      navigator.clipboard.writeText(settings.upi_id)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const fd = new FormData()
      fd.append('enrollment_id', enrollmentId)
      fd.append('transaction_ref', data.transaction_ref)
      if (data.payment_date) fd.append('payment_date', data.payment_date)
      if (data.amount_claimed) fd.append('amount_claimed', String(data.amount_claimed))
      if (receiptFile) fd.append('receipt', receiptFile)
      return enrollmentApi.submitPayment(fd)
    },
    onSuccess: () => setSubmitted(true),
  })

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
        <div className="max-w-md w-full card text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-display font-bold text-navy-900 mb-2">Payment Details Submitted!</h2>
          <p className="text-gray-600 mb-4">
            Your UPI transaction reference has been received. Our team will verify your payment and confirm your enrollment within 24–48 hours.
          </p>
          <div className="bg-navy-50 rounded-lg p-4">
            <p className="text-xs text-gray-500">Enrollment Reference</p>
            <p className="font-mono font-bold text-navy-900">{reference}</p>
          </div>
          <p className="text-sm text-gray-500 mt-4">
            You will be contacted on the email/phone you provided once your enrollment is confirmed.
          </p>
        </div>
      </div>
    )
  }

  if (!enrollmentId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="card max-w-md text-center py-12">
          <AlertCircle className="h-12 w-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-navy-900 mb-2">Invalid Link</h2>
          <p className="text-gray-500">Please use the link provided after completing your enrollment form.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-navy-900 text-white py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-4xl font-display font-bold mb-1">Complete Payment</h1>
          <p className="text-gray-300">Reference: <span className="font-mono font-semibold">{reference}</span></p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-10 space-y-6">
        {/* Payment instructions */}
        <div className="card">
          <h2 className="font-display font-semibold text-navy-900 text-lg mb-4">Pay via UPI</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* QR Code */}
            <div className="text-center">
              {settings?.upi_qr_path ? (
                <img
                  src={settings.upi_qr_path}
                  alt="UPI QR Code"
                  className="w-48 h-48 mx-auto rounded-lg border object-contain"
                />
              ) : (
                <div className="w-48 h-48 mx-auto bg-gray-100 rounded-lg flex items-center justify-center">
                  <QrCode className="h-16 w-16 text-gray-300" />
                </div>
              )}
              <p className="text-xs text-gray-500 mt-2">Scan with any UPI app</p>
            </div>

            {/* UPI Details */}
            <div className="space-y-3">
              {settings?.upi_name && (
                <div>
                  <p className="text-xs text-gray-500">Pay to</p>
                  <p className="font-semibold text-navy-900">{settings.upi_name}</p>
                </div>
              )}
              {settings?.upi_id && (
                <div>
                  <p className="text-xs text-gray-500">UPI ID</p>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="bg-gray-100 px-3 py-1.5 rounded text-sm font-mono text-navy-800 flex-1 select-all">
                      {settings.upi_id}
                    </code>
                    <button onClick={copyUPI} className="p-1.5 hover:bg-gray-100 rounded transition-colors" title="Copy UPI ID">
                      {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4 text-gray-500" />}
                    </button>
                  </div>
                </div>
              )}
              {settings?.payment_instructions && (
                <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-800 leading-relaxed">
                  {settings.payment_instructions}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Submit transaction ref */}
        {mutation.isError && (
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <p className="text-red-700 text-sm">
                {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Something went wrong. Please try again.'}
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(d => mutation.mutate(d))} className="card space-y-5">
          <h2 className="font-display font-semibold text-navy-900 text-lg">Submit Payment Details</h2>
          <p className="text-sm text-gray-500">After completing the UPI payment, enter your transaction reference below.</p>

          <div>
            <label className="label">UPI Transaction Reference / UTR Number *</label>
            <input
              {...register('transaction_ref')}
              className={`input-field ${errors.transaction_ref ? 'error' : ''}`}
              placeholder="e.g. 123456789012"
            />
            {errors.transaction_ref && <p className="error-text">{errors.transaction_ref.message}</p>}
            <p className="text-xs text-gray-400 mt-1">Find this in your UPI app under transaction history</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="label">Payment Date</label>
              <input
                {...register('payment_date')}
                type="date"
                className="input-field"
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <label className="label">Amount Paid (₹)</label>
              <input
                {...register('amount_claimed', { valueAsNumber: true })}
                type="number"
                step="0.01"
                className="input-field"
                placeholder="Amount you paid"
              />
            </div>
          </div>

          <div>
            <label className="label">Payment Screenshot (optional)</label>
            <label className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-200 rounded-lg hover:border-navy-400 cursor-pointer transition-colors">
              <Upload className="h-5 w-5 text-gray-400" />
              <span className="text-sm text-gray-500">
                {receiptFile ? receiptFile.name : 'Upload screenshot (JPG, PNG, PDF — max 5MB)'}
              </span>
              <input
                type="file"
                accept="image/*,.pdf"
                className="hidden"
                onChange={e => setReceiptFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full justify-center py-4 text-base"
          >
            {mutation.isPending ? 'Submitting...' : 'Submit Payment Details'}
          </button>

          <p className="text-xs text-gray-400 text-center">
            Your enrollment will be confirmed once an administrator verifies the payment.
          </p>
        </form>
      </div>
    </div>
  )
}
