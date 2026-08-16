# -*- coding: utf-8 -*-
"""Integra la LEY 2466 DE 2025 (fuente primaria/norma oficial) al indice de
recuperacion, usando la MISMA logica Parent-Child ya construida.
- Lee el markdown de la ley.
- Divide por articulos (ARTICULO X°. <titulo>).
- Genera parents (~800 tokens) y childs (~256 tokens, overlap 15%).
- Metadatos: documento="Ley 2466 de 2025", tipo_documento="norma_oficial_primaria",
  perfil="ambos", locator por articulo.
- Genera embeddings de childs y los ANEXA a los archivos de indice existentes
  (sin alterar los chunks de la Guia ya indexados).
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import json, pathlib, re, hashlib

LEY_MD = pathlib.Path("rag_laboral/01_fuente_original/LEY 2466 DE 2025.md")
OUT_CHUNKS = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child.jsonl")
OUT_EMB = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child_embeddings.jsonl")

DOC_META = {
    "autor": "Congreso de Colombia",
    "editor": "Congreso de Colombia",
    "fecha_creacion": "2025",
    "fecha_ultima_actualizacion": "2025",
    "departamento": "Legal - Derecho Laboral",
    "tipo_documento": "norma_oficial_primaria",
    "fuente_original": "Ley 2466 de 2025",
}

def n_tokens(texto):
    return int(len(texto.split()) / 0.75)

def split_por_oraciones(texto, max_tokens, overlap_tokens):
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
        if j >= len(oraciones):
            break
        back = 0
        btok = 0
        k = j - 1
        while k > i and btok < overlap_tokens:
            btok += n_tokens(oraciones[k])
            back += 1
            k -= 1
        i = j - back if back > 0 else j
    return frags

# --- Parsear la ley en articulos ---
texto = LEY_MD.read_text(encoding="utf-8")
# Normalizar: unir lineas partidas dentro de un parrafo
texto = re.sub(r"-\n", "", texto)  # guiones de corte
texto = re.sub(r"(?<!\n)\n(?![A-ZÁÉÍÓÚÑ#•\-\n])", " ", texto)  # unir lineas sin separador

# Separar articulos: ARTICULO X°. <titulo>
patron_art = re.compile(r"(?=^ART[ÍI]CULO\s+\d+[°°]?\.)", re.MULTILINE)
partes = patron_art.split(texto)
articulos = []
for p in partes:
    p = p.strip()
    if not p:
        continue
    m = re.match(r"ART[ÍI]CULO\s+(\d+)[°°]?\.\s*(.*?)(?:\n|$)", p, re.IGNORECASE)
    if not m:
        continue
    num = m.group(1)
    titulo = m.group(2).strip().rstrip(".")
    cuerpo = p[m.end():].strip()
    if len(cuerpo.split()) < 5:
        continue
    articulos.append({"num": num, "titulo": titulo, "cuerpo": cuerpo})

print(f"Articulos detectados: {len(articulos)}", flush=True)
if not articulos:
    raise SystemExit("No se detectaron articulos. Revisar parseo.")

# --- Construir chunks Parent-Child (prefijo ley_ para evitar colisiones) ---
nuevos = []
pid_n = 0
cid_n = 0
for art in articulos:
    num = art["num"]; tit = art["titulo"]; cuerpo = art["cuerpo"]
    tema = f"Ley 2466 de 2025 - Art. {num}. {tit}".strip(". ")
    topic_id = f"LEY2466-ART{int(num):03d}"
    locator = f"Art. {num}"
    parents_texto = split_por_oraciones(cuerpo, max_tokens=800, overlap_tokens=0)
    for pi, ptxt in enumerate(parents_texto):
        pid_n += 1
        pid = f"ley_parent_{pid_n:05d}"
        prefijo_parent = (f"En la Ley 2466 de 2025, articulo {num} ({tit}). "
                          f"Norma oficial primaria. Fragmento padre {pi+1}/{len(parents_texto)}.")
        parent = {
            "chunk_id": pid, "tipo": "parent", "texto": ptxt,
            "texto_enriquecido": prefijo_parent + "\n\n" + ptxt,
            "contexto_prefijo": prefijo_parent,
            "token_count": n_tokens(ptxt),
            "documento": "Ley 2466 de 2025", "topic_id": topic_id,
            "tema": tema, "bloque": "Reforma Laboral 2025", "subbloque": "Ley 2466 de 2025",
            "ruta_tematica": ["Normativa", "Ley 2466 de 2025", f"Art. {num}"],
            "paginas": [], "articulo": locator, "perfil": "ambos",
            "perfil_trabajador": True, "perfil_empresa": True,
            "parent_index": pi, "parent_total": len(parents_texto),
            "chunk_hash": hashlib.md5(ptxt.encode("utf-8")).hexdigest(),
            **DOC_META,
        }
        nuevos.append(parent)
        childs = split_por_oraciones(ptxt, max_tokens=256, overlap_tokens=38)
        for ci, ctxt in enumerate(childs):
            cid_n += 1
            cid = f"ley_child_{cid_n:06d}"
            prefijo_child = (f"En la Ley 2466 de 2025, articulo {num} ({tit}), "
                             f"este fragmento detalla un aspecto especifico de la norma.")
            child = {
                "chunk_id": cid, "tipo": "child", "texto": ctxt,
                "texto_enriquecido": prefijo_child + "\n\n" + ctxt,
                "contexto_prefijo": prefijo_child,
                "token_count": n_tokens(ctxt),
                "parent_id": pid, "documento": "Ley 2466 de 2025", "topic_id": topic_id,
                "tema": tema, "bloque": "Reforma Laboral 2025", "subbloque": "Ley 2466 de 2025",
                "ruta_tematica": ["Normativa", "Ley 2466 de 2025", f"Art. {num}"],
                "paginas": [], "articulo": locator, "perfil": "ambos",
                "perfil_trabajador": True, "perfil_empresa": True,
                "child_index": ci, "child_total": len(childs),
                "overlap_tokens": 38,
                "chunk_hash": hashlib.md5(ctxt.encode("utf-8")).hexdigest(),
                **DOC_META,
            }
            nuevos.append(child)

n_parent = sum(1 for c in nuevos if c["tipo"] == "parent")
n_child = sum(1 for c in nuevos if c["tipo"] == "child")
print(f"Nuevos chunks Ley 2466: {n_parent} parents + {n_child} childs", flush=True)

# --- Anexar a chunks_parent_child.jsonl (sin sobrescribir) ---
with OUT_CHUNKS.open("a", encoding="utf-8") as f:
    for c in nuevos:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"Anexados {len(nuevos)} chunks a {OUT_CHUNKS}", flush=True)

# --- Generar embeddings de los childs y anexar a chunks_parent_child_embeddings.jsonl ---
from sentence_transformers import SentenceTransformer
print("Cargando modelo de embeddings (CPU)...", flush=True)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
childs_nuevos = [c for c in nuevos if c["tipo"] == "child"]
textos = [c["texto_enriquecido"] for c in childs_nuevos]
print(f"Embebiendo {len(childs_nuevos)} childs...", flush=True)
embs = model.encode(textos, batch_size=128, show_progress_bar=True, device="cpu", convert_to_numpy=True)
for c, emb in zip(childs_nuevos, embs):
    c["embedding"] = emb.tolist()
with OUT_EMB.open("a", encoding="utf-8") as f:
    for c in childs_nuevos:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"Anexados {len(childs_nuevos)} childs con embeddings a {OUT_EMB}", flush=True)
print("INTEGRACION LEY 2466 COMPLETA")
