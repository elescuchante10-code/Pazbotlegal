# -*- coding: utf-8 -*-
"""Convierte la Guia Laboral 2026 (PDF) a Markdown legible con pymupdf4llm."""

import pathlib

import pymupdf4llm

SRC = "1767265164_Guia-Laboral-Gerencie.com-2026.pdf"
DST = pathlib.Path("guia-laboral-2026.md")
PAGINAS = 1169
PASO = 100

partes = []
for inicio in range(0, PAGINAS, PASO):
    fin = min(inicio + PASO, PAGINAS)
    md = pymupdf4llm.to_markdown(SRC, pages=list(range(inicio, fin)))
    partes.append(md)
    print(f"PROGRESO {fin}/{PAGINAS}", flush=True)

DST.write_text("\n".join(partes), encoding="utf-8")
print(f"LISTO -> {DST} ({DST.stat().st_size} bytes)", flush=True)
