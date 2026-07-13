# Despliegue de AlertaBOE

Topología: **web en Vercel** · **base de datos en Supabase** · **backend Python
(API + worker) en un host de contenedores** (Render recomendado; Fly/Railway
valen igual).

```
   Navegador ─► Vercel (Next.js, apps/web) ─► API FastAPI (contenedor) ─► Supabase (Postgres+pgvector)
                                                     ▲
                                          Worker (ingesta/alertas, contenedor)
```

## 1. Base de datos — Supabase ✅ (ya creada)

- Proyecto: **alerta-boe** (`agpcrbspxbrgdnciyuxa`), región eu-west-3.
- URL API: `https://agpcrbspxbrgdnciyuxa.supabase.co`
- Esquema aplicado (migraciones 0001–0003): 15 tablas, `pgvector`, columna
  generada `search_vector` (GIN) e índice HNSW. `alembic_version` = `0003`, así
  que el contenedor puede seguir aplicando futuras migraciones con normalidad.

**Cadena de conexión** (para `DATABASE_URL` del backend). Copia la contraseña
desde el dashboard → *Project Settings → Database* (o resetéala allí):

```
postgresql+asyncpg://postgres:<PASSWORD>@db.agpcrbspxbrgdnciyuxa.supabase.co:5432/postgres
```

> Usa la conexión **directa** (puerto 5432) para el contenedor persistente. Si
> usas el *pooler* en modo transacción (6543), añade `?statement_cache_size=0`
> por compatibilidad con asyncpg/PgBouncer.

### ⚠️ Seguridad: Row Level Security (RLS)

Las tablas están sin RLS. **En nuestra arquitectura el acceso es solo desde el
backend con el rol `postgres` por la cadena de conexión** (no usamos las
librerías cliente de Supabase con la `anon key`), así que la app no depende de
RLS. Pero la API REST automática de Supabase (PostgREST) sí quedaría expuesta con
la anon key. Recomendación: **activar RLS sin políticas** para cerrar esa vía
(el backend, que va por conexión directa, no se ve afectado):

```sql
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
-- ... (repetir para las 15 tablas; ver bloque completo en el chat)
```

Decides tú si aplicarlo. No se ha aplicado automáticamente.

## 2. Web — Vercel

La web (`apps/web`) es una app Next.js 14 lista para Vercel:

1. Importa el repo en Vercel y fija **Root Directory = `apps/web`**.
2. Variables de entorno:
   - `NEXT_PUBLIC_API_BASE` = URL pública de la API (paso 3), p. ej.
     `https://alertaboe-api.onrender.com`
   - `API_BASE` = la misma URL (usada en SSR).
   - `NEXT_PUBLIC_API_KEY` = una de las `API_KEYS` del backend (si activas auth).
3. Deploy. Next detecta el framework solo (`npm run build`).

## 3. Backend — todo gratis (API en Render + ingesta en GitHub Actions)

Render **no tiene plan gratis para workers**, así que separamos:

### 3a. API — Render (servicio web, plan free)

`infra/render.yaml` despliega solo la API:

1. Render → *New → Blueprint* → apunta a este repo. Crea `alertaboe-api`
   (web, Docker `infra/Dockerfile.api`, **plan free**, sin tarjeta).
2. Rellena los secretos (`sync:false`): `DATABASE_URL` (Supabase, paso 1),
   `API_CORS_ORIGINS` (tu dominio Vercel), `GROQ_API_KEY`, opcional
   `OPENROUTER_API_KEY` y `API_KEYS`.
3. La API aplica `alembic upgrade head` al arrancar (idempotente).
4. Copia la URL que te da Render (p. ej. `https://alertaboe-api.onrender.com`)
   para el paso 2 (Vercel).

> El plan free "duerme" la API tras ~15 min de inactividad; la primera petición
> tras dormir tarda unos segundos (cold start). Suficiente para empezar.

### 3b. Ingesta diaria — GitHub Actions (gratis)

`.github/workflows/ingest.yml` corre la ingesta+enriquecido+alertas cada día a
las 07:00 UTC (y a demanda desde *Actions → Run workflow*). Configura los
**secrets del repo** (GitHub → *Settings → Secrets and variables → Actions*):

- `DATABASE_URL` (el de Supabase, paso 1) y `GROQ_API_KEY` (mínimo).
- Opcionales: `OPENROUTER_API_KEY`, `SMTP_*`, `TELEGRAM_BOT_TOKEN`.

Así no necesitas ningún worker de pago. Si prefieres un worker siempre-encendido
en Render, el `render.yaml` incluye el bloque comentado (requiere plan de pago).

### Nota sobre embeddings

La búsqueda vectorial usa `sentence-transformers` (pesado). Ni la API de Render
free ni el runner de Actions lo instalan por defecto: la etapa EMBEDDED se marca
SKIPPED y la **búsqueda funciona en modo full-text**. Actívalo (extra
`[embeddings]`) cuando tengas un host con RAM suficiente.

## 4. Alternativas de host del backend

- **Fly.io**: `fly launch` con `infra/Dockerfile.api`; worker como proceso aparte.
- **Railway**: servicio Docker por cada Dockerfile; mismas variables.

## Checklist de variables de entorno

| Variable | Dónde se pone | Para qué |
|---|---|---|
| `DATABASE_URL` | Render (API) **+** GitHub Actions (secret) | Conexión a Supabase (asyncpg) |
| `GROQ_API_KEY` | Render (API) **+** GitHub Actions (secret) | LLM (resúmenes, chat, contenido) |
| `API_CORS_ORIGINS` | Render (API) | Permitir el dominio de la web |
| `OPENROUTER_API_KEY` | Render (API) + Actions | LLM de reserva (opcional) |
| `API_KEYS` | Render (API) | Auth de `/v1` por `X-API-Key` (opcional) |
| `SMTP_*` | GitHub Actions (secret) | Alertas por email (opcional) |
| `TELEGRAM_BOT_TOKEN` | GitHub Actions (secret) | Alertas por Telegram (opcional) |
| `NEXT_PUBLIC_API_BASE` / `API_BASE` | Vercel (web) | URL de la API de Render |
| `NEXT_PUBLIC_API_KEY` | Vercel (web) | Igual a `API_KEYS` si activas auth (opcional) |
