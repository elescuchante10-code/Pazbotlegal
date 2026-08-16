# -*- coding: utf-8 -*-
"""Regenera TODAS las fichas hermeneuticas con todos los campos redactados."""
import json, pathlib, re, pymupdf
from hermeneutica_helpers import *

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_HERM = pathlib.Path("rag_laboral/05_fichas_hermeneuticas")
DIR_HERM.mkdir(parents=True, exist_ok=True)

inventario = []
with INV.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))
for i, e in enumerate(inventario):
    fin = inventario[i+1]["pagina"]-1 if i+1 < len(inventario) else 1169
    e["_pags"] = list(range(e["pagina"], fin+1))
print(f"Inventario: {len(inventario)} temas", flush=True)

print("Extrayendo texto...", flush=True)
doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()
print(f"Paginas: {len(tp)}", flush=True)

print("Redactando fichas hermeneuticas completas...", flush=True)
n = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    sub = e["subbloque"]; ruta = e["ruta_tematica"]; pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = f"[Contenido limitado. Paginas: {pags}]"
    oc = oraciones_clave(texto); cit = citas_norm(texto); cps = conceptos(texto, tit)
    rsc = riesgo(tit, blk)
    lit = (texto[:1200]+"...") if len(texto)>1200 else texto
    pstr = str(pags[0]) if len(pags)==1 else f"{pags[0]}-{pags[-1]}"
    rstr = " > ".join(ruta)

    prob = (f"La guia aborda: {tit}. " if tit.startswith("\u00bf") else f"Regula el conflicto sobre {tit.lower()}. ")
    prob += f"Se enmarca en {blk.lower()}."
    tesis = (" ".join(oc[:2])[:600]) if oc else "La guia explica el tema sin tesis explicita. Se requiere revision juridica."
    conc = f"Sobre {tit.lower()}, la guia senala que {oc[0][:200].lower().rstrip('.')}." if oc else f"La guia explica {tit.lower()}."
    conc += " Se recomienda contrastar con la norma oficial." if rsc!="alto" else " Requiere verificacion con fuentes oficiales y revision juridica."
    lims = []
    if not cit: lims.append("La guia no cita explicitamente la norma. Requiere verificacion normativa.")
    if "2025" in texto or "2026" in texto: lims.append("Contiene informacion temporal (2026) que requiere actualizacion anual.")
    lims.append("Borrador generado automaticamente. Requiere revision juridica antes de produccion.")

    fin = gen_finalidad(cps, blk, tit)
    ip = gen_interp_principal(oc, cps, tit)
    ialt = gen_interp_alt(cps)
    sinc = gen_supuestos_inc(cps, tit)
    sexc = gen_supuestos_exc(cps, tit)
    hdec = gen_hechos_decisivos(cps, tit)

    fh = f"""# Ficha hermeneutica: {tit}

## Identificacion
- Tema: {tit}
- Capitulo (bloque): {blk}
- Subbloque: {sub}
- Paginas de la guia: {pstr}
- Fecha de vigencia: 2026
- Tipo de fuente: secundaria_explicativa
- topic_id: {tid}

## Problema regulado
{prob}

## Tesis interpretativa
{tesis}

## Contenido literal relevante
{lit}

## Contexto sistemtico
Se relaciona con: {rstr}. Conceptos clave: {', '.join(cps) if cps else 'no detectados'}.

## Finalidad
{fin}

## Interpretacion principal
{ip}

## Interpretaciones alternativas
{chr(10).join('- '+a for a in ialt)}

## Supuestos incluidos
{chr(10).join('- '+s for s in sinc)}

## Supuestos excluidos
{chr(10).join('- '+s for s in sexc)}

## Hechos decisivos
{chr(10).join('- '+h for h in hdec)}

## Fuentes oficiales relacionadas
{chr(10).join('- '+c for c in cit) if cit else '- [pendiente de verificacion]'}

## Conclusion para PAZ
{conc}

## Limites
{chr(10).join('- '+l for l in lims)}

## Estado de aprobacion
- estado_hermeneutico: pendiente
- estado_revision_juridica: pendiente
- aprobado_por: [pendiente]
- fecha_aprobacion: [pendiente]
"""
    (DIR_HERM/f"{tid}.md").write_text(fh, encoding="utf-8")
    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} fichas hermeneuticas redactadas", flush=True)
