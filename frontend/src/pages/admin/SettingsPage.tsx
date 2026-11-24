import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Upload, Eye, EyeOff } from 'lucide-react'
import { adminApi } from '@/services/api'

type Tab = 'institute' | 'upi' | 'content' | 'social'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card mb-4">
      <h2 className="font-semibold text-navy-900 mb-4 pb-2 border-b text-sm">{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export function SettingsPage() {
  const [tab, setTab] = useState<Tab>('institute')
  const [form, setForm] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)
  const logoRef = useRef<HTMLInputElement>(null)
  const qrRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()

  const { data: settings, isLoading } = useQuery({
    queryKey: ['admin-settings'],
    queryFn: adminApi.getSettings,
  })

  useEffect(() => {
    if (settings) setForm(settings as unknown as Record<string, string>)
  }, [settings])

  const saveMutation = useMutation({
    mutationFn: (data: Record<string, any>) => adminApi.updateSettings(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-settings'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    },
  })

  const logoMutation = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData(); fd.append('file', file)
      return adminApi.uploadLogo(fd)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-settings'] }),
  })

  const qrMutation = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData(); fd.append('file', file)
      return adminApi.uploadQR(fd)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-settings'] }),
  })

  const f = (key: string) => form[key] || ''
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handleSave = () => {
    const payload: Record<string, any> = {}
    const textFields = [
      'institute_name', 'tagline', 'contact_email', 'contact_phone', 'contact_address',
      'hero_heading', 'hero_subheading', 'about_text', 'enrollment_instructions',
      'upi_id', 'upi_name', 'payment_instructions',
      'facebook_url', 'instagram_url', 'youtube_url', 'twitter_url',
      'why_choose_us_json', 'faculty_json', 'faq_json',
    ]
    textFields.forEach(k => { if (form[k] !== undefined) payload[k] = form[k] })
    saveMutation.mutate(payload)
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'institute', label: 'Institute' },
    { id: 'upi', label: 'UPI / Payment' },
    { id: 'content', label: 'Website Content' },
    { id: 'social', label: 'Social & Links' },
  ]

  if (isLoading) return <div className="text-center py-10 text-gray-400">Loading settings...</div>

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-display font-bold text-navy-900">Site Settings</h1>
        <button
          onClick={handleSave}
          disabled={saveMutation.isPending}
          className="btn-primary text-sm px-5 py-2 flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          {saveMutation.isPending ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? 'border-navy-700 text-navy-900'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'institute' && (
        <>
          <Section title="Institute Information">
            <Field label="Institute Name">
              <input value={f('institute_name')} onChange={set('institute_name')} className="input-field" />
            </Field>
            <Field label="Tagline">
              <input value={f('tagline')} onChange={set('tagline')} className="input-field" placeholder="Your inspiring tagline" />
            </Field>
            <Field label="Contact Email">
              <input value={f('contact_email')} onChange={set('contact_email')} type="email" className="input-field" />
            </Field>
            <Field label="Contact Phone">
              <input value={f('contact_phone')} onChange={set('contact_phone')} className="input-field" />
            </Field>
            <Field label="Address">
              <textarea value={f('contact_address')} onChange={set('contact_address')} rows={3} className="input-field" />
            </Field>
          </Section>

          <Section title="Logo">
            {settings?.logo_path && (
              <img src={`/uploads/public/${settings.logo_path.split('/').pop()}`} alt="Logo" className="h-16 mb-3 object-contain" />
            )}
            <input ref={logoRef} type="file" accept="image/*" className="hidden"
              onChange={e => { if (e.target.files?.[0]) logoMutation.mutate(e.target.files[0]) }} />
            <button onClick={() => logoRef.current?.click()} className="btn-outline text-sm flex items-center gap-2">
              <Upload className="h-4 w-4" /> {logoMutation.isPending ? 'Uploading...' : 'Upload Logo'}
            </button>
          </Section>
        </>
      )}

      {tab === 'upi' && (
        <Section title="UPI Payment Configuration">
          <Field label="UPI ID">
            <input value={f('upi_id')} onChange={set('upi_id')} className="input-field" placeholder="yourname@upi" />
          </Field>
          <Field label="UPI Account Name">
            <input value={f('upi_name')} onChange={set('upi_name')} className="input-field" />
          </Field>
          <Field label="Payment Instructions (shown to students)">
            <textarea value={f('payment_instructions')} onChange={set('payment_instructions')} rows={5} className="input-field" placeholder="Step-by-step instructions..." />
          </Field>
          <div className="mt-4">
            <label className="label">UPI QR Code</label>
            {settings?.upi_qr_path && (
              <img src={`/uploads/public/${settings.upi_qr_path.split('/').pop()}`} alt="QR Code" className="h-40 mb-3 object-contain" />
            )}
            <input ref={qrRef} type="file" accept="image/*" className="hidden"
              onChange={e => { if (e.target.files?.[0]) qrMutation.mutate(e.target.files[0]) }} />
            <button onClick={() => qrRef.current?.click()} className="btn-outline text-sm flex items-center gap-2">
              <Upload className="h-4 w-4" /> {qrMutation.isPending ? 'Uploading...' : 'Upload QR Code'}
            </button>
          </div>
        </Section>
      )}

      {tab === 'content' && (
        <>
          <Section title="Hero Section">
            <Field label="Heading">
              <input value={f('hero_heading')} onChange={set('hero_heading')} className="input-field" />
            </Field>
            <Field label="Subheading">
              <textarea value={f('hero_subheading')} onChange={set('hero_subheading')} rows={3} className="input-field" />
            </Field>
          </Section>
          <Section title="About Section">
            <Field label="About Text">
              <textarea value={f('about_text')} onChange={set('about_text')} rows={6} className="input-field" />
            </Field>
          </Section>
          <Section title="Enrollment Instructions">
            <Field label="Shown at top of enrollment form">
              <textarea value={f('enrollment_instructions')} onChange={set('enrollment_instructions')} rows={4} className="input-field" />
            </Field>
          </Section>
          <Section title="Advanced (JSON — edit with care)">
            <Field label={`"Why Choose Us" items (JSON array of {icon, title, description})`}>
              <textarea value={f('why_choose_us_json')} onChange={set('why_choose_us_json')} rows={6} className="input-field font-mono text-xs" />
            </Field>
            <Field label={`FAQ items (JSON array of {question, answer})`}>
              <textarea value={f('faq_json')} onChange={set('faq_json')} rows={6} className="input-field font-mono text-xs" />
            </Field>
            <Field label={`Faculty (JSON array of {name, qualification, subject, photo_url})`}>
              <textarea value={f('faculty_json')} onChange={set('faculty_json')} rows={6} className="input-field font-mono text-xs" />
            </Field>
          </Section>
        </>
      )}

      {tab === 'social' && (
        <Section title="Social Media Links">
          {(['facebook_url', 'instagram_url', 'youtube_url', 'twitter_url'] as const).map(key => (
            <Field key={key} label={key.replace('_url', '').charAt(0).toUpperCase() + key.replace('_url', '').slice(1)}>
              <input value={f(key)} onChange={set(key)} className="input-field" placeholder="https://..." />
            </Field>
          ))}
        </Section>
      )}

      {saveMutation.isError && (
        <p className="text-sm text-red-600 mt-2">
          {(saveMutation.error as any)?.response?.data?.detail || 'Save failed'}
        </p>
      )}
    </div>
  )
}
