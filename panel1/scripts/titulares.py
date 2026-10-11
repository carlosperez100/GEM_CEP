# -*- coding: utf-8 -*-
"""Indicadores titulares: el Perú frente a los países miembros de la OCDE.
Lee salidas/ocde_peru_vs_ocde.csv y deja salidas/ocde_titulares.csv."""
import csv, io, os, sys
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "salidas")
rows = list(csv.DictReader(io.open(os.path.join(OUT, "ocde_peru_vs_ocde.csv"), encoding="utf-8-sig")))

# (grupo, flujo, medida, unidad, fichas que deben estar en «dimensiones», nombre en español, qué es mejor)
E = [
    ("Personal", "DF_NURSE", "HSE", "10P3HB", ["HEALTH_PROF=MINUQUAL", "STATUS=P"], "Enfermeras profesionales en ejercicio por 1 000 habitantes", "alto"),
    ("Personal", "DF_NURSE", "HSE", "10P3HB", ["HEALTH_PROF=MINU;", "STATUS=P"], "Personal de enfermería en ejercicio (profesional y asociado) por 1 000 habitantes", "alto"),
    ("Personal", "DF_REAC", "HSE", "10P3HB", ["HEALTH_PROF=PHYS", "STATUS=PA"], "Médicos profesionalmente activos por 1 000 habitantes", "alto"),
    ("Personal", "DF_MIDWIFE", "HSE", "10P3HB", ["STATUS=P"], "Obstetras en ejercicio por 1 000 habitantes", "alto"),
    ("Personal", "DF_REMUN", "AI", "USD_PPP", ["HEALTH_PROF=RINF"], "Ingreso anual de enfermeras de hospital asalariadas (dólares a paridad de poder adquisitivo)", "alto"),
    ("Recursos", "DF_HOSP_REAC", "HB", "10P3HB", ["OWNERSHIP_TYPE=_T"], "Camas hospitalarias por 1 000 habitantes", "alto", "Cobertura parcial: en la base de la OCDE el total del Perú (17 468 camas en 2025) coincide con sus camas públicas; la Superintendencia Nacional de Salud registra 40 593. No usar como titular."),
    ("Recursos", "DF_HOSP_REAC", "HBU_ICU_N", "10P5HB", [], "Camas de cuidados intensivos neonatales por 100 000 habitantes", "alto"),
    ("Recursos", "DF_HOSP_REAC", "HBU_ICU_P", "10P5HB", [], "Camas de cuidados intensivos pediátricos por 100 000 habitantes", "alto"),
    ("Recursos", "DF_HOSP_REAC", "MTU", "10P6HB", ["CT"], "Tomógrafos en hospitales por millón de habitantes", "alto", "Posible cobertura parcial del dato peruano: verificar antes de citar."),
    ("Recursos", "DF_HOSP_REAC", "MTU", "10P6HB", ["MRI"], "Resonadores magnéticos en hospitales por millón de habitantes", "alto", "Posible cobertura parcial del dato peruano: verificar antes de citar."),
    ("Gasto", "DF_SHA", "EXP_HEALTH", "PT_B1GQ", ["FINANCING_SCHEME=_T"], "Gasto corriente en salud como porcentaje del producto bruto interno", "alto"),
    ("Gasto", "DF_SHA", "EXP_HEALTH", "PT_EXP_HLTH", ["FINANCING_SCHEME=HF3"], "Gasto de bolsillo de los hogares como porcentaje del gasto corriente en salud", "bajo"),
    ("Gasto", "DF_SHA", "EXP_HEALTH", "PT_EXP_HLTH", ["FINANCING_SCHEME=HF1"], "Financiamiento público y obligatorio como porcentaje del gasto corriente en salud", "alto"),
    ("Cobertura", "DF_HEALTH_PROT", "HIC", "PT_POP", ["INSURANCE_TYPE=TPRIBASI"], "Población con cobertura de seguro de salud, pública o privada primaria (porcentaje)", "alto"),
    ("Resultados", "DF_HEALTH_STATUS", "LFEXP", "Y", ["AGE=Y0", "SEX=_T"], "Esperanza de vida al nacer (años)", "alto"),
    ("Resultados", "DF_HEALTH_STATUS", "INM", "DT_10P3BR_L", [], "Mortalidad infantil por 1 000 nacidos vivos", "bajo"),
    ("Resultados", "DF_HEALTH_STATUS", "NEOM", "DT_10P3BR_L", [], "Mortalidad neonatal por 1 000 nacidos vivos", "bajo"),
    ("Resultados", "DF_HEALTH_STATUS", "MATM", "DT_10P5BR_L", [], "Mortalidad materna por 100 000 nacidos vivos", "bajo"),
    ("Resultados", "DF_HEALTH_STATUS", "LOWB", "PT_BR_L", [], "Bajo peso al nacer (porcentaje de nacidos vivos)", "bajo"),
    ("Resultados", "DF_AM", "AVM", "DT_10P5HB", ["SEX=_T"], "Mortalidad evitable por 100 000 habitantes (estandarizada por edad)", "bajo"),
    ("Resultados", "DF_AM", "PREVM", "DT_10P5HB", ["SEX=_T"], "Mortalidad prevenible por 100 000 habitantes", "bajo"),
    ("Resultados", "DF_AM", "TRTM", "DT_10P5HB", ["SEX=_T"], "Mortalidad tratable por 100 000 habitantes", "bajo"),
    ("Prevención", "DF_KEY_INDIC", "IMMUN", "PT_CH_ELG_IM", ["DISEASE=DIPTETPERT"], "Vacunación contra difteria, tétanos y tos ferina (porcentaje de niños)", "alto"),
    ("Prevención", "DF_KEY_INDIC", "IMMUN", "PT_CH_ELG_IM", ["DISEASE=MEAS"], "Vacunación contra el sarampión (porcentaje de niños)", "alto"),
    ("Prevención", "DF_KEY_INDIC", "IMMUN", "PT_CH_ELG_IM", ["DISEASE=HEPB"], "Vacunación contra la hepatitis B (porcentaje de niños)", "alto"),
    ("Prevención", "DF_KEY_INDIC", "IMMUN", "PT_POP_Y_GE65", ["DISEASE=IFLU"], "Vacunación contra la influenza en personas de 65 años o más (porcentaje)", "alto"),
    ("Prevención", "DF_KEY_INDIC", "SCREEN", "PT_POP_SEX_AGE", [], "Tamizaje de cáncer de cuello uterino en mujeres de 20 a 69 años (porcentaje, por encuesta)", "alto", "Solo 12 países miembros tienen dato comparable por encuesta."),
    ("Uso", "DF_KEY_INDIC", "CONSULT", "CN_PS", [], "Consultas con dentista por persona al año", "alto", "La base solo trae para el Perú las consultas odontológicas."),
    ("Uso", "DF_KEY_INDIC", "DISCHARGE", "DSC_10P5PS", ["CARE_TYPE=_T", "FUNCTION=HC1"], "Egresos hospitalarios por 100 000 habitantes", "neutro", "Posible cobertura parcial del dato peruano: verificar antes de citar."),
    ("Uso", "DF_KEY_INDIC", "STAY", "D", [], "Estancia hospitalaria promedio (días)", "neutro"),
    ("Uso", "DF_KEY_INDIC", "OCC_RATE", "PT_BD_AV", [], "Ocupación de camas de agudos (porcentaje)", "neutro"),
    ("Uso", "DF_KEY_INDIC", "EXAM", "EXM_10P3PS", ["CT_SCAN"], "Tomografías por 1 000 habitantes", "neutro", "Posible cobertura parcial del dato peruano: verificar antes de citar."),
    ("Uso", "DF_KEY_INDIC", "EXAM", "EXM_10P3PS", ["MRI"], "Resonancias magnéticas por 1 000 habitantes", "neutro", "Posible cobertura parcial del dato peruano: verificar antes de citar."),
    ("Uso", "DF_KEY_INDIC", "PRC", "PRC_10P3BR_L", ["CM74_CAE", "MODE_PROVISION=_T"], "Cesáreas por 1 000 nacidos vivos", "bajo"),
    ("Espera", "DF_WAITING", "WAIT_MEDIAN", "D", ["CM131_138"], "Espera mediana para cirugía de catarata (días)", "bajo"),
    ("Espera", "DF_WAITING", "WAIT_MEDIAN", "D", ["CM8151_8153"], "Espera mediana para reemplazo de cadera (días)", "bajo"),
    ("Espera", "DF_WAITING", "WAIT_MEDIAN", "D", ["CM36_TRS"], "Espera mediana para angioplastia coronaria (días)", "bajo"),
    ("Espera", "DF_WAITING", "WAIT_MEDIAN", "D", ["CM603_606"], "Espera mediana para prostatectomía (días)", "bajo"),
    ("Espera", "DF_WAITING", "WAIT", "PT_PAT_WAIT_M_GT3", ["CM131_138"], "Pacientes que esperan más de tres meses por cirugía de catarata (porcentaje)", "bajo"),
    ("Calidad", "DF_HCQO", "OBSTVDWO", "10P2DLV", [], "Trauma obstétrico en parto vaginal sin instrumento (por 100 partos)", "bajo"),
    ("Calidad", "DF_HCQO", "OBSTVDWI", "10P2DLV", [], "Trauma obstétrico en parto vaginal con instrumento (por 100 partos)", "bajo"),
    ("Resultados", "DF_HEALTH_STATUS", "COMMD", "CS_10P5PS", ["DISEASE=HEPB"], "Incidencia de hepatitis B por 100 000 habitantes", "bajo"),
    ("Resultados", "DF_HEALTH_STATUS", "COMMD", "CS_10P5PS", ["DISEASE=AIDS"], "Incidencia de síndrome de inmunodeficiencia adquirida por 100 000 habitantes", "bajo"),
    ("Personal", "DF_REMUN", "AI", "USD_PPP", ["HEALTH_PROF=EMPLGENP"], "Ingreso anual de médicos generales asalariados (dólares a paridad de poder adquisitivo)", "alto"),
    ("Riesgo", "DF_HEALTH_LVNG", "SP_DS", "PT_POP", ["SEX=_T"], "Población que fuma a diario (porcentaje)", "bajo"),
    ("Riesgo", "DF_HEALTH_LVNG", "AC", "L_PS", [], "Consumo de alcohol (litros por persona al año)", "bajo"),
]

sal = []
for esp in E:
    grupo, fl, med, uni, fichas, nombre, mejor = esp[:7]
    nota = esp[7] if len(esp) > 7 else ""
    c = [r for r in rows if r["flujo"].endswith("@" + fl) and r["medida"] == med and r["unidad"] == uni and all(f in (r["dimensiones"] + ";") for f in fichas)]
    if not c:
        print("SIN SERIE:", nombre)
        continue
    c.sort(key=lambda r: (len(r["dimensiones"]), -int(r["ocde_n"])))
    r = c[0]
    per, media = float(r["peru"]), float(r["ocde_media"])
    pos, de = int(r["posicion_peru_de_menor_a_mayor"]), int(r["de"])
    if mejor == "alto":
        lugar = de - pos + 1            # 1 = el mejor
    elif mejor == "bajo":
        lugar = pos
    else:
        lugar = ""
    sal.append({"grupo": grupo, "indicador": nombre, "mejor_si": mejor, "peru": per, "peru_anio": r["peru_anio"], "ocde_media": media, "ocde_mediana": r["ocde_mediana"],
                "ocde_min": r["ocde_min"], "ocde_max": r["ocde_max"], "paises_ocde_con_dato": r["ocde_n"], "peru_sobre_media": r["peru_sobre_media"], "z": r["z"],
                "lugar_del_peru_1_es_el_mejor": lugar, "de": de, "chile": r["chl"], "colombia": r["col"], "costa_rica": r["cri"], "mexico": r["mex"], "brasil": r["bra"], "argentina": r["arg"],
                "nota": nota, "flujo": r["flujo"], "medida": r["medida"], "unidad": r["unidad"], "dimensiones": r["dimensiones"], "opciones": len(c),
                "enlace": "https://data-explorer.oecd.org/vis?df[ds]=dsDisseminateFinalDMZ&df[id]=%s&df[ag]=OECD.ELS.HD" % r["flujo"]})
with io.open(os.path.join(OUT, "ocde_titulares.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sal[0].keys()))
    w.writeheader()
    w.writerows(sal)
for s in sal:
    print("%-9s| %-62s| PER %8.2f (%s) | OCDE %8.2f n%-2s | x%-5s z%-6s | lugar %s/%s | op%d | %s" % (s["grupo"][:9], s["indicador"][:62], s["peru"], s["peru_anio"], s["ocde_media"], s["paises_ocde_con_dato"],
          s["peru_sobre_media"], s["z"], s["lugar_del_peru_1_es_el_mejor"], s["de"], s["opciones"], s["dimensiones"][:60]))
print(len(sal), "titulares")
