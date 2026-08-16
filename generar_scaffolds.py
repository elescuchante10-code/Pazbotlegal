# -*- coding: utf-8 -*-
"""Genera scaffolds de fichas hermeneuticas, fenomenologicas, verificacion normativa y formulas.

Crea un archivo por cada tema del inventario maestro, con la estructura vacia
definida en la especificacion (secciones 10-14). El abogado los redacta.
"""

import json
import pathlib

INVENTARIO = pathlib.Path("rag_laboral/02_inventario_cobertura/inventario_maestro.jsonl")
DIR_HERM = pathlib.Path("rag_laboral/05_fichas_hermeneuticas")
DIR_FENO = pathlib.Path("rag_laboral/06_fichas_fenomenologicas")
DIR_VERIF = pathlib.Path("rag_laboral/04_fuentes_oficiales")
DIR_FORM = pathlib.Path("rag_laboral/08_formulas_y_calculos")
DIR_SIM = pathlib.Path("rag_laboral/07_simulaciones")

for d in [DIR_HERM, DIR_FENO, DIR_VERIF, DIR_FORM, DIR_SIM]:
    d.mkdir(parents=True, exist_ok=True)

# Plantilla ficha hermeneutica (seccion 11)
TPL_HERM = """# Ficha hermeneutica: {titulo}

## Identificacion
- Tema: {titulo}
- Capitulo (bloque): {bloque}
- Subbloque: {subbloque}
- Paginas de la guia: {paginas}
- Fecha de vigencia: 2026
- Tipo de fuente: secundaria_explicativa
- topic_id: {topic_id}

## Problema regulado
[Explicacion del conflicto laboral que intenta resolver.]

## Tesis interpretativa
[Respuesta principal que se desprende del documento.]

## Contenido literal relevante
[Reglas, condiciones, excepciones y consecuencias explicadas por la guia.]

## Contexto sistemtico
[Relacion con otros capitulos, normas y conceptos.]

## Finalidad
[Derecho, equilibrio o interes que protege la regulacion.]

## Interpretacion principal
[Significado juridico mas consistente.]

## Interpretaciones alternativas
[Situaciones en las que la respuesta podria cambiar.]

## Supuestos incluidos
[Casos que normalmente ingresan en la regla.]

## Supuestos excluidos
[Casos que normalmente no ingresan.]

## Hechos decisivos
[Datos que modifican la interpretacion.]

## Fuentes oficiales relacionadas
[Normas y jurisprudencia que deben verificarse.]

## Conclusion para PAZ
[Explicacion clara y prudente para el usuario.]

## Limites
[Informacion faltante, controversias y necesidad de revision juridica.]

## Estado de aprobacion
- estado_hermeneutico: pendiente
- estado_revision_juridica: pendiente
- aprobado_por: [pendiente]
- fecha_aprobacion: [pendiente]
"""

# Plantilla ficha fenomenologica (seccion 12)
TPL_FENO = """# Ficha fenomenologica: {titulo}

## Como se vive
[Lenguaje cotidiano del trabajador o de la empresa.]

## Que suele ocurrir
[Acontecimientos observables y patrones frecuentes.]

## Actores
[Trabajador, empleador, jefe, companeros, contratante y autoridades.]

## Secuencia
[Inicio, evolucion, reaccion, queja y desenlace probable.]

## Epoje
[Conclusiones que PAZ debe suspender para no prejuzgar.]

## Hechos decisivos
[Circunstancias que permiten diferenciar escenarios.]

## Evidencias probables
[Contratos, desprendibles, correos, chats, turnos, testimonios y registros.]

## Simulacion compatible
[Caso que probablemente ingresa en la regla.]

## Simulacion no compatible
[Caso semejante que probablemente queda por fuera.]

## Simulacion dudosa
[Caso que admite mas de una interpretacion.]

## Respuesta base de PAZ
[Respuesta afirmativa y contextual antes de pedir informacion adicional.]

## Estado de aprobacion
- estado_fenomenologico: pendiente
- aprobado_por: [pendiente]
"""

# Plantilla verificacion normativa (seccion 10)
TPL_VERIF = """# Verificacion normativa: {titulo}

## Proposiciones a verificar

### claim_id: {topic_id}-001
- afirmacion_guia: [pendiente]
- pagina_guia: {paginas_str}
- norma_citada: [pendiente]
- articulo: [pendiente]
- fuente_oficial_url: [pendiente]
- fecha_verificacion: [pendiente]
- resultado: pendiente  # confirmada | confirmada_con_matiz | desactualizada | ambigua | error_editorial | pendiente
- texto_vigente: [pendiente]
- observacion_abogado: [pendiente]

## Notas
- Inconsistencia editorial conocida: pagina 28 menciona Ley 2466 de 2025; pagina 1161 menciona Ley 1466 de 2025.
- Toda cita debe verificarse en relatorias oficiales de la Corte Suprema y Corte Constitucional.
"""

# Plantilla formulas (seccion 14) - solo para temas de calculo
TPL_FORM = """# Formula: {titulo}

## Componente interpretativo
- concepto: {titulo}
- cuando_procede: [pendiente]
- variables: [pendiente]
- excepciones: [pendiente]
- fuente: [pendiente]
- informacion_faltante: [pendiente]

## Componente deterministico
```yaml
concepto: "{titulo}"
variables:
  - salario_base
  - dias_trabajados
formula: "(salario_base * dias_trabajados) / 360"
vigencia: "2026"
fuente_normativa: [pendiente]
reglas_especiales: [pendiente]
ejemplo_verificado: [pendiente]
```

## Pruebas unitarias
- [ ] Caso base aprobado por abogado
- [ ] Caso con topes aprobado
- [ ] Caso con redondeo aprobado
- estado_calculo: pendiente
"""

# Plantilla simulaciones (seccion 13)
TPL_SIM = """# Simulaciones: {titulo}

## Caso favorable al trabajador
[pendiente]

## Caso favorable a la empresa
[pendiente]

## Caso ambiguo
[pendiente]

## Caso excluido
[pendiente]

## Caso excepcional
[pendiente]

## Caso con prueba suficiente
[pendiente]

## Caso con prueba insuficiente
[pendiente]

## Caso con norma o termino temporal relevante
[pendiente]

## Estado
- estado_simulaciones: pendiente
- todas_ficticias: [pendiente - confirmar que ninguna simulacion usa datos reales]
"""

# Temas que requieren formula (seccion 14)
TEMAS_CALCULO = ["prima", "cesantias", "vacaciones", "liquidacion", "indemnizacion",
                 "salario", "recargo", "horas extras", "auxilio", "interes"]

# Cargar inventario
inventario = []
with INVENTARIO.open(encoding="utf-8") as f:
    for line in f:
        inventario.append(json.loads(line))

print(f"Generando scaffolds para {len(inventario)} temas...", flush=True)

herm = feno = verif = form = sim = 0
for entry in inventario:
    topic_id = entry["topic_id"]
    titulo = entry["titulo_normalizado"]
    bloque = entry["bloque"]
    subbloque = entry["subbloque"]
    paginas = entry["_paginas"] if "_paginas" in entry else [entry["pagina"]]
    paginas_str = ", ".join(str(p) for p in paginas[:5]) + ("..." if len(paginas) > 5 else "")

    vars_ = {"titulo": titulo, "bloque": bloque, "subbloque": subbloque,
             "paginas": paginas, "paginas_str": paginas_str, "topic_id": topic_id}

    # Ficha hermeneutica
    (DIR_HERM / f"{topic_id}.md").write_text(TPL_HERM.format(**vars_), encoding="utf-8")
    herm += 1

    # Ficha fenomenologica
    (DIR_FENO / f"{topic_id}.md").write_text(TPL_FENO.format(**vars_), encoding="utf-8")
    feno += 1

    # Verificacion normativa
    (DIR_VERIF / f"{topic_id}.md").write_text(TPL_VERIF.format(**vars_), encoding="utf-8")
    verif += 1

    # Simulaciones
    (DIR_SIM / f"{topic_id}.md").write_text(TPL_SIM.format(**vars_), encoding="utf-8")
    sim += 1

    # Formula (solo temas de calculo)
    if any(k in titulo.lower() for k in TEMAS_CALCULO):
        (DIR_FORM / f"{topic_id}.md").write_text(TPL_FORM.format(**vars_), encoding="utf-8")
        form += 1

print(f"  Fichas hermeneuticas: {herm}", flush=True)
print(f"  Fichas fenomenologicas: {feno}", flush=True)
print(f"  Verificaciones normativas: {verif}", flush=True)
print(f"  Simulaciones: {sim}", flush=True)
print(f"  Formulas (temas de calculo): {form}", flush=True)
print("LISTO", flush=True)
