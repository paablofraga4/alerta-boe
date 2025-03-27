# app/services/intent_parser.py

def detectar_extra_tag(texto: str) -> str | None:
    texto = texto.lower()
    if "autónomo" in texto or "autonomo" in texto:
        return "Autónomos"
    if "empresa" in texto or "comercio" in texto or "pyme" in texto:
        return "Empresas"
    if "educación" in texto or "profesor" in texto or "docente" in texto:
        return "Educación"
    if "universidad" in texto or "beca" in texto:
        return "Universidad"
    if "sanidad" in texto or "hospital" in texto or "salud" in texto:
        return "Sanidad"
    if "tecnología" in texto or "digital" in texto or "tic" in texto:
        return "Digitalización"
    if "justicia" in texto or "tribunal" in texto or "juzgado" in texto:
        return "Justicia"
    return None

def detectar_region(texto: str, regiones: list[str]) -> str | None:
    texto = texto.lower()
    for region in regiones:
        if region.lower() in texto:
            return region
    return None

def detectar_scope(texto: str, scopes: list[str]) -> str | None:
    texto = texto.lower()
    for scope in scopes:
        if scope.lower() in texto:
            return scope
    return None
