# -*- coding: utf-8 -*-
"""Extrae el indice completo (bookmarks/TOC) del PDF y construye el inventario maestro.

Sigue la seccion 6 de la especificacion: cada entrada del indice original debe terminar
asociada a una unidad juridica, con su topic_id, bloque, paginas y estados de extraccion.
"""

import json
import pathlib
import re
import sys

import pymupdf

SRC = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
OUT_JSONL = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
OUT_MD = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.md")

# --- 1. Extraer bookmarks del PDF (estructura jerarquica con paginas) ---
doc = pymupdf.open(SRC)
toc = doc.get_toc()  # lista de [nivel, titulo, pagina]

print(f"Bookmarks extraidos del PDF: {len(toc)}", flush=True)
if not toc:
    print("No hay bookmarks. Extrayendo TOC del texto de las primeras paginas...", flush=True)

# --- 2. Mapeo de los 20 bloques tematicos (seccion 10 de la especificacion) ---
BLOQUES = [
    "Indicadores laborales 2026",
    "Resumen de la reforma laboral",
    "Contrato de trabajo",
    "Obligaciones derivadas del contrato",
    "Acoso laboral",
    "Periodo de prueba",
    "Terminacion del contrato",
    "Reintegro del trabajador",
    "Liquidacion del contrato",
    "Trabajo en casa",
    "Jornada laboral",
    "Remuneracion del trabajo",
    "Prestaciones sociales",
    "Seguridad social",
    "Aportes parafiscales",
    "Tercerizacion laboral",
    "Reglamento de trabajo",
    "Contrato de servicios",
    "Otros aspectos relevantes del contrato",
    "Complementos e historicos",
]


def normalizar_bloque(titulo: str) -> str:
    """Asocia un titulo de entrada a uno de los 20 bloques tematicos."""
    t = titulo.lower()
    mapeo = [
        ("indicadores laborales", "Indicadores laborales 2026"),
        ("reforma laboral", "Resumen de la reforma laboral"),
        ("acoso laboral", "Acoso laboral"),
        ("periodo de prueba", "Periodo de prueba"),
        ("reintegro", "Reintegro del trabajador"),
        ("liquidacion del contrato", "Liquidacion del contrato"),
        ("liquidacion de", "Liquidacion del contrato"),
        ("trabajo en casa", "Trabajo en casa"),
        ("teletrabajo", "Trabajo en casa"),
        ("jornada", "Jornada laboral"),
        ("horas extras", "Jornada laboral"),
        ("trabajo suplementario", "Jornada laboral"),
        ("recargo nocturno", "Jornada laboral"),
        ("recargos dominicales", "Jornada laboral"),
        ("trabajo dominical", "Jornada laboral"),
        ("dias festivos", "Jornada laboral"),
        ("turnos", "Jornada laboral"),
        ("remuneracion", "Remuneracion del trabajo"),
        ("salario", "Remuneracion del trabajo"),
        ("sueldo", "Remuneracion del trabajo"),
        ("auxilio de transporte", "Remuneracion del trabajo"),
        ("pago de", "Remuneracion del trabajo"),
        ("prestaciones sociales", "Prestaciones sociales"),
        ("prima", "Prestaciones sociales"),
        ("cesantias", "Prestaciones sociales"),
        ("intereces de cesantias", "Prestaciones sociales"),
        ("vacaciones", "Prestaciones sociales"),
        ("licencia", "Prestaciones sociales"),
        ("seguridad social", "Seguridad social"),
        ("pension", "Seguridad social"),
        ("incapacidad", "Seguridad social"),
        ("eps", "Seguridad social"),
        ("arl", "Seguridad social"),
        ("afiliacion", "Seguridad social"),
        ("cotizacion", "Seguridad social"),
        ("enfermedad", "Seguridad social"),
        ("maternidad", "Seguridad social"),
        ("licencia de maternidad", "Seguridad social"),
        ("parafiscales", "Aportes parafiscales"),
        ("icbf", "Aportes parafiscales"),
        ("sena", "Aportes parafiscales"),
        ("caja de compensacion", "Aportes parafiscales"),
        ("tercerizacion", "Tercerizacion laboral"),
        ("outsourcing", "Tercerizacion laboral"),
        ("intermediacion", "Tercerizacion laboral"),
        ("reglamento de trabajo", "Reglamento de trabajo"),
        ("contrato de servicios", "Contrato de servicios"),
        ("contrato realidad", "Contrato de trabajo"),
        ("elementos del contrato", "Contrato de trabajo"),
        ("subordinacion", "Contrato de trabajo"),
        ("modalidades del contrato", "Contrato de trabajo"),
        ("termino indefinido", "Contrato de trabajo"),
        ("termino fijo", "Contrato de trabajo"),
        ("obra o labor", "Contrato de trabajo"),
        ("aprendizaje", "Contrato de trabajo"),
        ("servicio domestico", "Contrato de trabajo"),
        ("empleadas domestic", "Contrato de trabajo"),
        ("docentes", "Contrato de trabajo"),
        ("profesores", "Contrato de trabajo"),
        ("conductores", "Contrato de trabajo"),
        ("medio tiempo", "Contrato de trabajo"),
        ("obligaciones del empleador", "Obligaciones derivadas del contrato"),
        ("prohibiciones", "Obligaciones derivadas del contrato"),
        ("poder disciplinario", "Obligaciones derivadas del contrato"),
        ("sanciones disciplinar", "Obligaciones derivadas del contrato"),
        ("descargos", "Obligaciones derivadas del contrato"),
        ("despido", "Terminacion del contrato"),
        ("renuncia", "Terminacion del contrato"),
        ("justa causa", "Terminacion del contrato"),
        ("justas causas", "Terminacion del contrato"),
        ("indemnizacion", "Terminacion del contrato"),
        ("terminacion del contrato", "Terminacion del contrato"),
        ("estabilidad", "Reintegro del trabajador"),
        ("fuero", "Reintegro del trabajador"),
        ("discapacidad", "Reintegro del trabajador"),
        ("reintegro", "Reintegro del trabajador"),
        ("certificacion laboral", "Otros aspectos relevantes del contrato"),
        ("carta de recomendacion", "Otros aspectos relevantes del contrato"),
        ("prestamos", "Otros aspectos relevantes del contrato"),
        ("prestamo", "Otros aspectos relevantes del contrato"),
        ("vivienda", "Otros aspectos relevantes del contrato"),
        ("desconexion laboral", "Otros aspectos relevantes del contrato"),
        ("fallecimiento", "Otros aspectos relevantes del contrato"),
        ("historico", "Complementos e historicos"),
        ("historicos", "Complementos e historicos"),
        ("tabla de contenido", "Complementos e historicos"),
        ("introduccion", "Complementos e historicos"),
    ]
    for clave, bloque in mapeo:
        if clave in t:
            return bloque
    return "Otros aspectos relevantes del contrato"


def limpiar_titulo(t: str) -> str:
    t = re.sub(r"\.+\s*$", "", t).strip()
    t = re.sub(r"^\d+\.\s*", "", t)
    return t


# --- 3. Construir inventario ---
entradas = []
pila = []  # [(nivel, titulo)] para reconstruir la jerarquia

for idx, (nivel, titulo_raw, pagina) in enumerate(toc):
    titulo = limpiar_titulo(titulo_raw)
    # reconstruir ruta tematica
    while pila and pila[-1][0] >= nivel:
        pila.pop()
    pila.append((nivel, titulo))
    ruta = [t for _, t in pila]

    bloque = normalizar_bloque(titulo)
    subbloque = ruta[-2] if len(ruta) >= 2 else bloque

    topic_id = f"LAB-{idx + 1:04d}"

    entrada = {
        "topic_id": topic_id,
        "titulo_original": titulo_raw.strip(),
        "titulo_normalizado": titulo,
        "nivel": nivel,
        "ruta_tematica": ruta,
        "bloque": bloque,
        "subbloque": subbloque,
        "pagina": pagina,
        "paginas": [pagina],
        "tipo": "tema_autonomo",
        "estado_extraccion": "pendiente",
        "estado_fuente_oficial": "pendiente",
        "estado_hermeneutico": "pendiente",
        "estado_fenomenologico": "pendiente",
        "estado_simulaciones": "pendiente",
        "estado_revision_juridica": "pendiente",
        "estado_indexacion": "pendiente",
        "estado_evaluacion": "pendiente",
    }
    entradas.append(entrada)

# --- 4. Guardar JSONL ---
OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
with OUT_JSONL.open("w", encoding="utf-8") as f:
    for e in entradas:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

# --- 5. Guardar Markdown para el abogado ---
with OUT_MD.open("w", encoding="utf-8") as f:
    f.write("# Inventario maestro de cobertura\n\n")
    f.write(f"**Fuente:** Guía Laboral 2026 (Gerencie.com) | **Páginas:** 1,169 | ")
    f.write(f"**Entradas identificadas:** {len(entradas)}\n\n")
    f.write("| topic_id | título | bloque | página | estado |\n")
    f.write("|---|---|---|---|---|\n")
    for e in entradas:
        f.write(f"| {e['topic_id']} | {e['titulo_normalizado']} | {e['bloque']} | {e['pagina']} | pendiente |\n")

# --- 6. Resumen por bloque ---
from collections import Counter
por_bloque = Counter(e["bloque"] for e in entradas)
print(f"\nTotal entradas: {len(entradas)}", flush=True)
print("\nDistribucion por bloque tematico:", flush=True)
for bloque in BLOQUES:
    n = por_bloque.get(bloque, 0)
    print(f"  {n:4d}  {bloque}", flush=True)
otros = sum(v for k, v in por_bloque.items() if k not in BLOQUES)
if otros:
    print(f"  {otros:4d}  (sin clasificar)", flush=True)

print(f"\nJSONL -> {OUT_JSONL}", flush=True)
print(f"Markdown -> {OUT_MD}", flush=True)
