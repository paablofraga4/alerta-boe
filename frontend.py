# ⚙️ INICIO DE LA APP
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
from sqlalchemy import func
import matplotlib.pyplot as plt
from io import BytesIO


from app.db.session import SessionLocal
from app.db.models import Publication, Region, Scope
from app.services.semantic_search import buscar_similares
from app.services.intent_parser import detectar_region, detectar_scope, detectar_extra_tag
from app.services.classifier import clasificar_categoria_por_regex
from app.services.utils_publicaciones import extraer_categorias_unicas

# CONFIGURACIÓN GENERAL
st.set_page_config(
    page_title="📘 AlertaBOE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🌙 TOGGLE DE MODO OSCURO GLOBAL (ALMACENADO)
if "modo_oscuro" not in st.session_state:
    st.session_state.modo_oscuro = False

modo_oscuro = st.checkbox("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
st.session_state.modo_oscuro = modo_oscuro

# INSERTAR PLACEHOLDER PARA ANIMACIÓN DE CARGA
st.markdown("""
<div id="loader-placeholder"></div>
""", unsafe_allow_html=True)

# 💅 ESTILOS + FUNCIONALIDAD JAVASCRIPT
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: 'Segoe UI', sans-serif;
    scroll-behavior: smooth;
    background-color: {'#121212' if modo_oscuro else '#ffffff'};
    color: {'#ecf0f1' if modo_oscuro else '#2c3e50'};
}}

h1.big-title {{
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(90deg, #1abc9c, #3498db);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}}
.subtitle {{
    font-size: 1.3rem;
    color: {'#bdc3c7' if modo_oscuro else '#7f8c8d'};
    margin-bottom: 2rem;
}}

@keyframes fadeIn {{
    from {{opacity: 0; transform: translateY(20px);}}
    to {{opacity: 1; transform: translateY(0);}}
}}

@keyframes highlight {{
    0% {{ background-color: #dff9fb; }}
    100% {{ background-color: transparent; }}
}}

@keyframes float {{
  0% {{ transform: translateY(0px); }}
  50% {{ transform: translateY(-6px); }}
  100% {{ transform: translateY(0px); }}
}}

.tarjeta {{
    animation: fadeIn 0.6s ease forwards, highlight 2s ease;
    opacity: 0;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.5rem;
    border-radius: 18px;
    background: {'#2c3e50' if modo_oscuro else 'linear-gradient(135deg, #ffffff, #f8f9fa)'};
    border-left: 5px solid #1abc9c80;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.tarjeta:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}}
.tarjeta h4 {{
    color: {'#ecf0f1' if modo_oscuro else '#2c3e50'};
    margin-bottom: 0.5rem;
}}
div.stButton > button {{
    background: linear-gradient(to right, #1abc9c, #16a085);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: background 0.3s ease, transform 0.2s ease;
}}
div.stButton > button:hover {{
    background: linear-gradient(to right, #16a085, #1abc9c);
    transform: scale(1.03);
}}
input, select, textarea {{
    transition: box-shadow 0.3s ease, border 0.3s ease;
}}
input:focus, select:focus, textarea:focus {{
    border: 1.5px solid #1abc9c !important;
    box-shadow: 0 0 6px rgba(26, 188, 156, 0.3) !important;
}}
div.row-widget.stRadio > div {{
    gap: 1rem;
}}
a {{
    text-decoration: none;
    color: #2980b9;
}}
a:hover {{
    color: #1abc9c;
    text-decoration: underline;
}}
hr {{
    border-top: 2px solid #ecf0f1;
    margin: 2rem 0;
}}

.fab {{
    position: fixed;
    bottom: 25px;
    right: 25px;
    background: #1abc9c;
    color: white;
    border-radius: 50%;
    padding: 16px;
    font-size: 1.6rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    cursor: pointer;
    transition: all 0.3s ease;
    z-index: 9999;
}}
.fab:hover {{
    transform: scale(1.1);
}}
</style>
<script>
document.addEventListener("DOMContentLoaded", function() {{
    const fab = document.querySelector('.fab');
    if (fab) {{
        fab.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }}
}});
</script>
<div class="fab" title="Volver arriba">⬆️</div>
""", unsafe_allow_html=True)

# ✨ EFECTO DE INTRODUCCIÓN TIPO "ESCRIBIENDO"
st.markdown("""
<h1 style='text-align: center; font-size: 2rem;'>
  <span id="typewriter"></span>
</h1>
<script>
let txt = "Bienvenido a AlertaBOE, tu radar inteligente del BOE 🛰️";
let i = 0;
function typeWriter() {{
  if (i < txt.length) {{
    document.getElementById("typewriter").innerHTML += txt.charAt(i);
    i++;
    setTimeout(typeWriter, 40);
  }}
}}
typeWriter();
</script>
""", unsafe_allow_html=True)

# 💡 FUNCIÓN PARA MOSTRAR LOADER FAKE (SKELETON)
def mostrar_skeletons(cantidad=5):
    for _ in range(cantidad):
        st.markdown('<div class="skeleton-card"></div>', unsafe_allow_html=True)

# 💡 FUNCIÓN PARA MOSTRAR ESTADO VACÍO
empty_svg = "https://lottie.host/9b44bb6e-6016-41ab-8058-8426b772d1ee/mr7PKbQYdf.json"
def mostrar_estado_vacio():
    st.markdown("""
    <div style='text-align:center; margin:2rem 0;'>
        <lottie-player src='""" + empty_svg + """' background='transparent' speed='1' style='width: 300px; height: 300px; margin:auto;' loop autoplay></lottie-player>
        <h4 style='color: #7f8c8d;'>Ups... No encontramos publicaciones con esos criterios 😕</h4>
    </div>
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    """, unsafe_allow_html=True)

# 💡 FUNCIÓN PARA MOSTRAR DASHBOARD CATEGORÍAS
def mostrar_dashboard_categorias(publicaciones):
    categorias = []
    for pub in publicaciones:
        if isinstance(pub.get("category"), list):
            categorias.extend(pub.get("category"))
        elif pub.get("category"):
            categorias.append(pub.get("category"))
    if not categorias:
        return ""

    from collections import Counter
    import matplotlib.pyplot as plt
    import base64

    counter = Counter(categorias)
    fig, ax = plt.subplots(figsize=(5, min(10, len(counter) * 0.45)))
    ax.barh(list(counter.keys()), list(counter.values()), color="#1abc9c")
    ax.set_title("Categorías encontradas", fontsize=12)
    ax.tick_params(axis='y', labelsize=9)
    ax.tick_params(axis='x', labelsize=8)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()

    html_dashboard = f"""
    <div style="width: 100%; background-color: #f9f9f9; border: 1px solid #ddd; padding: 18px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h4 style="margin-top:0;font-size: 16px; color: #2c3e50; text-align:center;">📊 Categorías detectadas</h4>
        <img src="data:image/png;base64,{img_base64}" style="width:100%; border-radius: 10px;"/>
    </div>
    """
    return html_dashboard




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



def formato_categoria(categoria):
    if isinstance(categoria, list):
        return ", ".join(str(c) for c in categoria)
    elif isinstance(categoria, str):
        return categoria
    return "N/D"



def serializar_publicacion(pub: Publication) -> dict:
    return {
        "id": pub.id,
        "date": str(pub.date),
        "title": pub.title,
        "body": pub.body,
        "category": pub.category,
        "extra_tag": pub.extra_tag,
        "scope": pub.scope.name if pub.scope else None,
        "departamento": pub.departamento,
        "seccion": pub.seccion,
        "epigrafe": pub.epigrafe,
        "url_html": pub.url_html,
        "url_pdf": pub.url_pdf,
        "pages": pub.pages,
        "regions": [r.name for r in pub.regions],
    }


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
    def formato_categoria(categoria):
        if isinstance(categoria, list):
            return ", ".join([c for c in categoria if c and c.strip()])
        elif categoria:
            return str(categoria)
        else:
            return "N/D"

    title = html.escape(pub.get("title", "[Sin título]"))
    depto = html.escape(pub.get("departamento") or "N/D")
    seccion = html.escape(pub.get("seccion") or "N/D")
    epigrafe = html.escape(pub.get("epigrafe") or "")
    extra_tag = html.escape(pub.get("extra_tag", "")) if pub.get("extra_tag") else "Sin Etiqueta Extra"
    categoria_str = html.escape(formato_categoria(pub.get("category")))

    # 🧠 USAMOS RESUMEN REAL si existe
    resumen_real = pub.get("resumen", "")
    resumen = html.escape(resumen_real.strip()) if resumen_real else "Sin resumen disponible"

    html_tarjeta = f"""
    <div class='tarjeta'>
        <h4>📄 {title}</h4>
        <p style='margin: 0.3rem 0;'>
            🗓️ <b>Fecha:</b> {pub.get("date", "N/D")} &nbsp;&nbsp;
            🏛️ <b>Dpto:</b> {depto}
        </p>
        <p style='margin: 0.3rem 0;'>
            🏷️ <b>Categoría:</b> {categoria_str}
        </p>
    """

    if extra_tag:
        html_tarjeta += f"<p style='margin: 0.3rem 0;'>🔖 <b>Etiqueta:</b> {extra_tag}</p>"

    seccion_texto = seccion + (f" / {epigrafe}" if epigrafe and epigrafe != "N/D" else "")
    html_tarjeta += f"""
        <p style='margin: 0.3rem 0;'>
            📂 <b>Sección:</b> {seccion_texto}
        </p>
        <p style='margin-top: 1rem; color:#333;'>
            📝 <b>Resumen:</b><br>{resumen}
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

    st.markdown(f"<div style='margin-top: 5rem;'>{html_tarjeta}</div>", unsafe_allow_html=True)



# --- MODO CONSULTOR INTELIGENTE CON EFECTOS VISUALES ---
if mostrar_consultor:
    st.markdown("""
    <div style="max-width:720px;margin:2rem auto 1.5rem auto;padding:1.5rem 2rem;background:radial-gradient(circle at top left, #ecf9f8, #ffffff);border-radius:18px;box-shadow:0 6px 18px rgba(0,0,0,0.06);text-align:center;position:relative;">
        <div style="position:absolute;top:-30px;left:calc(50% - 30px);">
            <div style="background:#1abc9c;border-radius:50%;width:60px;height:60px;display:flex;align-items:center;justify-content:center;font-size:30px;color:white;box-shadow:0 4px 10px rgba(0,0,0,0.2);">
                🤖
            </div>
        </div>
        <h2 style="margin-top:1.2rem;font-size:1.5rem;color:#2c3e50;">Consultor Inteligente del BOE</h2>
        <p style="color:#7f8c8d;margin-top:0.2rem;margin-bottom:1.5rem;">Describe lo que necesitas y encontraremos las publicaciones más relevantes para ti.</p>
    </div>
    """, unsafe_allow_html=True)

    consulta = st.text_input("Ej: ayudas para autónomos en Galicia", label_visibility="collapsed")
    st.session_state.consulta_activa = consulta

    db = SessionLocal()

    categorias_disponibles = extraer_categorias_unicas(db)
    categorias_filtradas = ["Todas"] + [c for c in categorias_disponibles if c in CATEGORIAS_VALIDAS]
    categoria_seleccionada = st.selectbox("🎯 Filtrar por categoría", categorias_filtradas)

    regiones_disponibles = [r.name for r in db.query(Region).all()]
    scopes_disponibles = [s.name for s in db.query(Scope).all()]

    categoria_clasificada = clasificar_categoria_por_regex(consulta)
    region_detectada = detectar_region(consulta, regiones_disponibles)
    scope_detectado = detectar_scope(consulta, scopes_disponibles)
    extra_tag_detectado = detectar_extra_tag(consulta)

    st.markdown("📆 ¿Desde cuándo te interesan las publicaciones?")
    rango_tiempo = st.radio("🕒 Rango de fechas", ["Últimos 60 días", "Todo el histórico"])

    if consulta:
        st.info(f"""
        🔍 *Resumen de tu consulta:*

        • **Región:** {region_detectada or 'No detectada'}
        • **Alcance:** {scope_detectado or 'No detectado'}
        • **Etiqueta:** {extra_tag_detectado or 'No detectada'}
        • **Categoría:** {categoria_seleccionada if categoria_seleccionada != 'Todas' else categoria_clasificada or 'No detectada'}
        • **Rango temporal:** {rango_tiempo}
        """)

    buscar = st.button("🔍 Buscar publicaciones", key="buscar_consultor", use_container_width=True)

    if buscar:
        mostrar_skeletons(6)

        query = db.query(Publication)

        if rango_tiempo == "Últimos 60 días":
            desde = datetime.today().date() - timedelta(days=60)
            query = query.filter(Publication.date >= desde)

        if categoria_seleccionada != "Todas":
            query = query.filter(Publication.category.any(categoria_seleccionada))
        elif categoria_clasificada:
            query = query.filter(Publication.category.any(categoria_clasificada))

        if scope_detectado:
            query = query.join(Scope).filter(Scope.name.ilike(f"%{scope_detectado}%"))
        if extra_tag_detectado:
            query = query.filter(Publication.extra_tag.ilike(f"%{extra_tag_detectado}%"))

        publicaciones = query.all()

        if region_detectada:
            publicaciones = [p for p in publicaciones if any(r.name.lower() == region_detectada.lower() for r in p.regions)]

        similares = buscar_similares(consulta, [p.__dict__ for p in publicaciones], top_k=len(publicaciones))
        publicaciones_ordenadas = sorted(similares, key=lambda x: x["date"], reverse=True)

        if not publicaciones_ordenadas:
            mostrar_estado_vacio()
            st.stop()

        st.session_state.resultados_consultor = publicaciones_ordenadas
        st.session_state.pagina_consultor = 0

    # Mostrar resultados si existen
    if "resultados_consultor" in st.session_state and st.session_state.resultados_consultor:
        publicaciones_ordenadas = st.session_state.resultados_consultor
        pagina = st.session_state.get("pagina_consultor", 0)
        publicaciones_por_pagina = 10
        total_paginas = (len(publicaciones_ordenadas) - 1) // publicaciones_por_pagina + 1
        inicio = pagina * publicaciones_por_pagina
        fin = inicio + publicaciones_por_pagina

        # 📌 Layout alineado: botón + resultados + dashboard
        with st.container():
            col_izq, col_der = st.columns([3, 1.4])

            with col_izq:
                st.markdown(f"""
                    <div style="margin-top: 0.5rem;">
                        <h3 style="font-size: 1.6rem; color: #1abc9c; margin-bottom: 0.4rem;">
                            📄 Resultados para: <em style="color: #2c3e50;">{consulta}</em>
                        </h3>
                    </div>
                """, unsafe_allow_html=True)

            with col_der:
                dashboard_html = mostrar_dashboard_categorias(publicaciones_ordenadas)
                if dashboard_html:
                    st.markdown(f"<div style='margin-top: 1.5rem;'>{dashboard_html}</div>", unsafe_allow_html=True)

        # ✅ Tarjetas bien alineadas y full width
        for pub in publicaciones_ordenadas[inicio:fin]:
            st.markdown("""<div style="width: 100%;">""", unsafe_allow_html=True)
            mostrar_tarjeta(pub)
            st.markdown("</div>", unsafe_allow_html=True)

        # Navegación
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if pagina > 0:
                if st.button("◀️ Anterior", key="prev_pag_consultor"):
                    st.session_state.pagina_consultor -= 1
                    st.rerun()
        with col3:
            if pagina < total_paginas - 1:
                if st.button("Siguiente ▶️", key="next_pag_consultor"):
                    st.session_state.pagina_consultor += 1
                    st.rerun()

        st.markdown(f"<div style='text-align:center; margin-top:1rem;'>Página {pagina + 1} de {total_paginas}</div>", unsafe_allow_html=True)

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

