import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import dacoLogo from '@/assets/daco-logo.png'

const NAV_ITEMS = [
  { to: '/',            label: 'Dashboard',     icon: '◉' },
  { to: '/clientes',    label: 'Clientes',       icon: '⬡' },
  { to: '/cotizaciones',label: 'Cotizaciones',   icon: '◈' },
  { to: '/facturas',    label: 'Facturas',       icon: '◧' },
  { to: '/cobranza',    label: 'Cobranza',       icon: '◎' },
  { to: '/alertas',     label: 'Alertas',        icon: '◬' },
  { to: '/reportes',    label: 'Reportes',       icon: '▦' },
]

export default function AppLayout() {
  const logout = useAuthStore(s => s.logout)
  const user = useAuthStore(s => s.user)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#1a1714' }}>
      {/* Sidebar */}
      <aside className="w-56 flex flex-col border-r" style={{ backgroundColor: '#100e0c', borderColor: '#2a2420' }}>

        {/* Logo */}
        <div className="px-5 py-6 border-b" style={{ borderColor: '#2a2420' }}>
          <img src={dacoLogo} alt="DACO GROUP" className="w-full max-h-12 object-contain" />
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 ${
                  isActive
                    ? 'text-brand-100 font-medium'
                    : 'text-brand-400 hover:text-brand-200 hover:bg-dark-800'
                }`
              }
              style={({ isActive }) => isActive ? {
                backgroundColor: '#7a675a22',
                borderLeft: '2px solid #7a675a',
                paddingLeft: '10px',
              } : {}}
            >
              <span className="text-brand-500 text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t" style={{ borderColor: '#2a2420' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-brand-50"
              style={{ backgroundColor: '#7a675a' }}>
              {user?.full_name?.charAt(0) || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-brand-200 truncate">{user?.full_name || 'Admin'}</p>
              <p className="text-xs text-brand-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-xs text-brand-500 hover:text-brand-300 text-left transition-colors"
          >
            Cerrar sesión →
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto" style={{ backgroundColor: '#1a1714' }}>
        <Outlet />
      </main>
    </div>
  )
}
