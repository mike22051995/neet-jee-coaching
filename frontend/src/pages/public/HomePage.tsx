import { Link } from 'react-router-dom'
import { CheckCircle, Users, Clock, BookOpen, ChevronDown, ArrowRight, Phone, Mail } from 'lucide-react'
import { useSiteSettings, useActiveBatch } from '@/hooks/usePublicData'
import { Batch } from '@/services/api'

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

function HeroSection({ settings, batch }: { settings: ReturnType<typeof useSiteSettings>['data'], batch: { batch: Batch | null } | undefined }) {
  const activeBatch = batch?.batch
  return (
    <section className="bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 text-white py-20 px-4">
      <div className="max-w-4xl mx-auto text-center animate-fade-in">
        <div className="inline-flex items-center gap-2 bg-gold-500/20 text-gold-300 text-sm font-medium px-4 py-1.5 rounded-full mb-6 border border-gold-500/30">
          <span className="w-2 h-2 bg-gold-400 rounded-full animate-pulse"></span>
          {activeBatch?.status === 'enrollment_open' ? 'Enrollment Open Now' : 'NEET & JEE Preparation'}
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold leading-tight mb-6">
          {settings?.hero_heading || (
            <>
              Crack <span className="text-gold-400">NEET & JEE</span>
              <br />with Expert Guidance
            </>
          )}
        </h1>

        <p className="text-lg sm:text-xl text-gray-300 max-w-2xl mx-auto mb-8 leading-relaxed">
          {settings?.hero_subheading || 'Structured curriculum, experienced faculty, and proven strategies to help you achieve your medical and engineering dreams.'}
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/enroll" className="btn-secondary text-base px-8 py-4 shadow-lg">
            Enroll Now <ArrowRight className="h-5 w-5" />
          </Link>
          <Link to="/courses" className="btn-outline text-base px-8 py-4 border-gray-400 text-gray-200 hover:bg-white/10">
            View Courses
          </Link>
        </div>

        {activeBatch && (
          <div className="mt-10 inline-flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 border border-white/20">
            <span className="text-sm text-gray-300">Current Batch:</span>
            <span className="text-white font-semibold">{activeBatch.name}</span>
            {activeBatch.fee_amount && (
              <>
                <span className="text-gray-500">·</span>
                <span className="text-gold-400 font-semibold">{formatCurrency(activeBatch.fee_amount)}</span>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  )
}

function FeatureCards({ settings }: { settings: ReturnType<typeof useSiteSettings>['data'] }) {
  let items: Array<{ title: string; body: string }> = []
  try {
    if (settings?.why_choose_us_json) items = JSON.parse(settings.why_choose_us_json)
  } catch {}

  if (!items.length) {
    items = [
      { title: 'Expert Faculty', body: 'Experienced teachers with deep subject knowledge and exam expertise.' },
      { title: 'Structured Curriculum', body: 'Comprehensive syllabus coverage aligned with the latest exam patterns.' },
      { title: 'Regular Tests', body: 'Weekly tests and mock exams to track your preparation progress.' },
      { title: 'Doubt Clearing', body: 'Dedicated sessions to resolve doubts and strengthen weak areas.' },
    ]
  }

  const icons = [BookOpen, Users, CheckCircle, Clock]

  return (
    <section className="py-16 px-4 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="section-heading">Why Choose Us?</h2>
          <p className="section-subheading">Everything you need for exam success</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {items.map((item, i) => {
            const Icon = icons[i % icons.length]
            return (
              <div key={i} className="card hover:shadow-md transition-shadow">
                <div className="w-12 h-12 bg-navy-100 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="h-6 w-6 text-navy-700" />
                </div>
                <h3 className="font-display font-semibold text-navy-900 text-lg mb-2">{item.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{item.body}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function BatchHighlight({ batch }: { batch: Batch }) {
  return (
    <section className="py-16 px-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="section-heading">Current Batch</h2>
        </div>
        <div className="bg-navy-50 border border-navy-200 rounded-2xl p-8">
          <div className="flex flex-col md:flex-row gap-6 items-start">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <h3 className="text-2xl font-display font-bold text-navy-900">{batch.name}</h3>
                <span className={`badge ${batch.status === 'enrollment_open' ? 'badge-green' : 'badge-blue'}`}>
                  {batch.status === 'enrollment_open' ? 'Enrollment Open' : batch.status.replace('_', ' ')}
                </span>
              </div>
              {batch.description && <p className="text-gray-600 mb-4">{batch.description}</p>}
              <div className="grid grid-cols-2 gap-4 text-sm">
                {batch.start_date && (
                  <div>
                    <span className="text-gray-500">Starts:</span>
                    <p className="font-medium">{new Date(batch.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                  </div>
                )}
                {batch.class_days && (
                  <div>
                    <span className="text-gray-500">Class Days:</span>
                    <p className="font-medium capitalize">{batch.class_days.join(', ')}</p>
                  </div>
                )}
                {batch.class_start_time && (
                  <div>
                    <span className="text-gray-500">Timing (IST):</span>
                    <p className="font-medium">{batch.class_start_time} – {batch.class_end_time}</p>
                  </div>
                )}
                {batch.subjects && (
                  <div>
                    <span className="text-gray-500">Subjects:</span>
                    <p className="font-medium">{batch.subjects.join(', ')}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="text-center bg-white rounded-xl p-6 shadow-sm border border-navy-100 min-w-[180px]">
              <p className="text-sm text-gray-500 mb-1">Course Fee</p>
              <p className="text-3xl font-display font-bold text-navy-900">
                {batch.fee_amount ? formatCurrency(batch.fee_amount) : 'Contact Us'}
              </p>
              {batch.total_seats && (
                <p className="text-xs text-gray-500 mt-2">
                  {batch.available_seats ?? (batch.total_seats - batch.confirmed_enrollment_count)} seats left
                </p>
              )}
              <Link to="/enroll" className="btn-primary text-sm mt-4 w-full">Enroll Now</Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function FAQSection({ settings }: { settings: ReturnType<typeof useSiteSettings>['data'] }) {
  let faqs: Array<{ question: string; answer: string }> = []
  try {
    if (settings?.faq_json) faqs = JSON.parse(settings.faq_json)
  } catch {}

  if (!faqs.length) {
    faqs = [
      { question: 'When do classes start?', answer: 'Please check the current batch details above or contact us for the latest schedule.' },
      { question: 'What is the mode of teaching?', answer: 'Classes are conducted online via video conferencing. Details are shared after enrollment confirmation.' },
      { question: 'How do I pay the fees?', answer: 'Fees are accepted via UPI (Google Pay, PhonePe, Paytm). Payment instructions are shown after form submission.' },
      { question: 'Can I get a demo class?', answer: 'Please contact us to know about demo class availability.' },
    ]
  }

  return (
    <section className="py-16 px-4 bg-gray-50">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="section-heading">Frequently Asked Questions</h2>
        </div>
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <details key={i} className="card cursor-pointer group">
              <summary className="flex justify-between items-center font-semibold text-navy-900 list-none">
                {faq.question}
                <ChevronDown className="h-5 w-5 text-gray-400 group-open:rotate-180 transition-transform shrink-0 ml-3" />
              </summary>
              <p className="mt-3 text-gray-600 leading-relaxed">{faq.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

function ContactSection({ settings }: { settings: ReturnType<typeof useSiteSettings>['data'] }) {
  return (
    <section className="py-16 px-4 bg-navy-900 text-white">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl font-display font-bold mb-3">Get in Touch</h2>
        <p className="text-gray-300 mb-8">Have questions? We're here to help you.</p>
        <div className="flex flex-col sm:flex-row gap-6 justify-center">
          {settings?.contact_phone && (
            <a href={`tel:${settings.contact_phone}`} className="flex items-center gap-3 bg-navy-800 hover:bg-navy-700 rounded-xl px-6 py-4 transition-colors">
              <Phone className="h-5 w-5 text-gold-400" />
              <div className="text-left">
                <p className="text-xs text-gray-400">Call Us</p>
                <p className="font-semibold">{settings.contact_phone}</p>
              </div>
            </a>
          )}
          {settings?.contact_email && (
            <a href={`mailto:${settings.contact_email}`} className="flex items-center gap-3 bg-navy-800 hover:bg-navy-700 rounded-xl px-6 py-4 transition-colors">
              <Mail className="h-5 w-5 text-gold-400" />
              <div className="text-left">
                <p className="text-xs text-gray-400">Email Us</p>
                <p className="font-semibold">{settings.contact_email}</p>
              </div>
            </a>
          )}
        </div>
        <div className="mt-8">
          <Link to="/enroll" className="btn-secondary px-10 py-4 text-base shadow-lg">
            Start Your Journey — Enroll Today
          </Link>
        </div>
      </div>
    </section>
  )
}

export function HomePage() {
  const { data: settings } = useSiteSettings()
  const { data: batchData } = useActiveBatch()

  return (
    <>
      <HeroSection settings={settings} batch={batchData} />
      <FeatureCards settings={settings} />
      {batchData?.batch && <BatchHighlight batch={batchData.batch} />}
      <FAQSection settings={settings} />
      <ContactSection settings={settings} />
    </>
  )
}
