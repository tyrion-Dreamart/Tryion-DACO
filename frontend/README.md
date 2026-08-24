# DACO Frontend

React 18 + Vite + TailwindCSS — dark mode por defecto.

## Quick Start

```bash
cp .env.example .env
npm install
npm run dev
# http://localhost:5173
```

## Stack

| Librería | Uso |
|----------|-----|
| React 18 | UI |
| Vite 5 | Build tool |
| TailwindCSS 3 | Estilos + dark mode |
| React Router v6 | Navegación |
| TanStack Query v5 | Server state / cache |
| Zustand | Auth state |
| Axios | HTTP client (con JWT interceptors) |
| Recharts | Gráficas (próximo) |
| dayjs | Fechas en español |

## Estructura

```
src/
├── components/
│   ├── auth/        # Login
│   ├── layout/      # Sidebar, AppLayout
│   └── ui/          # KpiCard, Spinner, etc.
├── pages/           # Dashboard, Clientes, etc.
├── services/        # Axios instance + interceptors
├── store/           # Zustand (auth)
└── utils/           # format, badges
```

## Variables de entorno

```
VITE_API_URL=http://localhost:8000
```

## Módulos activos

- ✅ Login con JWT + auto-refresh
- ✅ Dashboard con KPIs
- ✅ Sidebar con navegación
- 🔜 Clientes
- 🔜 Cotizaciones
- 🔜 Facturas / CxC
- 🔜 Alertas
```
