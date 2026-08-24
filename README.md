# DACO ERP

ERP financiero-operativo privado para empresas de servicios e ingeniería.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 + FastAPI |
| Base de datos | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 async |
| Migraciones | Alembic |
| Cache | Redis 7 |
| Auth | JWT (python-jose + bcrypt) |
| Validación | Pydantic v2 |
| Infra | Docker Compose + Nginx |

## Estructura

```
daco/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Routers por módulo
│   │   ├── core/               # Config, security, deps
│   │   ├── db/                 # Engine, session, Base
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic (futuro)
│   │   └── utils/              # Helpers, seed
│   ├── alembic/                # Migraciones
│   └── tests/
├── infra/
│   ├── nginx/
│   └── postgres/
└── docker-compose.yml
```

## Quick Start

```bash
# 1. Variables de entorno
cp .env.example .env
# Editar SECRET_KEY y passwords

# 2. Levantar servicios
make up

# 3. Aplicar migraciones
make migrate

# 4. Crear super admin
make seed

# 5. API disponible en:
# http://localhost:8000/docs
```

## Módulos actuales

- **Auth**: Login JWT, refresh token, roles (super_admin, admin, manager, operator, viewer)
- **Corporativos**: CRUD de grupos corporativos
- **Razones Sociales**: CRUD de entidades legales (RFC, régimen fiscal, domicilio)
- **Contactos**: Personas de contacto por razón social (primario, facturación)
- **Cotizaciones**: CRUD con items, extracción de datos desde PDF vía Claude API
- **Facturas**: CRUD, ligadas a cotizaciones, estatus (pendiente/pagada/parcial/vencida/cancelada)
- **Dashboard ejecutivo**: facturado/cobrado/por cobrar, mix de servicios, cuentas por cobrar
- **Reportes**: antigüedad de saldos, exportación a Excel
- **Alertas de vencimiento**: automatizadas — un job programado (`app/services/alertas_job.py`,
  corre cada `ALERTAS_JOB_INTERVAL_HOURS` horas, default 6) marca facturas vencidas y
  cotizaciones expiradas sin depender de que alguien abra la pantalla de alertas

## Próximos módulos

- [ ] Facturación electrónica (CFDI / timbrado ante el SAT)
- [ ] Notificaciones por email de las alertas (falta configurar SMTP — ver `.env.example`)
- [ ] Cobranza (seguimiento de pagos parciales, recordatorios a clientes)

## API Docs

Disponible en `http://localhost:8000/docs` (solo desarrollo).

## Migraciones

```bash
# Nueva migración (auto-detect)
make revision msg="add quotes table"

# Aplicar
make migrate

# Revertir
make downgrade
```
