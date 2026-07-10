# 📰 AlertaBOE

**Sistema inteligente de consulta, clasificación y asistencia normativa del BOE**, diseñado para facilitar el acceso a la información relevante a autónomos, pymes y ciudadanos comunes.

> ⚙️ Scrapea, analiza, clasifica y explica publicaciones del BOE de forma automática.  
> 🎯 Pensado para ser realmente útil, accesible y entendible por cualquier persona.

---

## 🏗️ Refactor 2.0 (en curso)

El proyecto está siendo reescrito sobre una arquitectura nueva, documentada en
[`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): monorepo con paquete de dominio
`boe/`, API `apps/api` (FastAPI async), web `apps/web` (Next.js), PostgreSQL +
pgvector, grafo normativo ("hilo y precedentes") y fábrica de contenido para
redes. El código de la carpeta `app/` y `frontend.py` es **legacy** y se
retirará en fases posteriores; convive con el nuevo mientras dure la migración.

### Puesta en marcha (stack 2.0)

```bash
# 1. Instalar el paquete y las dependencias de desarrollo
pip install -e ".[dev]"

# 2. Configurar el entorno
cp .env.example .env    # edita GROQ_API_KEY, etc.

# 3. Levantar todo con Docker (Postgres+pgvector, API y worker)
docker compose -f infra/docker-compose.yml up --build
#    La API aplica las migraciones y queda en http://localhost:8000/docs

# --- o, sin Docker, contra tu propio Postgres con pgvector ---
alembic upgrade head             # crea la extensión vector + el esquema
uvicorn apps.api.main:app --reload --port 8000

# 4. Comprobar configuración y smoke test de los clientes del BOE
boe check
boe fetch-summary 20240709
```

### Calidad

```bash
ruff check boe apps tests     # lint
pytest -q                     # tests (parsing del BOE, router LLM, cliente HTTP)
```

El CI (GitHub Actions) ejecuta lint, tests y aplica las migraciones sobre un
Postgres con pgvector en cada PR.

### API v1 (endpoints principales)

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health`, `/health/db` | Salud del servicio y de la DB |
| GET | `/v1/digest/{fecha}` | El BOE del día: agrupado por ámbito, resumido y con destacados |
| GET | `/v1/documents` | Listado con filtros (fecha, departamento) |
| GET | `/v1/documents/{boe_id}` | Detalle de una publicación |
| GET | `/v1/documents/{boe_id}/thread` | El hilo normativo: precedentes y derivadas |
| POST | `/v1/search` | Búsqueda híbrida (full-text español + vectorial, RRF) con filtros |
| POST | `/v1/chat` | Chat RAG con citas obligatorias a los `boe_id` |

Los endpoints `/v1` aceptan la cabecera `X-API-Key` (obligatoria si `API_KEYS`
está definido; API abierta en desarrollo si no).

---

## 📜 Documentación legacy

> Lo que sigue describe el sistema actual (Streamlit + scripts), que se mantiene
> operativo durante el refactor.

---

## 🚀 ¿Qué hace?

✅ Funcionalidades principales:

- 📅 Consulta por fecha: Visualiza fácilmente todas las publicaciones oficiales de un día.
- 🧠 Consultor inteligente: Introduce una consulta en lenguaje natural y te devuelve las publicaciones relevantes clasificadas.
- 💬 Asistente personal: Recibe una explicación automática de cómo te afecta el BOE, según tu consulta.
- 🔍 Explorador de legislación consolidada: Encuentra normas legales históricas y actuales por comunidad autónoma, tema o palabras clave.
- 🧾 Resúmenes automáticos: Cada publicación se resume automáticamente en versión larga y en formato "TikTok" (titular breve).
- 🧠 Clasificación temática y por región: Toda publicación es categorizada y geolocalizada automáticamente.
- 🧠 Chat sobre cada publicación: Puedes hacer preguntas directamente sobre cualquier disposición del BOE (con texto enriquecido desde HTML o PDF).
- 📊 Dashboard de categorías detectadas para cada búsqueda.

---

## 👥 ¿Para quién es?

🔹 Autónomos, pymes, emprendedores  
🔹 Funcionarios o estudiantes de derecho  
🔹 Ciudadanos que quieren entender qué publica el BOE sin ser abogados  
🔹 Periodistas, analistas o consultores legales

Casos típicos:

- “Soy autónomo en Galicia, ¿hay nuevas ayudas?”  
- “¿Qué publicaciones recientes tratan sobre subvenciones?”  
- “¿Me afecta alguna normativa nueva sobre transporte escolar?”

---

## 🧠 ¿Qué tiene por dentro?

- FastAPI (backend y API REST)
- PostgreSQL (base de datos estructurada)
- Streamlit (interfaz web interactiva)
- Embeddings con `sentence-transformers` para búsquedas semánticas
- Modelos LLM vía Groq y Ollama para resúmenes e interacción
- Clasificación y detección de contexto por regex y NLP
- Infraestructura lista para procesamiento en batch

---

## 📁 Estructura del proyecto

alerta-boe/ │ ├── app/ # Backend con FastAPI │ ├── api/ # Endpoints REST │ ├── db/ # Modelos y sesión SQLAlchemy │ ├── schemas/ # Esquemas de entrada/salida (Pydantic) │ └── services/ # Scrapers, clasificadores, IA, etc. │ ├── scripts/ # Scripts ejecutables (resumidor, fetcher) ├── frontend.py # Interfaz completa en Streamlit ├── create_tables.py # Inicializa la base de datos ├── requirements.txt # Dependencias ├── .env.example # Plantilla de configuración └── README.md # Este archivo :)

yaml
Copy
Edit

---

## ⚙️ Requisitos

- Python 3.10+
- PostgreSQL (puerto por defecto: 5432)
- Groq API Key (opcional, para resumen vía LLM)
- Git + pip

---

## 🧪 Instalación local

```bash
# 1. Clona el repositorio
git clone https://github.com/TU_USUARIO/alerta-boe.git
cd alerta-boe

# 2. Crea y activa entorno virtual
python -m venv venv
source venv/bin/activate  # o .\venv\Scripts\activate en Windows

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Copia el archivo de entorno
cp .env.example .env  # y edítalo con tus credenciales

# 5. Crea la base de datos en PostgreSQL
#    nombre sugerido: alertaBOE

# 6. Ejecuta creación de tablas
python create_tables.py

# 7. Lanza backend y frontend
uvicorn app.main:app --reload         # Puerto 8000
streamlit run frontend.py             # Puerto 8501
🌐 Uso de la interfaz
Ve a 👉 http://localhost:8501 y prueba:

📅 Elige una fecha → BOE se scrapea y muestra

🤖 Haz una pregunta tipo: "Autónomo en Valencia, ¿subvenciones recientes?"

💬 Usa el asistente para recibir explicaciones directas

🔎 Consulta legislación histórica y filtrada por tema

🧠 Haz clic en cualquier tarjeta y habla con ella vía chat contextual

🧪 Scripts útiles
bash
Copy
Edit
# Descargar y guardar publicaciones del BOE por fecha
python -m scripts.fetch_boe 20240315

# Generar resúmenes para las publicaciones faltantes
python -m scripts.resumidor_offline --limit 50

# También puedes usar rangos
python -m scripts.resumidor_offline --from 2023-01-01 --to 2023-01-31
💡 Posibilidades futuras
Sistema de alertas por temas, regiones o categorías

Usuarios con login + favoritos + seguimiento normativo

Versión móvil / API pública para desarrolladores

Integración con Telegram o WhatsApp

Informes automáticos en PDF

Plugin para navegador que detecte si una ley te afecta

🛡️ Seguridad
Este repositorio no contiene claves sensibles ni sube el archivo .env.
Asegúrate de no subir tus credenciales ni tu entorno virtual.

🤝 Contribución
¿Te gusta el proyecto?
¿Quieres ayudar, proponer ideas, mejorar diseño o rendimiento?

bash
Copy
Edit
git checkout -b nueva-feature
Pull requests y sugerencias siempre son bienvenidas 🫶

📄 Licencia
MIT License.
Hecho para facilitar el acceso a la información pública y al BOE.
Úsalo, mejóralo, compártelo.

🧑‍💻 Autor
Pablo Fraga — Data Scientist, Developer & Product Thinker

Construido con Python, 💙 y muchas ganas de cambiar las cosas.