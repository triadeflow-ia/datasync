# FlowBase (datasync)

Sistema profissional de validacao e enriquecimento de dados para CRM. Valida emails, formata telefones brasileiros (E.164), separa contatos multiplos e prepara dados para importacao no GoHighLevel.

## Stack

- **Backend**: Python 3.11, FastAPI, PostgreSQL, Redis + RQ
- **Frontend**: Next.js 14, TypeScript, React 18
- **Deploy**: Docker (Render)

## Funcionalidades (MVP Phase 1)

- Upload de planilhas XLSX/CSV
- Mapeamento automatico de colunas (PT/EN)
- Normalizacao de emails (lowercase, dedup)
- Normalizacao de telefones (E.164, +55 BR)
- Geracao de CSV formato GHL (12 colunas)
- Preview dos dados (20 primeiras linhas)
- Relatorio de metricas do processamento
- Download do CSV processado
- Autenticacao JWT (register + login)
- Retry de jobs falhos

## Estrutura

```
datasync/
├── backend/
│   ├── app/           # FastAPI application
│   │   ├── main.py    # App entry point, routes
│   │   ├── config.py  # Environment config
│   │   ├── models.py  # SQLAlchemy models (User, Job)
│   │   ├── processing.py  # Core pipeline (mapping, normalization)
│   │   ├── routes_auth.py # Auth endpoints (register, login)
│   │   ├── routes_jobs.py # Job endpoints (upload, status, download)
│   │   ├── auth.py    # JWT helpers
│   │   ├── db.py      # Database session
│   │   ├── queue_rq.py    # Redis Queue config
│   │   ├── storage.py # File storage helpers
│   │   └── worker.py  # Background worker
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # Vanilla HTML frontend
├── frontend-next/     # Next.js frontend (in development)
└── docker-compose.yml # Postgres + Redis
```

## Setup Local

```bash
# 1. Copiar .env
cp .env.example .env

# 2. Subir Postgres e Redis
docker compose up -d

# 3. Backend
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Frontend Next.js
cd frontend-next
npm install
npm run dev
```

## Deploy

Backend hospedado no Render (Docker).

## Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | /auth/register | Criar conta |
| POST | /auth/login | Login (retorna JWT) |
| POST | /jobs | Upload arquivo |
| GET | /jobs | Listar jobs do usuario |
| GET | /jobs/{id} | Status do job |
| GET | /jobs/{id}/preview | Preview (20 linhas) |
| GET | /jobs/{id}/report | Relatorio de metricas |
| GET | /jobs/{id}/download | Download CSV GHL |
| POST | /jobs/{id}/retry | Retry job falho |
| GET | /health | Health check |
