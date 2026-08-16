# -*- coding: utf-8 -*-
"""Helpers de analisis hermeneutico para redactar fichas."""
import re

def oraciones_clave(texto, n=8):
    ors = re.split(r"(?<=[.!?])\s+", texto)
    pat = [r"debe",r"tiene derecho",r"se entiende",r"se considera",r"se presume",
           r"obligacion",r"procede",r"no constituye",r"constituye",r"articulo",
           r"ley",r"corte",r"siempre que",r"cuando",r"salvo"]
    out = []
    for o in ors:
        o = o.strip()
        if 30 <= len(o) <= 450 and any(re.search(p,o.lower()) for p in pat):
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

def riesgo(titulo, bloque):
    t = (titulo+" "+bloque).lower()
    if any(w in t for w in ["acoso","despido","terminacion","indemnizacion","estabilidad","fuero","maternidad","discapacidad","liquidacion"]): return "alto"
    if any(w in t for w in ["salario","jornada","horas extras","recargo","prima","cesantias","vacaciones","seguridad social","pension","contrato","prestaciones"]): return "medio"
    return "bajo"

MAPA_FIN = {
    "subordinacion": "la proteccion del trabajador frente al abuso de poder del empleador",
    "remuneracion": "la garantia del sustento del trabajador mediante contraprestacion economica",
    "salario": "la garantia de la remuneracion minima y la dignidad del trabajador",
    "jornada": "la salud del trabajador y el limite al aprovechamiento de su tiempo",
    "horas extras": "el equilibrio entre la productividad y la salud del trabajador",
    "recargo": "la compensacion justa por el sacrificio de horarios adversos",
    "prima": "la participacion del trabajador en las utilidades de la empresa",
    "cesantias": "la proteccion del trabajador frente al desempleo",
    "vacaciones": "el descanso y la salud mental del trabajador",
    "indemnizacion": "la reparacion del trabajador frente a un despido injusto",
    "despido": "la seguridad juridica en la terminacion del contrato",
    "estabilidad": "la proteccion del trabajador frente al despido arbitrario",
    "fuero": "la proteccion de trabajadores en situacion de vulnerabilidad",
    "acoso laboral": "la dignidad y la integridad moral del trabajador",
    "contrato realidad": "la primacia de la realidad sobre las formas contractuales",
    "contrato de servicios": "la claridad sobre la naturaleza de la relacion civil o laboral",
    "pension": "la proteccion del trabajador en la vejez o invalidez",
    "seguridad social": "la proteccion integral del trabajador frente a riesgos",
    "liquidacion": "la transparencia y completitud en la terminacion del contrato",
    "periodo de prueba": "la libertad de las partes para evaluar la relacion laboral",
}

def gen_finalidad(cps, bloque, titulo):
    partes = [MAPA_FIN[c] for c in cps if c in MAPA_FIN]
    if not partes:
        partes = [f"la regulacion adecuada de {titulo.lower()} dentro del marco laboral"]
    base = "Protege " + partes[0]
    if len(partes) > 1: base += ", asi como " + " y ".join(partes[1:])
    base += f". En el contexto de {bloque.lower()}, busca equilibrar los intereses del trabajador y del empleador."
    return base

def gen_interp_principal(ors, cps, titulo):
    if not ors:
        return f"La interpretacion mas consistente es que {titulo.lower()} se rige por las reglas del Codigo Sustantivo del Trabajo, aplicando el principio de primacia de la realidad sobre las formas."
    base = "El significado juridico mas consistente es: " + ors[0][:300].rstrip(".")
    if len(ors) >= 2: base += ". Ademas, " + ors[1][:200].lower().rstrip(".")
    base += ". Esta interpretacion aplica cuando concurren los elementos normativos señalados."
    return base

def gen_interp_alt(cps):
    a = []
    if any(c in cps for c in ["subordinacion","contrato realidad","contrato de servicios"]):
        a.append("Cambia si el trabajador tiene autonomia de horario, metodos y lugar, sin control permanente: la relacion podria ser civil, no laboral.")
    if "salario" in cps:
        a.append("Cambia si los pagos son liberalidades ocasionales o viaticos (art. 128 CST), no salario.")
    if "jornada" in cps or "horas extras" in cps:
        a.append("Cambia si la jornada es por turnos: el limite se calcula como promedio de tres semanas, no diariamente.")
    if "despido" in cps or "terminacion" in cps:
        a.append("Cambia si hay justa causa comprobada con procedimiento legal: no procede indemnizacion. Tambien si el trabajador renuncia voluntariamente.")
    if "estabilidad" in cps or "fuero" in cps:
        a.append("Cambia si el trabajador tiene fuero (maternidad, sindical, discapacidad): el despido requiere autorizacion del inspector de trabajo.")
    if "prima" in cps or "cesantias" in cps:
        a.append("Cambia segun el tiempo servido: si el contrato termina antes del semestre o ano, aplica pago proporcional.")
    if not a:
        a.append("La interpretacion varia segun las circunstancias especificas y excepciones normativas del tema.")
    return a

def gen_supuestos_inc(cps, titulo):
    inc = []
    if any(c in cps for c in ["subordinacion","contrato realidad"]):
        inc.append("Trabajador con ordenes directas, horario fijo, permisos para ausentarse y trabajo personal.")
        inc.append("Trabajador con pago mensual, sin importar el nombre del contrato.")
    if "salario" in cps: inc.append("Trabajador que devenga salario minimo o superior cumpliendo jornada completa.")
    if "jornada" in cps: inc.append("Trabajador que labora mas de 8 horas diarias o 48 semanales con autorizacion.")
    if "despido" in cps: inc.append("Trabajador despedido sin justa causa con mas de un ano de antiguedad.")
    if "prima" in cps: inc.append("Trabajador con mas de 6 meses al 30 de junio o 31 de diciembre.")
    if "acoso laboral" in cps: inc.append("Trabajador que sufre maltrato, persecucion o discriminacion repetitiva.")
    if not inc:
        inc.append(f"Casos que cumplen los elementos y condiciones de la guia para {titulo.lower()}.")
    return inc

def gen_supuestos_exc(cps, titulo):
    exc = []
    if any(c in cps for c in ["subordinacion","contrato realidad"]):
        exc.append("Contratista independiente con autonomia de horario, medios y delegacion.")
        exc.append("Contratista que solo entrega un resultado, sin control sobre el proceso.")
    if "salario" in cps: exc.append("Pagos ocasionales por liberalidad que no constituyen salario.")
    if "jornada" in cps: exc.append("Trabajador por turnos cuyo promedio semanal no excede 48 horas.")
    if "despido" in cps:
        exc.append("Despido con justa causa comprobada segun el articulo 7 del CST.")
        exc.append("Renuncia voluntaria sin causa imputable al empleador.")
    if "prima" in cps: exc.append("Trabajador con menos de un mes al corte (no genera derecho proporcional en algunos casos).")
    if not exc:
        exc.append(f"Casos que no cumplen los elementos señalados para {titulo.lower()}.")
    return exc

def gen_hechos_decisivos(cps, titulo):
    hd = []
    if any(c in cps for c in ["subordinacion","contrato realidad"]):
        hd.append("Intensidad del control: horario, lugar, metodo y permisos vs solo coordinacion de resultados.")
        hd.append("Exclusividad: prestacion personal vs posibilidad de delegar.")
        hd.append("Remuneracion: pago fijo periodico vs variable dependiente de resultados.")
    if "salario" in cps: hd.append("Naturaleza del pago: contraprestacion obligatoria (salario) vs liberalidad.")
    if "jornada" in cps: hd.append("Sistema de jornada: ordinaria, turnos, o promedio semanal.")
    if "despido" in cps:
        hd.append("Existencia o no de justa causa y su comprobacion.")
        hd.append("Antiguedad del trabajador (determina la indemnizacion).")
    if "estabilidad" in cps:
        hd.append("Existencia de fuero y autorizacion del inspector de trabajo.")
    if not hd:
        hd.append(f"Hechos especificos del caso que determinan si {titulo.lower()} aplica.")
    return hd


def gen_conclusion_paz_trabajador(titulo, cps, oc, blk):
    """Conclusion hermeneutica para PAZ desde la perspectiva del trabajador."""
    base = f"Como trabajador, sobre {titulo.lower()}: "
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        base += ("si los hechos demuestran horario, ordenes, control y pago periodico, podria existir relacion laboral "
                 "aunque el contrato diga otra cosa. Conserve correos, marcaciones y testigos para reclamar prestaciones.")
    elif "despido" in cps:
        base += ("si lo despedieron sin justa causa ni procedimiento, podria tener derecho a indemnizacion. "
                 "Solicite la carta de despido y conserve la liquidacion.")
    elif "salario" in cps:
        base += ("si le pagan por debajo del minimo o con descuentos no autorizados, podria reclamar la diferencia. "
                 "Conserve los desprendibles.")
    elif "jornada" in cps or "horas extras" in cps:
        base += ("si trabaja horas extras sin recargo, podria reclamar el pago. Conserve registros de jornada y turnos.")
    elif "acoso laboral" in cps:
        base += ("si sufre maltrato persistente, presente queja al comite de convivencia con correos y testigos. "
                 "Tiene derecho a medidas correctivas.")
    elif "prima" in cps or "cesantias" in cps or "vacaciones" in cps:
        base += "verifique el monto y la fecha de pago. Si no le pagaron, podria reclamar la prestacion."
    elif "pension" in cps or "incapacidad" in cps:
        base += "verifique la afiliacion y los aportes. Si no le pagan, podria reclamar ante la EPS o el fondo."
    else:
        base += "verifique sus derechos con los documentos del caso y consulte la norma oficial."
    base += " Esta lectura requiere contraste con la fuente normativa."
    return base


def gen_conclusion_paz_empresa(titulo, cps, oc, blk):
    """Conclusion hermeneutica para PAZ desde la perspectiva de la empresa."""
    base = f"Como empresa, sobre {titulo.lower()}: "
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        base += ("la denominacion del contrato no la protege si los hechos demuestran subordinacion. "
                 "Revise si hay horario, ordenes y control. Si los hay, considere regularizar la relacion para evitar condenas.")
    elif "despido" in cps:
        base += ("para terminar sin indemnizacion, documente la justa causa y siga el procedimiento. "
                 "Si no hay justa causa, calcule la indemnizacion segun antiguedad.")
    elif "salario" in cps:
        base += ("verifique que pagos constituyen salario (art. 127 CST) y cuales son liberalidades (art. 128 CST) "
                 "para calcular correctamente las prestaciones y evitar demandas.")
    elif "jornada" in cps or "horas extras" in cps:
        base += ("organice los turnos dentro de los limites legales y autorice las horas extras por escrito. "
                 "Lleve registros de jornada para probar el cumplimiento.")
    elif "acoso laboral" in cps:
        base += ("diferencie el poder de direccion del acoso. Implemente el comite de convivencia y actue ante quejas. "
                 "La inaccion puede generar responsabilidad.")
    elif "prima" in cps or "cesantias" in cps or "vacaciones" in cps:
        base += "calcule y pague en las fechas correctas, proporcional al tiempo servido, para evitar demandas."
    elif "pension" in cps or "incapacidad" in cps:
        base += "afilie y aporte a tiempo. Si no lo hace, asume responsabilidad solidaria y sanciones."
    else:
        base += "verifique sus obligaciones y documente el cumplimiento para evitar sanciones o demandas."
    base += " Esta lectura requiere contraste con la fuente normativa."
    return base


def gen_perfil_herm(bloque, titulo):
    """Perfil predominante para fichas hermeneuticas."""
    t = titulo.lower()
    if any(p in t for p in ["obligaciones del empleador","prohibiciones al empleador","sanciones al empleador","registro de trabajadores"]):
        return "empresa"
    if any(p in t for p in ["derechos del trabajador","prohibiciones al trabajador","obligaciones del trabajador"]):
        return "trabajador"
    return "ambos"
