import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { Page, Spinner, EmptyState } from '@/components/ui'
import { statusLabel, statusBadge } from '@/utils/format'
import useIsViewer from '@/hooks/useIsViewer'

const fetchClients = (search, page) =>
  api.get(`/api/v1/clients?page=${page}&page_size=20${search ? `&search=${search}` : ''}`).then(r => r.data)

const EMPTY_FORM = {
  legal_name: '',
  trade_name: '',
  rfc: '',
  phone: '',
  email: '',
  address_city: '',
  address_state: '',
  tax_regime: '',
  status: 'active',
  notes: '',
}

export default function ClientesPage() {
  const isViewer = useIsViewer()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['clients', search, page],
    queryFn: () => fetchClients(search, page),
  })

  const saveMutation = useMutation({
    mutationFn: (payload) =>
      editing
        ? api.patch(`/api/v1/clients/${editing.id}`, payload)
        : api.post('/api/v1/clients', payload),
    onSuccess: () => {
      qc.invalidateQueries(['clients'])
      qc.invalidateQueries(['clients-all'])
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
    mutationFn: (id) => api.delete(`/api/v1/clients/${id}`),
    onSuccess: () => qc.invalidateQueries(['clients']),
  })

  const openNew = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormError('')
    setShowForm(true)
  }

  const openEdit = (client) => {
    setEditing(client)
    setForm({
      legal_name: client.legal_name || '',
      trade_name: client.trade_name || '',
      rfc: client.rfc || '',
      phone: client.phone || '',
      email: client.email || '',
      address_city: client.address_city || '',
      address_state: client.address_state || '',
      tax_regime: client.tax_regime || '',
      status: client.status || 'active',
      notes: client.notes || '',
    })
    setFormError('')
    setShowForm(true)
  }

  const handleSubmit = () => {
    if (!form.legal_name.trim()) return setFormError('La razón social es obligatoria')
    saveMutation.mutate(form)
  }

  return (
    <Page>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Clientes</h1>
          <p className="text-gray-400 text-sm">{data?.total ?? 0} clientes registrados</p>
        </div>
        {!isViewer && (
          <button onClick={openNew} className="btn-primary">+ Nuevo cliente</button>
        )}
      </div>

      <div className="flex gap-3 mb-4">
        <input className="input max-w-xs" placeholder="Buscar por nombre o RFC..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
      </div>

      <div className="card">
        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : data?.items?.length ? (
          <>
            <table className="daco-table">
              <thead>
                <tr>
                  <th>Razón social</th>
                  <th>RFC</th>
                  <th>Ciudad</th>
                  <th>Teléfono</th>
                  <th>Estado</th>
                  <th>Contactos</th>
                  {!isViewer && <th></th>}
                </tr>
              </thead>
              <tbody>
                {data.items.map(c => (
                  <tr key={c.id}>
                    <td>
                      <p className="font-medium text-white">{c.legal_name}</p>
                      {c.trade_name && <p className="text-xs text-gray-500">{c.trade_name}</p>}
                    </td>
                    <td className="text-gray-400">{c.rfc || '—'}</td>
                    <td className="text-gray-400">{c.address_city || '—'}</td>
                    <td className="text-gray-400">{c.phone || '—'}</td>
                    <td>
                      <span className={`badge ${statusBadge[c.status] ?? 'badge-gray'}`}>
                        {statusLabel[c.status] ?? c.status}
                      </span>
                    </td>
                    <td className="text-gray-400">{c.contacts_count ?? 0}</td>
                    {!isViewer && (
                      <td>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => openEdit(c)} className="btn-ghost text-xs py-1">Editar</button>
                          <button onClick={() => window.confirm('¿Eliminar?') && deleteMutation.mutate(c.id)} className="btn-ghost text-xs py-1 text-red-400">Eliminar</button>
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
          <EmptyState message="Sin clientes registrados." />
        )}
      </div>

      {!isViewer && showForm && (
        <div className="fixed inset-0 bg-black/70 flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-gray-800 border border-gray-700 rounded-xl w-full max-w-lg my-4">
            <div className="flex items-center justify-between p-5 border-b border-gray-700">
              <h2 className="text-base font-semibold text-white">{editing ? 'Editar cliente' : 'Nuevo cliente'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Razón social *</label>
                  <input className="input" value={form.legal_name} onChange={e => setForm(f => ({ ...f, legal_name: e.target.value }))} placeholder="GH9 Shared Services SA de CV" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Nombre comercial</label>
                  <input className="input" value={form.trade_name} onChange={e => setForm(f => ({ ...f, trade_name: e.target.value }))} placeholder="Grupo Anderson's" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">RFC</label>
                  <input className="input" value={form.rfc} onChange={e => setForm(f => ({ ...f, rfc: e.target.value }))} placeholder="GSS210729UM7" />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Teléfono</label>
                  <input className="input" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Correo electrónico</label>
                  <input className="input" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Ciudad</label>
                  <input className="input" value={form.address_city} onChange={e => setForm(f => ({ ...f, address_city: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1.5">Estado</label>
                  <input className="input" value={form.address_state} onChange={e => setForm(f => ({ ...f, address_state: e.target.value }))} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Régimen fiscal</label>
                  <input className="input" value={form.tax_regime} onChange={e => setForm(f => ({ ...f, tax_regime: e.target.value }))} placeholder="Régimen General de Ley Personas Morales" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-400 mb-1.5">Estado</label>
                  <select className="input" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                    <option value="active">Activo</option>
                    <option value="inactive">Inactivo</option>
                    <option value="suspended">Suspendido</option>
                  </select>
                </div>
              </div>
              {formError && <p className="text-sm text-red-400 bg-red-900/20 border border-red-900/50 rounded-lg px-3 py-2">{formError}</p>}
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-gray-700">
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
              <button onClick={handleSubmit} disabled={saveMutation.isPending} className="btn-primary flex items-center gap-2">
                {saveMutation.isPending && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                {editing ? 'Guardar cambios' : 'Crear cliente'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Page>
  )
}
