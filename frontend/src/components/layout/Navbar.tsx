import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { Menu, X, BookOpen } from 'lucide-react'
import { useSiteSettings } from '@/hooks/usePublicData'
import clsx from 'clsx'

export function Navbar() {
  const [open, setOpen] = useState(false)
  const { data: settings } = useSiteSettings()
  const name = settings?.institute_name || 'Excellence Coaching'

  const links = [
    { to: '/', label: 'Home' },
    { to: '/courses', label: 'Courses' },
    { to: '/schedule', label: 'Schedule' },
    { to: '/enroll', label: 'Enroll' },
  ]

  return (
    <nav className="sticky top-0 z-50 bg-navy-900 shadow-lg">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 text-white font-display font-bold text-lg shrink-0">
            {settings?.logo_path ? (
              <img src={settings.logo_path} alt="Logo" className="h-8 w-8 rounded object-contain" />
            ) : (
              <BookOpen className="h-7 w-7 text-gold-400" />
            )}
            <span className="hidden sm:block">{name}</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {links.map(l => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  clsx('px-4 py-2 rounded-md text-sm font-medium transition-colors', {
                    'bg-navy-700 text-white': isActive,
                    'text-gray-300 hover:text-white hover:bg-navy-800': !isActive,
                  })
                }
              >
                {l.label}
              </NavLink>
            ))}
            <Link to="/enroll" className="ml-2 btn-secondary text-sm px-4 py-2">
              Enroll Now
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden text-gray-300 hover:text-white p-2"
            onClick={() => setOpen(o => !o)}
            aria-label="Toggle menu"
          >
            {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-navy-800 border-t border-navy-700 px-4 py-3 space-y-1">
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                clsx('block px-3 py-2 rounded-md text-sm font-medium', {
                  'bg-navy-700 text-white': isActive,
                  'text-gray-300 hover:bg-navy-700 hover:text-white': !isActive,
                })
              }
            >
              {l.label}
            </NavLink>
          ))}
          <Link
            to="/enroll"
            onClick={() => setOpen(false)}
            className="block mt-2 btn-secondary text-center text-sm py-2"
          >
            Enroll Now
          </Link>
        </div>
      )}
    </nav>
  )
}
