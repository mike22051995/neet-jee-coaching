import { Link } from 'react-router-dom'
import { Mail, Phone, MapPin, Youtube, BookOpen } from 'lucide-react'
import { useSiteSettings } from '@/hooks/usePublicData'

export function Footer() {
  const { data: settings } = useSiteSettings()

  return (
    <footer className="bg-navy-950 text-gray-300">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 text-white font-display font-bold text-lg mb-3">
              <BookOpen className="h-6 w-6 text-gold-400" />
              {settings?.institute_name || 'Excellence Coaching'}
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">
              {settings?.tagline || 'Preparing students for NEET & JEE with dedication and expertise.'}
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-3">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              {[['/', 'Home'], ['/courses', 'Courses'], ['/schedule', 'Schedule'], ['/enroll', 'Enroll']].map(([to, label]) => (
                <li key={to}>
                  <Link to={to} className="hover:text-gold-400 transition-colors">{label}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-white font-semibold mb-3">Contact Us</h3>
            <ul className="space-y-2 text-sm">
              {settings?.contact_phone && (
                <li className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-gold-400 shrink-0" />
                  <a href={`tel:${settings.contact_phone}`} className="hover:text-gold-400 transition-colors">
                    {settings.contact_phone}
                  </a>
                </li>
              )}
              {settings?.contact_email && (
                <li className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-gold-400 shrink-0" />
                  <a href={`mailto:${settings.contact_email}`} className="hover:text-gold-400 transition-colors">
                    {settings.contact_email}
                  </a>
                </li>
              )}
              {settings?.contact_address && (
                <li className="flex items-start gap-2">
                  <MapPin className="h-4 w-4 text-gold-400 shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{settings.contact_address}</span>
                </li>
              )}
              {settings?.social_youtube && (
                <li className="flex items-center gap-2">
                  <Youtube className="h-4 w-4 text-gold-400 shrink-0" />
                  <a href={settings.social_youtube} target="_blank" rel="noopener noreferrer" className="hover:text-gold-400 transition-colors">
                    YouTube Channel
                  </a>
                </li>
              )}
            </ul>
          </div>
        </div>

        <div className="border-t border-navy-800 mt-8 pt-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} {settings?.institute_name || 'Excellence Coaching Institute'}. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
