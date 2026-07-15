"""El parser de fechas en español debe fechar los plazos del agente."""

from datetime import date

from boe.enrich.plazos import parse_fecha_es

_REF = date(2026, 7, 15)


def test_fecha_larga_con_anio():
    assert parse_fecha_es("30 de septiembre de 2026", referencia=_REF) == date(2026, 9, 30)


def test_fecha_larga_dentro_de_frase():
    texto = "hasta el 1 de agosto de 2026 inclusive"
    assert parse_fecha_es(texto, referencia=_REF) == date(2026, 8, 1)


def test_fecha_sin_anio_usa_referencia():
    assert parse_fecha_es("30 de septiembre", referencia=_REF) == date(2026, 9, 30)


def test_fecha_sin_anio_ya_pasada_salta_al_siguiente():
    # En julio, "15 de enero" solo puede ser el enero siguiente.
    assert parse_fecha_es("15 de enero", referencia=_REF) == date(2027, 1, 15)


def test_fecha_numerica():
    assert parse_fecha_es("30/09/2026", referencia=_REF) == date(2026, 9, 30)


def test_fecha_iso():
    assert parse_fecha_es("2026-09-30", referencia=_REF) == date(2026, 9, 30)


def test_plazo_relativo_no_se_inventa():
    assert parse_fecha_es("3 meses desde la publicación", referencia=_REF) is None


def test_texto_vacio_o_invalido():
    assert parse_fecha_es("", referencia=_REF) is None
    assert parse_fecha_es("31 de febrero de 2026", referencia=_REF) is None
