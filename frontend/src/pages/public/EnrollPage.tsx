import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { CheckCircle, AlertCircle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { useSiteSettings, useActiveBatch } from '@/hooks/usePublicData'
import { enrollmentApi, Enrollment } from '@/services/api'

const schema = z.object({
  student_name: z.string().min(2, 'Full name is required'),
  email: z.string().email('Enter a valid email address'),
  phone: z.string().min(10, 'Enter a valid 10-digit phone number'),
  grade: z.string().min(1, 'Please select your class/grade'),
  exam_preference: z.enum(['neet', 'jee'], { required_error: 'Please select NEET or JEE' }),
  guardian_name: z.string().optional(),
  guardian_phone: z.string().optional(),
  privacy_acknowledged: z.literal(true, { errorMap: () => ({ message: 'You must accept the privacy policy to proceed' }) }),
})

type FormData = z.infer<typeof schema>

export function EnrollPage() {
  const { data: settings } = useSiteSettings()
  const { data: batchData } = useActiveBatch()
  const batch = batchData?.batch
  const [enrollmentResult, setEnrollmentResult] = useState<Enrollment | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      enrollmentApi.createEnrollment({
        ...data,
        batch_id: batch!.id,
        privacy_acknowledged: true,
      }),
    onSuccess: (result) => setEnrollmentResult(result),
  })

  if (enrollmentResult) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
        <div className="max-w-lg w-full card text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-display font-bold text-navy-900 mb-2">Enrollment Received!</h2>
          <p className="text-gray-600 mb-6">Your enrollment has been submitted successfully.</p>
          <div className="bg-navy-50 rounded-xl p-4 mb-6">
            <p className="text-sm text-gray-500">Your Enrollment Reference</p>
            <p className="text-2xl font-mono font-bold text-navy-900 mt-1">{enrollmentResult.reference}</p>
            <p className="text-xs text-gray-500 mt-2">Save this reference — you'll need it to track your status</p>
          </div>
          <div className="text-left bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-800">Complete Your Payment</p>
                <p className="text-sm text-amber-700 mt-1">
                  Your enrollment is pending payment. Please complete the UPI payment and submit your transaction reference.
                </p>
              </div>
            </div>
          </div>
          <a
            href={`/payment?ref=${enrollmentResult.reference}&id=${enrollmentResult.id}`}
            className="btn-primary w-full justify-center"
          >
            Proceed to Payment
          </a>
        </div>
      </div>
    )
  }

  if (!batch || batch.status !== 'enrollment_open') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="card max-w-md text-center py-12">
          <AlertCircle className="h-12 w-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-navy-900 mb-2">Enrollment Not Open</h2>
          <p className="text-gray-500">Enrollment is not currently open. Please check back later or contact us.</p>
          {settings?.contact_phone && (
            <a href={`tel:${settings.contact_phone}`} className="btn-outline mt-6 inline-flex">
              Call Us: {settings.contact_phone}
            </a>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-navy-900 text-white py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-4xl font-display font-bold mb-2">Enroll Now</h1>
          <p className="text-gray-300">Fill in your details to register for {batch.name}</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-10">
        {settings?.enrollment_instructions && (
          <div className="card bg-blue-50 border-blue-200 mb-6">
            <p className="text-blue-800 text-sm leading-relaxed">{settings.enrollment_instructions}</p>
          </div>
        )}

        {mutation.isError && (
          <div className="card bg-red-50 border-red-200 mb-6">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <p className="text-red-700 text-sm">
                {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Something went wrong. Please try again.'}
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="card space-y-5">
          <h2 className="font-display font-semibold text-navy-900 text-lg">Student Information</h2>

          <div>
            <label className="label">Full Name *</label>
            <input {...register('student_name')} className={`input-field ${errors.student_name ? 'error' : ''}`} placeholder="Enter your full name" />
            {errors.student_name && <p className="error-text">{errors.student_name.message}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="label">Email Address *</label>
              <input {...register('email')} type="email" className={`input-field ${errors.email ? 'error' : ''}`} placeholder="your@email.com" />
              {errors.email && <p className="error-text">{errors.email.message}</p>}
            </div>
            <div>
              <label className="label">Phone Number *</label>
              <input {...register('phone')} type="tel" className={`input-field ${errors.phone ? 'error' : ''}`} placeholder="10-digit mobile number" />
              {errors.phone && <p className="error-text">{errors.phone.message}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="label">Class / Grade *</label>
              <select {...register('grade')} className={`input-field ${errors.grade ? 'error' : ''}`}>
                <option value="">Select class</option>
                <option value="11">Class 11</option>
                <option value="12">Class 12</option>
                <option value="Dropper">Dropper / Repeater</option>
              </select>
              {errors.grade && <p className="error-text">{errors.grade.message}</p>}
            </div>
            <div>
              <label className="label">Exam Target *</label>
              <select {...register('exam_preference')} className={`input-field ${errors.exam_preference ? 'error' : ''}`}>
                <option value="">Select exam</option>
                <option value="neet">NEET (Medical)</option>
                <option value="jee">JEE (Engineering)</option>
              </select>
              {errors.exam_preference && <p className="error-text">{errors.exam_preference.message}</p>}
            </div>
          </div>

          <div className="border-t pt-5">
            <h3 className="font-medium text-gray-700 mb-4 text-sm">Parent / Guardian (optional)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="label">Guardian Name</label>
                <input {...register('guardian_name')} className="input-field" placeholder="Parent/guardian name" />
              </div>
              <div>
                <label className="label">Guardian Phone</label>
                <input {...register('guardian_phone')} type="tel" className="input-field" placeholder="Guardian's phone" />
              </div>
            </div>
          </div>

          <div className="border-t pt-5">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                {...register('privacy_acknowledged')}
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-gray-300 text-navy-600"
              />
              <span className="text-sm text-gray-600">
                I acknowledge that the information provided is accurate and I agree to the{' '}
                <span className="text-navy-700 font-medium">privacy policy</span>. I understand that my personal data will be used only for enrollment and communication purposes.
              </span>
            </label>
            {errors.privacy_acknowledged && <p className="error-text">{errors.privacy_acknowledged.message}</p>}
          </div>

          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full justify-center py-4 text-base"
          >
            {mutation.isPending ? 'Submitting...' : 'Submit Enrollment'}
          </button>
        </form>
      </div>
    </div>
  )
}
