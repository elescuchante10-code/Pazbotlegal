# -*- coding: utf-8 -*-
"""Genera embeddings para los child chunks (busqueda precisa)."""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import json, pathlib
from sentence_transformers import SentenceTransformer

CHUNKS = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child.jsonl")
OUT = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child_embeddings.jsonl")

print("Cargando modelo de embeddings (CPU)...", flush=True)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")

print("Cargando child chunks...", flush=True)
childs = []
with CHUNKS.open(encoding="utf-8") as f:
    for line in f:
        c = json.loads(line)
        if c.get("tipo") == "child":
            childs.append(c)
print(f"Childs a embebir: {len(childs)}", flush=True)

# Embebir usando texto_enriquecido (con prefijo de contexto)
textos = [c["texto_enriquecido"] for c in childs]
BATCH = 128
print("Generando embeddings...", flush=True)
embs = model.encode(textos, batch_size=BATCH, show_progress_bar=True, device="cpu", convert_to_numpy=True)

for c, emb in zip(childs, embs):
    c["embedding"] = emb.tolist()

print(f"Guardando {len(childs)} childs con embeddings...", flush=True)
with OUT.open("w", encoding="utf-8") as f:
    for c in childs:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")
print(f"LISTO: {OUT}")
