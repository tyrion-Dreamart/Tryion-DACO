import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { Page, Spinner, EmptyState } from '@/components/ui'
import { formatCurrency, formatDate, statusLabel, statusBadge } from '@/utils/format'
import useIsViewer from '@/hooks/useIsViewer'

const fetchQuotes = (search, page, status) =>
  api.get(`/api/v1/quotes?page=${page}&page_size=20${search ? `&search=${search}` : ''}${status ? `&status=${status}` : ''}`).then(r => r.data)

const fetchClients = () =>
  api.get('/api/v1/clients?page_size=100').then(r => r.data)

const STATUS_OPTIONS = [
  { value: '', label: 'Todos' },
  { value: 'draft', label: 'Borrador' },
  { value: 'sent', label: 'Enviada' },
  { value: 'approved', label: 'Aprobada' },
  { value: 'rejected', label: 'Rechazada' },
  { value: 'expired', label: 'Expirada' },
]

const EMPTY_ITEM = { concept: '', dimensions: '', quantity: 1, unit_price: 0 }

const EMPTY_FORM = {
  folio: '',
  client_id: '',
  attention_name: '',
  attention_area: '',
  issue_date: new Date().toISOString().slice(0, 10),
  expiry_date: '',
  status: 'draft',
  currency: 'MXN',
  exchange_rate: '',
  has_iva: true,
  iva_rate: 16,
  advance_pct: '',
  notes: '',
  items: [{ ...EMPTY_ITEM }],
}

function calcItemTotal(item) {
  return (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)
}

function calcTotals(items, has_iva, iva_rate) {
  const subtotal = items.reduce((s, i) => s + calcItemTotal(i), 0)
  const iva = has_iva ? subtotal * (parseFloat(iva_rate) / 100) : 0
  return { subtotal, iva, total: subtotal + iva }
}

export default function CotizacionesPage() {
  const isViewer = useIsViewer()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [filterStatus, setFilterStatus] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [extractError, setExtractError] = useState('')
  const fileRef = useRef(null)

  const { data, isLoading } = useQuery({
    queryKey: ['quotes', search, page, filterStatus],
    queryFn: () => fetchQuotes(search, page, filterStatus),
  })

  const { data: clientsData } = useQuery({
    queryKey: ['clients-all'],
    queryFn: fetchClients,
  })

  const saveMutation = useMutation({
    mutationFn: (payload) =>
      editing
        ? api.patch(`/api/v1/quotes/${editing.id}`, payload)
        : api.post('/api/v1/quotes', payload),
    onSuccess: () => {
      qc.invalidateQueries(['quotes'])
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

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/api/v1/quotes/${id}`),
    onSuccess: () => qc.invalidateQueries(['quotes']),
  })

  const openNew = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormError('')
    setExtractError('')
    setShowForm(true)
  }

  const openEdit = (quote) => {
    setEditing(quote)
    setForm({
      folio: quote.folio || '',
      client_id: quote.client_id || '',
      attention_name: quote.attention_name || '',
      attention_area: quote.attention_area || '',
      issue_date: quote.issue_date ? quote.issue_date.slice(0, 10) : '',
      expiry_date: quote.expiry_date ? quote.expiry_date.slice(0, 10) : '',
      status: quote.status || 'draft',
      currency: quote.currency || 'MXN',
      exchange_rate: quote.exchange_rate || '',
      has_iva: quote.has_iva !== false,
      iva_rate: quote.iva_rate || 16,
      advance_pct: quote.advance_pct || '',
      notes: quote.notes || '',
      items: quote.items?.length ? quote.items.map(i => ({
        concept: i.concept,
        dimensions: i.dimensions || '',
        quantity: i.quantity,
        unit_price: i.unit_price,
      })) : [{ ...EMPTY_ITEM }],
    })
    setFormError('')
    setExtractError('')
    setShowForm(true)
  }

  const handleExtract = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setExtracting(true)
    setExtractError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data: extracted } = await api.post('/api/v1/quotes/extract', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setForm(f => ({
        ...f,
        folio: extracted.folio || f.folio,
        attention_name: extracted.attention_name || f.attention_name,
        attention_area: extracted.attention_area || f.attention_area,
        issue_date: extracted.issue_date || f.issue_date,
        currency: extracted.currency || 'MXN',
        advance_pct: extracted.advance_pct || f.advance_pct,
        notes: extracted.notes || f.notes,
        items: extracted.items?.length ? extracted.items.map(i => ({
          concept: i.concept || '',
          dimensions: i.dimensions || '',
          quantity: i.quantity || 1,
          unit_price: i.unit_price || 0,
        })) : f.items,
      }))
    } catch (err) {
      setExtractError('No se pudo extraer el PDF. Revisa e ingresa los datos manualmente.')
    } finally {
      setExtracting(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const addItem = () => setForm(f => ({ ...f, items: [...f.items, { ...EMPTY_ITEM }] }))
  const removeItem = (i) => setForm(f => ({ ...f, items: f.items.filter((_, idx) => idx !== i) }))
  const updateItem = (i, field, value) => setForm(f => ({
    ...f,
    items: f.items.map((item, idx) => idx === i ? { ...item, [field]: value } : item),
  }))

  const handleSubmit = () => {
    if (!form.folio.trim()) return setFormError('El folio es obligatorio')
    if (!form.client_id) return setFormError('Selecciona un cliente')
    if (!form.issue_date) return setFormError('La fecha es obligatoria')
    if (form.items.length === 0) return setFormError('Agrega al menos un concepto')
    if (form.currency === 'USD' && !form.exchange_rate) return setFormError('Ingresa el tipo de cambio para cotizaciones en USD')

    const payload = {
      ...form,
      issue_date: new Date(form.issue_date + 'T12:00:00Z').toISOString(),
      expiry_date: form.expiry_date ? new Date(form.expiry_date + 'T12:00:00Z').toISOString() : null,
      advance_pct: form.advance_pct ? parseFloat(form.advance_pct) : null,
      exchange_rate: form.exchange_rate ? parseFloat(form.exchange_rate) : null,
      iva_rate: parseFloat(form.iva_rate),
      items: form.items.map((item, i) => ({
        ...item,
        quantity: parseFloat(item.quantity) || 1,
        unit_price: parseFloat(item.unit_price) || 0,
        sort_order: i,
      })),
    }
    saveMutation.mutate(payload)
  }

  const { subtotal, iva, total } = calcTotals(form.items, form.has_iva, form.iva_rate)
  const totalMXN = form.currency === 'USD' && form.exchange_rate ? total * parseFloat(form.exchange_rate) : null

  return (
    <Page>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Cotizaciones</h1>
          <p className="text-gray-400 text-sm">{data?.total ?? 0} cotizaciones registradas</p>
        </div>
        {!isViewer && (
          <button onClick={openNew} className="btn-primary">+ Nueva cotización</button>
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
                  <th>Atención</th>
                  <th>Fecha</th>
                  <th className="text-right">Total</th>
                  <th>Moneda</th>
                  <th>Estado</th>
                  {!isViewer && <th></th>}
                </tr>
              </thead>
              <tbody>
                {data.items.map(q => (
                  <tr key={q.id}>
                    <td className="font-medium text-white">{q.folio}</td>
                    <td className="text-gray-300">{q.client_name || '—'}</td>
                    <td className="text-gray-400 text-xs">
                      {q.attention_name && <div>{q.attention_name}</div>}
                      {q.attention_area && <div className="text-gray-500">{q.attention_area}</div>}
                    </td>
                    <td className="text-gray-400">{formatDate(q.issue_date)}</td>
                    <td className="text-right font-medium">
                      <span className="text-emerald-400">{formatCurrency(q.total)}</span>
                      {q.currency === 'USD' && q.exchange_rate && (
                        <div className="text-xs text-gray-500">≈ {formatCurrency(q.total * q.exchange_rate)} MXN</div>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${q.currency === 'USD' ? 'badge-blue' : 'badge-gray'}`}>
                        {q.currency}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${statusBadge[q.status] ?? 'badge-gray'}`}>
                        {statusLabel[q.status] ?? q.status}
                      </span>
                    </td>
                    {!isViewer && (
                      <td>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => openEdit(q)} className="btn-ghost text-xs py-1">Editar</button>
                          <button onClick={() => window.confirm('¿Eliminar?') && deleteMutation.mutate(q.id)} className="btn-ghost text-xs py-1 text-red-400">Eliminar</button>
                        </div>
                      </td>
                    )}
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
          <EmptyState message="Sin cotizaciones." />
        )}
      </div>

      {!isViewer && showForm && (
        <div className="fixed inset-0 bg-black/70 flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-3xl my-4">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">{editing ? 'Editar cotización' : 'Nueva cotización'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5 space-y-5">
              {!editing && (
                <div className="bg-brand-600/10 border border-brand-600/30 rounded-lg p-4">
                  <p className="text-sm font-medium text-brand-400 mb-2">⚡ Extraer datos desde PDF</p>
                  <p className="text-xs text-gray-400 mb-3">Sube la cotización en PDF y los datos se llenarán automáticamente.</p>
                  <input ref={fileRef} type="file" accept=".pdf" onChange={handleExtract} className="hidden" id="pdf-upload" />
                  <label htmlFor="pdf-upload" className={`btn-secondary cursor-pointer inline-flex items-center gap-2 ${extracting ? 'opacity-50 pointer-events-none' : ''}`}>
                    {extracting ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Extrayendo...</> : '📄 Subir PDF'}
                  </label>
                  {extractError && <p className="text-xs text-amber-400 mt-2">{extractError}</p>}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Folio *</label>
                  <input className="input" value={form.folio} onChange={e => setForm(f => ({ ...f, folio: e.target.value }))} placeholder="DK-001" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Cliente *</label>
                  <select className="input" value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))}>
                    <option value="">Seleccionar cliente...</option>
                    {clientsData?.items?.map(c => (
                      <option key={c.id} value={c.id}>{c.legal_name} {c.trade_name ? `(${c.trade_name})` : ''} {c.rfc ? `— ${c.rfc}` : ''}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">At'n.</label>
                  <input className="input" value={form.attention_name} onChange={e => setForm(f => ({ ...f, attention_name: e.target.value }))} placeholder="Nombre del contacto" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Área</label>
                  <input className="input" value={form.attention_area} onChange={e => setForm(f => ({ ...f, attention_area: e.target.value }))} placeholder="Dirección, Compras..." />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Fecha *</label>
                  <input type="date" className="input" value={form.issue_date} onChange={e => setForm(f => ({ ...f, issue_date: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Vence</label>
                  <input type="date" className="input" value={form.expiry_date} onChange={e => setForm(f => ({ ...f, expiry_date: e.target.value }))} />
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
                    <label className="block text-xs text-gray-400 mb-1.5">Tipo de cambio (MXN/USD) *</label>
                    <input
                      type="number"
                      className="input"
                      value={form.exchange_rate}
                      onChange={e => setForm(f => ({ ...f, exchange_rate: e.target.value }))}
                      placeholder="17.50"
                      step="0.01"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Estado</label>
                  <select className="input" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                    {STATUS_OPTIONS.filter(o => o.value).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">% Anticipo</label>
                  <input type="number" className="input" value={form.advance_pct} onChange={e => setForm(f => ({ ...f, advance_pct: e.target.value }))} placeholder="70" min="0" max="100" />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.has_iva} onChange={e => setForm(f => ({ ...f, has_iva: e.target.checked }))} className="w-4 h-4 rounded" />
                  <span className="text-sm text-gray-300">Aplicar IVA</span>
                </label>
                {form.has_iva && (
                  <div className="flex items-center gap-2">
                    <input type="number" className="input w-20" value={form.iva_rate} onChange={e => setForm(f => ({ ...f, iva_rate: e.target.value }))} />
                    <span className="text-gray-400 text-sm">%</span>
                  </div>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-white">Conceptos</p>
                  <button onClick={addItem} className="btn-ghost text-xs">+ Agregar</button>
                </div>
                <div className="space-y-3">
                  {form.items.map((item, i) => (
                    <div key={i} className="bg-gray-700/50 rounded-lg p-3 space-y-2">
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <label className="block text-xs text-gray-400 mb-1">Concepto *</label>
                          <textarea className="input resize-none text-xs" rows={2} value={item.concept} onChange={e => updateItem(i, 'concept', e.target.value)} placeholder="Descripción del producto o servicio" />
                        </div>
                        {form.items.length > 1 && (
                          <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-300 self-start mt-5 px-1">×</button>
                        )}
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Medidas</label>
                          <input className="input text-xs" value={item.dimensions} onChange={e => updateItem(i, 'dimensions', e.target.value)} placeholder="Opcional" />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Cantidad</label>
                          <input type="number" className="input text-xs" value={item.quantity} onChange={e => updateItem(i, 'quantity', e.target.value)} min="0" />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">P.U. {form.currency}</label>
                          <input type="number" className="input text-xs" value={item.unit_price} onChange={e => updateItem(i, 'unit_price', e.target.value)} min="0" />
                        </div>
                      </div>
                      <div className="text-right text-xs text-emerald-400 font-medium">
                        Total: {form.currency} {formatCurrency(calcItemTotal(item))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 bg-gray-700/30 rounded-lg p-3 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Subtotal {form.currency}</span>
                    <span className="text-white">{formatCurrency(subtotal)}</span>
                  </div>
                  {form.has_iva && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">IVA ({form.iva_rate}%)</span>
                      <span className="text-white">{formatCurrency(iva)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-base font-semibold border-t border-gray-600 pt-1 mt-1">
                    <span className="text-white">Total {form.currency}</span>
                    <span className="text-emerald-400">{formatCurrency(total)}</span>
                  </div>
                  {totalMXN && (
                    <div className="flex justify-between text-sm border-t border-gray-600 pt-1 mt-1">
                      <span className="text-gray-400">Equivalente MXN (TC: {form.exchange_rate})</span>
                      <span className="text-blue-400 font-medium">{formatCurrency(totalMXN)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs text-gray-400 mb-1.5">Notas y condiciones</label>
                <textarea className="input resize-none" rows={3} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Condiciones de pago, tiempos de entrega, etc." />
              </div>

              {formError && (
                <p className="text-sm text-red-400 bg-red-900/20 border border-red-900/50 rounded-lg px-3 py-2">{formError}</p>
              )}
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-gray-700">
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
              <button onClick={handleSubmit} disabled={saveMutation.isPending} className="btn-primary flex items-center gap-2">
                {saveMutation.isPending && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                {editing ? 'Guardar cambios' : 'Crear cotización'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
