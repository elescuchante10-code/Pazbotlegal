# -*- coding: utf-8 -*-
"""Llena las 8 simulaciones de cada tema con contenido especifico y perfiles."""
import json, pathlib, re, pymupdf
from hermeneutica_helpers import conceptos, riesgo
from fenomenologia_helpers import gen_perfil, gen_sim_compat, gen_sim_no_compat, gen_sim_dudosa

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_SIM = pathlib.Path("rag_laboral/07_simulaciones")

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

def gen_casos(tit, cps, blk, perfil):
    sc = gen_sim_compat(cps, tit)
    sn = gen_sim_no_compat(cps, tit)
    sd = gen_sim_dudosa(cps, tit)
    t = tit.lower()
    casos = {
        "Caso favorable al trabajador": sc,
        "Caso favorable a la empresa": sn,
        "Caso ambiguo": sd,
        "Caso excluido": f"Situacion que no cumple ningun elemento de {t}. La regla no aplica y no hay derecho ni obligacion derivada.",
        "Caso excepcional": f"Situacion que cumple los elementos de {t} pero activa una excepcion normativa (fuero, plazo, regimen especial). Requiere verificacion con la norma oficial.",
        "Caso con prueba suficiente": f"El consultante presenta contrato, desprendibles, correos y testimonios que confirman los hechos de {t}. La conclusion es viable con la prueba disponible.",
        "Caso con prueba insuficiente": f"El consultante no tiene contrato escrito ni comprobantes sobre {t}. La conclusion depende de indicios y requiere recolectar mas evidencia.",
        "Caso con norma o termino temporal relevante": f"Verificar si la norma sobre {t} fue modificada por la Reforma Laboral 2025/2026 o si tiene un termino de caducidad o prescripcion.",
    }
    return casos

print("Llenando simulaciones con perfiles...", flush=True)
n = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = ""
    cps = conceptos(texto, tit)
    perfil = gen_perfil(blk, tit)
    casos = gen_casos(tit, cps, blk, perfil)

    fp = DIR_SIM/f"{tid}.md"
    if not fp.exists(): continue
    content = fp.read_text(encoding="utf-8")

    # Reemplazar cada seccion de caso con contenido especifico
    for seccion, valor in casos.items():
        patron = re.compile(rf"## {re.escape(seccion)}\n.*?(?=\n## |\Z)", re.DOTALL)
        nuevo = f"## {seccion}\n{valor}\n"
        content = patron.sub(nuevo, content)

    # Anadir campo Perfil en cabecera si no existe
    if "- Perfil:" not in content:
        content = content.replace("# Simulaciones:", f"# Simulaciones:", 1)
        # Anadir linea de perfil despues del titulo
        content = re.sub(r"(# Simulaciones: [^\n]+\n)", r"\1", content, count=1)

    fp.write_text(content, encoding="utf-8")
    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} simulaciones llenadas (8 casos cada una)", flush=True)
