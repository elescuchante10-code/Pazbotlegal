# -*- coding: utf-8 -*-
"""Llena las verificaciones normativas: extrae normas citadas en el texto de cada tema."""
import json, pathlib, re, pymupdf
from hermeneutica_helpers import citas_norm, oraciones_clave

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_VER = pathlib.Path("rag_laboral/04_fuentes_oficiales")

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

print("Llenando verificaciones normativas...", flush=True)
n = 0; n_normas = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]
    pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    normas = citas_norm(texto)
    n_normas += len(normas)

    fp = DIR_VER/f"{tid}.md"
    if not fp.exists(): continue
    content = fp.read_text(encoding="utf-8")

    # Llenar cada proposicion: norma_citada y resultado
    def reemplazar_prop(m):
        bloque = m.group(0)
        if normas:
            norma_str = "; ".join(normas[:3])
            resultado = "norma_identificada_requiere_contraste"
        else:
            norma_str = "No se cita norma explicita en la guia"
            resultado = "sin_norma_citada_requiere_busqueda_manual"
        bloque = re.sub(r"- norma_citada: \[pendiente\]", f"- norma_citada: {norma_str}", bloque)
        bloque = re.sub(r"- resultado: pendiente", f"- resultado: {resultado}", bloque)
        return bloque

    content = re.sub(r"### claim_id: [^\n]+\n.*?(?=\n### |\n## |\Z)", reemplazar_prop, content, flags=re.DOTALL)

    fp.write_text(content, encoding="utf-8")
    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} verificaciones normativas llenadas", flush=True)
print(f"Total normas citadas detectadas: {n_normas}", flush=True)
