import streamlit as st
import subprocess
import requests
import sys
from datetime import date
from collections import Counter
import pandas as pd
import altair as alt
from app.services.semantic_search import buscar_similares  # Importar el buscador inteligente

# Config global
st.set_page_config(page_title="AlertaBOE", layout="wide")

# Estado global
if "publicaciones" not in st.session_state:
    st.session_state.publicaciones = []
if "ultima_fecha" not in st.session_state:
    st.session_state.ultima_fecha = None

# Hero Section
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem;'>📘 AlertaBOE</h1>
        <p style='font-size: 1.2rem; color: #6c6c6c;'>Tu radar inteligente para detectar lo importante en el BOE</p>
    </div>
""", unsafe_allow_html=True)

# Panel de Control
st.markdown("### 🎛️ Panel de control")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    fecha_obj = st.date_input("📅 Fecha a consultar", value=date.today())
with col2:
    ejecutar = st.button("🔍 Buscar")
with col3:
    reset = st.button("🔄 Reiniciar")

if reset:
    st.session_state.publicaciones = []
    st.session_state.ultima_fecha = None
    st.experimental_rerun()

if ejecutar:
    fecha = fecha_obj.strftime("%Y%m%d")
    if st.session_state.ultima_fecha != fecha:
        with st.spinner("📡 Consultando el BOE..."):
            result = subprocess.run([sys.executable, "-m", "scripts.fetch_boe", fecha])
            if result.returncode == 0:
                url_api = f"http://127.0.0.1:8000/publicaciones/fecha/{fecha_obj.strftime('%Y-%m-%d')}"
                try:
                    response = requests.get(url_api)
                    if response.status_code == 200:
                        st.session_state.publicaciones = response.json()
                        st.session_state.ultima_fecha = fecha
                        st.success("✅ Consulta completada.")
                    else:
                        st.error(f"❌ Error al consultar la API: {response.status_code}")
                except Exception as e:
                    st.error(f"⚠️ No se pudo conectar con la API: {e}")
            else:
                st.error("❌ Error al ejecutar el scraping.")
    else:
        st.info("Ya tienes cargadas las publicaciones de esa fecha ✅")

# Mostrar publicaciones
if st.session_state.publicaciones:
    publicaciones = st.session_state.publicaciones

    # Buscador semántico (🔥 nuevo)
    st.markdown("### 🔍 Búsqueda inteligente")
    query = st.text_input("🔎 Buscar por palabra clave o frase (ej: ayudas para autónomos)")
    if query:
        publicaciones = buscar_similares(query, publicaciones)
        st.success(f"🔎 Mostrando resultados más cercanos a: \"{query}\"")

    # Filtro por categoría
    st.markdown("### 🔎 Filtrar por categoría")
    categorias_raw = list(set([p.get("category", "otro") for p in publicaciones]))
    categorias_disponibles = sorted(categorias_raw, key=str.lower)
    categorias_formateadas = [cat.capitalize() for cat in categorias_disponibles]
    formato_a_original = {cat.capitalize(): cat for cat in categorias_disponibles}

    categoria_seleccionada = st.selectbox("Selecciona una categoría:", ["Todas"] + categorias_formateadas)

    if categoria_seleccionada != "Todas":
        publicaciones = [p for p in publicaciones if p.get("category") == formato_a_original[categoria_seleccionada]]

    # Dashboard resumen
    st.markdown("### 📊 Resumen del BOE")
    categorias = [p.get("category") for p in publicaciones if p.get("category")]
    departamentos = [p.get("departamento") for p in publicaciones if p.get("departamento")]
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📄 Total publicaciones", len(publicaciones))
        top_cat = Counter(categorias).most_common(1)
        top_dep = Counter(departamentos).most_common(1)
        st.metric("🏷️ Categoría top", top_cat[0][0].capitalize() if top_cat else "N/D")
        st.metric("🏛️ Dpto. top", top_dep[0][0] if top_dep else "N/D")
    with col2:
        if categorias:
            df_cat = pd.DataFrame(Counter(categorias).items(), columns=["Categoría", "Cantidad"])
            df_cat["Categoría"] = df_cat["Categoría"].str.capitalize()
            chart = alt.Chart(df_cat).mark_bar().encode(
                x="Cantidad:Q",
                y=alt.Y("Categoría:N", sort='-x'),
                tooltip=["Categoría", "Cantidad"]
            ).properties(height=220)
            st.altair_chart(chart, use_container_width=True)

    # Informe Ejecutivo
    st.markdown("### 🧠 Informe Ejecutivo")
    total = len(publicaciones)
    nombramientos = [p for p in publicaciones if "nombramiento" in (p.get("title") or "").lower()]
    leyes = [p for p in publicaciones if any(w in (p.get("title") or "").lower() for w in ["ley", "reglamento", "normativa"])]
    subvenciones = [p for p in publicaciones if any(w in (p.get("title") or "").lower() for w in ["subvención", "ayuda"])]
    empleo = [p for p in publicaciones if any(w in (p.get("title") or "").lower() for w in ["oposición", "concurso", "plazas"])]
    universidades = [p for p in publicaciones if "universidad" in (p.get("departamento") or "").lower()]

    st.info(f"""
📌 Hoy se han publicado {total} disposiciones oficiales:
- 🧾 {len(leyes)} normas o leyes
- 💸 {len(subvenciones)} subvenciones
- 👨‍⚖️ {len(nombramientos)} nombramientos
- 🧑‍💼 {len(empleo)} empleo público
- 📚 {len(universidades)} universidades
""")

    # Publicaciones detalladas
    st.markdown("### 📰 Publicaciones")
    for pub in publicaciones:
        with st.container(border=True):
            titulo = pub.get("title", "[Sin título]")
            url = pub.get("url_html")
            categoria = (pub.get("category") or "N/D").capitalize()
            st.markdown(f"**📄 [{titulo}]({url})**" if url else f"**📄 {titulo}**")
            st.markdown(f"🏷️ Categoría: `{categoria}`")
            st.write(f"📅 Fecha: `{pub.get('date', 'N/D')}`")
            st.write(f"🏛️ Departamento: `{pub.get('departamento') or 'N/D'}`")
            st.write(f"📂 Sección / Epígrafe: `{pub.get('seccion') or 'N/D'} / {pub.get('epigrafe') or 'N/D'}`")
            st.write(f"📄 Páginas: `{pub.get('pages') or 'N/D'}`")
            pdf = pub.get("url_pdf")
            if pdf:
                st.markdown(f"[⬇️ Descargar PDF]({pdf})")
            else:
                st.markdown("📎 PDF no disponible.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; font-size:0.85rem; color:gray;'>Hecho con 💙 por Pablo · AlertaBOE · 2025</div>", unsafe_allow_html=True)
