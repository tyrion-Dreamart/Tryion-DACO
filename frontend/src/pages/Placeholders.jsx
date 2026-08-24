import { Page } from '@/components/ui'

function Placeholder({ title }) {
  return (
    <Page>
      <h1 className="text-xl font-semibold text-white mb-2">{title}</h1>
      <p className="text-gray-400 text-sm">Módulo en construcción.</p>
    </Page>
  )
}

export const CotizacionesPage  = () => <Placeholder title="Cotizaciones" />
export const FacturasPage      = () => <Placeholder title="Facturas" />
export const CobranzaPage      = () => <Placeholder title="Cobranza" />
export const AlertasPage       = () => <Placeholder title="Alertas" />
export const ReportesPage      = () => <Placeholder title="Reportes" />