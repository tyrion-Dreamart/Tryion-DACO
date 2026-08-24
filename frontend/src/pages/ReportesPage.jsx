import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { Page, Spinner } from '@/components/ui'
import { formatCurrency, formatDate, statusLabel, statusBadge } from '@/utils/format'

const fetchEstadoCuenta = (clientId) =>
  api.get(`/api/v1/reportes/estado-cuenta${clientId ? `?client_id=${clientId}` : ''}`).then(r => r.data)

const fetchResumen = (year) =>
  api.get(`/api/v1/reportes/resumen-ejecutivo?year=${year}`).then(r => r.data)

const fetchAntiguedad = () =>
  api.get('/api/v1/reportes/antiguedad-saldos').then(r => r.data)

const fetchPipeline = () =>
  api.get('/api/v1/reportes/pipeline').then(r => r.data)

const fetchClients = () =>
  api.get('/api/v1/clients?page_size=100').then(r => r.data)

const TABS = [
  { id: 'estado', label: '📋 Estado de cuenta' },
  { id: 'resumen', label: '📊 Resumen ejecutivo' },
  { id: 'antiguedad', label: '⏱ Antigüedad de saldos' },
  { id: 'pipeline', label: '🎯 Pipeline' },
]

export default function ReportesPage() {
  const [tab, setTab] = useState('estado')
  const [clientId, setClientId] = useState('')
  const [year, setYear] = useState(new Date().getFullYear())

  const { data: clients } = useQuery({ queryKey: ['clients-all'], queryFn: fetchClients })

  const { data: estadoData, isLoading: loadingEstado } = useQuery({
    queryKey: ['reporte-estado', clientId],
    queryFn: () => fetchEstadoCuenta(clientId),
    enabled: tab === 'estado',
  })

  const { data: resumenData, isLoading: loadingResumen } = useQuery({
    queryKey: ['reporte-resumen', year],
    queryFn: () => fetchResumen(year),
    enabled: tab === 'resumen',
  })

  const { data: antiguedadData, isLoading: loadingAntiguedad } = useQuery({
    queryKey: ['reporte-antiguedad'],
    queryFn: fetchAntiguedad,
    enabled: tab === 'antiguedad',
  })

  const { data: pipelineData, isLoading: loadingPipeline } = useQuery({
    queryKey: ['reporte-pipeline'],
    queryFn: fetchPipeline,
    enabled: tab === 'pipeline',
  })

  const exportUrl = `${import.meta.env.VITE_API_URL}/api/v1/exportar/estado-cuenta${clientId ? `?client_id=${clientId}` : ''}`

const handleExport = async () => {
    const token = localStorage.getItem('access_token')
    const url = `${import.meta.env.VITE_API_URL}/api/v1/exportar/estado-cuenta${clientId ? `?client_id=${clientId}` : ''}`
    const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    const blob = await response.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `estado_cuenta_${new Date().toISOString().slice(0,10)}.xlsx`
    link.click()
  }
  return (
    <Page>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-white">Reportes</h1>
        <p className="text-gray-400 text-sm">Análisis financiero y operativo</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={tab === t.id ? 'btn-primary text-xs py-1.5' : 'btn-secondary text-xs py-1.5'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Estado de cuenta ──────────────────────────────────────────────── */}
      {tab === 'estado' && (
        <div>
          <div className="flex gap-3 mb-4 items-center">
            <select
              className="input max-w-xs"
              value={clientId}
              onChange={e => setClientId(e.target.value)}
            >
              <option value="">Todos los clientes</option>
              {clients?.items?.map(c => (
                <option key={c.id} value={c.id}>{c.trade_name || c.legal_name}</option>
              ))}
            </select>
<button onClick={handleExport} className="btn-secondary text-xs py-1.5">
              📥 Exportar Excel
            </button>
          </div>

          {loadingEstado ? (
            <div className="flex justify-center py-10"><Spinner /></div>
          ) : estadoData?.clientes?.map(item => (
            <div key={item.client.id} className="card mb-4">
              <div className="flex justify-between items-start mb-4 pb-4 border-b border-gray-700">
                <div>
                  <h2 className="text-base font-semibold text-white">{item.client.legal_name}</h2>
                  {item.client.trade_name && <p className="text-xs text-gray-400">{item.client.trade_name}</p>}
                  {item.client.rfc && <p className="text-xs text-gray-500">RFC: {item.client.rfc}</p>}
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">Saldo pendiente</p>
                  <p className={`text-lg font-semibold ${item.resumen.saldo_pendiente > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {formatCurrency(item.resumen.saldo_pendiente)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">Facturado</p>
                  <p className="text-white font-medium">{formatCurrency(item.resumen.total_facturado)}</p>
                </div>
                <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">Cobrado</p>
                  <p className="text-emerald-400 font-medium">{formatCurrency(item.resumen.total_cobrado)}</p>
                </div>
                <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">Pendiente</p>
                  <p className="text-amber-400 font-medium">{formatCurrency(item.resumen.saldo_pendiente)}</p>
                </div>
              </div>

              {item.facturas.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Facturas</p>
                  <table className="daco-table">
                    <thead>
                      <tr>
                        <th>Folio</th>
                        <th>Fecha</th>
                        <th>Vence</th>
                        <th className="text-right">Total</th>
                        <th className="text-right">Cobrado</th>
                        <th className="text-right">Saldo</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {item.facturas.map(f => (
                        <tr key={f.folio}>
                          <td className="font-medium text-white">{f.folio}</td>
                          <td className="text-gray-400">{formatDate(f.issue_date)}</td>
                          <td className="text-gray-400">{f.due_date ? formatDate(f.due_date) : '—'}</td>
                          <td className="text-right text-white">{formatCurrency(f.total)}</td>
                          <td className="text-right text-emerald-400">{formatCurrency(f.paid_amount)}</td>
                          <td className="text-right text-amber-400">{formatCurrency(f.balance)}</td>
                          <td><span className={`badge ${statusBadge[f.status] ?? 'badge-gray'}`}>{statusLabel[f.status] ?? f.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {item.cotizaciones.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Cotizaciones</p>
                  <table className="daco-table">
                    <thead>
                      <tr>
                        <th>Folio</th>
                        <th>Fecha</th>
                        <th className="text-right">Total</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {item.cotizaciones.map(q => (
                        <tr key={q.folio}>
                          <td className="font-medium text-white">{q.folio}</td>
                          <td className="text-gray-400">{formatDate(q.issue_date)}</td>
                          <td className="text-right text-white">{formatCurrency(q.total)}</td>
                          <td><span className={`badge ${statusBadge[q.status] ?? 'badge-gray'}`}>{statusLabel[q.status] ?? q.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Resumen ejecutivo ─────────────────────────────────────────────── */}
      {tab === 'resumen' && (
        <div>
          <div className="flex gap-3 mb-4">
            <select className="input w-32" value={year} onChange={e => setYear(parseInt(e.target.value))}>
              {[2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          {loadingResumen ? (
            <div className="flex justify-center py-10"><Spinner /></div>
          ) : resumenData && (
            <>
              <div className="grid grid-cols-4 gap-3 mb-6">
                {[
                  { label: 'Cotizado', val: resumenData.totales.cotizado, color: 'text-blue-400' },
                  { label: 'Facturado', val: resumenData.totales.facturado, color: 'text-white' },
                  { label: 'Cobrado', val: resumenData.totales.cobrado, color: 'text-emerald-400' },
                  { label: 'Pendiente', val: resumenData.totales.pendiente, color: 'text-amber-400' },
                ].map(k => (
                  <div key={k.label} className="kpi-card">
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{k.label}</p>
                    <p className={`text-xl font-semibold ${k.color}`}>{formatCurrency(k.val)}</p>
                  </div>
                ))}
              </div>

              <div className="card">
                <table className="daco-table">
                  <thead>
                    <tr>
                      <th>Mes</th>
                      <th className="text-right">Cotizado</th>
                      <th className="text-right">Facturado</th>
                      <th className="text-right">Cobrado</th>
                      <th className="text-right">Pendiente</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resumenData.meses.filter(m => m.cotizado > 0 || m.facturado > 0 || m.cobrado > 0).map(m => (
                      <tr key={m.mes}>
                        <td className="font-medium text-white">{m.nombre}</td>
                        <td className="text-right text-blue-400">{formatCurrency(m.cotizado)}</td>
                        <td className="text-right text-white">{formatCurrency(m.facturado)}</td>
                        <td className="text-right text-emerald-400">{formatCurrency(m.cobrado)}</td>
                        <td className="text-right text-amber-400">{formatCurrency(m.pendiente)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Antigüedad de saldos ──────────────────────────────────────────── */}
      {tab === 'antiguedad' && (
        <div>
          {loadingAntiguedad ? (
            <div className="flex justify-center py-10"><Spinner /></div>
          ) : antiguedadData && (
            <>
              <div className="grid grid-cols-5 gap-3 mb-6">
                {[
                  { key: 'corriente', label: 'Corriente', color: 'text-emerald-400' },
                  { key: '1_30', label: '1-30 días', color: 'text-yellow-400' },
                  { key: '31_60', label: '31-60 días', color: 'text-amber-400' },
                  { key: '61_90', label: '61-90 días', color: 'text-orange-400' },
                  { key: 'mas_90', label: '+90 días', color: 'text-red-400' },
                ].map(r => (
                  <div key={r.key} className="kpi-card text-center">
                    <p className="text-xs text-gray-400 mb-1">{r.label}</p>
                    <p className={`text-lg font-semibold ${r.color}`}>
                      {formatCurrency(antiguedadData.rangos[r.key]?.total || 0)}
                    </p>
                    <p className="text-xs text-gray-500">{antiguedadData.rangos[r.key]?.count || 0} facturas</p>
                  </div>
                ))}
              </div>

              {[
                { key: 'corriente', label: 'Corriente', color: 'text-emerald-400' },
                { key: '1_30', label: '1-30 días vencida', color: 'text-yellow-400' },
                { key: '31_60', label: '31-60 días vencida', color: 'text-amber-400' },
                { key: '61_90', label: '61-90 días vencida', color: 'text-orange-400' },
                { key: 'mas_90', label: '+90 días vencida', color: 'text-red-400' },
              ].map(r => {
                const rango = antiguedadData.rangos[r.key]
                if (!rango?.items?.length) return null
                return (
                  <div key={r.key} className="card mb-4">
                    <div className="flex justify-between items-center mb-3">
                      <p className={`text-sm font-medium ${r.color}`}>{r.label}</p>
                      <p className={`text-sm font-semibold ${r.color}`}>{formatCurrency(rango.total)}</p>
                    </div>
                    <table className="daco-table">
                      <thead>
                        <tr>
                          <th>Factura</th>
                          <th>Cliente</th>
                          <th>Vence</th>
                          <th className="text-right">Saldo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rango.items.map(item => (
                          <tr key={item.folio}>
                            <td className="font-medium text-white">{item.folio}</td>
                            <td className="text-gray-300">{item.client_name}</td>
                            <td className="text-gray-400">{item.due_date ? formatDate(item.due_date) : '—'}</td>
                            <td className={`text-right font-medium ${r.color}`}>{formatCurrency(item.balance)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}

      {/* ── Pipeline ──────────────────────────────────────────────────────── */}
      {tab === 'pipeline' && (
        <div>
          {loadingPipeline ? (
            <div className="flex justify-center py-10"><Spinner /></div>
          ) : pipelineData && (
            <>
              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="kpi-card">
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Pipeline activo</p>
                  <p className="text-2xl font-semibold text-brand-400">{formatCurrency(pipelineData.pipeline_total)}</p>
                </div>
                <div className="kpi-card">
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Tasa de conversión</p>
                  <p className="text-2xl font-semibold text-emerald-400">{pipelineData.tasa_conversion}%</p>
                </div>
                <div className="kpi-card">
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Cotizaciones activas</p>
                  <p className="text-2xl font-semibold text-white">
                    {(pipelineData.estados?.draft?.count || 0) + (pipelineData.estados?.sent?.count || 0)}
                  </p>
                </div>
              </div>

              <div className="card mb-4">
                <p className="text-sm font-medium text-white mb-3">Por estado</p>
                <table className="daco-table">
                  <thead>
                    <tr>
                      <th>Estado</th>
                      <th className="text-right">Cantidad</th>
                      <th className="text-right">Valor total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(pipelineData.estados).map(([key, val]) => (
                      <tr key={key}>
                        <td>
                          <span className={`badge ${statusBadge[key] ?? 'badge-gray'}`}>
                            {statusLabel[key] ?? key}
                          </span>
                        </td>
                        <td className="text-right text-gray-300">{val.count}</td>
                        <td className="text-right text-white">{formatCurrency(val.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {pipelineData.top_cotizaciones?.length > 0 && (
                <div className="card">
                  <p className="text-sm font-medium text-white mb-3">Top cotizaciones activas</p>
                  <table className="daco-table">
                    <thead>
                      <tr>
                        <th>Folio</th>
                        <th>Cliente</th>
                        <th>Fecha</th>
                        <th>Vence</th>
                        <th className="text-right">Total</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pipelineData.top_cotizaciones.map(q => (
                        <tr key={q.folio}>
                          <td className="font-medium text-white">{q.folio}</td>
                          <td className="text-gray-300">{q.client_name}</td>
                          <td className="text-gray-400">{formatDate(q.issue_date)}</td>
                          <td className="text-gray-400">{q.expiry_date ? formatDate(q.expiry_date) : '—'}</td>
                          <td className="text-right text-white">{formatCurrency(q.total)}</td>
                          <td><span className={`badge ${statusBadge[q.status] ?? 'badge-gray'}`}>{statusLabel[q.status] ?? q.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </Page>
  )
}
