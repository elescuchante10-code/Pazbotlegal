# -*- coding: utf-8 -*-
"""F1: Normaliza la jerarquia de titulos Markdown y extrae tablas del PDF como HTML estructurado."""
import pathlib, re, pymupdf

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
MD_IN = pathlib.Path("guia-laboral-2026-limpio.md")
MD_OUT = pathlib.Path("guia-laboral-2026-normalizado.md")
DIR_TABLAS = pathlib.Path("rag_laboral/01_fuente_original/tablas_html")
DIR_TABLAS.mkdir(parents=True, exist_ok=True)

# --- 1. Normalizar jerarquia Markdown ---
print("Normalizando jerarquia Markdown...", flush=True)
content = MD_IN.read_text(encoding="utf-8")

# Unificar lineas de titulo: asegurar espacio tras # y normalizar niveles
# pymupdf4llm usa # para titulos; normalizamos multiples # y espacios
def norm_heading(m):
    hashes = m.group(1)
    texto = m.group(2).strip()
    # Limitar a 6 niveles maximo
    nivel = min(len(hashes), 6)
    return "#" * nivel + " " + texto

content = re.sub(r"^(#{1,6})\s*(.+)$", norm_heading, content, flags=re.MULTILINE)
# Eliminar lineas vacias excesivas (mas de 2 seguidas)
content = re.sub(r"\n{3,}", "\n\n", content)
# Normalizar espacios multiples dentro de lineas (no en codigo)
content = re.sub(r"[ \t]{2,}", " ", content)

MD_OUT.write_text(content, encoding="utf-8")
print(f"Markdown normalizado: {MD_OUT} ({len(content.splitlines())} lineas)", flush=True)

# --- 2. Extraer tablas del PDF como HTML ---
print("Extrayendo tablas del PDF como HTML...", flush=True)
doc = pymupdf.open(SRC_PDF)
tablas_extraidas = 0
indice_tablas = []

for pnum in range(doc.page_count):
    page = doc[pnum]
    try:
        tabs = page.find_tables()
    except Exception:
        continue
    for ti, tab in enumerate(tabs):
        try:
            filas = tab.extract()
        except Exception:
            continue
        if not filas or len(filas) < 2:
            continue
        # Construir HTML
        html = ['<table border="1" cellpadding="4" cellspacing="0">']
        # Primera fila como header
        header = filas[0]
        html.append("<thead><tr>")
        for c in header:
            html.append(f"<th>{str(c or '').strip()}</th>")
        html.append("</tr></thead><tbody>")
        for fila in filas[1:]:
            html.append("<tr>")
            for c in fila:
                txt = str(c or "").strip().replace("\n", " ")
                html.append(f"<td>{txt}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        html_str = "\n".join(html)
        # Guardar tabla
        tid = f"tabla_p{pnum+1:04d}_{ti+1}"
        fp = DIR_TABLAS / f"{tid}.html"
        fp.write_text(html_str, encoding="utf-8")
        indice_tablas.append({"id": tid, "pagina": pnum+1, "filas": len(filas)})
        tablas_extraidas += 1

# Indice de tablas
import json
(DIR_TABLAS / "indice_tablas.json").write_text(
    json.dumps(indice_tablas, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Tablas extraidas como HTML: {tablas_extraidas} en {DIR_TABLAS}", flush=True)
print("F1 COMPLETO", flush=True)
