# -*- coding: utf-8 -*-
"""Anade campo perfil y separa actor_principal en perfil_trabajador / perfil_empresa en chunks JSONL."""
import json, pathlib

CHUNKS = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_por_problema_juridico.jsonl")

def gen_perfil(bloque, titulo):
    t = titulo.lower()
    if any(p in t for p in ["obligaciones del empleador","prohibiciones al empleador","sanciones al empleador","registro de trabajadores"]):
        return "empresa"
    if any(p in t for p in ["derechos del trabajador","prohibiciones al trabajador","obligaciones del trabajador"]):
        return "trabajador"
    return "ambos"

n = 0
out = []
with CHUNKS.open(encoding="utf-8") as f:
    for line in f:
        c = json.loads(line)
        blk = c.get("bloque","")
        tit = c.get("tema","")
        perfil = gen_perfil(blk, tit)
        c["perfil"] = perfil
        # Separar actor_principal en dos campos booleanos por perfil
        ap = c.get("actor_principal", [])
        c["perfil_trabajador"] = "trabajador" in ap or perfil in ("trabajador","ambos")
        c["perfil_empresa"] = "empleador" in ap or perfil in ("empresa","ambos")
        out.append(c)
        n += 1

with CHUNKS.open("w", encoding="utf-8") as f:
    for c in out:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

# Resumen de distribucion de perfiles
from collections import Counter
dist = Counter(c["perfil"] for c in out)
print(f"LISTO: {n} chunks actualizados con campo perfil")
print(f"Distribucion: {dict(dist)}")
print(f"perfil_trabajador=True: {sum(1 for c in out if c['perfil_trabajador'])}")
print(f"perfil_empresa=True: {sum(1 for c in out if c['perfil_empresa'])}")
