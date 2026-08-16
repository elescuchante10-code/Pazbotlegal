# -*- coding: utf-8 -*-
"""F2: Metadatos completos, deduplicacion, prefijos de contexto (Contextual Retrieval) y HyQ."""
import json, pathlib, re, hashlib

CHUNKS = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_por_problema_juridico.jsonl")
OUT = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_enriquecidos.jsonl")

# Metadatos globales del documento
DOC_META = {
    "autor": "Gerencie.com",
    "editor": "Gerencie.com",
    "fecha_creacion": "2026",
    "fecha_ultima_actualizacion": "2026",
    "departamento": "Legal - Derecho Laboral",
    "tipo_documento": "guia_explicativa_secundaria",
    "fuente_original": "Guia Laboral 2026. Gerencie.com",
    "url_fuente": "",
}

def gen_prefijo_contexto(c):
    """Contextual Retrieval (Anthropic style): prefijo que situa el chunk en el documento global."""
    tema = c.get("tema", "")
    bloque = c.get("bloque", "")
    pags = c.get("paginas", [])
    pstr = str(pags[0]) if len(pags)==1 else f"{pags[0]}-{pags[-1]}" if pags else ""
    ruta = " > ".join(c.get("ruta_tematica", []))
    return (f"En la Guia Laboral 2026 de Gerencie.com (fuente secundaria explicativa), "
            f"seccion '{tema}' dentro del bloque '{bloque}' ({ruta}), paginas {pstr}. "
            f"Este fragmento explica el tema y debe leerse como parte de esa seccion.")

def gen_hyq(c):
    """Genera 3 preguntas hipoteticas que el chunk responde (HyQ)."""
    tema = c.get("tema", "").lower().rstrip(".")
    t = tema
    return [
        f"¿Que dice la guia sobre {t}?",
        f"¿Cuales son los elementos o requisitos de {t}?",
        f"¿Que derechos u obligaciones genera {t} para el trabajador y la empresa?",
    ]

def hash_chunk(texto):
    return hashlib.md5(texto.encode("utf-8")).hexdigest()

print("Cargando chunks...", flush=True)
chunks = []
with CHUNKS.open(encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))
print(f"Cargados: {len(chunks)} chunks", flush=True)

# --- Metadatos completos + prefijo + HyQ + hash ---
print("Enriqueciendo chunks...", flush=True)
vistos = {}
deduplicados = 0
out = []
for c in chunks:
    # Metadatos de trazabilidad total
    for k, v in DOC_META.items():
        c.setdefault(k, v)
    # Prefijo de contexto (Contextual Retrieval)
    prefijo = gen_prefijo_contexto(c)
    c["contexto_prefijo"] = prefijo
    # Texto enriquecido = prefijo + texto (para embedding futuro)
    c["texto_enriquecido"] = prefijo + "\n\n" + c.get("texto", "")
    # Preguntas hipoteticas (HyQ)
    c["preguntas_hipoteticas"] = gen_hyq(c)
    # Hash del chunk para deduplicacion y change detection
    h = hash_chunk(c.get("texto", ""))
    c["chunk_hash"] = h
    # Deduplicacion
    if h in vistos:
        deduplicados += 1
        continue
    vistos[h] = True
    out.append(c)

with OUT.open("w", encoding="utf-8") as f:
    for c in out:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Chunks enriquecidos: {len(out)} (deduplicados: {deduplicados})", flush=True)
print(f"Salida: {OUT}", flush=True)
print("F2 COMPLETO")
