"""El triaje editorial clasifica por metadatos y prioriza lo que importa."""

from boe.enrich.triage import (
    CAT_ANUNCIOS,
    CAT_AYUDAS,
    CAT_JUSTICIA,
    CAT_NOMBRAMIENTOS,
    CAT_NORMAS,
    CAT_OPOSICIONES,
    CAT_OTRAS,
    triage,
)


def test_seccion_1_es_norma():
    t = triage(title="Ley 3/2026 de medidas fiscales", seccion_codigo="1", rango="Ley")
    assert t.category == CAT_NORMAS
    assert t.relevance >= 75


def test_nombramiento_es_ruido():
    t = triage(title="Resolución por la que se nombra a un alto cargo", seccion_codigo="2A")
    assert t.category == CAT_NOMBRAMIENTOS
    assert t.noise is True
    assert t.relevance < 20


def test_oposiciones_en_seccion_2():
    t = triage(
        title="Convocatoria de proceso selectivo para 200 plazas",
        seccion_codigo="2",
        epigrafe="Oposiciones y concursos",
    )
    assert t.category == CAT_OPOSICIONES
    assert t.noise is False


def test_ayudas_en_seccion_3():
    t = triage(
        title="Orden de subvenciones a autónomos afectados por la DANA",
        seccion_codigo="3",
    )
    assert t.category == CAT_AYUDAS
    # Ayudas + señales de impacto (autónomo/DANA) → muy relevante.
    assert t.relevance >= 90


def test_edictos_justicia_es_ruido():
    t = triage(title="Edicto del Juzgado de Primera Instancia nº 4", seccion_codigo="4")
    assert t.category == CAT_JUSTICIA
    assert t.noise is True


def test_anuncios_contratacion_es_ruido():
    t = triage(title="Anuncio de licitación de obras", seccion_codigo="5")
    assert t.category == CAT_ANUNCIOS
    assert t.noise is True


def test_seccion_3_tramite_es_otras():
    t = triage(title="Resolución sobre delegación de competencias", seccion_codigo="3")
    assert t.category == CAT_OTRAS
    assert t.noise is False


def test_relevancia_acotada_0_100():
    t = triage(
        title="Ley de ayudas y subvenciones a autónomos por DANA con plazo",
        seccion_codigo="1",
        rango="Ley",
    )
    assert 0 <= t.relevance <= 100
