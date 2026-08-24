// KPI Card
export function KpiCard({ label, value, sub, subColor = 'text-gray-400' }) {
  return (
    <div className="kpi-card">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">{label}</p>
      <p className="text-2xl font-semibold text-white">{value}</p>
      {sub && <p className={`text-xs mt-1 ${subColor}`}>{sub}</p>}
    </div>
  )
}

// Section header
export function SectionHeader({ title, sub, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h2 className="text-sm font-medium text-white">{title}</h2>
        {sub && <p className="text-xs text-gray-400">{sub}</p>}
      </div>
      {action}
    </div>
  )
}

// Empty state
export function EmptyState({ message = 'Sin datos' }) {
  return (
    <div className="py-10 text-center">
      <p className="text-gray-500 text-sm">{message}</p>
    </div>
  )
}

// Loading spinner
export function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 'w-4 h-4' : 'w-6 h-6'
  return (
    <span
      className={`${s} border-2 border-gray-600 border-t-brand-400 rounded-full animate-spin inline-block`}
    />
  )
}

// Page wrapper
export function Page({ children }) {
  return <div className="p-6 max-w-7xl mx-auto">{children}</div>
}

// Bar progress
export function ProgressBar({ pct = 0, color = 'bg-brand-500' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}
