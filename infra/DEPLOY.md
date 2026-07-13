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

## 3. Backend Python (API + worker) — Render

`infra/render.yaml` es un blueprint listo:

1. Render → *New → Blueprint* → apunta a este repo.
2. Crea dos servicios: `alertaboe-api` (web, Docker `infra/Dockerfile.api`) y
   `alertaboe-worker` (worker, Docker `infra/Dockerfile.worker`).
3. Rellena los secretos (`sync:false`): `DATABASE_URL` (Supabase, paso 1),
   `API_CORS_ORIGINS` (tu dominio Vercel), `GROQ_API_KEY`, `OPENROUTER_API_KEY`,
   y para alertas `SMTP_*` / `TELEGRAM_BOT_TOKEN`.
4. La API aplica `alembic upgrade head` al arrancar (idempotente: ya está en 0003).

### Notas de recursos

- **Embeddings**: el worker instala el extra `[embeddings]` (sentence-transformers
  + torch), que pesa. En planes pequeños puede quedarse sin memoria. Si no
  necesitas búsqueda vectorial de inmediato, quita `embeddings` del
  `Dockerfile.worker`: la etapa EMBEDDED se marca SKIPPED y la búsqueda funciona
  en modo full-text. Actívalo cuando tengas plan con RAM suficiente.
- **Ingesta programada**: el worker corre APScheduler (cron interno, 08:30). En
  alternativa serverless, un Vercel Cron puede golpear un endpoint de ingesta.

## 4. Alternativas de host del backend

- **Fly.io**: `fly launch` con `infra/Dockerfile.api`; worker como proceso aparte.
- **Railway**: servicio Docker por cada Dockerfile; mismas variables.

## Checklist de variables de entorno

| Variable | Dónde | Para qué |
|---|---|---|
| `DATABASE_URL` | API + worker | Conexión a Supabase (asyncpg) |
| `API_KEYS` | API (y web) | Auth de `/v1` por `X-API-Key` |
| `API_CORS_ORIGINS` | API | Permitir el dominio de la web |
| `GROQ_API_KEY` / `OPENROUTER_API_KEY` | API + worker | LLM (resúmenes, chat, contenido) |
| `SMTP_*` | worker | Alertas por email |
| `TELEGRAM_BOT_TOKEN` | worker | Alertas por Telegram |
| `NEXT_PUBLIC_API_BASE` / `API_BASE` | web | URL de la API |
