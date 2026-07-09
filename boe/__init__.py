"""AlertaBOE — dominio del producto.

Paquete instalable que agrupa la lógica de negocio (clientes de las APIs del BOE,
ingesta, enriquecido con LLM, búsqueda, grafo normativo y fábrica de contenido).
La capa HTTP vive en `apps/api`; los jobs, en `workers/`.
"""

__version__ = "0.2.0"
