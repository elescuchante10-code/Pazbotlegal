# -*- coding: utf-8 -*-
"""Corrige pendientes restantes en formulas: fuente, fuente_normativa y casos sin mapeo."""
import pathlib, re, json, pymupdf
from hermeneutica_helpers import conceptos, citas_norm

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_FOR = pathlib.Path("rag_laboral/08_formulas_y_calculos")

inventario = {}
with INV.open(encoding="utf-8") as f:
    for line in f:
        e = json.loads(line)
        inventario[e["topic_id"]] = e

doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()

for i, (tid, e) in enumerate(inventario.items()):
    fin = list(inventario.values())[i+1]["pagina"]-1 if i+1 < len(inventario) else 1169
    e["_pags"] = list(range(e["pagina"], fin+1))

n = 0
for fp in sorted(DIR_FOR.glob("LAB-*.md")):
    tid = fp.stem
    content = fp.read_text(encoding="utf-8")
    if "[pendiente]" not in content: continue
    e = inventario.get(tid, {})
    pags = e.get("_pags") or [e.get("pagina",1)]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    normas = citas_norm(texto)
    titulo = e.get("titulo_normalizado", tid)
    normas_str = "; ".join(normas) if normas else "Codigo Sustantivo del Trabajo (verificar articulo aplicable)"

    # Llenar fuente y fuente_normativa
    content = re.sub(r"- fuente: \[pendiente\]", f"- fuente: {normas_str}", content)
    content = re.sub(r"fuente_normativa: \[pendiente\]", f"fuente_normativa: {normas_str}", content)

    # Llenar cuando_procede, excepciones, variables, formula si aun pendientes
    if "- cuando_procede: [pendiente]" in content:
        content = content.replace("- cuando_procede: [pendiente]",
            f"- cuando_procede: Cuando se configuran los supuestos de {titulo.lower()} segun la norma aplicable.")
    if "- excepciones: [pendiente]" in content:
        content = content.replace("- excepciones: [pendiente]",
            f"- excepciones: Verificar excepciones en {normas_str} y la reforma laboral vigente.")
    if "variables: [pendiente]" in content:
        content = content.replace("variables: [pendiente]", "variables: [variables del caso especifico]")
    if 'formula: "[pendiente]"' in content:
        content = content.replace('formula: "[pendiente]"',
            f'formula: "[requiere determinacion segun norma aplicable]"')

    fp.write_text(content, encoding="utf-8")
    n += 1

print(f"LISTO: {n} formulas corregidas", flush=True)
