# AlertaBOE 2.0 — Arquitectura del refactor

> **Objetivo del producto**: democratizar la información del BOE. Una web donde cualquier persona pueda
> explorar las publicaciones, entender el **hilo normativo** (qué modifica, qué deroga, de dónde viene cada
> norma) y recibir explicaciones en lenguaje claro. Encima de esa base, una **fábrica de contenido**
> automatizada que publica de forma recurrente en LinkedIn / X / TikTok (texto y vídeo generado).

Este documento es el plan maestro del refactor: diagnóstico, arquitectura objetivo, decisiones de stack y
fases de desarrollo.

---

## 1. Diagnóstico del estado actual

Lo que ya funciona y merece conservarse **como lógica**, no como código:

| Pieza | Estado | Veredicto |
|---|---|---|
| Ingesta del sumario diario (`app/services/boe_fetcher.py`) | Funciona, síncrona, mezcla HTTP + parsing + clasificación + persistencia en una función | Reescribir en capas |
| Resúmenes con Groq (`summarizer_groq.py`, `llm_client.py`) | HTTP crudo con `requests`, prompts buenos, reintentos manuales | Conservar prompts, reescribir cliente |
| Legislación consolidada (`app/api/legislacion.py`) | Proxy directo a la API del BOE en el request path | Mover a ingesta + cache local |
| Búsqueda semántica (`semantic_search.py`) | `sentence-transformers` cargado en import, embeddings calculados **en cada request** | Sustituir por pgvector precalculado |
| Clasificación (regex regiones/ámbitos, categorías FAISS) | Útil como primera pasada | Conservar como etapa del pipeline |
| Frontend (`frontend.py`, Streamlit, 1.245 líneas) | Monolito de UI + lógica de negocio | Sustituir por Next.js |
| Modelos DB (`app/db/models.py`) | Sin migraciones, `category` como ARRAY, sin versiones ni referencias | Rediseñar esquema + Alembic |

Problemas transversales:

- `requirements.txt` está **corrupto** (guardado en UTF-16), no es instalable con pip tal cual.
- No hay tests, ni CI, ni Docker, ni migraciones. Scripts sueltos (`create_tables.py`, `drop_tables.py`, `bulk_scraper.py`) hacen de infraestructura.
- Todo el I/O es síncrono (`requests`) dentro de una app FastAPI async.
- El trabajo pesado (resúmenes LLM) se hace offline con scripts manuales, sin estado de pipeline: no se sabe qué publicación está en qué fase.

## 2. Las APIs del BOE (la materia prima)

Todo el producto se apoya en las APIs oficiales de datos abiertos (`https://boe.es/datosabiertos/api/...`):

1. **Sumario diario** — `GET /boe/sumario/{AAAAMMDD}`: todas las publicaciones del día con sección,
   departamento, epígrafe, URLs HTML/PDF/XML. Ya se usa hoy.
2. **Legislación consolidada** — `GET /legislacion-consolidada` (+ `/id/{id}/metadatos`, `/texto`,
   `/texto/indice`, `/texto/bloque/{bloque}`, `/analisis`): normas con su texto consolidado y versionado.
3. **El bloque `analisis` es la joya de la corona**: contiene `materias`, `notas` y sobre todo
   **`referencias/anteriores` y `referencias/posteriores`** con el tipo de relación (MODIFICA, DEROGA,
   DESARROLLA, PRORROGA, DE CONFORMIDAD CON...). Es exactamente lo que hace falta para el "hilo y
   precedentes de cada publicación": un **grafo normativo**.
4. **Tablas auxiliares** — departamentos, materias, ámbitos, rangos (ya hay un `poblar_tablas_auxiliares.py`).
5. **BORME** — misma API de sumarios; ampliación futura para contenido mercantil.

Principio rector del refactor: **el BOE se consulta una vez y se persiste**; la web y los agentes nunca
golpean boe.es en el request path.

---

## 3. Arquitectura objetivo

```
                    ┌─────────────────────────────────────────────────────┐
                    │                      WORKERS                        │
   boe.es APIs ───► │  ingesta ──► parseo ──► enriquecido ──► indexado    │
   (sumario,        │  (raw JSON)  (docs)     (LLM: resumen,  (embeddings │
   consolidada,     │                          clasif., grafo) pgvector)  │
   auxiliares)      └───────────────┬─────────────────────────────────────┘
                                    │ escribe
                                    ▼
                    ┌─────────────────────────────────────────────────────┐
                    │        PostgreSQL 16 + pgvector (única DB)          │
                    │  documents · document_versions · references (grafo) │
                    │  summaries · embeddings · topics · pipeline_state   │
                    └───────────────┬─────────────────────────────────────┘
                                    │ lee
                ┌───────────────────┴───────────────────┐
                ▼                                       ▼
   ┌────────────────────────┐             ┌───────────────────────────────┐
   │   API FastAPI (/v1)    │             │     CONTENT FACTORY           │
   │  búsqueda híbrida      │             │  Curador → Guionista →        │
   │  documento + hilo      │             │  Validador → Render →         │
   │  timeline de norma     │             │  Publicador                   │
   │  chat RAG con citas    │             │  (texto: LinkedIn/X;          │
   └───────────┬────────────┘             │   vídeo: Remotion+TTS→TikTok) │
               ▼                          └───────────────────────────────┘
   ┌────────────────────────┐
   │   Web Next.js 14       │
   │  "el BOE de hoy",      │
   │  explorador, norma +   │
   │  grafo visual, chat    │
   └────────────────────────┘
```

### 3.1 Estructura de repositorio (monorepo en alerta-boe)

```
alerta-boe/
├── apps/
│   ├── api/                  # FastAPI: SOLO capa HTTP (routers, deps, auth)
│   │   └── app/
│   │       ├── main.py
│   │       ├── deps.py
│   │       └── routers/      # v1: documents, search, graph, chat, digest
│   └── web/                  # Next.js 14 App Router + Tailwind
├── boe/                      # paquete Python instalable con el dominio
│   ├── core/                 #   settings (pydantic-settings), modelos SQLAlchemy,
│   │   │                     #   esquemas Pydantic, enums (DocumentStatus, RefType...)
│   ├── clients/              #   cliente httpx async tipado de las APIs del BOE
│   │   ├── boe_summary.py    #   sumario diario
│   │   ├── boe_consolidated.py # legislación consolidada + análisis
│   │   └── boe_tables.py     #   tablas auxiliares
│   ├── ingest/               #   pipeline ETL idempotente por etapas
│   ├── enrich/               #   resúmenes, clasificación, extracción de metadatos vía LLM
│   ├── llm/                  #   router de proveedores (Groq → OpenRouter → OpenAI)
│   ├── search/               #   embeddings + búsqueda híbrida (tsvector + pgvector)
│   ├── graph/                #   grafo normativo: construcción y consultas (recursive CTE)
│   └── content/              #   fábrica de contenido
│       ├── curator.py        #   selección de publicaciones "publicables"
│       ├── writer.py         #   guiones por canal (LinkedIn, X, TikTok)
│       ├── video/            #   render (plantillas Remotion / ffmpeg + TTS)
│       └── publishers/       #   linkedin.py, x.py, tiktok.py (colas + aprobación)
├── workers/                  # entrypoints de jobs (ingesta diaria, enriquecido, contenido)
├── alembic/                  # migraciones
├── tests/                    # pytest (unit + integración con fixtures JSON reales del BOE)
├── infra/
│   ├── docker-compose.yml    # postgres+pgvector, api, worker, web
│   └── Dockerfile.{api,worker,web}
├── pyproject.toml            # sustituye al requirements.txt corrupto (uv/pip instalable)
└── docs/                     # este documento, ADRs, guía de las APIs del BOE
```

### 3.2 Modelo de datos (núcleo)

```sql
documents            -- toda publicación BOE/BORME (boe_id único, fecha, sección, departamento,
                     -- epígrafe, rango, urls, texto_html cacheado, tsvector generado)
document_versions    -- versiones de normas consolidadas (texto por bloques, fecha_vigencia)
references           -- EL GRAFO: (source_id, target_id, rel_type, direction)
                     -- rel_type ∈ {MODIFICA, DEROGA, DESARROLLA, PRORROGA, CORRIGE, ...}
summaries            -- resumen largo, resumen breve ("tiktok"), guion de vídeo; por documento,
                     -- con modelo y versión de prompt usados (reproducibilidad)
embeddings           -- vector(1024) pgvector por documento/chunk, índice HNSW
topics / regions     -- clasificación multi-etiqueta (se migran las tablas actuales)
pipeline_state       -- estado por documento y etapa: pending|running|done|failed + intentos
content_posts        -- piezas de contenido: canal, guion, asset (vídeo/imagen), estado
                     -- (draft → approved → scheduled → published), métricas
users / alerts       -- fase posterior: suscripciones por tema/región
```

Decisiones clave:

- **Una sola base de datos**: PostgreSQL + **pgvector** sustituye a FAISS + embeddings al vuelo. Búsqueda
  híbrida = `tsvector` (BM25-ish, español) + coseno vectorial + re-rank. Menos piezas, backups triviales.
- **Grafo en Postgres**, no Neo4j: la tabla `references` + recursive CTEs cubre "hilo y precedentes"
  (profundidad 2-3 típica). Si algún día hace falta análisis de grafo serio, se exporta.
- **`pipeline_state` explícito**: cada documento sabe en qué fase está; los workers son reanudables e
  idempotentes. Se acabó el "¿a cuáles les falta resumen?" implícito.
- El JSON crudo de cada respuesta del BOE se guarda (columna JSONB o bucket) → reprocesable sin re-fetch.

### 3.3 Pipeline de ingesta y enriquecido

Etapas desacopladas, cada una barata de reintentar:

1. **fetch_summary** (diario, ~08:30): sumario del día → upsert de `documents` (metadatos). Idempotente por `boe_id`.
2. **fetch_text**: descarga HTML/XML del documento, texto limpio a DB.
3. **classify**: regex regiones/ámbito (se conserva el actual) + clasificación multi-etiqueta LLM barata.
4. **summarize**: resumen largo + breve + gancho, en **una sola llamada LLM con salida JSON estructurada**
   (hoy son 2 llamadas separadas con `time.sleep(2.1)` hardcodeado).
5. **embed**: embeddings multilingües (`BAAI/bge-m3` o `intfloat/multilingual-e5-large` vía
   sentence-transformers en el worker, o API de HF/Jina si no queremos GPU/CPU pesada) → pgvector.
6. **link_graph**: para disposiciones con id de consolidada, fetch de `analisis` → filas en `references`.
7. **backfill**: mismo pipeline sobre rangos históricos, con rate-limit respetuoso hacia boe.es.

Orquestación: **empezar simple** — un proceso worker con APScheduler (cron interno) y ejecución por etapas
sobre `pipeline_state`. Nada de Celery/Redis hasta que el volumen lo pida (el BOE publica ~500-900 items/día;
un worker lo digiere de sobra). Los cron también pueden dispararse desde GitHub Actions en el MVP desplegado.

### 3.4 Capa LLM (open source primero)

Un único módulo `boe/llm/` con:

- **Cliente OpenAI-compatible** (SDK `openai` apuntando a base_url configurable) + **router de proveedores**
  con fallback y presupuesto:
  1. **Groq** (Llama 3.3 70B / Llama 4) → volumen barato/rápido: resúmenes, clasificación, guiones.
  2. **OpenRouter** → fallback y acceso a modelos abiertos grandes (DeepSeek, Qwen) para tareas de más razonamiento (análisis del hilo normativo, chat).
  3. **OpenAI/Anthropic** opcional detrás de la misma interfaz para tareas premium si hiciera falta.
- **Salidas estructuradas** con Pydantic (`response_format` JSON + validación; `instructor` si conviene):
  los prompts actuales de `summarizer_groq.py` se conservan y se versionan en `boe/llm/prompts/`.
- **Sin LangChain**: para resúmenes/clasificación/RAG no aporta y añade capas. **LangGraph solo para la
  content factory**, donde sí hay un flujo multi-paso con validación y reintentos.
- Trazabilidad: cada salida LLM guarda modelo + versión de prompt + tokens (y opcionalmente Langfuse).

### 3.5 API pública (`apps/api`, FastAPI async, `/v1`)

- `GET /v1/digest/{fecha}` — el BOE del día: agrupado, resumido, con destacados.
- `GET /v1/documents` — filtros: fecha, sección, departamento, región, tema, rango.
- `GET /v1/documents/{boe_id}` — documento + resúmenes + metadatos.
- `GET /v1/documents/{boe_id}/thread` — **el hilo**: precedentes y derivadas con tipo de relación y profundidad configurable (recursive CTE sobre `references`).
- `GET /v1/laws/{id}/timeline` — versiones de una norma consolidada + qué la modificó y cuándo.
- `POST /v1/search` — búsqueda híbrida (texto + vector + filtros), con "explica por qué es relevante".
- `POST /v1/chat` — RAG conversacional **con citas obligatorias** a boe_id/artículo (streaming SSE).
- Auth por API key desde el día 1 (aunque sea gratis): habilita la "API pública para desarrolladores" del roadmap.

### 3.6 Web (`apps/web`, Next.js 14)

Sustituye al Streamlit. Páginas núcleo:

1. **Home / "El BOE de hoy en 2 minutos"**: destacados del día en lenguaje claro, filtro por perfil (autónomo, empresa, ciudadano, opositor) y región.
2. **Explorador**: búsqueda híbrida con filtros facetados.
3. **Página de documento**: resumen claro + texto original + **visualización del hilo** (grafo/timeline interactivo — react-flow o d3) + chat contextual con citas.
4. **Página de norma consolidada**: timeline de versiones ("esta ley ha cambiado 14 veces, esto cambió en 2023...").
5. **Alertas** (fase posterior): suscripción por tema/región → email/Telegram.

SSR/ISR de Next.js para que cada documento tenga URL indexable por Google — el SEO es el canal de adquisición natural de este producto.

### 3.7 Content factory (LinkedIn / X / TikTok)

Pipeline agentico (grafo LangGraph con roles y validación), ejecutado en cron diario/semanal:

1. **Curador**: puntúa las publicaciones del día por "interés general" (impacto en bolsillos, ayudas, novedad, alcance) y elige 1-3 candidatas. Señales: rango de la norma, departamento, materias, tamaño del hilo de referencias.
2. **Guionista**: por canal —
   - LinkedIn: post 800-1200 caracteres, tono profesional, gancho + 3 claves + enlace a la web.
   - X: hilo de 3-5 tuits.
   - TikTok/Reels/Shorts: guion de 45-60 s (gancho ≤3 s, 3 puntos, CTA), con texto para TTS y subtítulos.
3. **Validador**: segunda pasada LLM con checklist: fidelidad al texto original (anti-alucinación, citando boe_id), tono, longitudes, disclaimers ("esto no es asesoramiento legal").
4. **Render de vídeo** (solo TikTok):
   - **TTS**: `edge-tts` (gratis, voces es-ES buenas) para arrancar; ElevenLabs como upgrade.
   - **Vídeo**: **Remotion** (React → mp4: plantillas de marca con titular, bullets animados, subtítulos karaoke, fondo) — encaja con el stack Next.js. Alternativa 100 % Python: moviepy/ffmpeg con plantillas.
   - Subtítulos generados del propio guion (no hace falta ASR).
5. **Publicador**: cola `content_posts` con estados. **Human-in-the-loop al principio**: el pipeline deja el post en `draft` y lo apruebas desde un panel en la web (un clic) antes de publicar. Cuando la calidad esté probada, se pasa a auto-publish.
   - LinkedIn: API oficial (`w_member_social`, posts + subida de vídeo).
   - X: API v2 (free tier permite publicar; media upload para vídeo).
   - TikTok: Content Posting API (requiere app aprobada; mientras tanto, el vídeo queda listo para subida manual — el render es el 90 % del trabajo).

### 3.8 Infra y calidad

- **Docker Compose**: `postgres` (pgvector/pgvector:pg16), `api`, `worker`, `web`. Un `make up` y todo corre.
- **pyproject.toml** (reemplaza el requirements.txt corrupto) + `uv` para lockfile.
- **Alembic** para migraciones; se acabaron `create_tables.py`/`drop_tables.py`.
- **CI (GitHub Actions)**: ruff + pytest en cada PR; job cron opcional para ingesta en el MVP.
- **Tests**: fixtures con JSON reales del BOE (sumario, consolidada, análisis) → el parseo, que es la parte más frágil (dict-o-lista en cada nivel, como ya sufre `boe_fetcher.py`), queda blindado.
- **Observabilidad**: logging estructurado (structlog) + estado del pipeline consultable vía `GET /v1/admin/pipeline`.
- Despliegue objetivo barato: un VPS (Hetzner) con Compose, o Railway/Fly.io; la web también puede ir a Vercel apuntando a la API.

---

## 4. Fases de desarrollo

| Fase | Entregable | Contenido |
|---|---|---|
| **F0 — Saneo** (base) ✅ | Repo instalable y arrancable | pyproject + uv, estructura monorepo, docker-compose con pgvector, Alembic con esquema nuevo, CI, migración de datos existentes |
| **F1 — Ingesta** ✅ | Pipeline completo y backfill | Clientes httpx tipados de las APIs, etapas fetch→text→classify→summarize→embed→link con `pipeline_state` idempotente/reanudable, router LLM, backfill histórico, grafo desde `analisis`, CLI (`boe ingest/backfill/enrich/status`) y worker diario |
| **F2 — API v1** ✅ | API pública consumible | Endpoints de digest/documents/thread/search híbrida (full-text español + pgvector con RRF)/chat RAG con citas obligatorias; auth por API key; índices GIN + HNSW |
| **F3 — Web** ✅ | Sustituto de Streamlit | Next.js 14 (App Router + Tailwind): home "BOE de hoy" (SSR), explorador de búsqueda, página de documento (SSR, SEO) con resumen, hilo normativo visual y chat. `frontend.py` queda marcado como legacy |
| **F4 — Grafo** | El diferenciador | Ingesta de `analisis` (referencias), tabla `references`, endpoints thread/timeline, visualización interactiva del hilo |
| **F5 — Content factory** ✅ | Publicación recurrente | Curador (scoring de interés) → Guionista (LinkedIn/X/TikTok) → Validador (anti-alucinación con citas); cola `content_posts` con aprobación humana vía `/v1/content` y **panel web `/contenido`**; publicadores (dry-run + interfaz real); **vídeo end-to-end**: guion→SRT + narración edge-tts + **plantilla Remotion** (`apps/video`) que renderiza el mp4 vertical |
| **F6 — Alertas y usuarios** ✅ | Retención | Usuarios ligeros por email, suscripciones por tema/región/ámbito/palabra clave, matcher idempotente y notificadores email (SMTP) y Telegram (con dry-run); endpoints `/v1/subscriptions` y job diario en el worker |

Cada fase termina con algo usable en producción. F1-F2 pueden solaparse; F5 (texto) puede adelantarse en
cuanto exista F1, porque solo necesita resúmenes buenos.

---

## 5. Decisiones de stack (resumen)

| Ámbito | Elección | Por qué |
|---|---|---|
| Backend | FastAPI async + httpx + SQLAlchemy 2 async | Continuidad con lo que hay, todo async de verdad |
| DB | PostgreSQL 16 + pgvector | Relacional + vectorial + grafo (CTE) en una sola pieza |
| LLM volumen | Groq (Llama 3.3/4) vía SDK openai | Ya en uso, gratis/barato, rápido |
| LLM fallback/razonamiento | OpenRouter (DeepSeek/Qwen) | Open source, un solo formato de API |
| Embeddings | bge-m3 / multilingual-e5 (HF) | Multilingüe, open source, precalculado en worker |
| Orquestación agentes | LangGraph **solo** en content factory | Flujo multi-paso real con validación. Resto: SDK plano + Pydantic |
| Frontend | Next.js 14 + Tailwind | SEO (SSR/ISR), ecosistema React (react-flow para el grafo, Remotion para vídeo) |
| Vídeo | Remotion + edge-tts | Plantillas React reutilizables, TTS gratis es-ES |
| Jobs | APScheduler en worker (→ arq/Celery si crece) | Volumen del BOE no justifica más |
| Calidad | uv + ruff + pytest + Alembic + GH Actions | Estándar moderno, repo instalable |

---

## 6. Riesgos y mitigaciones

- **Rate limits / disponibilidad de boe.es**: cache agresivo del raw JSON, reintentos con backoff (tenacity), backfill nocturno lento.
- **Alucinaciones legales**: RAG con citas obligatorias, agente Validador en contenido social, disclaimer visible, resúmenes siempre enlazados al original.
- **APIs de redes sociales** (aprobación de apps TikTok/LinkedIn): el pipeline produce el asset final aunque la publicación sea manual al principio; la automatización total es incremental.
- **Coste LLM en backfill histórico**: resúmenes bajo demanda para histórico (solo se resume lo que alguien consulta o lo que el curador selecciona), completo solo para el flujo diario.
- **Migración de datos actuales**: script de migración one-shot del esquema viejo al nuevo dentro de F0; nada se tira.
