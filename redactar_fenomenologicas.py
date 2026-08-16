# -*- coding: utf-8 -*-
"""Regenera TODAS las fichas fenomenologicas con todos los campos redactados."""
import json, pathlib, re, pymupdf
from fenomenologia_helpers import *
from hermeneutica_helpers import oraciones_clave, conceptos, riesgo

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_FENO = pathlib.Path("rag_laboral/06_fichas_fenomenologicas")
DIR_FENO.mkdir(parents=True, exist_ok=True)

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

print("Redactando fichas fenomenologicas completas...", flush=True)
n = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    sub = e["subbloque"]; ruta = e["ruta_tematica"]; pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    cps = conceptos(texto, tit)
    rsc = riesgo(tit, blk)
    pstr = str(pags[0]) if len(pags)==1 else f"{pags[0]}-{pags[-1]}"
    rstr = " > ".join(ruta)

    cv_t = gen_como_se_vive(tit, cps, "trabajador")
    cv_e = gen_como_se_vive(tit, cps, "empresa")
    qso = gen_que_suele_ocurrir(cps)
    act = gen_actores(cps)
    sec = gen_secuencia(cps)
    epo = gen_epoje(cps)
    ev = gen_evidencias(cps)
    sc = gen_sim_compat(cps, tit)
    sn = gen_sim_no_compat(cps, tit)
    sd = gen_sim_dudosa(cps, tit)
    rp_t = gen_respuesta_paz_perfil(tit, cps, rsc, "trabajador")
    rp_e = gen_respuesta_paz_perfil(tit, cps, rsc, "empresa")
    perfil = gen_perfil(blk, tit)

    ff = f"""# Ficha fenomenologica: {tit}

## Identificacion
- Tema: {tit}
- Bloque: {blk}
- Subbloque: {sub}
- Paginas: {pstr}
- topic_id: {tid}
- Perfil: {perfil}

## Como se vive (trabajador)
{cv_t}

## Como se vive (empresa)
{cv_e}

## Que suele ocurrir
{chr(10).join('- '+h for h in qso)}

## Actores
{', '.join(act)}.

## Secuencia
{sec}

## Epoje
{chr(10).join('- '+e for e in epo)}

## Hechos decisivos
{chr(10).join('- '+c for c in cps) if cps else '- Hechos especificos del caso a verificar'}

## Evidencias probables
{chr(10).join('- '+e for e in ev)}

## Simulacion compatible (perfil trabajador)
{sc}

## Simulacion no compatible (perfil trabajador)
{sn}

## Simulacion dudosa (perfil trabajador)
{sd}

## Respuesta base de PAZ (perfil trabajador)
{rp_t}

## Respuesta base de PAZ (perfil empresa)
{rp_e}

## Estado de aprobacion
- estado_fenomenologico: pendiente
- aprobado_por: [pendiente]
"""
    (DIR_FENO/f"{tid}.md").write_text(ff, encoding="utf-8")
    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} fichas fenomenologicas redactadas", flush=True)
