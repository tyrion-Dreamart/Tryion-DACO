import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '@/services/api'
import { Spinner } from '@/components/ui'
import { formatCurrency, formatDate, daysDiff, statusLabel, statusBadge } from '@/utils/format'

const fetchSummary = () => api.get('/api/v1/dashboard/summary').then(r => r.data)
const fetchAlertas = () => api.get('/api/v1/alertas').then(r => r.data)

function KpiCard({ label, value, sub, subColor }) {
  return (
    <div className="kpi-card">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">{label}</p>
      <p className="text-2xl font-semibold text-white">{value}</p>
      {sub && <p className={`text-xs mt-1 ${subColor || 'text-gray-400'}`}>{sub}</p>}
    </div>
  )
}

function SectionHeader({ title, sub }) {
  return (
    <div className="mb-3">
      <p className="text-sm font-semibold text-white">{title}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchSummary,
    refetchInterval: 60000,
  })

  const { data: alertasData } = useQuery({
    queryKey: ['alertas'],
    queryFn: fetchAlertas,
    refetchInterval: 60000,
  })

  if (isLoading) return (
    <div className="flex justify-center items-center h-64"><Spinner /></div>
  )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm">Bienvenido, DACO Administrator</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard
          label="Facturado"
          value={formatCurrency(summary?.facturado ?? 0)}
          sub={summary?.periodo}
        />
        <KpiCard
          label="Cobrado"
          value={formatCurrency(summary?.cobrado ?? 0)}
          sub={`${summary?.pct_cobrado ?? 0}% del facturado`}
          subColor="text-emerald-400"
        />
        <KpiCard
          label="Por cobrar"
          value={formatCurrency(summary?.por_cobrar ?? 0)}
          sub={`${summary?.facturas_vigentes ?? 0} facturas vigentes`}
          subColor="text-amber-400"
        />
        <KpiCard
          label="Vencido"
          value={formatCurrency(summary?.vencido ?? 0)}
          sub={`${summary?.facturas_vencidas ?? 0} facturas vencidas`}
          subColor="text-red-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* CxC agrupado por corporativo */}
        <div className="card">
          <SectionHeader title="Cuentas por cobrar" sub="agrupado por corporativo" />
          {summary?.cxc_grupos?.length ? (
            <div className="space-y-4">
              {summary.cxc_grupos.map((grupo, gi) => (
                <div key={gi} className="border border-gray-700 rounded-lg overflow-hidden">
                  {/* Corporativo header */}
                  <div className="bg-gray-700/50 px-3 py-2 flex justify-between items-center">
                    <p className="text-sm font-semibold text-white">{grupo.corporativo}</p>
                    <p className="text-sm font-semibold text-amber-400">{formatCurrency(grupo.total_saldo)}</p>
                  </div>
                  {/* Sub-cuentas */}
                  {grupo.sub_cuentas.map((sub, si) => (
                    <div key={si} className="px-3 py-2 border-t border-gray-700/50">
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <p className="text-xs font-medium text-gray-200">{sub.legal_name}</p>
                          {sub.rfc && <p className="text-xs text-gray-500">RFC: {sub.rfc}</p>}
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-amber-400 font-medium">{formatCurrency(sub.saldo)}</p>
                          <p className="text-xs text-gray-500">{sub.facturas} factura{sub.facturas !== 1 ? 's' : ''}</p>
                        </div>
                      </div>
                      {/* Detalle facturas */}
                      {sub.detalle?.map((inv, ii) => {
                        const dias = inv.due_date ? daysDiff(inv.due_date) : null
                        return (
                          <div key={ii} className="flex justify-between items-center mt-1 pl-2 border-l-2 border-gray-600">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-400">{inv.folio}</span>
                              {dias !== null && (
                                <span className={`text-xs ${dias < 0 ? 'text-red-400' : dias <= 7 ? 'text-amber-400' : 'text-gray-500'}`}>
                                  {dias < 0 ? `${Math.abs(dias)}d vencida` : `${dias}d`}
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-300">{formatCurrency(inv.balance)}</span>
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm text-center py-6">Sin cuentas por cobrar</p>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Cotizaciones activas */}
          <div className="card">
            <SectionHeader title="Cotizaciones activas" />
            <div className="space-y-2">
              {[
                { label: 'En revisión', val: summary?.cotizaciones?.draft ?? 0 },
                { label: 'Enviadas', val: summary?.cotizaciones?.sent ?? 0 },
                { label: 'Aprobadas', val: summary?.cotizaciones?.approved ?? 0, color: 'text-emerald-400' },
                { label: 'Rechazadas', val: summary?.cotizaciones?.rejected ?? 0, color: 'text-red-400' },
                { label: 'Valor pipeline', val: formatCurrency(summary?.cotizaciones?.pipeline ?? 0) },
              ].map(item => (
                <div key={item.label} className="flex justify-between items-center py-1 border-b border-gray-700/50 last:border-0">
                  <span className="text-sm text-gray-400">{item.label}</span>
                  <span className={`text-sm font-medium ${item.color || 'text-white'}`}>
                    {typeof item.val === 'number' ? item.val : item.val}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Clientes */}
          <div className="card">
            <SectionHeader title="Clientes" />
            <div className="space-y-2">
              {[
                { label: 'Total clientes', val: summary?.clientes_total ?? 0 },
                { label: 'Con factura vigente', val: summary?.facturas_vigentes ?? 0 },
                { label: 'Sin actividad +60d', val: summary?.clientes_inactivos ?? 0, color: 'text-amber-400' },
              ].map(item => (
                <div key={item.label} className="flex justify-between items-center py-1 border-b border-gray-700/50 last:border-0">
                  <span className="text-sm text-gray-400">{item.label}</span>
                  <span className={`text-sm font-medium ${item.color || 'text-white'}`}>{item.val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Alertas */}
          <div className="card">
            <SectionHeader title="Alertas" sub="requieren atención" />
            {alertasData?.items?.length ? (
              <div className="space-y-2">
                {alertasData.items.slice(0, 4).map(a => (
                  <div
                    key={a.id}
                    className={`flex items-center justify-between p-2 rounded-lg cursor-pointer ${
                      a.priority === 'high' ? 'bg-red-900/20' : a.priority === 'medium' ? 'bg-amber-900/20' : 'bg-blue-900/20'
                    }`}
                    onClick={() => navigate('/alertas')}
                  >
                    <div>
                      <p className={`text-xs font-medium ${a.priority === 'high' ? 'text-red-400' : a.priority === 'medium' ? 'text-amber-400' : 'text-blue-400'}`}>
                        {a.title}
                      </p>
                      <p className="text-xs text-gray-500">{a.subtitle}</p>
                    </div>
                    <span className={`text-xs badge ${a.priority === 'high' ? 'badge-red' : a.priority === 'medium' ? 'badge-amber' : 'badge-blue'}`}>
                      {a.label}
                    </span>
                  </div>
                ))}
                {alertasData.items.length > 4 && (
                  <button onClick={() => navigate('/alertas')} className="text-xs text-gray-400 hover:text-white w-full text-center pt-1">
                    Ver todas ({alertasData.items.length}) →
                  </button>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-sm text-center py-3">Sin alertas activas ✓</p>
            )}
          </div>
        </div>
      </div>

      {/* Mix de servicios */}
      <div className="card">
        <SectionHeader title="Mix de servicios" sub={summary?.periodo} />
        {summary?.mix_servicios?.length ? (
          <table className="daco-table">
            <thead>
              <tr>
                <th>Servicio</th>
                <th className="text-right">Facturado</th>
                <th className="text-right">%</th>
              </tr>
            </thead>
            <tbody>
              {summary.mix_servicios.map((s, i) => (
                <tr key={i}>
                  <td className="text-gray-300">{s.name}</td>
                  <td className="text-right text-white">{formatCurrency(s.amount)}</td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-brand-500 rounded-full" style={{ width: `${s.pct}%` }} />
                      </div>
                      <span className="text-xs text-gray-400 w-8">{s.pct}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-500 text-sm text-center py-4">Sin datos de servicios</p>
        )}
      </div>
    </div>
  )
}
