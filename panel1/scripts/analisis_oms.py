# -*- coding: utf-8 -*-
r"""Países con jefatura nacional de enfermería en el gobierno y sus indicadores (Organización Mundial de la Salud).

Lee los archivos que deja cargar_oms_sown.py en T:\BASES SISOL\pais\descargas\oms_sown\ y produce:
  oms_jefatura_enfermeria_paises.csv   una fila por país (194), con su fuente
  oms_jefatura_resumen.csv             conteos por edición, región y grupo de ingreso
  oms_jefatura_indicadores.csv         mediana de cada indicador según tenga o no jefatura, en total y por grupo de ingreso
Comparar grupos de países muestra asociación, no causa.

Uso: python -I analisis_oms.py [carpeta_salida]
"""
import csv, io, os, statistics, sys
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
D = r"T:\BASES SISOL\pais\descargas\oms_sown"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "salidas_pg")
os.makedirs(OUT, exist_ok=True)


def lee(n):
    return list(csv.DictReader(io.open(os.path.join(D, n), encoding="utf-8-sig")))


perf = lee("sown_perfil.csv")
gho = lee("gho_obs.csv")
bm = {r["iso3"]: r for r in lee("bm_pais.csv")}
IND = [("UHC_INDEX_REPORTED", "indice_cobertura", "Índice de cobertura de servicios (0 a 100)", "alto"),
       ("WHOSIS_000001", "esperanza_vida", "Esperanza de vida al nacer (años)", "alto"),
       ("MDG_0000000026", "mortalidad_materna", "Mortalidad materna por 100 000 nacidos vivos", "bajo"),
       ("MDG_0000000007", "mortalidad_menores5", "Mortalidad de menores de cinco años por 1 000 nacidos vivos", "bajo"),
       ("WHOSIS_000003", "mortalidad_neonatal", "Mortalidad neonatal por 1 000 nacidos vivos", "bajo"),
       ("HWF_0006", "enfermeria_por_10000", "Personal de enfermería y partería por 10 000 habitantes", "alto"),
       ("GHED_CHE_pc_US_SHA2011", "gasto_salud_por_habitante", "Gasto corriente en salud por habitante (dólares)", "alto")]
ult = {}
for r in gho:
    try:
        v, a = float(r["valor"]), int(r["anio"])
    except (TypeError, ValueError):
        continue
    k = (r["iso3"], r["indicador"])
    if k not in ult or a > ult[k][1]:
        ult[k] = (v, a)

INGRESO = {"High income": "Ingreso alto", "Upper middle income": "Ingreso mediano alto", "Lower middle income": "Ingreso mediano bajo", "Low income": "Ingreso bajo"}
REGION = {"Latin America & Caribbean": "América Latina y el Caribe", "North America": "América del Norte", "Europe & Central Asia": "Europa y Asia Central", "East Asia & Pacific": "Asia Oriental y el Pacífico",
          "Middle East & North Africa": "Oriente Medio y Norte de África", "Middle East, North Africa, Afghanistan & Pakistan": "Oriente Medio, Norte de África, Afganistán y Pakistán",
          "South Asia": "Asia Meridional", "Sub-Saharan Africa": "África subsahariana"}
VAL = {"Yes": "Sí", "No": "No", "Partial": "Parcial", "NR": "No reportado", "??": "Por revisar"}
p20 = {r["iso3"]: r for r in perf if r["edicion"] == "2020"}
p25 = {r["iso3"]: r for r in perf if r["edicion"] == "2025"}
paises = sorted(set(p20) | set(p25))
filas = []
for iso in paises:
    a, b, w = p20.get(iso, {}), p25.get(iso, {}), bm.get(iso, {})
    f = {"iso3": iso, "pais": b.get("pais") or a.get("pais"), "region_banco_mundial": REGION.get((w.get("region") or "").strip(), (w.get("region") or "").strip()), "grupo_ingreso": INGRESO.get(w.get("grupo_ingreso"), w.get("grupo_ingreso", "")),
         "jefatura_enfermeria_2020": VAL.get(a.get("jefatura_enfermeria"), ""), "programa_liderazgo_2020": VAL.get(a.get("programa_liderazgo"), ""),
         "jefatura_enfermeria_2025": VAL.get(b.get("jefatura_enfermeria"), ""), "programa_liderazgo_2025": VAL.get(b.get("programa_liderazgo"), "")}
    for cod, clave, nom, mejor in IND:
        v = ult.get((iso, cod))
        f[clave] = v[0] if v else ""
        f[clave + "_anio"] = v[1] if v else ""
    f["fuente_2020"] = a.get("url_perfil", "")
    f["fuente_2025"] = b.get("url_perfil", "")
    f["fuente_indicadores"] = "https://ghoapi.azureedge.net/api/<código>: " + ", ".join(c[0] for c in IND)
    f["fuente_ingreso"] = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    filas.append(f)
with io.open(os.path.join(OUT, "oms_jefatura_enfermeria_paises.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)

res = []
for ed in ("2020", "2025"):
    k = "jefatura_enfermeria_" + ed
    for nivel, llave in (("Mundo", None), ("Región", "region_banco_mundial"), ("Ingreso", "grupo_ingreso")):
        grupos = {}
        for f in filas:
            g = "Todos" if llave is None else (f[llave] or "Sin clasificar")
            grupos.setdefault(g, []).append(f[k])
        for g, vals in sorted(grupos.items()):
            c = {v: vals.count(v) for v in ("Sí", "Parcial", "No", "No reportado", "Por revisar", "")}
            resp = c["Sí"] + c["Parcial"] + c["No"]
            res.append({"edicion": ed, "nivel": nivel, "grupo": g, "paises": len(vals), "si": c["Sí"], "parcial": c["Parcial"], "no": c["No"], "no_reportado": c["No reportado"], "por_revisar": c["Por revisar"] + c[""],
                        "respondieron": resp, "porcentaje_si_entre_los_que_respondieron": round(100.0 * c["Sí"] / resp, 1) if resp else ""})
with io.open(os.path.join(OUT, "oms_jefatura_resumen.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
    w.writeheader()
    w.writerows(res)

comp = []
for ed in ("2020", "2025"):
    k = "jefatura_enfermeria_" + ed
    for estrato in ["Todos"] + list(INGRESO.values()):
        base = [f for f in filas if estrato == "Todos" or f["grupo_ingreso"] == estrato]
        for cod, clave, nom, mejor in IND:
            si = [f[clave] for f in base if f[k] == "Sí" and f[clave] != ""]
            no = [f[clave] for f in base if f[k] in ("No", "Parcial") and f[clave] != ""]
            nr = [f[clave] for f in base if f[k] == "No reportado" and f[clave] != ""]
            fila = {"edicion": ed, "estrato": estrato, "indicador": nom, "mejor_si": mejor, "n_si": len(si), "mediana_si": round(statistics.median(si), 2) if si else "",
                    "n_no_o_parcial": len(no), "mediana_no_o_parcial": round(statistics.median(no), 2) if no else "", "n_no_reportado": len(nr), "mediana_no_reportado": round(statistics.median(nr), 2) if nr else "",
                    "p_mann_whitney_si_frente_a_no": ""}
            if len(si) >= 5 and len(no) >= 5:
                fila["p_mann_whitney_si_frente_a_no"] = float("%.4g" % stats.mannwhitneyu(si, no, alternative="two-sided").pvalue)
            comp.append(fila)
with io.open(os.path.join(OUT, "oms_jefatura_indicadores.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(comp[0].keys()))
    w.writeheader()
    w.writerows(comp)

print("países:", len(filas))
for r in res:
    if r["nivel"] in ("Mundo", "Ingreso") or r["grupo"] in ("América Latina y el Caribe", "América del Norte"):
        print("%s | %-7s | %-28s | países %3d | sí %3d | parcial %2d | no %3d | no reportado %3d | revisar %d | sí entre los que respondieron: %s %%" % (
            r["edicion"], r["nivel"], r["grupo"][:28], r["paises"], r["si"], r["parcial"], r["no"], r["no_reportado"], r["por_revisar"], r["porcentaje_si_entre_los_que_respondieron"]))
print()
for c in comp:
    if c["estrato"] in ("Todos", "Ingreso mediano alto"):
        print("%s | %-20s | %-46s | sí n=%-3s med %-8s | no n=%-3s med %-8s | nr n=%-3s med %-8s | p=%s" % (c["edicion"], c["estrato"][:20], c["indicador"][:46], c["n_si"], c["mediana_si"], c["n_no_o_parcial"], c["mediana_no_o_parcial"],
              c["n_no_reportado"], c["mediana_no_reportado"], c["p_mann_whitney_si_frente_a_no"]))
per = next(f for f in filas if f["iso3"] == "PER")
print("\nPERÚ:", {k: v for k, v in per.items() if not k.startswith("fuente")})
