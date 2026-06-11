# Eta Factory ERP

A full-featured ERP system for small-to-medium manufacturing operations with multi-branch support. Manages sales, inventory, production, warehouse operations, and financial transactions.

## Tech Stack

**Frontend:** React 19, TypeScript, Material UI 6, Vite, Zustand, TanStack Query, Recharts
**Backend:** Flask 3, Python 3.12, SQLAlchemy, PostgreSQL 16
**Infrastructure:** Docker, Nginx, Gunicorn

## Features

- **Sales Management** — Quotations, orders, invoices, payments
- **Inventory Control** — Stock levels, ledger, transfers, GRV/GIV, adjustments, stocktake
- **Production** — Batch manufacturing tracking
- **Warehouse Management** — Multi-warehouse with goods receipt/issue
- **Multi-Branch** — Branch-scoped data access with role-based permissions
- **Reporting** — Sales, inventory, production, and financial reports
- **Audit Logging** — Full activity trail
- **User & Role Management** — Granular access control

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 16 (or Docker)

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python seed_data.py
python run.py           # http://localhost:5000
```

### Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api/v1

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-this-in-production` | Flask secret key |
| `JWT_SECRET_KEY` | `change-this-in-production` | JWT signing key |
| `DATABASE_URL` | `sqlite:///eta_dev.db` | Database connection string |

## Project Structure

```
frontend/           React SPA (Vite)
  src/
    api/            HTTP client & endpoint definitions
    components/     Reusable UI components
    pages/          Route-level page components
    store/          Zustand state stores
    routes/         Route definitions
    types/          TypeScript interfaces

backend/            Flask API
  src/
    api/            Route blueprints (auth, users, products, etc.)
    models/         SQLAlchemy models
    services/       Business logic
    schemas/        Marshmallow validation schemas
    repositories/   Data access layer
  migrations/       Alembic migrations
  tests/            Pytest test suite
```

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start frontend dev server |
| `npm run build` | Production build |
| `npm run lint` | Run ESLint |
| `python seed_data.py` | Seed database with demo data |
| `python reset_data.py` | Reset database to initial state |

## API

All endpoints are prefixed with `/api/v1` and use JWT authentication. See backend route blueprints for full documentation.
