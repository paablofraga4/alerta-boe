"""Tests de las etapas de enriquecido puras (sin red ni DB)."""

from boe.core.enums import Scope
from boe.enrich.classify import classify_by_regex
from boe.enrich.regions import detect_regions, detect_scope
from boe.enrich.text import clean_html


def test_detect_regions():
    assert "Galicia" in detect_regions("La Xunta de Galicia aprueba ayudas")
    assert detect_regions("Texto sin región") == []
    regions = detect_regions("Convenio entre Madrid y Cataluña")
    assert "Madrid" in regions and "Cataluña" in regions


def test_detect_scope_priority():
    assert detect_scope("Reglamento (UE) 2024/1 del Parlamento") == Scope.EUROPEO
    assert detect_scope("Jefatura del Estado. Ley Orgánica") == Scope.NACIONAL
    assert detect_scope("La Xunta de Galicia") == Scope.AUTONOMICO
    assert detect_scope("Anuncio de una empresa privada") == Scope.OTRO


def test_classify_by_regex():
    cats = classify_by_regex("Orden de subvenciones y ayudas a autónomos")
    assert "Subvención" in cats
    assert "Empresa y comercio" in cats
    assert classify_by_regex("texto totalmente neutro xyz") == []


def test_clean_html_strips_scripts():
    html = """
    <html><body>
      <script>ignora esto</script>
      <div class="documento"><h1>Título</h1><p>Contenido legal.</p></div>
    </body></html>
    """
    text = clean_html(html)
    assert "Contenido legal." in text
    assert "ignora esto" not in text
