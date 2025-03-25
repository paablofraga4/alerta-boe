import requests
from app.db.session import SessionLocal
from app.db.models import Publication
from app.services.classifier import classify_with_ai
from datetime import datetime

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

            # 🔧 Normalizar departamento
            departamentos = seccion.get("departamento", [])
            if isinstance(departamentos, str):
                departamentos = [{"nombre": departamentos}]
            elif isinstance(departamentos, dict):
                departamentos = [departamentos]

            for departamento in departamentos:
                nombre_dep = departamento.get("nombre") or "N/D"

                # 🔧 Normalizar epígrafes
                epigrafes = departamento.get("epigrafe", [])
                if isinstance(epigrafes, dict):
                    epigrafes = [epigrafes]

                for epigrafe in epigrafes:
                    nombre_epigrafe = epigrafe.get("nombre") or "N/D"

                    # 🔧 Normalizar ítems
                    items = epigrafe.get("item", [])
                    if isinstance(items, dict):
                        items = [items]

                    for item in items:
                        titulo = item.get("titulo", "[Sin título]")
                        category = classify_with_ai(titulo)
                        scope = f"{nombre_seccion} / {nombre_dep}"

                        boe_id = item.get("identificador", None)
                        url_html = item.get("url_html", None)

                        # ✅ url_pdf
                        url_pdf_data = item.get("url_pdf")
                        url_pdf = url_pdf_data.get("texto") if isinstance(url_pdf_data, dict) else None

                        # ✅ páginas
                        pagina_ini = item.get("pagina_inicial")
                        pagina_fin = item.get("pagina_final")
                        try:
                            pagina_ini = int(pagina_ini)
                            pagina_fin = int(pagina_fin)
                            pages = pagina_fin - pagina_ini + 1
                        except (TypeError, ValueError):
                            pages = None

                        # ❌ Duplicado por boe_id
                        exists = session.query(Publication).filter_by(boe_id=boe_id).first()
                        if exists:
                            # print("🔍 Publicación:")
                            # print(f"  📰 {titulo}")
                            # print(f"  🏛️ Departamento: {nombre_dep}")
                            # print(f"  📂 Sección: {nombre_seccion}")
                            # print(f"  📑 Epígrafe: {nombre_epigrafe}")
                            continue

                        pub = Publication(
                            date=datetime.strptime(fecha, "%Y%m%d").date(),
                            title=titulo,
                            body=titulo,
                            category=category,
                            scope=scope,
                            boe_id=boe_id,
                            departamento=nombre_dep,
                            seccion=nombre_seccion,
                            epigrafe=nombre_epigrafe,
                            url_html=url_html,
                            url_pdf=url_pdf,
                            pages=pages
                        )
                        # print("🔍 Publicación:")
                        # print(f"  📰 {titulo}")
                        # print(f"  🏛️ Departamento: {nombre_dep}")
                        # print(f"  📂 Sección: {nombre_seccion}")
                        # print(f"  📑 Epígrafe: {nombre_epigrafe}")


                        session.add(pub)
                        publicaciones += 1

    session.commit()
    session.close()
    print(f"✅ {publicaciones} publicaciones guardadas.")
