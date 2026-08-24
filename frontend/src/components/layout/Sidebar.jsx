import { NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import clsx from 'clsx'

const navItems = [
  { to: '/',             icon: '⊞', label: 'Dashboard' },
  { to: '/clientes',     icon: '🏢', label: 'Clientes' },
  { to: '/cotizaciones', icon: '📄', label: 'Cotizaciones' },
  { to: '/facturas',     icon: '🧾', label: 'Facturas' },
  { to: '/cobranza',     icon: '💳', label: 'Cobranza' },
  { to: '/alertas',      icon: '🔔', label: 'Alertas' },
  { to: '/reportes',     icon: '📊', label: 'Reportes' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()

  return (
    <aside className="w-52 min-w-[208px] bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="text-white font-semibold text-sm">DACO</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx('nav-item', isActive && 'active')
            }
          >
            <span className="text-base leading-none">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-7 h-7 rounded-full bg-brand-600/30 flex items-center justify-center text-xs font-medium text-brand-400">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-200 truncate">
              {user?.full_name || 'Usuario'}
            </p>
            <p className="text-xs text-gray-500 capitalize">{user?.role || ''}</p>
          </div>
        </div>
        <button onClick={logout} className="btn-ghost w-full text-left text-xs py-1.5">
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
