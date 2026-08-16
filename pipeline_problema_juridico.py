# -*- coding: utf-8 -*-
"""Chunking por problema juridico: extrae texto por pagina del PDF y agrupa por tema.

Enfoque robusto (secciones 8 y 19):
1. Extrae texto de cada pagina del PDF con pymupdf
2. Mapea cada pagina al tema del inventario maestro (por pagina de inicio)
3. Agrupa el texto de cada tema y lo chunk-ea respetando oraciones y limite de tokens
4. Asigna metadatos enriquecidos (seccion 8) a cada chunk
5. Genera embeddings
"""

import json
import os
import pathlib
import re

os.environ["SENTENCE_TRANSFORMERS_MODEL"] = "paraphrase-multilingual-MiniLM-L12-v2"

import pymupdf
import tiktoken
from sentence_transformers import SentenceTransformer

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INVENTARIO = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
OUT = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_por_problema_juridico.jsonl")

# --- 1. Cargar inventario y calcular rangos de pagina por tema ---
inventario = []
with INVENTARIO.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))

# Cada tema va desde su pagina hasta la pagina del siguiente tema - 1
for i, entry in enumerate(inventario):
    pag_inicio = entry["pagina"]
    pag_fin = inventario[i + 1]["pagina"] - 1 if i + 1 < len(inventario) else 1169
    entry["_paginas"] = list(range(pag_inicio, pag_fin + 1))

print(f"Inventario: {len(inventario)} temas", flush=True)

# --- 2. Extraer texto de cada pagina del PDF ---
print("Extrayendo texto por pagina del PDF...", flush=True)
doc = pymupdf.open(SRC_PDF)
texto_por_pagina = {}
for p in range(doc.page_count):
    texto = doc[p].get_text("text")
    # Limpiar pie de pagina repetido y numero de pagina suelto
    texto = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?", "", texto)
    texto = re.sub(r"^\s*\d{1,4}\s*$", "", texto, flags=re.MULTILINE)
    texto_por_pagina[p + 1] = texto.strip()  # paginas son 1-indexed
print(f"Paginas extraidas: {len(texto_por_pagina)}", flush=True)

# --- 3. Agrupar texto por tema ---
print("Agrupando texto por tema juridico...", flush=True)
enc = tiktoken.encoding_for_model("text-embedding-3-large")
MAX_TOKENS = 512

chunks = []
temas_con_texto = 0
for entry in inventario:
    paginas = entry["_paginas"]
    texto_tema = "\n\n".join(texto_por_pagina.get(p, "") for p in paginas).strip()
    if len(texto_tema.split()) < 15:
        continue
    temas_con_texto += 1

    # Chunkear respetando oraciones y limite de tokens
    oraciones = re.split(r"(?<=[.!?])\s+", texto_tema)
    sub_textos = []
    actual = []
    actual_tokens = 0
    for oracion in oraciones:
        t = len(enc.encode(oracion))
        if actual_tokens + t > MAX_TOKENS and actual:
            sub_textos.append(" ".join(actual))
            actual = [oracion]
            actual_tokens = t
        else:
            actual.append(oracion)
            actual_tokens += t
    if actual:
        sub_textos.append(" ".join(actual))

    for j, sub in enumerate(sub_textos):
        if len(sub.split()) < 10:
            continue
        chunk = {
            "chunk_id": f"chunk_{len(chunks):04d}",
            "texto": sub,
            "token_count": len(enc.encode(sub)),
            # Metadatos enriquecidos (seccion 8)
            "documento": "Guia Laboral 2026",
            "tipo_fuente": "fuente secundaria explicativa",
            "tema": entry["titulo_normalizado"],
            "ruta_tematica": entry["ruta_tematica"],
            "bloque": entry["bloque"],
            "subbloque": entry["subbloque"],
            "topic_id": entry["topic_id"],
            "paginas": paginas,
            "actor_principal": ["trabajador", "empleador"],
            "sector": ["privado"],
            "vigencia_referencial": 2026,
            "requiere_verificacion_normativa": True,
            "estado_revision": "draft",
            "nivel_riesgo": "medio",
            "tipo_contenido": ["explicacion"],
            "sub_chunk_index": j,
            "sub_chunk_total": len(sub_textos),
        }
        chunks.append(chunk)

print(f"Temas con texto: {temas_con_texto}", flush=True)
print(f"Chunks por problema juridico: {len(chunks)}", flush=True)

# --- 4. Embeddings ---
print("Generando embeddings (CPU)...", flush=True)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
texts = [c["texto"] for c in chunks]
vectores = model.encode(texts, show_progress_bar=False, batch_size=64, device="cpu")
for i, v in enumerate(vectores):
    chunks[i]["embedding"] = v.tolist()
print(f"Embeddings: {len(vectores)} vectores de {vectores.shape[1]} dims", flush=True)

# --- 5. Guardar ---
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"LISTO -> {OUT} ({OUT.stat().st_size:,} bytes)", flush=True)

# --- 6. Resumen por bloque ---
from collections import Counter
por_bloque = Counter(c["bloque"] for c in chunks)
print("\nDistribucion de chunks por bloque tematico:", flush=True)
for bloque, n in por_bloque.most_common():
    print(f"  {n:5d}  {bloque}", flush=True)
