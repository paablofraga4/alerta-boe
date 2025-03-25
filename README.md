# 📰 AlertaBOE

Sistema inteligente de consulta, clasificación y visualización de publicaciones del BOE (Boletín Oficial del Estado), orientado a facilitar el acceso a la información relevante para autónomos, pymes y ciudadanos.

---

## 🚀 ¿Qué hace?

- Permite seleccionar una fecha para consultar el BOE.
- Extrae todas las publicaciones oficiales del día.
- Clasifica automáticamente cada publicación (subvención, sanción, normativa, etc.).
- Guarda los resultados en una base de datos PostgreSQL.
- Expone una API REST para consumir los datos.
- Interfaz web construida en Streamlit para consulta directa.

---

## 🧠 ¿Para quién es?

Autónomos, emprendedores, pequeñas empresas y ciudadanos que necesitan estar informados sobre:

- Subvenciones
- Sanciones o notificaciones
- Cambios normativos
- Comunicados oficiales

---

## 📁 Estructura del proyecto

alerta-boe/ │ ├── app/ # Backend con FastAPI │ ├── api/ # Endpoints de la API REST │ ├── core/ # Configuraciones (.env) │ ├── db/ # Modelos y conexión a la base de datos │ ├── schemas/ # Esquemas de entrada/salida (Pydantic) │ └── services/ # Lógica de negocio (scraper y clasificador) │ ├── scripts/ # Scripts ejecutables │ └── fetch_boe.py # Descarga y guarda BOE de un día │ ├── venv/ # Entorno virtual (ignorado) ├── .env # Variables de entorno (ignorado) ├── .gitignore # Archivos a ignorar por Git ├── README.md # Este archivo :) ├── requirements.txt # Dependencias del proyecto ├── create_tables.py # Inicializa las tablas en la base de datos └── frontend.py # Interfaz Streamlit para uso interactivo


---

## ⚙️ Requisitos

- Python 3.10+
- PostgreSQL (puerto por defecto: 5432)
- pip
- Git

---

## 🧪 Instalación local

```bash
# 1. Clona el repositorio
git clone https://github.com/TU_USUARIO/alerta-boe.git
cd alerta-boe

# 2. Crea entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura tu archivo .env
copy .env.example .env
# (modifica tu contraseña y nombre de base de datos)

# 5. Crea la base de datos en PostgreSQL: alertaBOE
# 6. Ejecuta creación de tablas
python create_tables.py

# 7. (Opcional) Lanza API y frontend por separado
uvicorn app.main:app --reload
streamlit run frontend.py

🌐 Uso de la interfaz
Ve a http://localhost:8501

Introduce una fecha (formato YYYYMMDD)

Se lanzará automáticamente el scraping

Luego se mostrarán los resultados en pantalla

También puedes consultarlos vía http://localhost:8000/docs

💡 Posibilidades futuras
Clasificación con IA (GPT, embeddings)

Sistema de alertas (correo, Telegram, notificaciones)

Filtros avanzados por sector/ámbito

Dashboard interactivo para visualización

API pública con autenticación

🛡️ Seguridad
Este repositorio no sube .env, contraseñas ni entornos virtuales. Asegúrate de tener .gitignore activo y no subir datos sensibles.

🤝 Contribución
¿Te gustaría aportar ideas o funcionalidades?
¡Haz un fork, crea un branch y lánzate!

bash
Copy
git checkout -b nueva-feature
Pull requests y sugerencias siempre son bienvenidas.

📄 Licencia
MIT License.
Este proyecto es abierto para ayudar a democratizar el acceso al BOE y a la información pública.

🧑‍💻 Autor
Pablo Fraga — Data Scientist, Developer & Product Thinker
Construido con Python, ❤️ y ganas de cambiar las cosas.
