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


# CONFIGURACIÓN GENERAL
st.set_page_config(
    page_title="📘 AlertaBOE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# INYECCIÓN DE ESTILOS Y ANIMACIONES
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

.tarjeta {
    animation: fadeIn 0.6s ease forwards;
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

/* BOTONES */
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

/* CAMPOS INPUT */
input, select, textarea {
    transition: box-shadow 0.3s ease, border 0.3s ease;
}
input:focus, select:focus, textarea:focus {
    border: 1.5px solid #1abc9c !important;
    box-shadow: 0 0 6px rgba(26, 188, 156, 0.3) !important;
}

/* RADIO BUTTONS */
div.row-widget.stRadio > div {
    gap: 1rem;
}

/* LINKS */
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
""", unsafe_allow_html=True)

# CABECERA
st.markdown("""
<div style='
    text-align: center;
    padding: 1.2rem 0 0.5rem 0;
    position: relative;
'>
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

# MODO DE USO
st.markdown("""
<div style='
    background-color: #f7fafa;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    margin-bottom: 1.5rem;
'>
""", unsafe_allow_html=True)

modo = st.radio("🧭 ¿Cómo quieres explorar el BOE hoy?", ["🔍 Explorar por fecha", "🤖 Consultor inteligente del BOE"], horizontal=True)

st.markdown("</div>", unsafe_allow_html=True)


# COMPONENTE DE TARJETA
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
if modo == "🤖 Consultor inteligente del BOE":
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
        categoria_clasificada = clasificar_categoria(consulta)
    except Exception:
        pass

    region_detectada = detectar_region(consulta, regiones_disponibles)
    scope_detectado = detectar_scope(consulta, scopes_disponibles)
    extra_tag_detectado = detectar_extra_tag(consulta)

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

# CONSULTA POR FECHA
else:
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

# DASHBOARD
if st.session_state.publicaciones:
    publicaciones = st.session_state.publicaciones
    st.subheader("📰 Publicaciones")
    for pub in publicaciones:
        mostrar_tarjeta(pub)

# 🎁 REGALITO VISUAL – Mensaje final animado
st.markdown(f"""
<hr>
<div style='text-align:center; font-size:0.95rem; color:#7f8c8d; padding: 2rem 0; animation: fadeIn 1s ease forwards;'>
    <p>Hecho con 💙 en Galicia · <b>AlertaBOE</b> · {datetime.now().year}</p>
    <p style="font-size:1.1rem; margin-top:1rem;">✨ Que hoy encuentres justo la publicación que estabas esperando ✨</p>
</div>
""", unsafe_allow_html=True)
