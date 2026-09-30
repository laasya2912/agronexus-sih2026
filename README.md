# AgroNexus — One Platform. Multiple Government Services.
SIH 2026 prototype: "System integration and interoperability among government digital platforms, resulting in fragmented service delivery."

> Government department integrations shown in this prototype are simulated APIs for demonstration (labelled "Demo Government API"). Production deployment would require authorized government API access and agreements.

## Architecture
Farmer → React UI → FastAPI gateway → simulated connectors (`/api/gov/*`: Agriculture, Revenue, Welfare, Insurance, Water Resources; each returns its own field names) → **normalization layer** (`normalize()` in `backend/main.py`) → common object `{service_id, department, status, application_id, last_updated, required_action}`.

## Run locally
```
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp ../.env.example .env
uvicorn main:app --reload --port 8000     # Swagger at http://localhost:8000/docs (DB auto-seeded)
cd frontend && npm install && npm run dev  # http://localhost:5173 (proxies /api to :8000)
```
Build: `npm run build`. Deploy: backend on Render/Railway (`uvicorn main:app --host 0.0.0.0 --port $PORT`, set JWT_SECRET, CORS_ORIGINS); frontend on Vercel/Netlify (serve `dist`, route `/api` to the backend URL).

## Demo credentials (password `Demo@123`)
Farmers 9000000001 (AP, Paddy, 3ac), 9000000002 (AP, Chilli, 5ac), 9000000003 (Telangana, Cotton, 4ac) · Village Head 9000000004 · Official 9000000005 · Admin 9000000006

## Env vars
JWT_SECRET, DATABASE_URL, CORS_ORIGINS, GEMINI_API_KEY (optional; without it AI Mithra runs in labelled demo mode).

## Database
users, schemes (with rule columns), applications, grievances, notifications, consents, audit.

## Limitations / not yet done
Community module, grievance image upload, admin CRUD screens (users/scheme rules), separate FarmerProfile/Comment tables, React Router (tab state used), and translation beyond navigation/key labels are not implemented. **This code was written without being able to install dependencies or run it — expect to fix small errors on first run.**
