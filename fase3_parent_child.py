# -*- coding: utf-8 -*-
"""F3: Rechunking con estrategia Parent-Child + solapamiento 10-20% + 256-512 tokens.
- Parent: fragmento grande (~800 tokens) que se entrega al LLM.
- Child: fragmento pequeno (~200-256 tokens) para busqueda precisa.
- Solapamiento 15% entre childs.
"""
import json, pathlib, re, hashlib
import pymupdf

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
OUT = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child.jsonl")

DOC_META = {
    "autor": "Gerencie.com", "editor": "Gerencie.com",
    "fecha_creacion": "2026", "fecha_ultima_actualizacion": "2026",
    "departamento": "Legal - Derecho Laboral",
    "tipo_documento": "guia_explicativa_secundaria",
    "fuente_original": "Guia Laboral 2026. Gerencie.com",
}

# Tokenizador simple por palabras (aprox 1 token ~ 0.75 palabra en espanol)
def n_tokens(texto):
    return int(len(texto.split()) / 0.75)

def split_por_oraciones(texto, max_tokens, overlap_tokens):
    """Divide texto en sub-fragmentos por oraciones con solapamiento."""
    oraciones = re.split(r"(?<=[.!?])\s+", texto)
    oraciones = [o.strip() for o in oraciones if o.strip()]
    frags = []
    i = 0
    while i < len(oraciones):
        frag = []
        tok = 0
        j = i
        while j < len(oraciones) and tok < max_tokens:
            o = oraciones[j]
            ot = n_tokens(o)
            if tok + ot > max_tokens and frag:
                break
            frag.append(o)
            tok += ot
            j += 1
        if not frag:
            frag = [oraciones[i]]
            j = i + 1
        frags.append(" ".join(frag))
        # Solapamiento: retroceder para overlap
        if j >= len(oraciones):
            break
        # Calcular cuantas oraciones cubren overlap_tokens
        back = 0
        btok = 0
        k = j - 1
        while k > i and btok < overlap_tokens:
            btok += n_tokens(oraciones[k])
            back += 1
            k -= 1
        i = j - back if back > 0 else j
    return frags

# Cargar inventario
inventario = []
with INV.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))
for i, e in enumerate(inventario):
    fin = inventario[i+1]["pagina"]-1 if i+1 < len(inventario) else 1169
    e["_pags"] = list(range(e["pagina"], fin+1))

print("Extrayendo texto del PDF...", flush=True)
doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()

def gen_perfil(bloque, titulo):
    t = titulo.lower()
    if any(p in t for p in ["obligaciones del empleador","prohibiciones al empleador","sanciones al empleador","registro de trabajadores"]):
        return "empresa"
    if any(p in t for p in ["derechos del trabajador","prohibiciones al trabajador","obligaciones del trabajador"]):
        return "trabajador"
    return "ambos"

print("Construyendo chunks Parent-Child...", flush=True)
chunks = []
parent_id = 0
child_id = 0

for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    sub = e["subbloque"]; ruta = e["ruta_tematica"]; pags = e["_pags"] or [e["pagina"]]
    texto_tema = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto_tema.split()) < 10:
        continue
    perfil = gen_perfil(blk, tit)
    pstr = str(pags[0]) if len(pags)==1 else f"{pags[0]}-{pags[-1]}"

    # Parent: dividir el texto del tema en padres de ~800 tokens
    parents_texto = split_por_oraciones(texto_tema, max_tokens=800, overlap_tokens=0)
    for pi, ptxt in enumerate(parents_texto):
        parent_id += 1
        pid = f"parent_{parent_id:05d}"
        prefijo_parent = (f"En la Guia Laboral 2026 de Gerencie.com, seccion '{tit}' "
                          f"(bloque '{blk}', paginas {pstr}). Fragmento padre {pi+1}/{len(parents_texto)}.")
        parent = {
            "chunk_id": pid, "tipo": "parent", "texto": ptxt,
            "texto_enriquecido": prefijo_parent + "\n\n" + ptxt,
            "contexto_prefijo": prefijo_parent,
            "token_count": n_tokens(ptxt),
            "documento": "Guia Laboral 2026", "topic_id": tid,
            "tema": tit, "bloque": blk, "subbloque": sub,
            "ruta_tematica": ruta, "paginas": pags, "perfil": perfil,
            "perfil_trabajador": perfil in ("trabajador","ambos"),
            "perfil_empresa": perfil in ("empresa","ambos"),
            "parent_index": pi, "parent_total": len(parents_texto),
            "chunk_hash": hashlib.md5(ptxt.encode("utf-8")).hexdigest(),
            **DOC_META,
        }
        chunks.append(parent)
        # Child: dividir el parent en childs de ~256 tokens con overlap 15% (~38 tokens)
        childs = split_por_oraciones(ptxt, max_tokens=256, overlap_tokens=38)
        for ci, ctxt in enumerate(childs):
            child_id += 1
            cid = f"child_{child_id:06d}"
            prefijo_child = (f"En la Guia Laboral 2026, seccion '{tit}', este fragmento detalla "
                             f"un aspecto especifico del tema (paginas {pstr}).")
            child = {
                "chunk_id": cid, "tipo": "child", "texto": ctxt,
                "texto_enriquecido": prefijo_child + "\n\n" + ctxt,
                "contexto_prefijo": prefijo_child,
                "token_count": n_tokens(ctxt),
                "parent_id": pid, "documento": "Guia Laboral 2026", "topic_id": tid,
                "tema": tit, "bloque": blk, "subbloque": sub,
                "ruta_tematica": ruta, "paginas": pags, "perfil": perfil,
                "perfil_trabajador": perfil in ("trabajador","ambos"),
                "perfil_empresa": perfil in ("empresa","ambos"),
                "child_index": ci, "child_total": len(childs),
                "overlap_tokens": 38,
                "chunk_hash": hashlib.md5(ctxt.encode("utf-8")).hexdigest(),
                **DOC_META,
            }
            chunks.append(child)
    if parent_id % 500 == 0:
        print(f"  padres: {parent_id}, childs: {child_id}...", flush=True)

with OUT.open("w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

n_parent = sum(1 for c in chunks if c["tipo"]=="parent")
n_child = sum(1 for c in chunks if c["tipo"]=="child")
print(f"LISTO: {n_parent} parents + {n_child} childs = {len(chunks)} chunks total")
print(f"Salida: {OUT}")
print("F3 COMPLETO")
