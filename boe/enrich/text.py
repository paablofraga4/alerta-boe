"""Extracción de texto limpio del HTML de una publicación del BOE.

Migrado de `app/services/summarizer.py`. La descarga usa el cliente httpx
compartido; el parseo con BeautifulSoup es una función pura y testeable.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from boe.clients.base import BOEHttpClient

_MAX_CHARS = 20000


def clean_html(html: str) -> str:
    """Extrae el texto legible de un HTML del BOE."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    # El cuerpo del BOE vive en <div class="documento"> o similar; si no, todo.
    container = soup.find("div", class_="documento") or soup.body or soup
    text = container.get_text(separator="\n", strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)[:_MAX_CHARS]


async def fetch_text(http: BOEHttpClient, url_html: str | None) -> str | None:
    """Descarga y limpia el HTML de una publicación. None si no hay URL/contenido."""
    if not url_html:
        return None
    html = await http.get_html(url_html)
    if not html:
        return None
    return clean_html(html) or None
