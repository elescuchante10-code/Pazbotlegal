# -*- coding: utf-8 -*-
"""Helpers fenomenologicos compactos."""

def gen_como_se_vive(titulo, cps, perfil="trabajador"):
    t = titulo.lower().strip().rstrip(".")
    if perfil == "empresa":
        M_E = {
            "contrato realidad": "Un contratista me demanda diciendo que es mi empleado, pero el firmo contrato de servicios, usa sus medios y no tiene horario fijo. Tengo miedo de que me condenen a prestaciones retroactivas.",
            "subordinacion": "Me acusan de subordinacion por dar instrucciones, pero dirigir un trabajo no es lo mismo que subordinar. Necesito probar que hubo autonomia.",
            "despido": "Tengo que terminar un contrato. Quiero hacerlo bien, con justa causa y procedimiento, para no pagar indemnizacion. O el trabajador se fue y me exige reintegro.",
            "salario": "Tengo dudas sobre que pagos constituyen salario y cuales no, para no pagar mas prestaciones de las debidas y evitar demandas.",
            "jornada": "Necesito organizar los turnos y las horas extras sin pasarme de los limites legales, para evitar sanciones del ministerio.",
            "horas extras": "El trabajador alega horas extras que no autorice ni registre. Necesito probar la jornada real para no pagar lo que no se trabajo.",
            "acoso laboral": "Me acusan de acoso por exigir resultados. Necesito diferenciar el poder de direccion del acoso y proteger a la empresa.",
            "prima": "Tengo que calcular y pagar la prima en las fechas correctas, proporcional al tiempo servido, para evitar demandas.",
            "cesantias": "Debo consignar cesantias a tiempo y en la base correcta, o el trabajador puede reclamar indemnizacion moratoria.",
            "vacaciones": "El trabajador pide vacaciones continuas y yo necesito programarlas para no parar la operacion. Quiero saber mis obligaciones.",
            "pension": "Tengo que afiliar y aportar a pension. Si no lo hago, soy solidariamente responsable. Necesito cumplir para evitar sanciones.",
            "incapacidad": "El trabajador va a incapacidad y no se si debo pagarla, desde cuando, y si puedo reemplazarlo temporalmente.",
            "seguridad social": "Debo afiliar al trabajador a EPS, pension y ARL. Si no lo hago, asumo la responsabilidad solidaria.",
        }
        for c in cps:
            if c in M_E: return M_E[c]
        return f"Como empresa tengo obligaciones y riesgos sobre {t}. Necesito saber que debo hacer para cumplir y evitar sanciones o demandas."
    M = {
        "contrato realidad": "Mi contrato dice que soy independiente, pero me tratan como empleado: tengo horario, me dan ordenes y no puedo faltar.",
        "subordinacion": "Me dan ordenes todos los dias, me controlan el horario y no puedo decidir como trabajar.",
        "despido": "Me echaron sin motivo, sin carta, sin explicacion. O me renunciaron solito.",
        "salario": "Me pagan menos de lo acordado, no me dan recibos, o me descuentan cosas que no entiendo.",
        "jornada": "Trabajo muchas horas y no me pagan las extras, o me cambian el turno sin avisar.",
        "horas extras": "Trabajo horas extras y no me las pagan o no me dan el recargo.",
        "acoso laboral": "Mi jefe me grita, me humilla, me aisla. Llego a casa llorando y con miedo.",
        "prima": "No me pagaron mi prima, o me pagaron menos de lo que era.",
        "cesantias": "No me consignaron mis cesantias, o me las consignaron mal.",
        "vacaciones": "No me quieren dar mis vacaciones, o no me las quieren pagar.",
        "pension": "Me enferme y no me quieren pagar la incapacidad, o la EPS me demora meses.",
        "incapacidad": "Me enferme y no me quieren pagar la incapacidad.",
        "seguridad social": "No me afiliaron a EPS ni pension, o me afiliaron tarde.",
    }
    for c in cps:
        if c in M: return M[c]
    return f"Tengo una duda o un problema con {t} y no se si tengo derecho ni como reclamar."

def gen_que_suele_ocurrir(cps):
    h = []
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        h += ["El trabajador firma contrato de servicios pero recibe ordenes y horario.",
               "El empleador denomina la relacion como civil para evitar prestaciones."]
    if "despido" in cps:
        h += ["El empleador despide sin carta ni causa ni procedimiento.",
              "El trabajador descubre que la liquidacion no incluye indemnizacion."]
    if "salario" in cps:
        h.append("El trabajador recibe pago sin recibo, con descuentos no autorizados o por debajo del minimo.")
    if "jornada" in cps or "horas extras" in cps:
        h.append("El trabajador labora horas extras sin recargo ni autorizacion del inspector.")
    if "acoso laboral" in cps:
        h += ["El trabajador sufre maltrato repetitivo o discriminacion.",
              "La empresa no actua o no tiene comite de convivencia."]
    if "prima" in cps:
        h.append("El trabajador llega al corte y no recibe el pago de prima.")
    if not h:
        h = ["El trabajador o empleador enfrenta una situacion del tema y surge una duda sobre sus derechos."]
    return h

def gen_actores(cps):
    a = ["trabajador", "empleador"]
    if "acoso laboral" in cps: a.append("comite de convivencia")
    if "pension" in cps or "incapacidad" in cps: a += ["EPS", "fondo de pensiones"]
    if "despido" in cps: a.append("inspector de trabajo")
    if "seguridad social" in cps: a += ["EPS", "ARL"]
    return list(dict.fromkeys(a))

def gen_secuencia(cps):
    if "despido" in cps:
        return "1) Relacion vigente. 2) Surge conflicto o causa. 3) Empleador despide o trabajador renuncia. 4) Trabajador cuestiona la terminacion. 5) Liquidacion, demanda, indemnizacion o reintegro."
    if "acoso laboral" in cps:
        return "1) Ambiente normal. 2) Conductas de acoso. 3) Trabajador las sufre. 4) Queja al comite. 5) Medidas, sancion o renuncia motivada."
    if "salario" in cps:
        return "1) Trabajador recibe salario. 2) Descubre descuentos o pago incompleto. 3) Pregunta al empleador. 4) Derecho de peticion o demanda. 5) Pago de diferencias o morosidad."
    if "jornada" in cps or "horas extras" in cps:
        return "1) Jornada ordinaria. 2) Se exige horas extras o turnos sin recargo. 3) Trabajador las labora. 4) Reclama el pago. 5) Pago de recargos o conflicto."
    return "1) Situacion normal. 2) Surge duda o conflicto. 3) Reaccion. 4) Queja o reclamo. 5) Resolucion segun reglas."

def gen_epoje(cps):
    e = ["No presumir que la denominacion del contrato define su naturaleza sin verificar hechos.",
         "No concluir que cualquier instruccion demuestra subordinacion sin evaluar su intensidad."]
    if "salario" in cps: e.append("No asumir que todo pago constituye salario sin verificar si es liberalidad.")
    if "despido" in cps: e.append("No presumir despido injusto sin verificar justa causa y procedimiento.")
    if "acoso laboral" in cps: e.append("No dar por probado el acoso sin verificar periodicidad y prueba.")
    if "prima" in cps or "cesantias" in cps: e.append("No calcular el monto sin verificar tiempo servido y base salarial.")
    return e[:4]

def gen_evidencias(cps):
    ev = ["Contrato de trabajo o servicios", "Desprendibles de pago"]
    if "jornada" in cps or "horas extras" in cps: ev.append("Registros de jornada y turnos")
    if "salario" in cps: ev.append("Comprobantes de pago y deducciones")
    if "despido" in cps: ev.append("Carta de despido o liquidacion")
    if "acoso laboral" in cps: ev.append("Correos, chats y quejas al comite")
    if "contrato realidad" in cps: ev.append("Correos con ordenes y registros de horario")
    ev += ["Correos electronicos y mensajes", "Testimonios de companeros"]
    return list(dict.fromkeys(ev))[:7]

def gen_sim_compat(cps, titulo):
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        return ("Carolina debe cumplir horario, pedir permiso, seguir ordenes diarias, trabajar personalmente "
                "y aceptar sanciones. Recibe pago mensual. Aunque su contrato dice prestacion de servicios, "
                "la acumulacion de control y remuneracion periodica indica subordinacion real. La regla aplica.")
    if "despido" in cps:
        return ("Juan lleva 3 anos, sin fuero, despedido sin justa causa ni procedimiento. La indemnizacion procede.")
    if "salario" in cps:
        return ("Maria devenga salario minimo y cumple jornada. Le pagan por debajo del minimo. La diferencia procede.")
    if "jornada" in cps or "horas extras" in cps:
        return ("Pedro labora 10 horas diarias sin autorizacion ni recargo. Las horas extras proceden.")
    if "acoso laboral" in cps:
        return ("Laura sufre gritos y aislamiento por 8 meses. Presenta queja con correos y testigos. Constituye acoso.")
    if "prima" in cps:
        return ("Carlos llevo 8 meses al 30 de junio. Tiene derecho a prima proporcional. La regla aplica.")
    return f"Trabajador que cumple los elementos de {titulo.lower()}. La regla aplica y la respuesta es afirmativa."

def gen_sim_no_compat(cps, titulo):
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        return ("Daniel determina su horario, usa sus medios, puede delegar y solo entrega resultados. "
                "Hay autonomia significativa. Se aproxima a prestacion civil. La regla no aplica.")
    if "despido" in cps:
        return ("Ana es despedida con justa causa, proceso verbal, carta y descargos. Hubo procedimiento legal. No procede indemnizacion.")
    if "salario" in cps:
        return ("Carlos recibe bonificacion anual por liberalidad, no pactada ni periodica. No es salario (art. 128 CST).")
    if "jornada" in cps:
        return ("Sofia trabaja por turnos de 3 semanas. Un dia hace 10 horas pero el promedio no excede 48. No hay extras.")
    return f"Caso semejante donde faltan elementos centrales de {titulo.lower()}. La regla no aplica."

def gen_sim_dudosa(cps, titulo):
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        return ("Javier tiene contrato de servicios, recibe ordenes y reportes semanales, pero puede organizar su horario "
                "y trabajar desde casa. No hay control fijo pero si exigencia de resultados. Admite dos lecturas. "
                "Requiere verificar intensidad del control, exclusividad y potestad sancionatoria.")
    if "despido" in cps:
        return ("Maria fue despedida. El empleador alega justa causa pero la carta es vaga y el procedimiento tuvo irregularidades. "
                "Admite dos lecturas. Requiere verificar pruebas y procedimiento.")
    if "salario" in cps:
        return ("Pedro recibe pago mensual fijo llamado 'apoyo economico', sin recibo ni clausula. Podria ser salario "
                "o apoyo voluntario. Requiere verificar periodicidad y obligatoriedad.")
    return (f"Caso con indicadores a favor y en contra de {titulo.lower()}. Depende de hechos decisivos a verificar. "
            "Requiere analisis adicional.")

def gen_respuesta_paz(titulo, cps, rsc):
    base = f"La situacion se enmarca en {titulo.lower()}. "
    if any(c in cps for c in ["contrato realidad","subordinacion"]):
        base += ("La denominacion del contrato no define la naturaleza. Los hechos presentan indicadores "
                 "que requieren verificacion: control de horario, forma de ejecucion, permisos y consecuencias "
                 "del incumplimiento. Se requiere contrastar el contrato con la realidad del servicio. ")
    elif "despido" in cps:
        base += "La terminacion genera derechos segun causa y antiguedad. Se requiere verificar la justa causa, el procedimiento y la antiguedad. "
    elif "salario" in cps:
        base += "Se requiere verificar la naturaleza del pago (salario o liberalidad) y el monto respecto al minimo. "
    elif "acoso laboral" in cps:
        base += "Se requiere verificar la periodicidad, intencionalidad y prueba del acoso. "
    if rsc == "alto":
        base += "Dado el nivel de riesgo, se requiere verificacion con fuentes oficiales y revision juridica."
    else:
        base += "Se necesita el dato decisivo que falte para dar una respuesta precisa."
    return base


# --- Mapeo de perfil por bloque tematico ---
PERFIL_POR_BLOQUE = {
    "Contrato de trabajo": "ambos",
    "Jornada y descansos": "ambos",
    "Salario y pagos": "ambos",
    "Prestaciones sociales": "ambos",
    "Seguridad social": "ambos",
    "Despido y terminacion": "ambos",
    "Estabilidad y fueros": "ambos",
    "Acoso laboral y convivencia": "ambos",
    "Trabajo de mujeres y familia": "ambos",
    "Menores y aprendices": "ambos",
    "Trabajadores especiales": "ambos",
    "Sindicatos y negociacion colectiva": "ambos",
    "Procedimiento laboral": "ambos",
    "Inspeccion y sanciones": "ambos",
    "Teletrabajo y plataformas": "ambos",
    "Trabajo domestico": "ambos",
    "Sector publico": "ambos",
    "Pensiones y jubilacion": "ambos",
    "Reforma laboral 2026": "ambos",
    "Complementos e historicos": "ambos",
}

def gen_perfil(bloque, titulo):
    """Devuelve el perfil predominante del tema."""
    t = titulo.lower()
    if any(p in t for p in ["obligaciones del empleador","prohibiciones al empleador","sanciones al empleador","registro de trabajadores"]):
        return "empresa"
    if any(p in t for p in ["derechos del trabajador","prohibiciones al trabajador","obligaciones del trabajador","derechos del trabajador"]):
        return "trabajador"
    return PERFIL_POR_BLOQUE.get(bloque, "ambos")


def gen_respuesta_paz_perfil(titulo, cps, rsc, perfil):
    """Respuesta PAZ diferenciada por perfil del consultante."""
    base = f"La situacion se enmarca en {titulo.lower()}. "
    if perfil == "trabajador":
        if any(c in cps for c in ["contrato realidad","subordinacion"]):
            base += ("Aunque su contrato diga otra cosa, lo que cuenta es la realidad del servicio. "
                     "Si hay horario, ordenes, control y pago, podria existir relacion laboral. "
                     "Conserve correos, marcaciones y testigos. ")
        elif "despido" in cps:
            base += ("Si lo despedieron sin justa causa ni procedimiento, podria tener derecho a indemnizacion. "
                     "Solicite la carta de despido y conserve la liquidacion. ")
        elif "salario" in cps:
            base += ("Si le pagan por debajo del minimo o con descuentos no autorizados, podria reclamar la diferencia. "
                     "Conserve los desprendibles. ")
        elif "acoso laboral" in cps:
            base += ("Si sufre maltrato persistente, presente queja al comite de convivencia con correos y testigos. "
                     "Tiene derecho a medidas correctivas. ")
        else:
            base += "Conserve los documentos del caso para evaluar sus derechos. "
    else:  # empresa
        if any(c in cps for c in ["contrato realidad","subordinacion"]):
            base += ("La denominacion del contrato no la protege si los hechos demuestran subordinacion. "
                     "Revise si hay horario, ordenes y control. Si los hay, considere regularizar la relacion. ")
        elif "despido" in cps:
            base += ("Para terminar el contrato sin indemnizacion, documente la justa causa y siga el procedimiento. "
                     "Si no hay justa causa, calcule la indemnizacion segun antiguedad. ")
        elif "salario" in cps:
            base += ("Verifique que pagos constituyen salario (art. 127 CST) y cuales son liberalidades (art. 128 CST) "
                     "para calcular correctamente las prestaciones. ")
        elif "acoso laboral" in cps:
            base += ("Diferencie el poder de direccion del acoso. Implemente el comite de convivencia y actue ante quejas. "
                     "La inaccion puede generar responsabilidad. ")
        else:
            base += "Verifique sus obligaciones y documente el cumplimiento para evitar sanciones. "
    if rsc == "alto":
        base += "Dado el riesgo, se requiere verificacion con fuentes oficiales y revision juridica."
    else:
        base += "Se necesita el dato decisivo que falte para dar una respuesta precisa."
    return base
