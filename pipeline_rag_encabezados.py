# -*- coding: utf-8 -*-
"""Pipeline RAG mejorado: Markdown limpio -> chunks por encabezados -> embeddings."""

import json
import os
import pathlib
import re

os.environ["SENTENCE_TRANSFORMERS_MODEL"] = "paraphrase-multilingual-MiniLM-L12-v2"

import tiktoken
from chunknorris.parsers import MarkdownParser
from chunknorris.chunkers import MarkdownChunker
from chunknorris.pipelines import BasePipeline
from sentence_transformers import SentenceTransformer

SRC_MD = pathlib.Path("guia-laboral-2026.md")
CLEAN_MD = pathlib.Path("guia-laboral-2026-limpio.md")
OUT = pathlib.Path("chunks_embeddings_encabezados.jsonl")

# --- 1. Limpiar el Markdown: pies de pagina y numeros de pagina sueltos ---
print("PASO 1/4: limpiando Markdown (pies de pagina, numeros sueltos)...", flush=True)
FOOTER = re.compile(r"^\*?\*?Gui\u0301a Laboral 2026\. Gerencie\.com\*?\*?\s*$", re.IGNORECASE)
PAGE_NUM = re.compile(r"^\d{1,4}\s*$")

limpias = 0
lineas_out = []
for linea in SRC_MD.read_text(encoding="utf-8").splitlines():
    if FOOTER.match(linea.strip()) or PAGE_NUM.match(linea.strip()):
        limpias += 1
        continue
    lineas_out.append(linea)
CLEAN_MD.write_text("\n".join(lineas_out), encoding="utf-8")
print(f"  -> {limpias:,} lineas de ruido eliminadas -> {CLEAN_MD}", flush=True)

# --- 2. Chunking por encabezados con chunknorris ---
print("PASO 2/4: chunking por encabezados (chunknorris)...", flush=True)
enc = tiktoken.encoding_for_model("text-embedding-3-large")
chunker = MarkdownChunker(
    max_headers_to_use="h4",
    max_chunk_word_count=150,
    hard_max_chunk_word_count=300,
    min_chunk_word_count=15,
    hard_max_chunk_token_count=512,
    tokenizer=enc,
)
pipe = BasePipeline(MarkdownParser(), chunker)
chunks = pipe.chunk_file(str(CLEAN_MD))
print(f"  -> {len(chunks):,} chunks por encabezado (con contexto de seccion)", flush=True)

# --- 3. Embeddings multilingues ---
print("PASO 3/4: embeddings (paraphrase-multilingual-MiniLM-L12-v2)...", flush=True)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
texts = [c.get_text() for c in chunks]
vectores = model.encode(texts, show_progress_bar=False, batch_size=64)
print(f"  -> {len(vectores):,} vectores de {vectores.shape[1]} dimensiones", flush=True)

# --- 4. Guardar JSONL con metadatos ---
print("PASO 4/4: guardando JSONL...", flush=True)
def _header_text(h):
    """Extrae texto limpio de un encabezado MarkdownLine (# **Titulo** -> Titulo)."""
    raw = getattr(h, "text", str(h))
    return re.sub(r"^#{1,6}\s*", "", raw).strip().strip("*")


with OUT.open("w", encoding="utf-8") as f:
    for i, (c, v) in enumerate(zip(chunks, vectores)):
        headers_objs = c.headers if hasattr(c, "headers") else []
        headers_clean = [_header_text(h) for h in headers_objs]
        content_objs = c.content if hasattr(c, "content") and isinstance(c.content, list) else []
        content_text = "\n".join(getattr(line, "text", str(line)) for line in content_objs) or c.get_text()
        reg = {
            "chunk_id": i,
            "text": c.get_text(),
            "content": content_text,
            "headers": headers_clean,
            "section_path": " > ".join(headers_clean),
            "end_page": getattr(c, "end_page", None),
            "token_count": len(enc.encode(c.get_text())),
            "embedding": v.tolist(),
        }
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
print(f"LISTO -> {OUT} ({OUT.stat().st_size:,} bytes)", flush=True)

# --- Muestra ---
print("\n===== MUESTRA DE 3 CHUNKS (con contexto de seccion) =====", flush=True)
for i in (10, len(chunks) // 2, len(chunks) - 5):
    c = chunks[i]
    headers_objs = c.headers if hasattr(c, "headers") else []
    headers_clean = [_header_text(h) for h in headers_objs]
    path = " > ".join(headers_clean)
    preview = " ".join(c.get_text().split())[:350]
    print(f"\n--- chunk #{i} | seccion: {path} ---", flush=True)
    print(preview, flush=True)
