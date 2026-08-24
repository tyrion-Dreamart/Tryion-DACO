import dayjs from 'dayjs'
import 'dayjs/locale/es'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
dayjs.locale('es')

export const formatCurrency = (amount, currency = 'MXN') =>
  new Intl.NumberFormat('es-MX', { style: 'currency', currency }).format(amount ?? 0)

export const formatDate = (date, fmt = 'DD MMM YYYY') =>
  date ? dayjs(date).format(fmt) : '—'

export const formatRelative = (date) =>
  date ? dayjs(date).fromNow() : '—'

export const daysDiff = (date) => {
  if (!date) return null
  return dayjs(date).diff(dayjs(), 'day')
}

export const statusLabel = {
  active:    'Activo',
  inactive:  'Inactivo',
  suspended: 'Suspendido',
  draft:     'Borrador',
  sent:      'Enviada',
  approved:  'Aprobada',
  rejected:  'Rechazada',
  expired:   'Expirada',
  pending:   'Pendiente',
  paid:      'Pagada',
  overdue:   'Vencida',
  partial:   'Parcial',
  issued:    'Emitida',
  cancelled: 'Cancelada',
  invoiced:  'Facturada',
}

export const statusBadge = {
  active:    'badge-green',
  paid:      'badge-green',
  approved:  'badge-green',
  pending:   'badge-amber',
  sent:      'badge-blue',
  partial:   'badge-amber',
  overdue:   'badge-red',
  rejected:  'badge-red',
  expired:   'badge-red',
  inactive:  'badge-gray',
  draft:     'badge-gray',
}
