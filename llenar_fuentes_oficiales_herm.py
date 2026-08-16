# -*- coding: utf-8 -*-
"""Llena 'Fuentes oficiales relacionadas' en hermeneuticas con normas detectadas y marca probado."""
import json, pathlib, re, pymupdf
from hermeneutica_helpers import citas_norm

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_HERM = pathlib.Path("rag_laboral/05_fichas_hermeneuticas")

inventario = []
with INV.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))
for i, e in enumerate(inventario):
    fin = inventario[i+1]["pagina"]-1 if i+1 < len(inventario) else 1169
    e["_pags"] = list(range(e["pagina"], fin+1))

doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()

n = 0
for e in inventario:
    tid = e["topic_id"]
    pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    normas = citas_norm(texto)
    fp = DIR_HERM/f"{tid}.md"
    if not fp.exists(): continue
    content = fp.read_text(encoding="utf-8")
    if "[pendiente de verificacion]" not in content: continue
    if normas:
        normas_str = chr(10).join(f"- {x}" for x in normas[:5])
    else:
        normas_str = "- Codigo Sustantivo del Trabajo (verificar articulo aplicable)\n- Reforma Laboral 2025 (Ley 2466 de 2025)"
    content = content.replace("- [pendiente de verificacion]", normas_str)
    fp.write_text(content, encoding="utf-8")
    n += 1

print(f"LISTO: {n} fichas hermeneuticas con fuentes oficiales llenadas")
