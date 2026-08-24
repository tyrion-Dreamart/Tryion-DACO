from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, contacts, corporates, legal_entities, clients, dashboard, quotes, invoices, alertas, reportes, exportar
from app.core.deps import require_editor

api_router = APIRouter(prefix="/api/v1")

# Rutas públicas (solo lectura permitida para viewer)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(alertas.router)
api_router.include_router(reportes.router)
api_router.include_router(exportar.router)

# Rutas de solo lectura
api_router.include_router(corporates.router)
api_router.include_router(legal_entities.router)
api_router.include_router(contacts.router)
api_router.include_router(clients.router)
api_router.include_router(quotes.router)
api_router.include_router(invoices.router)