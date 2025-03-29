import re
import requests
from datetime import datetime

from app.db.session import SessionLocal
from app.db.models import Publication, Region, Scope

from app.services.classifier import extra_tag_por_contexto
from app.services.categoria_engine import clasificar_publicacion



# 🔍 Regex por comunidad autónoma
REGION_REGEX = {
    "Andalucía": r"\b(andaluc[ií]a|junta de andaluc[ií]a)\b",
    "Aragón": r"\b(arag[oó]n|gobierno de arag[oó]n)\b",
    "Asturias": r"\b(asturias|principado de asturias)\b",
    "Islas Baleares": r"\b(illes balears|baleares|islas baleares)\b",
    "Canarias": r"\b(canarias|gobierno de canarias)\b",
    "Cantabria": r"\bcantabria\b",
    "Castilla-La Mancha": r"\bcastilla[- ]la mancha\b",
    "Castilla y León": r"\bcastilla y le[oó]n\b",
    "Cataluña": r"\b(catalu[ññ]a|catalunya)\b",
    "Comunidad Valenciana": r"\b(comunidad valenciana|generalitat valenciana)\b",
    "Extremadura": r"\bextremadura\b",
    "Galicia": r"\b(galicia|xunta de galicia)\b",
    "Madrid": r"\b(comunidad de madrid|madrid)\b",
    "Murcia": r"\b(murcia|servicio murciano de salud)\b",
    "Navarra": r"\b(navarra|comunidad foral de navarra)\b",
    "País Vasco": r"\b(pa[ií]s vasco|euskadi)\b",
    "La Rioja": r"\bla rioja\b",
    "Ceuta": r"\bceuta\b",
    "Melilla": r"\bmelilla\b"
}

# 🔎 Scope: UE / Nacional / Autonómico
SCOPE_RULES = [
    (r"\b(unión europea|europeo|ue)\b", "Europeo"),
    (r"\b(estado|gobierno de españa|bolet[ií]n oficial del estado)\b", "Nacional"),
    (r"|".join(pat for pat in REGION_REGEX.values()), "Autonómico"),
]

def detectar_regiones(texto: str, session):
    texto = texto.lower()
    regiones_detectadas = []
    for region, patron in REGION_REGEX.items():
        if re.search(patron, texto):
            region_obj = session.query(Region).filter_by(name=region).first()
            if region_obj and region_obj not in regiones_detectadas:
                regiones_detectadas.append(region_obj)
    return regiones_detectadas

def get_or_create_scope(texto: str, session) -> int:
    texto = texto.lower()
    for regex, nombre_scope in SCOPE_RULES:
        if re.search(regex, texto):
            scope = session.query(Scope).filter_by(name=nombre_scope).first()
            if not scope:
                scope = Scope(name=nombre_scope)
                session.add(scope)
                session.commit()
            return scope.id
    default_scope = session.query(Scope).filter_by(name="Otro").first()
    if not default_scope:
        default_scope = Scope(name="Otro")
        session.add(default_scope)
        session.commit()
    return default_scope.id

def fetch_boe_json(fecha: str):
    url = f"https://boe.es/datosabiertos/api/boe/sumario/{fecha}"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        print(f"❌ No hay BOE publicado para la fecha {fecha} (¿domingo o festivo?)")
        return
    elif response.status_code != 200:
        print(f"❌ Error {response.status_code} al consultar el BOE")
        return

    try:
        diario = response.json()["data"]["sumario"]["diario"]
    except Exception as e:
        print("❌ Error leyendo el JSON del BOE:", e)
        return

    session = SessionLocal()
    publicaciones = 0

    for dia in diario:
        for seccion in dia.get("seccion", []):
            nombre_seccion = seccion.get("nombre") or "N/D"
            codigo_seccion = seccion.get("codigo") or "N/D"
            departamentos = seccion.get("departamento", [])

            # Asegurar que es lista
            if isinstance(departamentos, dict):
                departamentos = [departamentos]
            elif isinstance(departamentos, str):
                departamentos = [{"nombre": departamentos}]

            for departamento in departamentos:
                nombre_dep = departamento.get("nombre") or "N/D"

                # 🧠 CASO A: estructura con epigrafes
                if "epigrafe" in departamento:
                    epigrafes = departamento.get("epigrafe", [])
                    if isinstance(epigrafes, dict):
                        epigrafes = [epigrafes]

                    for epigrafe in epigrafes:
                        nombre_epigrafe = epigrafe.get("nombre") or "N/D"
                        items = epigrafe.get("item", [])
                        if isinstance(items, dict):
                            items = [items]

                        for item in items:
                            publicaciones += procesar_item(item, fecha, session, nombre_seccion, codigo_seccion, nombre_dep, nombre_epigrafe)

                # 🧠 CASO B: estructura sin epigrafes
                elif "item" in departamento:
                    items = departamento.get("item", [])
                    if isinstance(items, dict):
                        items = [items]

                    for item in items:
                        publicaciones += procesar_item(item, fecha, session, nombre_seccion, codigo_seccion, nombre_dep, None)

    session.commit()
    session.close()
    print(f"✅ {publicaciones} publicaciones guardadas.")

def procesar_item(item, fecha, session, seccion, seccion_codigo, departamento, epigrafe):
    titulo = item.get("titulo", "[Sin título]")
    extra_tag = extra_tag_por_contexto(titulo)

    boe_id = item.get("identificador")
    url_html = item.get("url_html")
    url_pdf_data = item.get("url_pdf", {})
    url_pdf = url_pdf_data.get("texto") if isinstance(url_pdf_data, dict) else None

    try:
        pagina_ini = int(url_pdf_data.get("pagina_inicial"))
        pagina_fin = int(url_pdf_data.get("pagina_final"))
        pages = pagina_fin - pagina_ini + 1
    except (TypeError, ValueError):
        pages = None

    if session.query(Publication).filter_by(boe_id=boe_id).first():
        return 0

    # ✅ TEXTO COMPLETO para clasificador
    texto_completo = f"{seccion} {departamento} {epigrafe or ''} {titulo}"

    resultado = clasificar_publicacion(texto_completo)

    if isinstance(resultado, list):
        categorias = resultado
    elif isinstance(resultado, str):
        categorias = [resultado]
    else:
        categorias = []


    regiones = detectar_regiones(texto_completo, session)
    scope_id = get_or_create_scope(texto_completo, session)

    pub = Publication(
        date=datetime.strptime(fecha, "%Y%m%d").date(),
        title=titulo,
        body=titulo,
        category=categorias,  # 🔁 AHORA ES UNA LISTA
        extra_tag=extra_tag,
        scope_id=scope_id,
        boe_id=boe_id,
        departamento=departamento,
        seccion=seccion,
        epigrafe=epigrafe,
        url_html=url_html,
        url_pdf=url_pdf,
        pages=pages,
    )

    session.add(pub)
    session.flush()
    pub.regions = regiones
    return 1

