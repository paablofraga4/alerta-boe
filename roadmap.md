# 🧭 Roadmap de AlertaBOE

Este documento contiene ideas, funcionalidades y mejoras que se pueden ir incorporando a futuro. Clasificadas por prioridad y complejidad.

---

## 🚀 MVP actual (completado)

- [x] Scraper del BOE por fecha
- [x] Clasificador básico por palabras clave
- [x] Almacenamiento en PostgreSQL
- [x] API REST con FastAPI
- [x] Interfaz web con Streamlit
- [x] Selector de fecha en frontend
- [x] Visualización inmediata de publicaciones
- [x] Scripts automáticos (`start.ps1`)
- [x] Documentación pro (`README.md`)

---

## 🟢 FASE 2 — Mejoras funcionales

| Idea                                    | Prioridad | Tipo       |
|-----------------------------------------|-----------|------------|
| Añadir filtro por categoría en frontend | Alta      | UI         |
| Guardar más campos del BOE (resumen, enlace) | Alta  | Backend    |
| Clasificación con NLP/embeddings        | Media     | IA/NLP     |
| Paginación o scroll infinito en Streamlit | Media    | UI         |
| Filtro por ámbito geográfico            | Media     | Backend/UI |
| Dashboard con métricas (Dash/Plotly)    | Media     | Visualización |
| Cambiar almacenamiento a SQLite para entorno sin PostgreSQL | Baja | Infraestructura |

---

## 🔔 FASE 3 — Funcionalidades avanzadas

| Idea                                           | Prioridad | Tipo        |
|------------------------------------------------|-----------|-------------|
| Alerta por email o Telegram                   | Alta      | Automatización |
| Sistema de usuarios con perfiles personalizados | Alta     | Seguridad/UI |
| Historial de búsquedas por usuario            | Media     | UX/DB       |
| Autenticación para acceder a la API           | Media     | Seguridad   |
| Clasificador entrenado con GPT/transformers   | Media     | IA          |
| Modo CLI (línea de comandos para scraping)    | Baja      | Dev Tools   |
| Exportar resultados a PDF o Excel             | Baja      | Data Output |

---

## 🧪 Ideas locas / a experimentar

- Generar resumen automático con LLM
- Conectar con Notion, Airtable o Google Sheets
- Notificaciones por cambios normativos a medida
- Widget embebible para páginas web o dashboards
- App móvil mini para freelancers

---

## ✏️ Notas del autor

> Pablo Fraga — Este roadmap es vivo, flexible y pensante. Cualquier idea que surja en medio de un café, aquí tiene su lugar.

---

