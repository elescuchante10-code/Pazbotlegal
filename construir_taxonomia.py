# -*- coding: utf-8 -*-
"""Construye la taxonomia juridica con relaciones tipificadas (seccion 7).

Genera:
- rag_laboral/02_inventario_cobertura/taxonomia.json: arbol juridico + relaciones horizontales
- Define los 20 bloques con sus subtemas y las relaciones tipificadas
"""

import json
import pathlib

OUT = pathlib.Path("rag_laboral/02_inventario_cobertura/taxonomia.json")

# Tipos de relacion definidos en la seccion 7
TIPOS_RELACION = [
    "es_subtema_de",
    "es_variante_de",
    "se_diferencia_de",
    "requiere_verificar",
    "genera_consecuencia",
    "tiene_excepcion",
    "se_calcula_con",
    "se_prueba_con",
    "se_relaciona_con",
    "actualiza_a",
    "deroga_o_modifica",
    "aplica_a_actor",
    "aplica_a_sector",
]

# Arbol juridico: bloque -> subbloques -> temas (seccion 10 + ejemplo de la seccion 7)
TAXONOMIA = {
    "bloques": [
        {
            "bloque_id": "B01",
            "nombre": "Indicadores laborales 2026",
            "tipo_vigencia": "temporal",
            "vigente_desde": "2026-01-01",
            "vigente_hasta": "2026-12-31",
            "requiere_actualizacion_anual": True,
            "subbloques": [
                {"subbloque": "Salario minimo", "temas": ["Salario minimo 2026", "Auxilio de transporte 2026", "UVT 2026"]},
                {"subbloque": "Jornada maxima", "temas": ["Jornada maxima 2026"]},
            ],
        },
        {
            "bloque_id": "B02",
            "nombre": "Resumen de la reforma laboral",
            "tipo_vigencia": "mixta",
            "subbloques": [
                {"subbloque": "Ley 2466 de 2025", "temas": ["Contrato a termino fijo", "Jornada laboral", "Horas extras", "Recargo nocturno", "Procedimiento disciplinario", "Contrato de aprendizaje", "Plataformas digitales", "Trabajo domestico"]},
            ],
        },
        {
            "bloque_id": "B03",
            "nombre": "Contrato de trabajo",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Elementos del contrato", "temas": ["Prestacion personal", "Remuneracion", "Subordinacion", "Presuncion laboral"]},
                {"subbloque": "Contrato realidad", "temas": ["Requisitos del contrato realidad", "Carga de la prueba", "Consecuencias", "Mimetizacion o camuflaje"]},
                {"subbloque": "Modalidades", "temas": ["Termino indefinido", "Termino fijo", "Obra o labor", "Accidental o transitorio", "Aprendizaje", "Servicio domestico", "Docentes", "Conductores", "Medio tiempo", "Domicilio"]},
                {"subbloque": "Clausulas", "temas": ["Clausulas ineficaces", "Exclusividad", "No concurrencia", "Permanencia"]},
                {"subbloque": "Duracion", "temas": ["Periodo de prueba", "Preaviso", "Prorroga"]},
            ],
        },
        {
            "bloque_id": "B04",
            "nombre": "Obligaciones derivadas del contrato",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Obligaciones del empleador", "temas": ["Obligaciones especiales", "Prohibiciones al empleador"]},
                {"subbloque": "Poder disciplinario", "temas": ["Sanciones disciplinarias", "Procedimiento sancionatorio", "Descargos"]},
            ],
        },
        {
            "bloque_id": "B05",
            "nombre": "Acoso laboral",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Definicion y tipos", "temas": ["Acoso laboral", "Violencia laboral", "Discriminacion"]},
                {"subbloque": "Procedimiento", "temas": ["Queja por acoso", "Comite de convivencia", "Medidas correctivas"]},
            ],
        },
        {
            "bloque_id": "B06",
            "nombre": "Periodo de prueba",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Reglas generales", "temas": ["Duracion del periodo de prueba", "Prorroga", "Terminacion en periodo de prueba"]},
            ],
        },
        {
            "bloque_id": "B07",
            "nombre": "Terminacion del contrato",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Causas de terminacion", "temas": ["Justas causas", "Despido sin justa causa", "Renuncia", "Mutuo consentimiento", "Muerte del trabajador", "Liquidacion"]},
                {"subbloque": "Indemnizaciones", "temas": ["Indemnizacion por despido", "Indemnizacion moratoria"]},
                {"subbloque": "Renuncia motivada", "temas": ["Despido indirecto", "Renuncia por acoso"]},
            ],
        },
        {
            "bloque_id": "B08",
            "nombre": "Reintegro del trabajador",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Estabilidad reforzada", "temas": ["Estabilidad laboral reforzada", "Fuero de maternidad", "Fuero sindical", "Trabajadores con discapacidad", "Pre-pensionados"]},
                {"subbloque": "Reintegro", "temas": ["Procedimiento de reintegro", "Indemnizacion por reintegro"]},
            ],
        },
        {
            "bloque_id": "B09",
            "nombre": "Liquidacion del contrato",
            "tipo_vigencia": "mixta",
            "subbloques": [
                {"subbloque": "Componentes de liquidacion", "temas": ["Cesantias", "Interses de cesantias", "Prima de servicios", "Vacaciones", "Salario pendiente", "Indemnizacion"]},
                {"subbloque": "Formulas", "temas": ["Calculo de cesantias", "Calculo de prima", "Calculo de vacaciones", "Calculo de indemnizacion"]},
            ],
        },
        {
            "bloque_id": "B10",
            "nombre": "Trabajo en casa",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Teletrabajo", "temas": ["Teletrabajo", "Trabajo en casa", "Desconexion laboral"]},
            ],
        },
        {
            "bloque_id": "B11",
            "nombre": "Jornada laboral",
            "tipo_vigencia": "mixta",
            "subbloques": [
                {"subbloque": "Jornada ordinaria", "temas": ["Jornada maxima", "Jornada diurna", "Jornada nocturna", "Trabajo por turnos"]},
                {"subbloque": "Trabajo suplementario", "temas": ["Horas extras", "Recargo nocturno", "Recargo dominical", "Recargo festivo", "Limite del trabajo suplementario"]},
                {"subbloque": "Descansos", "temas": ["Descanso dominical", "Dias festivos", "Permisos", "Licencias"]},
            ],
        },
        {
            "bloque_id": "B12",
            "nombre": "Remuneracion del trabajo",
            "tipo_vigencia": "mixta",
            "subbloques": [
                {"subbloque": "Salario", "temas": ["Salario", "Salario minimo", "Pagos no salariales", "Salario en especie", "Comisiones", "Destajo", "Auxilio de transporte"]},
                {"subbloque": "Descuentos", "temas": ["Descuentos permitidos", "Retenciones", "Libretas"]},
            ],
        },
        {
            "bloque_id": "B13",
            "nombre": "Prestaciones sociales",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Prima de servicios", "temas": ["Prima de servicios", "Prima en servicio domestico", "Pago proporcional", "Fechas de pago"]},
                {"subbloque": "Cesantias", "temas": ["Cesantias", "Interses de cesantias", "Fondo de cesantias"]},
                {"subbloque": "Vacaciones", "temas": ["Vacaciones", "Vacaciones compensadas", "Pago de vacaciones"]},
                {"subbloque": "Dotacion", "temas": ["Dotacion de calzado y vestido"]},
            ],
        },
        {
            "bloque_id": "B14",
            "nombre": "Seguridad social",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Salud", "temas": ["EPS", "Afiliacion a salud", "Incapacidades", "Licencia de maternidad", "Licencia de paternidad"]},
                {"subbloque": "Pension", "temas": ["Pension", "Fondo de pensiones", "Invalidez", "Sobrevivientes"]},
                {"subbloque": "Riesgos laborales", "temas": ["ARL", "Accidente laboral", "Enfermedad profesional"]},
            ],
        },
        {
            "bloque_id": "B15",
            "nombre": "Aportes parafiscales",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Parafiscales", "temas": ["ICBF", "SENA", "Cajas de compensacion familiar"]},
            ],
        },
        {
            "bloque_id": "B16",
            "nombre": "Tercerizacion laboral",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Intermediacion", "temas": ["Intermediacion laboral", "Subcontratacion", "Solidaridad empresarial", "Responsabilidad solidaria"]},
            ],
        },
        {
            "bloque_id": "B17",
            "nombre": "Reglamento de trabajo",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Reglamento", "temas": ["Reglamento de trabajo", "Obligacion de elaborarlo", "Sanciones del reglamento"]},
            ],
        },
        {
            "bloque_id": "B18",
            "nombre": "Contrato de servicios",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Diferencia con contrato de trabajo", "temas": ["Contrato de servicios", "Independencia vs subordinacion", "Elementos excluyentes"]},
            ],
        },
        {
            "bloque_id": "B19",
            "nombre": "Otros aspectos relevantes del contrato",
            "tipo_vigencia": "permanente",
            "subbloques": [
                {"subbloque": "Certificacion y documentos", "temas": ["Certificacion laboral", "Carta de recomendacion", "Derecho de peticion"]},
                {"subbloque": "Prestamos", "temas": ["Prestamos al trabajador", "Descuentos por prestamo"]},
                {"subbloque": "Vivienda y otros", "temas": ["Subsidio de vivienda", "Capacitacion", "Estudios"]},
            ],
        },
        {
            "bloque_id": "B20",
            "nombre": "Complementos e historicos",
            "tipo_vigencia": "historico",
            "subbloques": [
                {"subbloque": "Historicos", "temas": ["Salario minimo historico", "Indicadores historicos"]},
            ],
        },
    ],
    "tipos_relacion": TIPOS_RELACION,
    # Relaciones horizontales de ejemplo (seccion 7)
    "relaciones_ejemplo": [
        {"origen": "Renuncia motivada", "relacion": "es_subtema_de", "destino": "Terminacion del contrato"},
        {"origen": "Renuncia motivada", "relacion": "se_relaciona_con", "destino": "Acoso laboral"},
        {"origen": "Renuncia motivada", "relacion": "se_relaciona_con", "destino": "Indemnizacion"},
        {"origen": "Renuncia motivada", "relacion": "se_prueba_con", "destino": "Carta de renuncia"},
        {"origen": "Renuncia motivada", "relacion": "se_relaciona_con", "destino": "Prescripcion o caducidad"},
        {"origen": "Contrato realidad", "relacion": "se_diferencia_de", "destino": "Contrato de servicios"},
        {"origen": "Contrato realidad", "relacion": "requiere_verificar", "destino": "Articulo 23 CST"},
        {"origen": "Contrato realidad", "relacion": "genera_consecuencia", "destino": "Prestaciones retroactivas"},
        {"origen": "Prima de servicios", "relacion": "se_calcula_con", "destino": "Formula prima"},
        {"origen": "Prima de servicios en servicio domestico", "relacion": "es_variante_de", "destino": "Prima de servicios"},
        {"origen": "Estabilidad reforzada", "relacion": "aplica_a_actor", "destino": "trabajador"},
        {"origen": "Estabilidad reforzada", "relacion": "aplica_a_sector", "destino": "privado"},
    ],
}

OUT.write_text(json.dumps(TAXONOMIA, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Taxonomia -> {OUT}", flush=True)
print(f"  Bloques: {len(TAXONOMIA['bloques'])}", flush=True)
print(f"  Tipos de relacion: {len(TAXONOMIA['tipos_relacion'])}", flush=True)
print(f"  Relaciones de ejemplo: {len(TAXONOMIA['relaciones_ejemplo'])}", flush=True)
