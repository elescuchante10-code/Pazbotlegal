# -*- coding: utf-8 -*-
"""Redacta todas las fichas con contenido real extraido de la guia."""
import json, pathlib, re, pymupdf

SRC_PDF = pathlib.Path("1767265164_Guia-Laboral-Gerencie.com-2026.pdf")
INV = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIRS = {
    "herm": pathlib.Path("rag_laboral/05_fichas_hermeneuticas"),
    "feno": pathlib.Path("rag_laboral/06_fichas_fenomenologicas"),
    "verif": pathlib.Path("rag_laboral/04_fuentes_oficiales"),
    "sim": pathlib.Path("rag_laboral/07_simulaciones"),
    "form": pathlib.Path("rag_laboral/08_formulas_y_calculos"),
}
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

CALCULO = ["prima","cesantias","vacaciones","liquidacion","indemnizacion","salario",
           "recargo","horas extras","auxilio","interes","aportes","cotizacion","pension","incapacidad"]

# Cargar inventario
inventario = []
with INV.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))
for i, e in enumerate(inventario):
    fin = inventario[i+1]["pagina"]-1 if i+1 < len(inventario) else 1169
    e["_pags"] = list(range(e["pagina"], fin+1))
print(f"Inventario: {len(inventario)} temas", flush=True)

# Extraer texto por pagina
print("Extrayendo texto...", flush=True)
doc = pymupdf.open(SRC_PDF)
tp = {}
for p in range(doc.page_count):
    t = doc[p].get_text("text")
    t = re.sub(r"Gu\u00eda Laboral 2026\. Gerencie\.com\s*\n?","",t)
    t = re.sub(r"^\s*\d{1,4}\s*$","",t,flags=re.MULTILINE)
    tp[p+1] = t.strip()
print(f"Paginas: {len(tp)}", flush=True)

# --- Helpers ---
def oraciones_clave(texto, n=5):
    ors = re.split(r"(?<=[.!?])\s+", texto)
    pat = [r"debe",r"tiene derecho",r"se entiende",r"se considera",r"se presume",
           r"obligacion",r"procede",r"no constituye",r"constituye",r"articulo",r"ley",r"corte"]
    out = []
    for o in ors:
        o = o.strip()
        if 30 <= len(o) <= 400 and any(re.search(p,o.lower()) for p in pat):
            out.append(o)
        if len(out) >= n: break
    return out

def citas_norm(texto):
    c = []
    for m in re.finditer(r"art[i\u00ed]culo\s+(\d+[A-Za-z]?[-\d]*)", texto, re.I): c.append(f"Articulo {m.group(1)}")
    for m in re.finditer(r"ley\s+(\d+\s+de\s+\d{4})", texto, re.I): c.append(f"Ley {m.group(1).strip()}")
    for m in re.finditer(r"(C-\d+|T-\d+|SU-\d+|radicaci[o\u00f3]n\s+\d+)", texto, re.I): c.append(m.group(0))
    for m in re.finditer(r"decreto\s+\d+", texto, re.I): c.append(m.group(0))
    if re.search(r"c[o\u00f3]digo sustantivo", texto, re.I): c.append("Codigo Sustantivo del Trabajo")
    return list(dict.fromkeys(c))[:10]

def conceptos(texto, titulo):
    t = (texto+" "+titulo).lower()
    cps = ["subordinacion","remuneracion","prestacion personal","salario","jornada",
           "horas extras","recargo","prima","cesantias","vacaciones","indemnizacion",
           "despido","renuncia","terminacion","estabilidad","fuero","periodo de prueba",
           "contrato realidad","contrato de servicios","acoso laboral","incapacidad",
           "pension","seguridad social","afiliacion","cotizacion","prestaciones","liquidacion"]
    return [c for c in cps if c in t][:8]

def actor(texto, titulo):
    t = (texto+" "+titulo).lower()
    a = []
    if any(w in t for w in ["trabajador","empleado","obrero"]): a.append("trabajador")
    if any(w in t for w in ["empleador","empresa","patron"]): a.append("empleador")
    return a or ["trabajador","empleador"]

def riesgo(titulo, bloque):
    t = (titulo+" "+bloque).lower()
    alto = ["acoso","despido","terminacion","indemnizacion","estabilidad","fuero","maternidad","discapacidad","liquidacion"]
    medio = ["salario","jornada","horas extras","recargo","prima","cesantias","vacaciones","seguridad social","pension","contrato","prestaciones"]
    if any(w in t for w in alto): return "alto"
    if any(w in t for w in medio): return "medio"
    return "bajo"

def tipo_contenido(texto, titulo):
    t = (texto+" "+titulo).lower()
    tp = []
    if any(w in t for w in ["formula","calculo","se calcula","se divide"]): tp.append("calculo")
    if any(w in t for w in ["sentencia","corte","jurisprudencia"]): tp.append("jurisprudencia")
    if any(w in t for w in ["articulo","ley","decreto","codigo","norma"]): tp.append("normativa")
    if any(w in t for w in ["ejemplo","supongamos","caso","situacion"]): tp.append("ejemplo")
    return tp or ["explicacion"]

# --- Generar fichas ---
print("Redactando fichas...", flush=True)
n = 0
for e in inventario:
    tid = e["topic_id"]; tit = e["titulo_normalizado"]; blk = e["bloque"]
    sub = e["subbloque"]; ruta = e["ruta_tematica"]; pags = e["_pags"] or [e["pagina"]]
    texto = "\n\n".join(tp.get(p,"") for p in pags).strip()
    if len(texto.split()) < 10: texto = f"[Contenido limitado. Paginas: {pags}]"
    oc = oraciones_clave(texto); cit = citas_norm(texto); cps = conceptos(texto, tit)
    act = actor(texto, tit); rsc = riesgo(tit, blk); tpc = tipo_contenido(texto, tit)
    lit = (texto[:1200]+"...") if len(texto)>1200 else texto
    pstr = str(pags[0]) if len(pags)==1 else f"{pags[0]}-{pags[-1]}"
    rstr = " > ".join(ruta)

    # FICHA HERMENEUTICA
    prob = (f"La guia aborda: {tit}. " if tit.startswith("\u00bf") else f"Regula el conflicto sobre {tit.lower()}. ")
    prob += f"Se enmarca en {blk.lower()}."
    tesis = (" ".join(oc[:2])[:600]) if oc else "La guia explica el tema sin tesis explicita. Requiere revision juridica."
    conc = f"Sobre {tit.lower()}, la guia senala que {oc[0][:200].lower().rstrip('.')}." if oc else f"La guia explica {tit.lower()}."
    conc += " Se recomienda contrastar con la norma oficial." if rsc!="alto" else " Requiere verificacion con fuentes oficiales y revision juridica."
    lims = []
    if not cit: lims.append("La guia no cita explicitamente la norma. Requiere verificacion normativa.")
    if "2025" in texto or "2026" in texto: lims.append("Contiene informacion temporal (2026) que requiere actualizacion anual.")
    lims.append("Borrador generado automaticamente. Requiere revision juridica antes de produccion.")

    fh = f"""# Ficha hermeneutica: {tit}

## Identificacion
- Tema: {tit}
- Capitulo (bloque): {blk}
- Subbloque: {sub}
- Paginas de la guia: {pstr}
- Fecha de vigencia: 2026
- Tipo de fuente: secundaria_explicativa
- topic_id: {tid}

## Problema regulado
{prob}

## Tesis interpretativa
{tesis}

## Contenido literal relevante
{lit}

## Contexto sistemtico
Se relaciona con: {rstr}. Conceptos clave: {', '.join(cps) if cps else 'no detectados'}.

## Finalidad
[Requiere redaccion del abogado sobre el derecho o interes que protege esta regulacion.]

## Interpretacion principal
[Requiere redaccion del abogado. La guia ofrece los elementos literales arriba.]

## Interpretaciones alternativas
[Requiere redaccion del abogado segun las excepciones y variaciones del tema.]

## Supuestos incluidos
[Requiere redaccion del abogado.]

## Supuestos excluidos
[Requiere redaccion del abogado.]

## Hechos decisivos
[Requiere redaccion del abogado.]

## Fuentes oficiales relacionadas
{chr(10).join('- '+c for c in cit) if cit else '- [pendiente de verificacion]'}

## Conclusion para PAZ
{conc}

## Limites
{chr(10).join('- '+l for l in lims)}

## Estado de aprobacion
- estado_hermeneutico: pendiente
- estado_revision_juridica: pendiente
- aprobado_por: [pendiente]
- fecha_aprobacion: [pendiente]
"""
    (DIRS["herm"]/f"{tid}.md").write_text(fh, encoding="utf-8")

    # FICHA FENOMOLOGICA
    epo = ["No presumir que la denominacion del contrato define su naturaleza sin verificar hechos.",
           "No concluir que cualquier instruccion demuestra subordinacion."]
    if "salario" in cps: epo.append("No asumir que todo pago constituye salario sin verificar su naturaleza.")
    if "despido" in cps or "terminacion" in cps: epo.append("No presumir justa causa sin verificar pruebas y procedimiento.")
    sim_c = f"Persona en situacion de '{tit.lower()}' que cumple los elementos de la guia. Respuesta afirmativa."
    sim_n = "Caso semejante pero faltan elementos centrales (autonomia, ausencia de remuneracion). Queda por fuera."
    sim_d = "Caso con indicadores a favor y en contra. Depende de hechos decisivos a verificar."
    resp_paz = (f"La situacion se relaciona con {tit.lower()}. La guia explica las reglas. "
                f"{'Requiere verificacion y revision juridica.' if rsc=='alto' else 'Se necesita el dato decisivo que falte.'}")
    sec = ("1) Relacion vigente. 2) Surge conflicto. 3) Reaccion. 4) Queja. 5) Desenlace.")
    if "acoso" in cps: sec = "1) Ambiente normal. 2) Conductas de acoso. 3) Trabajador las sufre. 4) Queja al comite. 5) Medidas o renuncia."
    ev = ["Contrato","Desprendibles de pago","Correos y chats","Testimonios"]
    if "jornada" in cps: ev.append("Registros de turnos")
    if "despido" in cps: ev.append("Carta de despido")

    ff = f"""# Ficha fenomenologica: {tit}

## Como se vive
{('Mi contrato dice una cosa pero la realidad es otra.' if 'contrato' in str(cps).lower() else 'Situacion cotidiana del trabajador o empresa frente a ' + tit.lower() + '.')}

## Que suele ocurrir
{('Trabajador recibe instrucciones, controles o pagos que generan duda sobre la naturaleza de la relacion.' if cps else 'Acontecimientos propios del tema ' + tit.lower() + '.')}

## Actores
{', '.join(act)}.

## Secuencia
{sec}

## Epoje
{chr(10).join('- '+e for e in epo)}

## Hechos decisivos
{chr(10).join('- '+c for c in cps) if cps else '- [requiere redaccion]'}

## Evidencias probables
{chr(10).join('- '+e for e in ev)}

## Simulacion compatible
{sim_c}

## Simulacion no compatible
{sim_n}

## Simulacion dudosa
{sim_d}

## Respuesta base de PAZ
{resp_paz}

## Estado de aprobacion
- estado_fenomenologico: pendiente
- aprobado_por: [pendiente]
"""
    (DIRS["feno"]/f"{tid}.md").write_text(ff, encoding="utf-8")

    # VERIFICACION NORMATIVA
    props = []
    for i, o in enumerate(oc[:3]):
        props.append(f"### claim_id: {tid}-{i+1:03d}\n- afirmacion_guia: {o[:200]}\n- pagina_guia: {pstr}\n- norma_citada: [pendiente]\n- resultado: pendiente")
    fv = f"""# Verificacion normativa: {tit}

## Proposiciones a verificar

{chr(10).join(props) if props else '### claim_id: '+tid+'-001\n- [sin proposiciones detectadas]'}

## Notas
- Inconsistencia editorial: pag 28 menciona Ley 2466 de 2025; pag 1161 menciona Ley 1466 de 2025.
- Toda cita debe verificarse en relatorias oficiales de la Corte Suprema y Corte Constitucional.
"""
    (DIRS["verif"]/f"{tid}.md").write_text(fv, encoding="utf-8")

    # SIMULACIONES (8 casos)
    fs = f"""# Simulaciones: {tit}

## Caso favorable al trabajador
{sim_c}

## Caso favorable a la empresa
{sim_n}

## Caso ambiguo
{sim_d}

## Caso excluido
Situacion que no cumple ningun elemento del tema. La regla no aplica.

## Caso excepcional
Situacion que cumple los elementos pero activa una excepcion normativa. Requiere verificacion.

## Caso con prueba suficiente
El trabajador presenta contrato, desprendibles y testimonios que confirman los hechos.

## Caso con prueba insuficiente
El trabajador no tiene contrato escrito ni comprobantes. La conclusion depende de indicios.

## Caso con norma o termino temporal relevante
{'Contiene informacion temporal 2026. Verificar vigencia.' if '2026' in texto else 'Verificar si la norma ha sido modificada.'}

## Estado
- estado_simulaciones: pendiente
- todas_ficticias: [pendiente]
"""
    (DIRS["sim"]/f"{tid}.md").write_text(fs, encoding="utf-8")

    # FORMULA (solo temas de calculo)
    if any(k in tit.lower() for k in CALCULO):
        ffo = f"""# Formula: {tit}

## Componente interpretativo
- concepto: {tit}
- cuando_procede: [pendiente]
- variables: {', '.join(cps) if cps else '[pendiente]'}
- excepciones: [pendiente]
- fuente: {', '.join(cit) if cit else '[pendiente]'}

## Componente deterministico
```yaml
concepto: "{tit}"
variables: [pendiente]
formula: "[pendiente]"
vigencia: "2026"
fuente_normativa: {', '.join(cit) if cit else '[pendiente]'}
```

## Pruebas
- [ ] Caso base aprobado
- estado_calculo: pendiente
"""
        (DIRS["form"]/f"{tid}.md").write_text(ffo, encoding="utf-8")

    n += 1
    if n % 200 == 0: print(f"  {n}/{len(inventario)}...", flush=True)

print(f"LISTO: {n} temas procesados", flush=True)
print(f"  Hermeneuticas: {len(list(DIRS['herm'].glob('*.md')))}", flush=True)
print(f"  Fenomenologicas: {len(list(DIRS['feno'].glob('*.md')))}", flush=True)
print(f"  Verificaciones: {len(list(DIRS['verif'].glob('*.md')))}", flush=True)
print(f"  Simulaciones: {len(list(DIRS['sim'].glob('*.md')))}", flush=True)
print(f"  Formulas: {len(list(DIRS['form'].glob('*.md')))}", flush=True)
