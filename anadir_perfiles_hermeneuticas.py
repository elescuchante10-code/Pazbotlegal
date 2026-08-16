# -*- coding: utf-8 -*-
"""Anade conclusiones PAZ por perfil y campo perfil a las fichas hermeneuticas existentes."""
import json, pathlib, re, pymupdf
from hermeneutica_helpers import (oraciones_clave, conceptos, riesgo,
    gen_conclusion_paz_trabajador, gen_conclusion_paz_empresa, gen_perfil_herm)

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

print("Extrayendo texto...", flush=True)
doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()

print("Actualizando fichas hermeneuticas con perfiles...", flush=True)
n = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    cps = conceptos(texto, tit)
    oc = oraciones_clave(texto)
    perfil = gen_perfil_herm(blk, tit)
    ct = gen_conclusion_paz_trabajador(tit, cps, oc, blk)
    ce = gen_conclusion_paz_empresa(tit, cps, oc, blk)

    fp = DIR_HERM/f"{tid}.md"
    if not fp.exists(): continue
    content = fp.read_text(encoding="utf-8")

    # Anadir campo Perfil en Identificacion si no existe
    if "## Identificacion" in content and "- Perfil:" not in content:
        content = content.replace(
            f"- topic_id: {tid}",
            f"- topic_id: {tid}\n- Perfil: {perfil}"
        )

    # Reemplazar la seccion "Conclusion para PAZ" por las dos versiones por perfil
    old_sec = re.search(r"## Conclusion para PAZ\n.*?(?=\n## |\Z)", content, re.DOTALL)
    if old_sec:
        new_sec = (f"## Conclusion para PAZ (perfil trabajador)\n{ct}\n\n"
                   f"## Conclusion para PAZ (perfil empresa)\n{ce}\n")
        content = content[:old_sec.start()] + new_sec + content[old_sec.end():]

    fp.write_text(content, encoding="utf-8")
    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} fichas hermeneuticas actualizadas con perfiles", flush=True)
