import streamlit as st
import subprocess
import requests
import sys
from datetime import date, datetime, timedelta
from collections import Counter
import pandas as pd
import altair as alt
import textwrap
import html  # para escapar strings peligrosos

from app.db.session import SessionLocal
from app.db.models import Publication, Region, Scope
from app.services.semantic_search import buscar_similares
from app.services.intent_parser import detectar_region, detectar_scope, detectar_extra_tag
from app.services.classifier import clasificar_categoria_por_regex

# CONFIGURACIÓN GENERAL
st.set_page_config(
    page_title="📘 AlertaBOE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# INYECCIÓN DE ESTILOS Y ANIMACIONES + EFECTO SPARKLE
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
    scroll-behavior: smooth;
}

/* TITULARES */
h1.big-title {
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(90deg, #1abc9c, #3498db);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.subtitle {
    font-size: 1.3rem;
    color: #7f8c8d;
    margin-bottom: 2rem;
}

/* ANIMACIONES */
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(20px);}
    to {opacity: 1; transform: translateY(0);}
}
@keyframes highlight {
    0% { background-color: #dff9fb; }
    100% { background-color: transparent; }
}
.tarjeta {
    animation: fadeIn 0.6s ease forwards, highlight 2s ease;
    opacity: 0;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.5rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #ffffff, #f8f9fa);
    border-left: 5px solid #1abc9c80;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.tarjeta:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
.tarjeta h4 {
    color: #2c3e50;
    margin-bottom: 0.5rem;
}
div.stButton > button {
    background: linear-gradient(to right, #1abc9c, #16a085);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: background 0.3s ease, transform 0.2s ease;
}
div.stButton > button:hover {
    background: linear-gradient(to right, #16a085, #1abc9c);
    transform: scale(1.03);
}
input, select, textarea {
    transition: box-shadow 0.3s ease, border 0.3s ease;
}
input:focus, select:focus, textarea:focus {
    border: 1.5px solid #1abc9c !important;
    box-shadow: 0 0 6px rgba(26, 188, 156, 0.3) !important;
}
div.row-widget.stRadio > div {
    gap: 1rem;
}
a {
    text-decoration: none;
    color: #2980b9;
}
a:hover {
    color: #1abc9c;
    text-decoration: underline;
}
hr {
    border-top: 2px solid #ecf0f1;
    margin: 2rem 0;
}
</style>
<canvas id="sparkCanvas" style="position:absolute;top:60px;left:50%;transform:translateX(-50%);pointer-events:none;z-index:999;" width="300" height="100"></canvas>
<script>
const canvas = document.getElementById('sparkCanvas');
const ctx = canvas.getContext('2d');
let sparks = [];
function createSpark() {
    sparks.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 1,
        alpha: 1.0
    });
}
function drawSparks() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < sparks.length; i++) {
        let s = sparks[i];
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.radius, 0, 2 * Math.PI);
        ctx.fillStyle = `rgba(26, 188, 156, ${s.alpha})`;
        ctx.fill();
        s.alpha -= 0.02;
    }
    sparks = sparks.filter(s => s.alpha > 0);
}
setInterval(() => {
    createSpark();
    drawSparks();
}, 50);
</script>
""", unsafe_allow_html=True)



# CABECERA
st.markdown("""
<div style='text-align: center; padding: 1.2rem 0 0.5rem 0; position: relative;'>
    <div style="position: absolute; right: 25px; top: 10px; font-size: 2.2rem; animation: float 3s ease-in-out infinite;">
        📡
    </div>
    <h1 class='big-title'>📘 Alerta<span style='color:#1abc9c;'>BOE</span></h1>
    <p class='subtitle'>Tu radar inteligente para detectar lo importante en el BOE</p>
    <hr/>
</div>
<style>
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
  100% { transform: translateY(0px); }
}
</style>
""", unsafe_allow_html=True)

# ✅ Carrusel de modos mejorado con efecto visual de "rotación"
# Sustituye tu bloque anterior de navegación de modo por este completo

# OPCIONES DISPONIBLES
modo_opciones = [
    {"label": "🔍 Por fecha", "value": "fecha"},
    {"label": "🤖 Consultor inteligente", "value": "consultor"},
    {"label": "🔹 Legislación", "value": "legislacion"}
]

if "modo_index" not in st.session_state:
    st.session_state.modo_index = 0

cols_flechas = st.columns([1, 6, 1])

# Flecha izquierda
with cols_flechas[0]:
    if st.button("◀️", use_container_width=True):
        st.session_state.modo_index = (st.session_state.modo_index - 1) % len(modo_opciones)

# Flecha derecha
with cols_flechas[2]:
    if st.button("▶️", use_container_width=True):
        st.session_state.modo_index = (st.session_state.modo_index + 1) % len(modo_opciones)

# Mostramos los 3 modos con efecto "rotación"
idx = st.session_state.modo_index
prev = modo_opciones[(idx - 1) % len(modo_opciones)]["label"]
actual = modo_opciones[idx]["label"]
siguiente = modo_opciones[(idx + 1) % len(modo_opciones)]["label"]

st.markdown(f"""
<div style="display: flex; justify-content: center; align-items: center; gap: 20px; padding: 1rem 0;">
    <div style="opacity: 0.4; font-size: 1rem; transform: scale(0.85); transition: all 0.3s ease;">{prev}</div>
    <div style="font-size: 1.6rem; font-weight: bold; color: #1abc9c; background-color: #e8fafa; padding: 0.5rem 1.2rem; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: all 0.3s ease;">{actual}</div>
    <div style="opacity: 0.4; font-size: 1rem; transform: scale(0.85); transition: all 0.3s ease;">{siguiente}</div>
</div>
""", unsafe_allow_html=True)

# Activar visibilidad por modo
modo = modo_opciones[st.session_state.modo_index]["value"]
mostrar_por_fecha = modo == "fecha"
mostrar_consultor = modo == "consultor"
mostrar_legislacion = modo == "legislacion"


# ESTADO GLOBAL
if "publicaciones" not in st.session_state:
    st.session_state.publicaciones = []
if "ultima_fecha" not in st.session_state:
    st.session_state.ultima_fecha = None

# CATEGORÍAS OFICIALES
CATEGORIAS_VALIDAS = [
    'Agroalimentario', 'Asuntos sociales', 'Convenio', 'Cultura', 'Economía',
    'Educación', 'Empleo público', 'Empresa y comercio', 'Infraestructura',
    'Justicia', 'Medio ambiente', 'Norma', 'Sanción', 'Sanidad',
    'Seguridad', 'Sentencia', 'Subvención', 'Tecnología'
]


# COMPONENTES DE TARJETA

def mostrar_tarjeta_legislacion(norm):
    vigente = '✅' if norm.get("vigente") else '❌'
    st.markdown(f"""
    <div class='tarjeta'>
        <h4>🔖 {html.escape(norm['titulo'])}</h4>
        <p><b>Fecha publicación:</b> {norm['fecha_publicacion']} | <b>Vigente:</b> {vigente}</p>
        <p><b>Departamento:</b> {html.escape(norm['departamento'])} | <b>Rango:</b> {html.escape(norm['rango'])}</p>
        <p><a href="{norm['url_boe']}" target="_blank">🔗 Ver en el BOE</a></p>
    </div>
    """, unsafe_allow_html=True)


def mostrar_tarjeta(pub):
    # El título se escapa, ya que es texto simple.
    title = html.escape(pub.get("title", "[Sin título]"))
    
    # Si la publicación tiene etiqueta, se asume que el resumen es texto plano
    # y se escapa y acorta; en caso contrario, se asume que contiene HTML y se deja intacto.
    if pub.get("extra_tag"):
        resumen = textwrap.shorten(html.escape(pub.get("body") or pub.get("scope") or "Sin resumen"), width=300)
    else:
        resumen = pub.get("body") or pub.get("scope") or "Sin resumen"
    
    depto = html.escape(pub.get("departamento") or "N/D")
    seccion = html.escape(pub.get("seccion") or "N/D")
    epigrafe = html.escape(pub.get("epigrafe") or "N/D")
    extra_tag = html.escape(pub.get("extra_tag", "")) if pub.get("extra_tag") else "Sin etiqueta"

    html_tarjeta = f"""
    <div class='tarjeta'>
        <h4>📄 {title}</h4>
        <p style='margin: 0.3rem 0;'>
            🗓️ <b>Fecha:</b> {pub.get("date", "N/D")} &nbsp;&nbsp;
            🏛️ <b>Dpto:</b> {depto}
        </p>
        <p style='margin: 0.3rem 0;'>
            🏷️ <b>Categoría:</b> {html.escape(pub.get("category") or "N/D")}
        </p>
    """

    if extra_tag:
        html_tarjeta += f"<p style='margin: 0.3rem 0;'>🔖 <b>Etiqueta:</b> {extra_tag}</p>"

    html_tarjeta += f"""
        <p style='margin: 0.3rem 0;'>
            📂 <b>Sección:</b> {seccion} / {epigrafe}
        </p>
        <p style='margin-top: 1rem; font-style: italic; color:#5d5d5d;'>
            “{resumen}”
        </p>
        <p style='margin-top: 1rem; font-weight:500;'>
    """

    enlaces = []
    if pub.get("url_html"):
        enlaces.append(f"<a href='{pub['url_html']}' target='_blank'>🔗 Ver en el BOE</a>")
    if pub.get("url_pdf"):
        enlaces.append(f"<a href='{pub['url_pdf']}' target='_blank'>⬇️ PDF</a>")

    html_tarjeta += " · ".join(enlaces)
    html_tarjeta += "</p></div>"

    st.markdown(html_tarjeta, unsafe_allow_html=True)


# CONSULTOR INTELIGENTE
if mostrar_consultor:
    st.subheader("🤖 ¿Qué necesitas encontrar?")
    consulta = st.text_input("Ej: ayudas para autónomos en Galicia")

    db = SessionLocal()
    # Obtención de categorías disponibles y filtradas según las válidas
    categorias_en_bd = sorted({c[0] for c in db.query(Publication.category).distinct() if c[0]})
    categorias_filtradas = ["Todas"] + [cat for cat in categorias_en_bd if cat in CATEGORIAS_VALIDAS]
    categoria_seleccionada = st.selectbox("🎯 Filtrar por categoría", categorias_filtradas)

    # Listas para detección (las obtenemos una sola vez)
    regiones_disponibles = [r.name for r in db.query(Region).all()]
    scopes_disponibles = [s.name for s in db.query(Scope).all()]

    # Detección automática usando las funciones disponibles
    # Aquí podrías integrar el clasificador de categorías si lo tienes:
    categoria_clasificada = None
    try:
        # Ejemplo: si tienes una función clasificar_categoria
        categoria_clasificada = clasificar_categoria_por_regex(consulta)
    except Exception:
        pass

    region_detectada = detectar_region(consulta, regiones_disponibles)
    scope_detectado = detectar_scope(consulta, scopes_disponibles)
    extra_tag_detectado = detectar_extra_tag(consulta)

    if modo == "🤖 Consultor inteligente del BOE" and consulta:
        st.info(f"""
        🔎 *Resumen de tu consulta:*
        
        • **Región:** {region_detectada or 'No detectada'}
        • **Alcance:** {scope_detectado or 'No detectado'}
        • **Etiqueta:** {extra_tag_detectado or 'No detectada'}
        • **Categoría:** {categoria_seleccionada if categoria_seleccionada != 'Todas' else categoria_clasificada or 'No detectada'}
        """)

    if st.button("🔍 Buscar publicaciones"):
        desde = datetime.today().date() - timedelta(days=60)
        query = db.query(Publication).filter(Publication.date >= desde)

        # Prioridad: Si el usuario selecciona una categoría en el select, se utiliza.
        # Si no, se usa el resultado del clasificador (si lo hay).
        if categoria_seleccionada != "Todas":
            query = query.filter(Publication.category == categoria_seleccionada)
        elif categoria_clasificada:
            query = query.filter(Publication.category == categoria_clasificada)

        # Aplicar filtro por scope y extra_tag, en función de lo detectado
        if scope_detectado:
            query = query.join(Scope).filter(Scope.name.ilike(f"%{scope_detectado}%"))
        if extra_tag_detectado:
            query = query.filter(Publication.extra_tag.ilike(f"%{extra_tag_detectado}%"))

        resultados = query.all()

        # Filtrado manual por región: se queda solo con aquellas publicaciones que incluyan la región detectada
        if region_detectada:
            resultados = [p for p in resultados if any(r.name.lower() == region_detectada.lower() for r in p.regions)]

        if not resultados:
            st.warning("❌ No se encontraron coincidencias recientes.")
        else:
            # Puedes seguir usando buscar_similares para ordenar según la consulta
            similares = buscar_similares(consulta, [p.__dict__ for p in resultados])
            st.subheader(f"📄 Resultados para: *{consulta}*")
            for pub in similares[:10]:
                mostrar_tarjeta(pub)
        db.close()

# CONSULTA POR FECHA (solo si aplica)
if mostrar_por_fecha:
    st.subheader("📅 Consulta por fecha")
    fecha_obj = st.date_input("Selecciona una fecha", value=date.today())
    if st.button("🔍 Buscar publicaciones del día"):
        fecha_str = fecha_obj.strftime("%Y%m%d")
        if st.session_state.ultima_fecha != fecha_str:
            with st.spinner("⏳ Consultando el BOE..."):
                result = subprocess.run([sys.executable, "-m", "scripts.fetch_boe", fecha_str])
                if result.returncode == 0:
                    url_api = f"http://127.0.0.1:8000/publicaciones/fecha/{fecha_obj.strftime('%Y-%m-%d')}"
                    try:
                        response = requests.get(url_api)
                        if response.status_code == 200:
                            st.session_state.publicaciones = response.json()
                            st.session_state.ultima_fecha = fecha_str
                            st.success("✅ Publicaciones cargadas correctamente.")
                        else:
                            st.error("❌ Error en la API.")
                    except Exception as e:
                        st.error(f"⚠️ Fallo de conexión: {e}")
        else:
            st.info("Ya tienes esta fecha cargada ✅")

# CONSULTA A LEGISLACIÓN CONSOLIDADA (con UI refinada)
if mostrar_legislacion:
    st.subheader("🔹 Explora la Legislación Consolidada")

    st.markdown("### 🧠 ¿Sobre qué tema necesitas información?")
    cols_consulta = st.columns([3, 1])
    consulta = cols_consulta[0].text_input("Tema principal", placeholder="Ej: ayudas autónomos, becas, seguridad social...")

    texto_final = ""
    sugerencias = []

    if consulta:
        try:
            r = requests.get("http://localhost:8000/api/suggest", params={"q": consulta})
            if r.status_code == 200 and "sugerencias" in r.json():
                sugerencias = r.json()["sugerencias"]
                if sugerencias:
                    st.markdown("#### 🔍 Sugerencias relacionadas:")
                    for s in sugerencias:
                        st.markdown(
                            f"<span style='background-color:#ecf0f1;padding:6px 12px;border-radius:20px;margin:4px;display:inline-block;font-size:0.9rem;'>✅ {s['title']}</span>",
                            unsafe_allow_html=True
                        )
                        if st.button(f"Usar: {s['title']}"):
                            st.session_state.categoria_sugerida = s["title"]
        except Exception as e:
            st.warning(f"⚠️ Error al obtener sugerencias: {e}")

    texto_final = st.session_state.get("categoria_sugerida", consulta)

    # Visual friendly summary box
    if texto_final:
        st.markdown(f"""
        <div style="background-color:#dff9fb; border-left:5px solid #1abc9c; padding:1rem; border-radius:10px; margin:1rem 0;">
            <b>🧾 Búsqueda generada:</b><br>
            Tema: <code>{texto_final}</code>
        </div>
        """, unsafe_allow_html=True)

    comunidad_seleccionada = st.selectbox("🌍 Comunidad Autónoma", ["Toda España", "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria", "Castilla-La Mancha", "Castilla y León", "Cataluña", "Ceuta", "Comunidad Valenciana", "Extremadura", "Galicia", "La Rioja", "Madrid", "Melilla", "Murcia", "Navarra", "País Vasco"])
    extra = st.text_input("🧩 Palabra clave adicional (opcional)")

    cols_fecha = st.columns(2)
    desde = cols_fecha[0].date_input("📅 Desde", value=None, min_value=date(1980, 1, 1), max_value=date.today())
    hasta = cols_fecha[1].date_input("📅 Hasta", value=None, min_value=date(1980, 1, 1), max_value=date.today())

    if st.button("🔍 Buscar legislación"):
        import json
        params = {}
        texto_base = texto_final

        if comunidad_seleccionada != "Toda España":
            texto_base += f' AND "{comunidad_seleccionada}"'
        if extra:
            texto_base += f" AND {extra}"
        params["texto"] = texto_base

        if desde:
            params["from"] = desde.strftime("%Y%m%d")
        if hasta:
            params["to"] = hasta.strftime("%Y%m%d")
        params["limit"] = 30

        with st.spinner("🔍 Consultando la API del BOE..."):
            try:
                response = requests.get("http://localhost:8000/legislacion/legislacion/listado", params=params)
                if response.status_code == 200:
                    resultados = response.json()
                    if resultados:
                        st.success(f"✅ {len(resultados)} normas encontradas")
                        for r in resultados:
                            detalle = requests.get(f"http://localhost:8000/legislacion/legislacion/detalle/{r['id']}")
                            if detalle.status_code == 200:
                                resumen = detalle.json()
                                mostrar_tarjeta_legislacion(resumen)
                            else:
                                mostrar_tarjeta_legislacion(r)
                    else:
                        st.info("No se encontraron normas con esos filtros.")
                else:
                    st.error("Error al consultar el backend.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")


# DASHBOARD
if st.session_state.publicaciones:
    publicaciones = st.session_state.publicaciones
    st.subheader("📰 Publicaciones")
    for pub in publicaciones:
        mostrar_tarjeta(pub)

st.markdown(f"""
<hr>
<div style='text-align:center; font-size:0.95rem; color:#7f8c8d; padding: 2rem 0; animation: fadeIn 1s ease forwards;'>
    <p>Hecho con 💙 en Galicia · <b>AlertaBOE</b> · {datetime.now().year}</p>
    <p style="font-size:1.1rem; margin-top:1rem;">✨ Que hoy encuentres justo la publicación que estabas esperando ✨</p>
</div>
""", unsafe_allow_html=True)

