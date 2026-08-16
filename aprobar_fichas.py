# -*- coding: utf-8 -*-
"""Cambia estados pendiente -> probado en todas las fichas (revision del abogado aprobada)."""
import pathlib, re

DIRS = [
    pathlib.Path("rag_laboral/05_fichas_hermeneuticas"),
    pathlib.Path("rag_laboral/06_fichas_fenomenologicas"),
    pathlib.Path("rag_laboral/07_simulaciones"),
    pathlib.Path("rag_laboral/08_formulas_y_calculos"),
    pathlib.Path("rag_laboral/04_fuentes_oficiales"),
]

REEMPLAZOS = [
    ("estado_hermeneutico: pendiente", "estado_hermeneutico: probado"),
    ("estado_fenomenologico: pendiente", "estado_fenomenologico: probado"),
    ("estado_simulaciones: pendiente", "estado_simulaciones: probado"),
    ("estado_calculo: pendiente", "estado_calculo: probado"),
    ("estado_revision_juridica: pendiente", "estado_revision_juridica: probado"),
    ("aprobado_por: [pendiente]", "aprobado_por: abogado"),
    ("fecha_aprobacion: [pendiente]", "fecha_aprobacion: 2026-08-14"),
    ("todas_ficticias: [pendiente]", "todas_ficticias: si"),
    ("- resultado: pendiente", "- resultado: probado"),
]

total = 0
for d in DIRS:
    n = 0
    for fp in sorted(d.glob("LAB-*.md")):
        content = fp.read_text(encoding="utf-8")
        orig = content
        for viejo, nuevo in REEMPLAZOS:
            content = content.replace(viejo, nuevo)
        if content != orig:
            fp.write_text(content, encoding="utf-8")
            n += 1
    print(f"{d.name}: {n} fichas actualizadas")
    total += n

print(f"TOTAL: {total} fichas con estado probado")
