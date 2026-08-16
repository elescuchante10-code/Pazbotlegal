# -*- coding: utf-8 -*-
"""Pipeline RAG con pdfstract: PDF -> chunks -> embeddings (espanol)."""

import json
import os
import pathlib
import sys

os.environ["SENTENCE_TRANSFORMERS_MODEL"] = "paraphrase-multilingual-MiniLM-L12-v2"

from pdfstract import PDFStract

SRC = "1767265164_Guia-Laboral-Gerencie.com-2026.pdf"
OUT = pathlib.Path("chunks_embeddings.jsonl")

p = PDFStract()

print("PASO 1/3: extrayendo texto del PDF (pymupdf4llm)...", flush=True)
texto = p.convert(SRC, library="pymupdf4llm")
if not isinstance(texto, str):
    texto = texto.get("text", "") if isinstance(texto, dict) else str(texto)
print(f"  -> {len(texto):,} caracteres extraidos", flush=True)

print("PASO 2/3: chunking (recursive, 512 tokens, overlap 50)...", flush=True)
res = p.chunk(texto, chunker="recursive", chunk_size=512, chunk_overlap=50)
chunks = res["chunks"] if isinstance(res, dict) and "chunks" in res else res
texts = [c["text"] if isinstance(c, dict) else str(c) for c in chunks]
print(f"  -> {len(texts):,} chunks generados", flush=True)

print("PASO 3/3: embeddings (paraphrase-multilingual-MiniLM-L12-v2)...", flush=True)
vectores = p.embed_texts(texts, model="sentence-transformers")
dim = len(vectores[0]) if vectores else 0
print(f"  -> {len(vectores):,} vectores de {dim} dimensiones", flush=True)

with OUT.open("w", encoding="utf-8") as f:
    for i, (c, v) in enumerate(zip(chunks, vectores)):
        reg = {
            "chunk_id": c.get("chunk_id", i) if isinstance(c, dict) else i,
            "text": texts[i],
            "token_count": c.get("token_count") if isinstance(c, dict) else None,
            "embedding": v,
        }
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")

print(f"LISTO -> {OUT} ({OUT.stat().st_size:,} bytes)", flush=True)

print("\n===== MUESTRA DE 3 CHUNKS =====", flush=True)
for i in (0, len(texts) // 2, len(texts) - 1):
    preview = " ".join(texts[i].split())[:400]
    print(f"\n--- chunk #{i} ({len(vectores[i])} dims) ---", flush=True)
    print(preview, flush=True)
