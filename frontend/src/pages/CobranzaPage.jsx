import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { Page, Spinner, EmptyState } from '@/components/ui'
import { formatCurrency, formatDate, daysDiff } from '@/utils/format'
import useIsViewer from '@/hooks/useIsViewer'

const fetchCobranza = () =>
  api.get('/api/v1/invoices?page_size=100').then(r => r.data)

function UrgencyBadge({ days }) {
  if (days === null) return <span className="badge badge-gray">Sin fecha</span>
  if (days < 0) return <span className="badge badge-red">Vencida {Math.abs(days)}d</span>
  if (days <= 7) return <span className="badge badge-amber">Vence en {days}d</span>
  return <span className="badge badge-green">Vence en {days}d</span>
}

function ProgressBar({ paid, total }) {
  const pct = total > 0 ? Math.round((paid / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${pct === 100 ? 'bg-emerald-500' : pct > 0 ? 'bg-amber-500' : 'bg-gray-600'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function CobranzaPage() {
  const isViewer = useIsViewer()
  const qc = useQueryClient()
  const [showPayment, setShowPayment] = useState(null)
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentNote, setPaymentNote] = useState('')
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10))
  const [paymentReference, setPaymentReference] = useState('')
  const [filter, setFilter] = useState('pending')

  const { data, isLoading } = useQuery({
    queryKey: ['cobranza'],
    queryFn: fetchCobranza,
    refetchInterval: 60000,
  })

  const paymentMutation = useMutation({
    mutationFn: ({ id, amount, notes, reference, payment_date }) =>
      api.post(`/api/v1/invoices/${id}/payment`, { amount: parseFloat(amount), notes, reference, payment_date }),
    onSuccess: () => {
      qc.invalidateQueries(['cobranza'])
      qc.invalidateQueries(['invoices'])
      qc.invalidateQueries(['dashboard-summary'])
      setShowPayment(null)
      setPaymentAmount('')
      setPaymentNote('')
      setPaymentReference('')
      setPaymentDate(new Date().toISOString().slice(0, 10))
    },
  })

  const allInvoices = data?.items || []

  const filtered = allInvoices.filter(inv => {
    if (filter === 'pending') return inv.status !== 'paid' && inv.status !== 'cancelled'
    if (filter === 'overdue') return inv.status === 'overdue' || (inv.due_date && daysDiff(inv.due_date) < 0)
    if (filter === 'paid') return inv.status === 'paid'
    return true
  }).sort((a, b) => {
    const da = daysDiff(a.due_date)
    const db = daysDiff(b.due_date)
    if (da === null) return 1
    if (db === null) return -1
    return da - db
  })

  const totalPendiente = allInvoices
    .filter(i => i.status !== 'paid' && i.status !== 'cancelled')
    .reduce((s, i) => s + parseFloat(i.balance || 0), 0)

  const totalVencido = allInvoices
    .filter(i => i.status === 'overdue' || (i.due_date && daysDiff(i.due_date) < 0))
    .reduce((s, i) => s + parseFloat(i.balance || 0), 0)

  const totalCobrado = allInvoices
    .reduce((s, i) => s + parseFloat(i.paid_amount || 0), 0)

  return (
    <Page>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-white">Cobranza</h1>
        <p className="text-gray-400 text-sm">Control de cuentas por cobrar</p>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="kpi-card">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Por cobrar</p>
          <p className="text-2xl font-semibold text-amber-400">{formatCurrency(totalPendiente)}</p>
          <p className="text-xs text-gray-400 mt-1">{filtered.length} facturas pendientes</p>
        </div>
        <div className="kpi-card">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Vencido</p>
          <p className="text-2xl font-semibold text-red-400">{formatCurrency(totalVencido)}</p>
          <p className="text-xs text-gray-400 mt-1">Acción requerida</p>
        </div>
        <div className="kpi-card">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Cobrado total</p>
          <p className="text-2xl font-semibold text-emerald-400">{formatCurrency(totalCobrado)}</p>
          <p className="text-xs text-gray-400 mt-1">Pagos registrados</p>
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        {[
          { value: 'pending', label: 'Pendientes' },
          { value: 'overdue', label: 'Vencidas' },
          { value: 'paid', label: 'Pagadas' },
          { value: 'all', label: 'Todas' },
        ].map(f => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={filter === f.value ? 'btn-primary text-xs py-1.5' : 'btn-secondary text-xs py-1.5'}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="card">
        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : filtered.length ? (
          <table className="daco-table">
            <thead>
              <tr>
                <th>Factura</th>
                <th>Cliente</th>
                <th>Cotización</th>
                <th className="text-right">Total</th>
                <th className="text-right">Cobrado</th>
                <th className="text-right">Saldo</th>
                <th style={{ width: 120 }}>Avance</th>
                <th>Vencimiento</th>
                {!isViewer && <th></th>}
              </tr>
            </thead>
            <tbody>
              {filtered.map(inv => {
                const dias = daysDiff(inv.due_date)
                return (
                  <tr key={inv.id}>
                    <td className="font-medium text-white">{inv.folio}</td>
                    <td className="text-gray-300">{inv.client_name || '—'}</td>
                    <td className="text-gray-400 text-xs">{inv.quote_folio || '—'}</td>
                    <td className="text-right text-white">{formatCurrency(inv.total)}</td>
                    <td className="text-right text-emerald-400">{formatCurrency(inv.paid_amount)}</td>
                    <td className="text-right">
                      <span className={parseFloat(inv.balance) > 0 ? 'text-amber-400 font-medium' : 'text-emerald-400'}>
                        {formatCurrency(inv.balance)}
                      </span>
                    </td>
                    <td><ProgressBar paid={parseFloat(inv.paid_amount)} total={parseFloat(inv.total)} /></td>
                    <td><UrgencyBadge days={dias} /></td>
                    {!isViewer && (
                      <td>
                        {inv.status !== 'paid' && inv.status !== 'cancelled' && (
                          <button
                            onClick={() => { setShowPayment(inv); setPaymentAmount(inv.balance) }}
                            className="btn-primary text-xs py-1 px-3"
                          >
                            + Pago
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        ) : (
          <EmptyState message="Sin facturas en esta categoría" />
        )}
      </div>

      {/* Modal Pago */}
      {!isViewer && showPayment && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-sm">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">Registrar pago</h2>
              <button onClick={() => setShowPayment(null)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="bg-gray-700/50 rounded-lg p-3 space-y-1">
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Factura</span>
                  <span className="text-white font-medium">{showPayment.folio}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Cliente</span>
                  <span className="text-white">{showPayment.client_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Total</span>
                  <span className="text-white">{formatCurrency(showPayment.total)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Ya cobrado</span>
                  <span className="text-emerald-400">{formatCurrency(showPayment.paid_amount)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-600 pt-1 mt-1">
                  <span className="text-xs text-gray-400">Saldo</span>
                  <span className="text-amber-400 font-semibold">{formatCurrency(showPayment.balance)}</span>
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Fecha de pago *</label>
                <input type="date" className="input" value={paymentDate} onChange={e => setPaymentDate(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Monto del pago *</label>
                <input type="number" className="input" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} autoFocus />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Referencia / Notas</label>
                <input className="input" value={paymentReference} onChange={e => setPaymentReference(e.target.value)} placeholder="Transferencia #123, cheque, efectivo..." />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Notas</label>
                <input className="input" value={paymentNote} onChange={e => setPaymentNote(e.target.value)} placeholder="Concepto..." />
              </div>
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-gray-700">
              <button onClick={() => setShowPayment(null)} className="btn-secondary">Cancelar</button>
              <button
                onClick={() => paymentMutation.mutate({
                  id: showPayment.id,
                  amount: paymentAmount,
                  notes: paymentNote,
                  reference: paymentReference,
                  payment_date: new Date(paymentDate + 'T12:00:00Z').toISOString()
                })}
                disabled={!paymentAmount || paymentMutation.isPending}
                className="btn-primary flex items-center gap-2"
              >
                {paymentMutation.isPending && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                Registrar pago
              </button>
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
