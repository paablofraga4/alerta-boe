import streamlit as st
import subprocess
import requests
import sys
from datetime import date, datetime, timedelta
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import io
import base64
from bs4 import BeautifulSoup
import PyPDF2
import html

# Importaciones desde tu backend
try:
    from app.db.session import SessionLocal
    from app.db.models import Publication, Region, Scope
    from app.services.semantic_search import buscar_similares_por_embedding
    from app.services.intent_parser import detectar_region, detectar_scope, detectar_extra_tag
    from app.services.classifier import clasificar_categoria_por_regex
    from app.services.utils_publicaciones import extraer_categorias_unicas
except ImportError:
    st.error("⚠️ No se pudieron importar los módulos del backend. Asegúrate de que el entorno está configurado correctamente.")

# Configuración de la página
st.set_page_config(
    page_title="📘 AlertaBOE",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicialización de estado
if "modo_oscuro" not in st.session_state:
    st.session_state.modo_oscuro = False
if "publicaciones" not in st.session_state:
    st.session_state.publicaciones = []
if "ultima_fecha" not in st.session_state:
    st.session_state.ultima_fecha = None
if "modo_index" not in st.session_state:
    st.session_state.modo_index = 1  # Por defecto, mostrar el consultor inteligente
if "detalle_abierto" not in st.session_state:
    st.session_state.detalle_abierto = None

# Toggle de modo oscuro
modo_oscuro = st.checkbox("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
if modo_oscuro != st.session_state.modo_oscuro:
    st.session_state.modo_oscuro = modo_oscuro
    st.rerun()

# Estilos CSS mejorados con soporte para modo oscuro
def cargar_css():
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Estilos base */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        scroll-behavior: smooth;
        background-color: {st.session_state.modo_oscuro and '#121212' or '#ffffff'};
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#2c3e50'};
    }}
    
    /* Título principal */
    h1.big-title {{
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #1abc9c, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
    }}
    
    /* Subtítulo */
    .subtitle {{
        font-size: 1.3rem;
        color: {st.session_state.modo_oscuro and '#bdc3c7' or '#7f8c8d'};
        margin-bottom: 2rem;
        text-align: center;
    }}
    
    /* Animaciones */
    @keyframes fadeIn {{
        from {{opacity: 0; transform: translateY(20px);}}
        to {{opacity: 1; transform: translateY(0);}}
    }}
    
    @keyframes highlight {{
        0% {{ background-color: {st.session_state.modo_oscuro and '#2c3e50' or '#dff9fb'}; }}
        100% {{ background-color: {st.session_state.modo_oscuro and '#1e1e1e' or 'transparent'}; }}
    }}
    
    @keyframes float {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-6px); }}
        100% {{ transform: translateY(0px); }}
    }}
    
    /* Tarjetas de publicación */
    .tarjeta {{
        animation: fadeIn 0.6s ease forwards, highlight 2s ease;
        opacity: 0;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.5rem;
        border-radius: 18px;
        background: {st.session_state.modo_oscuro and '#1e1e1e' or 'linear-gradient(135deg, #ffffff, #f8f9fa)'};
        border-left: 5px solid #1abc9c80;
        box-shadow: 0 4px 12px rgba(0,0,0,{st.session_state.modo_oscuro and '0.2' or '0.06'});
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .tarjeta:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,{st.session_state.modo_oscuro and '0.3' or '0.08'});
    }}
    
    .tarjeta h4 {{
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#2c3e50'};
        margin-bottom: 0.5rem;
    }}
    
    /* Botones */
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
    
    /* Inputs y campos de formulario */
    input, select, textarea {{
        background-color: {st.session_state.modo_oscuro and '#2c3e50' or '#ffffff'} !important;
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#2c3e50'} !important;
        border: 1px solid {st.session_state.modo_oscuro and '#34495e' or '#e0e0e0'} !important;
        transition: box-shadow 0.3s ease, border 0.3s ease;
    }}
    
    input:focus, select:focus, textarea:focus {{
        border: 1.5px solid #1abc9c !important;
        box-shadow: 0 0 6px rgba(26, 188, 156, 0.3) !important;
    }}
    
    /* Navegación */
    .nav-item {{
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        background-color: {st.session_state.modo_oscuro and '#2c3e50' or '#f8f9fa'};
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        font-weight: 500;
    }}
    
    .nav-item:hover {{
        background-color: {st.session_state.modo_oscuro and '#34495e' or '#e9ecef'};
    }}
    
    .nav-item.active {{
        background-color: #1abc9c;
        color: white;
    }}
    
    /* Etiquetas */
    .tag {{
        display: inline-block;
        background-color: {st.session_state.modo_oscuro and '#2c3e50' or '#e0f7fa'};
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#0097a7'};
        border-radius: 16px;
        padding: 0.3rem 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    /* Mensajes de chat */
    .chat-message-user {{
        background-color: {st.session_state.modo_oscuro and '#2c3e50' or '#d9eaff'};
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#333'};
    }}
    
    .chat-message-assistant {{
        background-color: {st.session_state.modo_oscuro and '#34495e' or '#f1f1f1'};
        padding: 0.8rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        max-width: 80%;
        color: {st.session_state.modo_oscuro and '#ecf0f1' or '#333'};
    }}
    
    /* Modal */
    .modal-container {{
        background-color: {st.session_state.modo_oscuro and '#1e1e1e' or '#ffffff'};
        padding: 2rem 3rem;
        border: 1px solid {st.session_state.modo_oscuro and '#2c3e50' or '#ddd'};
        border-radius: 16px;
        margin-top: 1rem;
        font-family: 'Inter', sans-serif;
    }}
    
    .modal-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    /* Skeleton loading */
    .skeleton-card {{
        height: 180px;
        background: linear-gradient(90deg, 
            {st.session_state.modo_oscuro and '#2c3e50' or '#f0f0f0'}, 
            {st.session_state.modo_oscuro and '#34495e' or '#e0e0e0'}, 
            {st.session_state.modo_oscuro and '#2c3e50' or '#f0f0f0'});
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 18px;
        margin-bottom: 1rem;
    }}
    
    @keyframes loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    /* Botón flotante para volver arriba */
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
        opacity: 0;
    }}
    
    .fab:hover {{
        transform: scale(1.1);
    }}
    
    /* Secciones especiales */
    .feature-section {{
        max-width: 720px;
        margin: 2rem auto 1.5rem auto;
        padding: 1.5rem 2rem;
        background: {st.session_state.modo_oscuro and 'linear-gradient(135deg, #1e1e1e, #2c3e50)' or 'radial-gradient(circle at top left, #ecf9f8, #ffffff)'};
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,{st.session_state.modo_oscuro and '0.2' or '0.06'});
        text-align: center;
        position: relative;
    }}
    
    /* Dashboard */
    .dashboard-card {{
        width: 100%;
        background-color: {st.session_state.modo_oscuro and '#1e1e1e' or '#f9f9f9'};
        border: 1px solid {st.session_state.modo_oscuro and '#2c3e50' or '#ddd'};
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,{st.session_state.modo_oscuro and '0.2' or '0.08'});
    }}
    </style>
    
    <script>
    // Funcionalidad para el botón de volver arriba
    document.addEventListener("DOMContentLoaded", function() {{
        const fab = document.querySelector('.fab');
        if (fab) {{
            fab.addEventListener('click', () => {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }});
            
            // Mostrar/ocultar según la posición del scroll
            window.addEventListener('scroll', () => {{
                if (window.scrollY > 300) {{
                    fab.style.opacity = '1';
                }} else {{
                    fab.style.opacity = '0';
                }}
            }});
        }}
    }});
    </script>
    """

# Inyectar CSS
st.markdown(cargar_css(), unsafe_allow_html=True)

# Botón flotante para volver arriba
st.markdown(
    """
    <div class="fab" title="Volver arriba">⬆️</div>
    """,
    unsafe_allow_html=True
)

# Cabecera
st.markdown(
    """
    <div style='text-align: center; padding: 1.2rem 0 0.5rem 0; position: relative;'>
        <div style="position: absolute; right: 25px; top: 10px; font-size: 2.2rem; animation: float 3s ease-in-out infinite;">
            📡
        </div>
        <h1 class='big-title'>📘 Alerta<span style='color:#1abc9c;'>BOE</span></h1>
        <p class='subtitle'>Tu radar inteligente para detectar lo importante en el BOE</p>
        <hr/>
    </div>
    """,
    unsafe_allow_html=True
)

# Efecto de introducción tipo "escribiendo"
st.markdown(
    """
    <h1 style='text-align: center; font-size: 2rem;'>
      <span id="typewriter"></span>
    </h1>
    <script>
    let txt = "Bienvenido a AlertaBOE, tu radar inteligente del BOE 🛰️";
    let i = 0;
    function typeWriter() {
      if (i < txt.length) {
        document.getElementById("typewriter").innerHTML += txt.charAt(i);
        i++;
        setTimeout(typeWriter, 40);
      }
    }
    typeWriter();
    </script>
    """,
    unsafe_allow_html=True
)

# Opciones de navegación
modo_opciones = [
    {"label": "🔍 Por fecha", "value": "fecha"},
    {"label": "🤖 Consultor inteligente", "value": "consultor"},
    {"label": "💬 Asistente personal", "value": "asistente"},
    {"label": "🔹 Legislación", "value": "legislacion"}
]

# Navegación mejorada con tabs
cols = st.columns(len(modo_opciones))
for i, opcion in enumerate(modo_opciones):
    with cols[i]:
        activo = st.session_state.modo_index == i
        st.markdown(
            f"""
            <div class="nav-item {'active' if activo else ''}" 
                 onclick="document.getElementById('btn_nav_{i}').click();">
                {opcion['label']}
            </div>
            <div style="display: none;">
            """,
            unsafe_allow_html=True
        )
        if st.button(f"Seleccionar {opcion['value']}", key=f"btn_nav_{i}"):
            st.session_state.modo_index = i
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Obtener el modo actual
modo = modo_opciones[st.session_state.modo_index]["value"]

# Constantes
CATEGORIAS_VALIDAS = [
    'Agroalimentario', 'Asuntos sociales', 'Convenio', 'Cultura', 'Economía',
    'Educación', 'Empleo público', 'Empresa y comercio', 'Infraestructura',
    'Justicia', 'Medio ambiente', 'Norma', 'Sanción', 'Sanidad',
    'Seguridad', 'Sentencia', 'Subvención', 'Tecnología'
]

# Funciones auxiliares
def formato_categoria(categoria):
    """Formatea una categoría para mostrarla"""
    if isinstance(categoria, list):
        return ", ".join(str(c) for c in categoria)
    elif isinstance(categoria, str):
        return categoria
    return "N/D"

def serializar_publicacion(pub):
    """Convierte un objeto Publication o un diccionario a un diccionario"""
    # Si ya es un diccionario, devuélvelo directamente
    if isinstance(pub, dict):
        return pub
    
    # Si es un objeto, extrae sus atributos
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

def extraer_texto_de_html(url):
    """Extrae el texto de una URL HTML"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        st.error(f"Error al obtener HTML: {e}")
    return ""

def extraer_texto_de_pdf(url):
    """Extrae el texto de una URL PDF"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with io.BytesIO(response.content) as f:
                reader = PyPDF2.PdfReader(f)
                texto = ""
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    texto += page_text
                return texto
    except Exception as e:
        st.error(f"Error al obtener PDF: {e}")
    return ""

def mostrar_dashboard_categorias(publicaciones):
    """Genera y muestra un dashboard de categorías"""
    categorias = []
    for pub in publicaciones:
        if isinstance(pub.get("category"), list):
            categorias.extend(pub.get("category"))
        elif pub.get("category"):
            categorias.append(pub.get("category"))
    
    if not categorias:
        return ""

    counter = Counter(categorias)
    fig, ax = plt.subplots(figsize=(5, min(10, len(counter) * 0.45)))
    
    # Configurar colores según el modo oscuro
    if st.session_state.modo_oscuro:
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        ax.spines['bottom'].set_color('#666666')
        ax.spines['top'].set_color('#666666') 
        ax.spines['right'].set_color('#666666')
        ax.spines['left'].set_color('#666666')
        ax.tick_params(axis='x', colors='#cccccc')
        ax.tick_params(axis='y', colors='#cccccc')
        ax.set_title("Categorías encontradas", fontsize=12, color='#cccccc')
    else:
        ax.set_title("Categorías encontradas", fontsize=12)
    
    ax.barh(list(counter.keys()), list(counter.values()), color="#1abc9c")
    ax.tick_params(axis='y', labelsize=9)
    ax.tick_params(axis='x', labelsize=8)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=st.session_state.modo_oscuro)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()

    return f"""
    <div class="dashboard-card">
        <h4 style="margin-top:0;font-size: 16px; text-align:center;">📊 Categorías detectadas</h4>
        <img src="data:image/png;base64,{img_base64}" style="width:100%; border-radius: 10px;"/>
    </div>
    """

def mostrar_estado_vacio():
    """Muestra un estado vacío cuando no hay resultados"""
    st.markdown(
        f"""
        <div style='text-align:center; margin:2rem 0;'>
            <div style="font-size:4rem; margin-bottom:1rem;">🔍</div>
            <h3 style="color:{st.session_state.modo_oscuro and '#bdc3c7' or '#7f8c8d'};">
                No encontramos publicaciones con esos criterios
            </h3>
            <p style="color:{st.session_state.modo_oscuro and '#95a5a6' or '#95a5a6'};">
                Intenta con otros filtros o términos de búsqueda
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def mostrar_skeletons(cantidad=5):
    """Muestra tarjetas de carga (skeleton)"""
    for _ in range(cantidad):
        st.markdown('<div class="skeleton-card"></div>', unsafe_allow_html=True)

def mostrar_tarjeta(pub):
    # Asegurar que pub es un diccionario
    if not isinstance(pub, dict):
        pub = serializar_publicacion(pub)
        
    """Muestra una tarjeta de publicación"""
    pub_id = pub.get("id")
    
    # Inicializar historial de chat si no existe
    if f"chat_historial_{pub_id}" not in st.session_state:
        st.session_state[f"chat_historial_{pub_id}"] = []
    
    # Extraer datos de la publicación
    resumen_tiktok = pub.get("resumen_tiktok") or "<p>🌀 No hay resumen breve aún.</p>"
    categoria = html.escape(formato_categoria(pub.get("category") or ""))
    dpto = html.escape(str(pub.get("departamento") or "N/D"))
    fecha = str(pub.get("date") or "N/D")
    title = html.escape(str(pub.get("title") or "[Sin título]"))
    extra_tag = html.escape(str(pub.get("extra_tag") or "Sin etiqueta extra"))
    url_html = str(pub.get("url_html") or "#")
    url_pdf = str(pub.get("url_pdf") or "")
    
    # Manejar anclas para navegación
    if "volver_a_pub" in st.session_state:
        anchor = st.session_state.pop("volver_a_pub")
        st.markdown(f"<script>window.location.hash = '#{anchor}'</script>", unsafe_allow_html=True)
    
    # Vista normal (tarjeta cerrada)
    if st.session_state.detalle_abierto != pub_id:
        st.markdown(f"<a id='pub_{pub_id}'></a>", unsafe_allow_html=True)
        
        # Crear etiquetas HTML para categorías
        categorias_html = ""
        if categoria:
            for cat in categoria.split(','):
                if cat.strip():
                    categorias_html += f'<span class="tag">{cat.strip()}</span>'

        print(resumen_tiktok)
        
        # Renderizar tarjeta
        st.markdown(
            f"""
            <div class="tarjeta">
                <h4 style="margin-bottom: 0.6rem;">📄 {title}</h4>
                <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.8rem;">
                    <div style="display:flex; align-items:center; gap:0.3rem;">
                        <span style="font-weight:500;">🗓️ Fecha:</span> {fecha}
                    </div>
                    <div style="display:flex; align-items:center; gap:0.3rem;">
                        <span style="font-weight:500;">🏛️ Dpto:</span> {dpto}
                    </div>
                </div>
                <div style="margin-bottom:0.8rem;">
                    <span style="font-weight:500;">🏷️ Categoría:</span>
                    <div style="margin-top:0.3rem;">
                        {categorias_html}
                    </div>
                </div>
                {f'<div style="margin-bottom:0.8rem;"><span style="font-weight:500;">🔖 Etiqueta:</span> {extra_tag}</div>' if extra_tag and extra_tag != "Sin etiqueta extra" else ''}
                <div style="margin-top:1rem; margin-bottom:1rem;">
                    <span style="font-weight:500;">📌 Resumen breve:</span>
                    <div style="margin-top:0.3rem;">
                        st.code(resumen_tiktok, language="html")  # 
                        {(html.unescape(resumen_tiktok))}
                    </div>
                </div>
                <div style="display:flex; gap:1rem;">
                    <a href="{url_html}" target="_blank" style="text-decoration:none; color:#2980b9;">🔗 Ver en BOE</a>
                    {f'<a href="{url_pdf}" target="_blank" style="text-decoration:none; color:#2980b9;">⬇️ PDF</a>' if url_pdf else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⭐ Guardar como favorito", key=f"btn_fav_{pub_id}"):
                try:
                    r = requests.post(
                        f"http://localhost:8000/publicaciones/favorito/{pub_id}",
                        params={"session_id": "test"},
                        timeout=10
                    )
                    if r.status_code == 200:
                        st.success("✅ Guardado como favorito")
                    else:
                        st.warning("⚠️ No se pudo guardar")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")
        
        with col2:
            if st.button("🧠 Ver detalle / Chatear", key=f"btn_detalle_{pub_id}"):
                st.session_state.detalle_abierto = pub_id
                st.rerun()
    
    # Vista de detalle (tarjeta abierta)
    else:
        # resumen_detallado = html.escape(str(pub.get("resumen_tiktok") or "🌀 No hay resumen detallado aún."))
        historial = st.session_state[f"chat_historial_{pub_id}"]
        
        # Ocultar elementos de la interfaz para el modo detalle
        st.markdown(
            """
            <style>
                header, footer, .stSidebar { display: none !important; }
                .block-container { padding-top: 0rem !important; }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        # Forzar scroll hacia la tarjeta
        st.markdown(
            f"<script>setTimeout(function(){{document.getElementById('pub_{pub_id}').scrollIntoView({{behavior:'smooth', block:'start'}});}}, 100);</script>",
            unsafe_allow_html=True
        )
        
        # Contenedor de detalle
        with st.container():
            st.markdown(f"<a id='pub_{pub_id}'></a>", unsafe_allow_html=True)
            
            # Modal de detalle
            st.markdown(
                f"""
                <div class="modal-container">
                    <div class="modal-header">
                        <span style="font-weight: 600; font-size: 1rem; color: {st.session_state.modo_oscuro and '#bdc3c7' or '#999'};">
                            Detalle de publicación
                        </span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 1.5rem; line-height: 1.5; color: {st.session_state.modo_oscuro and '#ecf0f1' or '#222'};">
                        📄 {title}
                    </div>
                    <p style="margin-top: 1rem; font-size: 1rem; line-height: 1.6; color: {st.session_state.modo_oscuro and '#ecf0f1' or '#333'};">
                            st.code(resumen_tiktok, language="html")
                        🧾 <b>Resumen detallado:</b><br>{(html.unescape(resumen_tiktok)) or "Sin resumen"}
                    </p>
                    <p style="margin-top: 1rem; font-size: 0.95rem;">
                        <a href="{url_html}" target="_blank" style="color:{st.session_state.modo_oscuro and '#3498db' or '#2980b9'};">🔗 Ver en BOE</a>
                        {" · " if url_pdf else ""}
                        <a href="{url_pdf}" target="_blank" style="color:{st.session_state.modo_oscuro and '#3498db' or '#2980b9'};">⬇️ PDF</a>
                    </p>
                    <hr style="margin: 2rem 0; border-color: {st.session_state.modo_oscuro and '#34495e' or '#eee'};" />
                    <h3>💬 Chat sobre esta publicación</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Mostrar historial de chat
            for msg in historial[-10:]:
                if msg["role"] == "user":
                    st.markdown(
                        f"""
                        <div class="chat-message-user">
                            <b>Tú:</b> {msg["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="chat-message-assistant">
                            <b>Asistente:</b> {msg["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Formulario de chat
            with st.form(key=f"form_chat_{pub_id}", clear_on_submit=True):
                st.markdown("<label style='display:none'>Pregunta</label>", unsafe_allow_html=True)
                pregunta = st.text_input(
                    "Pregunta",
                    key=f"chat_input_{pub_id}_text",
                    placeholder="✍️ Escribe tu pregunta sobre esta publicación..."
                )
                submitted = st.form_submit_button("Enviar")
                
                if submitted and pregunta.strip():
                    with st.spinner("Pensando..."):
                        try:
                            # Obtener el texto del documento
                            if url_html != "#" and url_html.strip():
                                texto_contexto = extraer_texto_de_html(url_html)
                            elif url_pdf.strip():
                                texto_contexto = extraer_texto_de_pdf(url_pdf)
                            else:
                                texto_contexto = ""
                            
                            # Enviar al API
                            r = requests.post(
                                "http://localhost:8000/api/chat-documento",
                                json={
                                    "texto": texto_contexto,
                                    "historial": historial + [{"role": "user", "content": pregunta}]
                                },
                                timeout=60
                            )
                            
                            if r.status_code == 200:
                                data = r.json()
                                respuesta = data.get("respuesta", "(sin respuesta)")
                                historial.append({"role": "user", "content": pregunta})
                                historial.append({"role": "assistant", "content": respuesta})
                                st.rerun()
                            else:
                                st.warning("⚠️ El asistente no respondió.")
                        except Exception as e:
                            st.warning(f"⚠️ Error: {e}")
            
            # Botones adicionales
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💡 Probar con ejemplo", key=f"dummy_{pub_id}"):
                    historial.append({"role": "user", "content": "¿De qué trata esta publicación?"})
                    historial.append({"role": "assistant", "content": "Este documento trata sobre un convenio para informes médicos del INSS."})
                    st.rerun()
            
            with col2:
                if st.button("❌ Cerrar vista", key=f"cerrar_{pub_id}"):
                    st.session_state.detalle_abierto = None
                    st.session_state.volver_a_pub = f"pub_{pub_id}"
                    st.rerun()

# MODO CONSULTOR INTELIGENTE
if modo == "consultor":
    st.markdown(
        """
        <div class="feature-section">
            <div style="position:absolute;top:-30px;left:calc(50% - 30px);">
                <div style="background:#1abc9c;border-radius:50%;width:60px;height:60px;display:flex;align-items:center;justify-content:center;font-size:30px;color:white;box-shadow:0 4px 10px rgba(0,0,0,0.2);">
                    🤖
                </div>
            </div>
            <h2 style="margin-top:1.2rem;font-size:1.5rem;">Consultor Inteligente del BOE</h2>
            <p style="margin-top:0.2rem;margin-bottom:1.5rem;">Describe lo que necesitas y encontraremos las publicaciones más relevantes para ti.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    consulta = st.text_input("Tu consulta", placeholder="Ej: ayudas para autónomos en Galicia")
    st.session_state.consulta_activa = consulta
    
    try:
        db = SessionLocal()
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            categorias_disponibles = extraer_categorias_unicas(db)
            categorias_filtradas = ["Todas"] + [c for c in categorias_disponibles if c in CATEGORIAS_VALIDAS]
            categoria_seleccionada = st.selectbox("🎯 Filtrar por categoría", categorias_filtradas)
        
        with col2:
            st.markdown("📆 ¿Desde cuándo te interesan las publicaciones?")
            rango_tiempo = st.radio("Rango de fechas", ["Últimos 60 días", "Todo el histórico"], horizontal=True)
        
        # Detectar intenciones y entidades
        if consulta:
            regiones_disponibles = [r.name for r in db.query(Region).all()]
            scopes_disponibles = [s.name for s in db.query(Scope).all()]
            
            categoria_clasificada = clasificar_categoria_por_regex(consulta)
            region_detectada = detectar_region(consulta, regiones_disponibles)
            scope_detectado = detectar_scope(consulta, scopes_disponibles)
            extra_tag_detectado = detectar_extra_tag(consulta)
            
            # Mostrar resumen de la consulta
            st.info(
                f"""
                🔍 **Resumen de tu consulta:**
                
                • **Región:** {region_detectada or 'No detectada'}
                • **Alcance:** {scope_detectado or 'No detectado'}
                • **Etiqueta:** {extra_tag_detectado or 'No detectada'}
                • **Categoría:** {categoria_seleccionada if categoria_seleccionada != 'Todas' else categoria_clasificada or 'No detectada'}
                • **Rango temporal:** {rango_tiempo}
                """
            )
        
        # Botón de búsqueda
        buscar = st.button("🔍 Buscar publicaciones", key="buscar_consultor", use_container_width=True)
        
        if buscar:
            with st.spinner("Buscando publicaciones relevantes..."):
                skeleton_placeholder = st.empty()
                with skeleton_placeholder.container():
                    mostrar_skeletons(5)
                
                # Construir la consulta
                query = db.query(Publication)
                
                # Filtrar por fecha
                if rango_tiempo == "Últimos 60 días":
                    desde = datetime.today().date() - timedelta(days=60)
                    query = query.filter(Publication.date >= desde)
                
                # Filtrar por categoría
                if categoria_seleccionada != "Todas":
                    query = query.filter(Publication.category.any(categoria_seleccionada))
                elif categoria_clasificada:
                    query = query.filter(Publication.category.any(categoria_clasificada))
                
                # Filtrar por scope y etiqueta
                if scope_detectado:
                    query = query.join(Scope).filter(Scope.name.ilike(f"%{scope_detectado}%"))
                if extra_tag_detectado:
                    query = query.filter(Publication.extra_tag.ilike(f"%{extra_tag_detectado}%"))
                
                # Ejecutar consulta
                publicaciones = query.all()
                
                # Filtrar por región
                if region_detectada:
                    publicaciones = [p for p in publicaciones if any(r.name.lower() == region_detectada.lower() for r in p.regions)]
                
                # Buscar similares por embedding
                publicaciones_serializadas = [serializar_publicacion(p) for p in publicaciones]
                similares = buscar_similares_por_embedding(consulta, publicaciones_serializadas, top_k=len(publicaciones_serializadas), modo="consultor_inteligente")

                publicaciones_ordenadas = sorted(similares, key=lambda x: x["date"], reverse=True)
                
                # Guardar resultados en session state
                st.session_state.resultados_consultor = publicaciones_ordenadas
                st.session_state.pagina_consultor = 0
                
                # Mostrar mensaje si no hay resultados
                if not publicaciones_ordenadas:
                    mostrar_estado_vacio()
                skeleton_placeholder.empty()
        
        # Mostrar resultados si existen
        if "resultados_consultor" in st.session_state and st.session_state.resultados_consultor:
            publicaciones_ordenadas = st.session_state.resultados_consultor
            pagina = st.session_state.get("pagina_consultor", 0)
            publicaciones_por_pagina = 10
            total_paginas = (len(publicaciones_ordenadas) - 1) // publicaciones_por_pagina + 1
            inicio = pagina * publicaciones_por_pagina
            fin = inicio + publicaciones_por_pagina
            
            # Layout: resultados + dashboard
            col_izq, col_der = st.columns([3, 1.4])
            
            with col_izq:
                st.markdown(
                    f"""
                    <div style="margin-top: 0.5rem;">
                        <h3 style="font-size: 1.6rem; color: #1abc9c; margin-bottom: 0.4rem;">
                            📄 Resultados para: <em>{consulta}</em>
                        </h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Mostrar publicaciones de la página actual
                for pub in publicaciones_ordenadas[inicio:fin]:
                    mostrar_tarjeta(pub)
                
                # Navegación entre páginas
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if pagina > 0:
                        if st.button("◀️ Anterior", key="prev_pag_consultor"):
                            st.session_state.pagina_consultor -= 1
                            st.rerun()
                
                with col2:
                    st.markdown(
                        f"""
                        <div style="text-align:center; margin-top:1rem;">
                            Página {pagina + 1} de {total_paginas}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col3:
                    if pagina < total_paginas - 1:
                        if st.button("Siguiente ▶️", key="next_pag_consultor"):
                            st.session_state.pagina_consultor += 1
                            st.rerun()
            
            with col_der:
                dashboard_html = mostrar_dashboard_categorias(publicaciones_ordenadas)
                if dashboard_html:
                    st.markdown(f"<div style='margin-top: 1.5rem;'>{dashboard_html}</div>", unsafe_allow_html=True)
        
        db.close()
    except Exception as e:
        st.error(f"Se produjo un error: {e}")
        st.exception(e)  # Esto mostrará el traceback en la interfaz de Streamlit
        raise e          # Esto relanza la excepción y la verás en la consola/terminal


# MODO CONSULTA POR FECHA
elif modo == "fecha":
    st.subheader("📅 Consulta por fecha")
    
    fecha_obj = st.date_input("Selecciona una fecha", value=date.today())
    
    if st.button("🔍 Buscar publicaciones del día", use_container_width=True):
        fecha_str = fecha_obj.strftime("%Y%m%d")
        
        if st.session_state.ultima_fecha != fecha_str:
            with st.spinner("⏳ Consultando el BOE..."):
                try:
                    # Ejecutar script para obtener publicaciones
                    result = subprocess.run([sys.executable, "-m", "scripts.fetch_boe", fecha_str])
                    
                    if result.returncode == 0:
                        # Consultar API para obtener las publicaciones
                        url_api = f"http://127.0.0.1:8000/publicaciones/fecha/{fecha_obj.strftime('%Y-%m-%d')}"
                        response = requests.get(url_api)
                        
                        if response.status_code == 200:
                            st.session_state.publicaciones = response.json()
                            st.session_state.ultima_fecha = fecha_str
                            st.success("✅ Publicaciones cargadas correctamente.")
                        else:
                            st.error(f"❌ Error en la API: {response.status_code}")
                    else:
                        st.error("❌ Error al ejecutar el script de obtención de publicaciones.")
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")
        else:
            st.info("Ya tienes esta fecha cargada ✅")
    
    # Mostrar publicaciones
    if st.session_state.publicaciones:
        st.subheader(f"📰 Publicaciones del {fecha_obj.strftime('%d/%m/%Y')}")
        
        for pub in st.session_state.publicaciones:
            mostrar_tarjeta(pub)
    
# MODO ASISTENTE PERSONAL
elif modo == "asistente":
    st.session_state.detalle_abierto = None
    st.markdown(
        """
        <div class="feature-section">
            <div style="position:absolute;top:-30px;left:calc(50% - 30px);">
                <div style="background:#1abc9c;border-radius:50%;width:60px;height:60px;display:flex;align-items:center;justify-content:center;font-size:30px;color:white;box-shadow:0 4px 10px rgba(0,0,0,0.2);">
                    💬
                </div>
            </div>
            <h2 style="margin-top:1.2rem;font-size:1.5rem;">Asistente Personal del BOE</h2>
            <p style="margin-top:0.2rem;margin-bottom:1.5rem;">Describe qué te interesa o qué necesitas saber, y te mostraremos publicaciones relevantes con una explicación clara.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    consulta_asistente = st.text_area(
        "Tu consulta", 
        placeholder="Ej: Soy autónomo en Galicia y busco ayudas disponibles",
        height=100
    )
    
    if st.button("🔍 Consultar asistente", use_container_width=True):
        with st.spinner("🧠 Analizando tu mensaje y buscando coincidencias..."):
            skeleton_placeholder = st.empty()
            with skeleton_placeholder.container():
                mostrar_skeletons(3)
            
            try:
                r = requests.post(
                    "http://localhost:8000/api/asistente-personal",
                    json={"mensaje": consulta_asistente},
                    timeout=45
                )
                skeleton_placeholder.empty()
                
                if r.status_code == 200:
                    data = r.json()
                    explicacion = data.get("explicacion")
                    if explicacion != "⚠️ El sistema está sobrecargado. Por favor, inténtalo de nuevo en unos minutos.":
                        publicaciones = data.get("publicaciones", [])
                        
                        if explicacion:
                            st.markdown(
                                f"""
                                <div style="background-color:{st.session_state.modo_oscuro and '#2c3e50' or '#f1f8f6'};
                                    border-left:5px solid #1abc9c;
                                    padding:1.5rem;
                                    border-radius:12px;
                                    margin:1.5rem 0;">
                                    <h3 style="margin-top:0;">💡 Explicación del asistente</h3>
                                    <p style="margin-bottom:0;">{explicacion}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        if publicaciones:
                            st.subheader("📄 Publicaciones relacionadas")
                            for pub in publicaciones:
                                mostrar_tarjeta(pub)
                        else:
                            mostrar_estado_vacio()
                    else:
                        st.markdown(f"{explicacion}")
                else:
                    st.error(f"❌ Error en la API: {r.status_code}")
            except Exception as e:
                st.error(f"⚠️ Error de conexión: {e}")

# MODO LEGISLACIÓN
elif modo == "legislacion":
    st.markdown(
        """
        <div class="feature-section">
            <div style="position:absolute;top:-30px;left:calc(50% - 30px);">
                <div style="background:#1abc9c;border-radius:50%;width:60px;height:60px;display:flex;align-items:center;justify-content:center;font-size:30px;color:white;box-shadow:0 4px 10px rgba(0,0,0,0.2);">
                    🔹
                </div>
            </div>
            <h2 style="margin-top:1.2rem;font-size:1.5rem;">Explora la Legislación Consolidada</h2>
            <p style="margin-top:0.2rem;margin-bottom:1.5rem;">Encuentra normas legales históricas y actuales por comunidad autónoma, tema o palabras clave.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("### 🧠 ¿Sobre qué tema necesitas información?")
    
    consulta = st.text_input("Tema principal", placeholder="Ej: ayudas autónomos, becas, seguridad social...")
    
    texto_final = ""
    sugerencias = []
    
    # Obtener sugerencias
    if consulta:
        try:
            r = requests.get("http://localhost:8000/api/suggest", params={"q": consulta})
            if r.status_code == 200 and "sugerencias" in r.json():
                sugerencias = r.json()["sugerencias"]
                
                if sugerencias:
                    st.markdown("#### 🔍 Sugerencias relacionadas:")
                    
                    # Mostrar sugerencias como tags
                    tags_html = ""
                    for i, s in enumerate(sugerencias):
                        tags_html += f"""
                        <span style='background-color:{st.session_state.modo_oscuro and '#2c3e50' or '#ecf0f1'};
                              padding:6px 12px;
                              border-radius:20px;
                              margin:4px;
                              display:inline-block;
                              font-size:0.9rem;
                              cursor:pointer;'
                              onclick="document.getElementById('btn_sugerencia_{i}').click();">
                            ✅ {s['title']}
                        </span>
                        """
                    
                    st.markdown(f"<div style='margin-bottom:1rem;'>{tags_html}</div>", unsafe_allow_html=True)
                    
                    # Botones ocultos para las sugerencias
                    for i, s in enumerate(sugerencias):
                        if st.button(f"Usar: {s['title']}", key=f"btn_sugerencia_{i}", label_visibility="collapsed"):
                            st.session_state.categoria_sugerida = s["title"]
                            st.rerun()
        except Exception as e:
            st.warning(f"⚠️ Error al obtener sugerencias: {e}")
    
    # Usar sugerencia seleccionada o consulta original
    texto_final = st.session_state.get("categoria_sugerida", consulta)
    
    # Mostrar resumen de búsqueda
    if texto_final:
        st.markdown(
            f"""
            <div style="background-color:{st.session_state.modo_oscuro and '#2c3e50' or '#dff9fb'};
                  border-left:5px solid #1abc9c;
                  padding:1rem;
                  border-radius:10px;
                  margin:1rem 0;">
                <b>🧾 Búsqueda generada:</b><br>
                Tema: <code>{texto_final}</code>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Filtros adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        comunidad_seleccionada = st.selectbox(
            "🌍 Comunidad Autónoma",
            ["Toda España", "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", "Cantabria",
             "Castilla-La Mancha", "Castilla y León", "Cataluña", "Ceuta", "Comunidad Valenciana",
             "Extremadura", "Galicia", "La Rioja", "Madrid", "Melilla", "Murcia", "Navarra", "País Vasco"]
        )
    
    with col2:
        extra = st.text_input("🧩 Palabra clave adicional (opcional)")
    
    # Rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        desde = st.date_input("📅 Desde", value=date.today(), min_value=date(1980, 1, 1), max_value=date.today())
    with col2:
        hasta = st.date_input("📅 Hasta", value=date.today(), min_value=date(1980, 1, 1), max_value=date.today())
    
    # Botón de búsqueda
    if st.button("🔍 Buscar legislación", use_container_width=True):
        if not texto_final:
            st.warning("⚠️ Por favor, introduce un tema de búsqueda")
        else:
            with st.spinner("🔍 Consultando la API del BOE..."):
                # Crear el placeholder para los skeletons
                skeleton_placeholder = st.empty()
                with skeleton_placeholder.container():
                    mostrar_skeletons(3)
                
                try:
                    # Construir consulta
                    texto_base = texto_final
                    
                    if comunidad_seleccionada != "Toda España":
                        texto_base += f' AND "{comunidad_seleccionada}"'
                    if extra:
                        texto_base += f" AND {extra}"
                    
                    # Parámetros
                    params = {
                        "texto": texto_base,
                        "limit": 30
                    }
                    
                    if desde:
                        params["from"] = desde.strftime("%Y%m%d")
                    if hasta:
                        params["to"] = hasta.strftime("%Y%m%d")
                    
                    # Llamar a la API
                    response = requests.get(
                        "http://localhost:8000/legislacion/legislacion/listado",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        skeleton_placeholder.empty()
                        resultados = response.json()
                        
                        if resultados:
                            st.success(f"✅ {len(resultados)} normas encontradas")
                            
                            # Mostrar resultados
                            for r in resultados:
                                try:
                                    # Obtener detalles
                                    detalle = requests.get(f"http://localhost:8000/legislacion/legislacion/detalle/{r['id']}")
                                    
                                    if detalle.status_code == 200:
                                        resumen = detalle.json()
                                        
                                        # Mostrar tarjeta
                                        st.markdown(
                                            f"""
                                            <div class="tarjeta">
                                                <h4>{resumen.get('titulo', r.get('titulo', 'Sin título'))}</h4>
                                                <div style="margin-bottom:0.8rem;">
                                                    <span style="font-weight:500;">📅 Fecha:</span> {resumen.get('fecha_publicacion', 'N/D')}
                                                </div>
                                                <div style="margin-bottom:0.8rem;">
                                                    <span style="font-weight:500;">🏛️ Departamento:</span> {resumen.get('departamento', 'N/D')}
                                                </div>
                                                <div style="margin-bottom:0.8rem;">
                                                    <span style="font-weight:500;">📝 Rango:</span> {resumen.get('rango', 'N/D')}
                                                </div>
                                                {f'<div style="margin-bottom:1rem;"><span style="font-weight:500;">📌 Resumen:</span> {resumen.get("resumen_tiktok", "")}</div>' if resumen.get("resumen_tiktok") else ''}
                                                <a href="{resumen.get('url', '#')}" target="_blank" style="text-decoration:none; color:#2980b9;">🔗 Ver en BOE</a>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                    else:
                                        # Mostrar versión básica si no hay detalles
                                        st.markdown(
                                            f"""
                                            <div class="tarjeta">
                                                <h4>{r.get('titulo', 'Sin título')}</h4>
                                                <a href="{r.get('url', '#')}" target="_blank" style="text-decoration:none; color:#2980b9;">🔗 Ver en BOE</a>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                except Exception as e:
                                    st.warning(f"⚠️ Error al obtener detalles: {e}")
                        else:
                            mostrar_estado_vacio()
                    else:
                        st.error(f"❌ Error en la API: {response.status_code}")
                except Exception as e:
                    st.error(f"⚠️ Error de conexión: {e}")

# Pie de página
st.markdown(
    f"""
    <hr>
    <div style='text-align:center; font-size:0.95rem; color:{st.session_state.modo_oscuro and '#bdc3c7' or '#7f8c8d'}; padding: 2rem 0; animation: fadeIn 1s ease forwards;'>
        <p>Hecho con 💙 en Galicia · <b>AlertaBOE</b> · {datetime.now().year}</p>
        <p style="font-size:1.1rem; margin-top:1rem;">✨ Que hoy encuentres justo la publicación que estabas esperando ✨</p>
    </div>
    """,
    unsafe_allow_html=True
)
