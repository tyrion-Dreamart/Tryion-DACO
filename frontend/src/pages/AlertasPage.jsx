import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Page, Spinner, EmptyState } from '@/components/ui'

const fetchAlertas = () => api.get('/api/v1/alertas').then(r => r.data)

const PRIORITY_COLORS = {
  high:   { bg: 'bg-red-900/20',    border: 'border-red-900/50',    text: 'text-red-400',    badge: 'badge-red' },
  medium: { bg: 'bg-amber-900/20',  border: 'border-amber-900/50',  text: 'text-amber-400',  badge: 'badge-amber' },
  low:    { bg: 'bg-blue-900/20',   border: 'border-blue-900/50',   text: 'text-blue-400',   badge: 'badge-blue' },
}

const TYPE_ICONS = {
  overdue:   '🔴',
  due_soon:  '🟡',
  expired:   '⭕',
  expiring:  '🟠',
}

export default function AlertasPage() {
  const navigate = useNavigate()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['alertas-page'],
    queryFn: fetchAlertas,
    refetchInterval: 60000,
  })

  const handleAction = (alerta) => {
    if (alerta.entity_type === 'invoice') navigate('/cobranza')
    if (alerta.entity_type === 'quote') navigate('/cotizaciones')
  }

  return (
    <Page>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Alertas</h1>
          <p className="text-gray-400 text-sm">Actualizadas automáticamente</p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary text-xs">
          Actualizar
        </button>
      </div>

      {/* Summary KPIs */}
      {data && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="kpi-card border-red-900/30">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Alta prioridad</p>
            <p className="text-2xl font-semibold text-red-400">{data.high}</p>
            <p className="text-xs text-gray-500 mt-1">Acción inmediata</p>
          </div>
          <div className="kpi-card border-amber-900/30">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Media prioridad</p>
            <p className="text-2xl font-semibold text-amber-400">{data.medium}</p>
            <p className="text-xs text-gray-500 mt-1">Atender pronto</p>
          </div>
          <div className="kpi-card border-blue-900/30">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Baja prioridad</p>
            <p className="text-2xl font-semibold text-blue-400">{data.low}</p>
            <p className="text-xs text-gray-500 mt-1">Informativo</p>
          </div>
        </div>
      )}

      {/* Alerts list */}
      {isLoading ? (
        <div className="flex justify-center py-10"><Spinner /></div>
      ) : data?.items?.length ? (
        <div className="space-y-3">
          {data.items.map(alerta => {
            const colors = PRIORITY_COLORS[alerta.priority] || PRIORITY_COLORS.low
            return (
              <div
                key={alerta.id}
                className={`${colors.bg} border ${colors.border} rounded-xl p-4 flex items-center justify-between`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-xl mt-0.5">{TYPE_ICONS[alerta.type] || '⚠️'}</span>
                  <div>
                    <p className={`text-sm font-medium ${colors.text}`}>{alerta.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{alerta.subtitle}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span className={`badge ${colors.badge}`}>{alerta.label}</span>
                  <button
                    onClick={() => handleAction(alerta)}
                    className="btn-ghost text-xs py-1"
                  >
                    Ver →
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">✅</p>
          <p className="text-white font-medium">Sin alertas activas</p>
          <p className="text-gray-400 text-sm mt-1">Todo está al corriente</p>
        </div>
      )}
    </Page>
  )
}
