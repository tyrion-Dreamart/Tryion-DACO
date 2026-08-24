import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { Page, Spinner, EmptyState } from '@/components/ui'
import { formatCurrency, formatDate, statusLabel, statusBadge } from '@/utils/format'
import useIsViewer from '@/hooks/useIsViewer'

const fetchInvoices = (search, page, status) =>
  api.get(`/api/v1/invoices?page=${page}&page_size=20${search ? `&search=${search}` : ''}${status ? `&status=${status}` : ''}`).then(r => r.data)

const fetchClients = () =>
  api.get('/api/v1/clients?page_size=100').then(r => r.data)

const fetchQuotes = () =>
  api.get('/api/v1/quotes?page_size=100').then(r => r.data)

const STATUS_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'issued', label: 'Emitida' },
  { value: 'partial', label: 'Parcial' },
  { value: 'paid', label: 'Pagada' },
  { value: 'overdue', label: 'Vencida' },
  { value: 'cancelled', label: 'Cancelada' },
]

const EMPTY_FORM = {
  folio: '',
  client_id: '',
  quote_id: '',
  quote_ids: [],
  issue_date: new Date().toISOString().slice(0, 10),
  due_date: '',
  status: 'issued',
  currency: 'MXN',
  exchange_rate: '',
  subtotal: '',
  iva_amount: '',
  total: '',
  notes: '',
}

export default function FacturasPage() {
  const isViewer = useIsViewer()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [filterStatus, setFilterStatus] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showPayment, setShowPayment] = useState(null)
  const [showHistory, setShowHistory] = useState(null)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentNote, setPaymentNote] = useState('')
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10))
  const [paymentReference, setPaymentReference] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', search, page, filterStatus],
    queryFn: () => fetchInvoices(search, page, filterStatus),
  })

  const { data: clientsData } = useQuery({ queryKey: ['clients-all'], queryFn: fetchClients })
  const { data: quotesData } = useQuery({ queryKey: ['quotes-all'], queryFn: fetchQuotes })

  const { data: paymentsData } = useQuery({
    queryKey: ['payments', showHistory?.id],
    queryFn: () => api.get(`/api/v1/invoices/${showHistory?.id}/payments`).then(r => r.data),
    enabled: !!showHistory,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) =>
      editing
        ? api.patch(`/api/v1/invoices/${editing.id}`, payload)
        : api.post('/api/v1/invoices', payload),
    onSuccess: () => {
      qc.invalidateQueries(['invoices'])
      setShowForm(false)
      setEditing(null)
      setForm(EMPTY_FORM)
      setFormError('')
    },
    onError: (err) => {
      const detail = err.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : 'Error al guardar')
    },
  })

  const paymentMutation = useMutation({
    mutationFn: ({ id, amount, notes, reference, payment_date }) =>
      api.post(`/api/v1/invoices/${id}/payment`, { amount: parseFloat(amount), notes, reference, payment_date }),
    onSuccess: () => {
      qc.invalidateQueries(['invoices'])
      setShowPayment(null)
      setPaymentAmount('')
      setPaymentNote('')
      setPaymentReference('')
      setPaymentDate(new Date().toISOString().slice(0, 10))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/api/v1/invoices/${id}`),
    onSuccess: () => qc.invalidateQueries(['invoices']),
  })

  const openNew = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormError('')
    setShowForm(true)
  }

  const openEdit = (inv) => {
    setEditing(inv)
    setForm({
      folio: inv.folio || '',
      client_id: inv.client_id || '',
      quote_id: inv.quote_id || '',
      quote_ids: inv.quote_ids || [],
      issue_date: inv.issue_date ? inv.issue_date.slice(0, 10) : '',
      due_date: inv.due_date ? inv.due_date.slice(0, 10) : '',
      status: inv.status || 'issued',
      currency: inv.currency || 'MXN',
      exchange_rate: inv.exchange_rate || '',
      subtotal: inv.subtotal || '',
      iva_amount: inv.iva_amount || '',
      total: inv.total || '',
      notes: inv.notes || '',
    })
    setFormError('')
    setShowForm(true)
  }

  const handleQuoteSelect = (quoteId) => {
    const quote = quotesData?.items?.find(q => q.id === quoteId)
    if (quote) {
      setForm(f => ({
        ...f,
        quote_id: quoteId,
        quote_ids: [quoteId],
        client_id: f.client_id || quote.client_id,
        subtotal: quote.subtotal,
        iva_amount: quote.iva_amount,
        total: quote.total,
        currency: quote.currency || 'MXN',
        exchange_rate: quote.exchange_rate || '',
      }))
    } else {
      setForm(f => ({ ...f, quote_id: '', quote_ids: [] }))
    }
  }

  const toggleQuoteId = (qid) => {
    setForm(f => {
      const exists = f.quote_ids.includes(qid)
      const newIds = exists
        ? f.quote_ids.filter(id => id !== qid)
        : [...f.quote_ids, qid]
      return { ...f, quote_ids: newIds }
    })
  }

  const handleSubmit = () => {
    if (!form.folio.trim()) return setFormError('El folio es obligatorio')
    if (!form.client_id) return setFormError('Selecciona un cliente')
    if (!form.issue_date) return setFormError('La fecha es obligatoria')
    if (!form.total) return setFormError('El total es obligatorio')

    const payload = {
      ...form,
      issue_date: new Date(form.issue_date + 'T12:00:00Z').toISOString(),
      due_date: form.due_date ? new Date(form.due_date + 'T12:00:00Z').toISOString() : null,
      subtotal: parseFloat(form.subtotal) || 0,
      iva_amount: parseFloat(form.iva_amount) || 0,
      total: parseFloat(form.total) || 0,
      exchange_rate: form.exchange_rate ? parseFloat(form.exchange_rate) : null,
      quote_id: form.quote_ids[0] || form.quote_id || null,
      quote_ids: form.quote_ids,
    }
    saveMutation.mutate(payload)
  }

  const totalMXN = form.currency === 'USD' && form.exchange_rate && form.total
    ? parseFloat(form.total) * parseFloat(form.exchange_rate)
    : null

  // Cotizaciones del cliente seleccionado
  const clientQuotes = quotesData?.items?.filter(q => q.client_id === form.client_id) || []

  return (
    <Page>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Facturas</h1>
          <p className="text-gray-400 text-sm">{data?.total ?? 0} facturas registradas</p>
        </div>
        {!isViewer && (
          <button onClick={openNew} className="btn-primary">+ Nueva factura</button>
        )}
      </div>

      <div className="flex gap-3 mb-4">
        <input className="input max-w-xs" placeholder="Buscar por folio..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
        <select className="input w-40" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(1) }}>
          {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : data?.items?.length ? (
          <>
            <table className="daco-table">
              <thead>
                <tr>
                  <th>Folio</th>
                  <th>Cliente</th>
                  <th>Cotizaciones</th>
                  <th>Fecha</th>
                  <th>Vence</th>
                  <th className="text-right">Total</th>
                  <th className="text-right">Saldo</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map(inv => (
                  <tr key={inv.id}>
                    <td className="font-medium text-white">{inv.folio}</td>
                    <td className="text-gray-300">{inv.client_name || '—'}</td>
                    <td className="text-gray-400 text-xs">
                      {inv.quotes_folios?.length > 0
                        ? inv.quotes_folios.join(', ')
                        : inv.quote_folio || '—'}
                    </td>
                    <td className="text-gray-400">{formatDate(inv.issue_date)}</td>
                    <td className="text-gray-400">{inv.due_date ? formatDate(inv.due_date) : '—'}</td>
                    <td className="text-right">
                      <span className="text-white font-medium">
                        {inv.currency === 'USD' ? 'USD ' : ''}{formatCurrency(inv.total)}
                      </span>
                      {inv.currency === 'USD' && inv.exchange_rate && (
                        <div className="text-xs text-gray-500">≈ {formatCurrency(inv.total * inv.exchange_rate)} MXN</div>
                      )}
                      {inv.currency === 'USD' && !inv.exchange_rate && (
                        <div className="text-xs text-amber-500">⚠ Sin TC</div>
                      )}
                    </td>
                    <td className="text-right">
                      <span className={inv.balance > 0 ? 'text-amber-400' : 'text-emerald-400'}>
                        {inv.currency === 'USD' ? 'USD ' : ''}{formatCurrency(inv.balance)}
                      </span>
                    </td>
                    <td>
                      <div className="flex flex-col gap-1">
                        <span className={`badge ${statusBadge[inv.status] ?? 'badge-gray'}`}>
                          {statusLabel[inv.status] ?? inv.status}
                        </span>
                        {inv.currency === 'USD' && (
                          <span className="badge badge-blue">USD</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="flex gap-1 justify-end">
                        {!isViewer && inv.status !== 'paid' && inv.status !== 'cancelled' && (
                          <button onClick={() => { setShowPayment(inv); setPaymentAmount(inv.balance) }} className="btn-ghost text-xs py-1 text-emerald-400">
                            + Pago
                          </button>
                        )}
                        <button onClick={() => setShowHistory(inv)} className="btn-ghost text-xs py-1 text-blue-400">
                          Historial
                        </button>
                        {!isViewer && (
                          <>
                            <button onClick={() => openEdit(inv)} className="btn-ghost text-xs py-1">Editar</button>
                            <button onClick={() => window.confirm('¿Eliminar?') && deleteMutation.mutate(inv.id)} className="btn-ghost text-xs py-1 text-red-400">Eliminar</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.pages > 1 && (
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-700">
                <span className="text-xs text-gray-400">Página {page} de {data.pages}</span>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs py-1 px-3 disabled:opacity-40">Anterior</button>
                  <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="btn-secondary text-xs py-1 px-3 disabled:opacity-40">Siguiente</button>
                </div>
              </div>
            )}
          </>
        ) : (
          <EmptyState message="Sin facturas." />
        )}
      </div>

      {/* Modal Factura */}
      {!isViewer && showForm && (
        <div className="fixed inset-0 bg-black/70 flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-lg my-4">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">{editing ? 'Editar factura' : 'Nueva factura'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Folio factura *</label>
                  <input className="input" value={form.folio} onChange={e => setForm(f => ({ ...f, folio: e.target.value }))} placeholder="F-0001" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Cliente *</label>
                  <select className="input" value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value, quote_ids: [] }))}>
                    <option value="">Seleccionar...</option>
                    {clientsData?.items?.map(c => (
                      <option key={c.id} value={c.id}>{c.legal_name} {c.trade_name ? `(${c.trade_name})` : ''} {c.rfc ? `— ${c.rfc}` : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Fecha emisión *</label>
                  <input type="date" className="input" value={form.issue_date} onChange={e => setForm(f => ({ ...f, issue_date: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Fecha vencimiento</label>
                  <input type="date" className="input" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Moneda</label>
                  <select className="input" value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value, exchange_rate: '' }))}>
                    <option value="MXN">MXN — Peso mexicano</option>
                    <option value="USD">USD — Dólar americano</option>
                  </select>
                </div>
                {form.currency === 'USD' && (
                  <div>
                    <label className="block text-xs text-gray-400 mb-1.5">Tipo de cambio (MXN/USD)</label>
                    <input type="number" className="input" value={form.exchange_rate} onChange={e => setForm(f => ({ ...f, exchange_rate: e.target.value }))} placeholder="17.50" step="0.01" />
                  </div>
                )}
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Subtotal</label>
                  <input type="number" className="input" value={form.subtotal} onChange={e => setForm(f => ({ ...f, subtotal: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">IVA</label>
                  <input type="number" className="input" value={form.iva_amount} onChange={e => setForm(f => ({ ...f, iva_amount: e.target.value }))} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Total {form.currency} *</label>
                  <input type="number" className="input" value={form.total} onChange={e => setForm(f => ({ ...f, total: e.target.value }))} />
                </div>
                {totalMXN && (
                  <div className="col-span-2 bg-blue-900/20 border border-blue-900/40 rounded-lg px-3 py-2">
                    <p className="text-xs text-gray-400">Equivalente MXN (TC: {form.exchange_rate})</p>
                    <p className="text-blue-400 font-semibold">{formatCurrency(totalMXN)}</p>
                  </div>
                )}
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Estado</label>
                  <select className="input" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                    {STATUS_OPTIONS.filter(o => o.value).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>

              {/* Cotizaciones vinculadas */}
              {form.client_id && clientQuotes.length > 0 && (
                <div>
                  <label className="block text-xs text-gray-400 mb-2">Cotizaciones vinculadas</label>
                  <div className="space-y-1 max-h-40 overflow-y-auto border border-gray-700 rounded-lg p-2">
                    {clientQuotes.map(q => (
                      <label key={q.id} className="flex items-center gap-2 cursor-pointer p-1.5 rounded hover:bg-gray-700/50">
                        <input
                          type="checkbox"
                          checked={form.quote_ids.includes(q.id)}
                          onChange={() => toggleQuoteId(q.id)}
                          className="w-4 h-4 rounded"
                        />
                        <span className="text-xs text-white font-medium">{q.folio}</span>
                        <span className="text-xs text-gray-400">{q.attention_name || '—'}</span>
                        <span className="text-xs text-emerald-400 ml-auto">{formatCurrency(q.total)}</span>
                      </label>
                    ))}
                  </div>
                  {form.quote_ids.length > 0 && (
                    <p className="text-xs text-brand-400 mt-1">{form.quote_ids.length} cotización(es) seleccionada(s)</p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Notas</label>
                <textarea className="input resize-none" rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
              </div>
              {formError && <p className="text-sm text-red-400 bg-red-900/20 border border-red-900/50 rounded-lg px-3 py-2">{formError}</p>}
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-gray-700">
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
              <button onClick={handleSubmit} disabled={saveMutation.isPending} className="btn-primary flex items-center gap-2">
                {saveMutation.isPending && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                {editing ? 'Guardar' : 'Crear factura'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Pago */}
      {!isViewer && showPayment && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-sm">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">Registrar pago</h2>
              <button onClick={() => setShowPayment(null)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="bg-gray-700/50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Factura</p>
                <p className="text-white font-medium">{showPayment.folio}</p>
                {showPayment.currency === 'USD' && <p className="text-xs text-blue-400 mt-0.5">Factura en USD</p>}
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-400">Total</span>
                  <span className="text-white">{showPayment.currency === 'USD' ? 'USD ' : ''}{formatCurrency(showPayment.total)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Pagado</span>
                  <span className="text-emerald-400">{formatCurrency(showPayment.paid_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Saldo</span>
                  <span className="text-amber-400 font-medium">{showPayment.currency === 'USD' ? 'USD ' : ''}{formatCurrency(showPayment.balance)}</span>
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Fecha de pago *</label>
                <input type="date" className="input" value={paymentDate} onChange={e => setPaymentDate(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Monto {showPayment.currency === 'USD' ? '(USD)' : ''} *</label>
                <input type="number" className="input" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} autoFocus />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Referencia</label>
                <input className="input" value={paymentReference} onChange={e => setPaymentReference(e.target.value)} placeholder="No. transferencia, cheque..." />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Notas</label>
                <input className="input" value={paymentNote} onChange={e => setPaymentNote(e.target.value)} placeholder="Concepto del pago..." />
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

      {/* Modal Historial */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">Historial — {showHistory.folio}</h2>
              <button onClick={() => setShowHistory(null)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5">
              <div className="bg-gray-700/30 rounded-lg p-3 mb-4">
                <div className="flex justify-between mb-2">
                  <div>
                    <p className="text-xs text-gray-400">Total {showHistory.currency}</p>
                    <p className="text-white font-medium">{formatCurrency(showHistory.total)}</p>
                    {showHistory.currency === 'USD' && showHistory.exchange_rate && (
                      <p className="text-xs text-blue-400">≈ {formatCurrency(showHistory.total * showHistory.exchange_rate)} MXN</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Cobrado</p>
                    <p className="text-emerald-400 font-medium">{formatCurrency(showHistory.paid_amount)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Saldo</p>
                    <p className="text-amber-400 font-medium">{formatCurrency(showHistory.balance)}</p>
                  </div>
                </div>
                {showHistory.quotes_folios?.length > 0 && (
                  <p className="text-xs text-gray-400 mt-1">
                    Cotizaciones: <span className="text-brand-300">{showHistory.quotes_folios.join(', ')}</span>
                  </p>
                )}
              </div>
              {paymentsData?.items?.length ? (
                <table className="daco-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Referencia</th>
                      <th>Notas</th>
                      <th className="text-right">Monto</th>
                      {!isViewer && <th></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {paymentsData.items.map(p => (
                      <tr key={p.id}>
                        <td className="text-gray-300">{formatDate(p.payment_date)}</td>
                        <td className="text-gray-300">{p.reference || '—'}</td>
                        <td className="text-gray-400 text-xs">{p.notes || '—'}</td>
                        <td className="text-right text-emerald-400 font-medium">{formatCurrency(p.amount)}</td>
                        {!isViewer && (
                          <td>
                            <button
                              onClick={() => {
                                if (window.confirm('¿Eliminar este pago?')) {
                                  api.delete(`/api/v1/invoices/${showHistory.id}/payments/${p.id}`)
                                    .then(() => {
                                      qc.invalidateQueries(['payments', showHistory.id])
                                      qc.invalidateQueries(['invoices'])
                                    })
                                }
                              }}
                              className="btn-ghost text-xs py-0.5 text-red-400"
                            >
                              Eliminar
                            </button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400 text-center py-4">Sin pagos registrados</p>
              )}
            </div>
            <div className="flex justify-end p-5 border-t border-gray-700">
              <button onClick={() => setShowHistory(null)} className="btn-secondary">Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
