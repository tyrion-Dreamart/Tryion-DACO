import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/components/auth/LoginPage'
import Dashboard from '@/pages/Dashboard'
import ClientesPage from '@/pages/ClientesPage'
import CotizacionesPage from '@/pages/CotizacionesPage'
import FacturasPage from '@/pages/FacturasPage'
import CobranzaPage from '@/pages/CobranzaPage'
import AlertasPage from '@/pages/AlertasPage'
import ReportesPage from '@/pages/ReportesPage'

function RequireAuth({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  useEffect(() => { if (isAuthenticated) fetchMe() }, [isAuthenticated])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<RequireAuth><AppLayout /></RequireAuth>}>
          <Route index element={<Dashboard />} />
          <Route path="clientes" element={<ClientesPage />} />
          <Route path="cotizaciones" element={<CotizacionesPage />} />
          <Route path="facturas" element={<FacturasPage />} />
          <Route path="cobranza" element={<CobranzaPage />} />
          <Route path="alertas" element={<AlertasPage />} />
          <Route path="reportes" element={<ReportesPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}