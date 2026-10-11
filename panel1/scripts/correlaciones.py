# -*- coding: utf-8 -*-
r"""Correlaciones entre países con los datos de salud de la OCDE: dotación de enfermería y resultados.

Arma una matriz país x indicador (último valor de 2018 a 2025) y calcula, entre países:
  - correlación de Spearman y de Pearson de la densidad de enfermería con cada resultado;
  - la misma correlación de Spearman «parcial», descontando el gasto en salud por habitante
    (se correlacionan los residuos de los rangos).
Una correlación entre países describe asociación; no prueba causa.

Uso:  python -I correlaciones.py [sqlite|pg] [carpeta_salida]
"""
import csv, io, json, math, os, sys
import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
MODO = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "salidas")
os.makedirs(OUT, exist_ok=True)
OCDE = set("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split())

if MODO == "pg":
    sys.path.insert(0, r"T:\BASES SISOL\pais\scripts")
    import _entorno  # noqa
    import psycopg
    cfg = {}
    for l in open(r"T:\BASES SISOL\pais\.env", encoding="utf-8"):
        l = l.strip()
        if l and not l.startswith("#") and "=" in l:
            k, v = l.split("=", 1)
            cfg[k.strip()] = v.strip()
    con = psycopg.connect(host=cfg["PGHOST"], port=cfg["PGPORT"], user=cfg["PGUSER"], password=cfg["PGPASSWORD"], dbname=cfg.get("PGDATABASE", "bases_pais"), options="-c default_transaction_read_only=on")

    def q(sql, par=()):
        cur = con.cursor()
        cur.execute(sql.replace("?", "%s"), par)
        return cur.fetchall()
    T, CP, CV, CD = "ocde.salud_obs", "ref_area", "valor", "dims::text"
else:
    import sqlite3
    con = sqlite3.connect(r"file:T:\OCDE_SALUD\ocde_salud.db?mode=ro", uri=True)

    def q(sql, par=()):
        return con.execute(sql, par).fetchall()
    T, CP, CV, CD = "obs", "pais", "valor_txt", "dims"

# clave, nombre, flujo, medida, unidad, condiciones sobre las dimensiones (todas deben cumplirse; lista de alternativas en orden de preferencia)
IND = [
    ("enf_total", "Personal de enfermería por 1 000 habitantes (en ejercicio; si falta, profesionalmente activo)", "DSD_HEALTH_REAC_EMP@DF_NURSE", "HSE", "10P3HB",
     [{"HEALTH_PROF": "MINU", "HEALTH_PROF_ACTIVITY_STATUS": "P"}, {"HEALTH_PROF": "MINU", "HEALTH_PROF_ACTIVITY_STATUS": "PA"}, {"HEALTH_PROF": "MINU", "HEALTH_PROF_ACTIVITY_STATUS": "L"}]),
    ("enf_prof", "Enfermeras profesionales por 1 000 habitantes (en ejercicio; si falta, profesionalmente activas)", "DSD_HEALTH_REAC_EMP@DF_NURSE", "HSE", "10P3HB",
     [{"HEALTH_PROF": "MINUQUAL", "HEALTH_PROF_ACTIVITY_STATUS": "P"}, {"HEALTH_PROF": "MINUQUAL", "HEALTH_PROF_ACTIVITY_STATUS": "PA"}]),
    ("medicos", "Médicos por 1 000 habitantes (en ejercicio; si falta, profesionalmente activos)", "DSD_HEALTH_EMP_REAC@DF_PHYS", "HSE", "10P3HB",
     [{"HEALTH_PROF": "PHYS", "HEALTH_PROF_ACTIVITY_STATUS": "P"}, {"HEALTH_PROF": "PHYS", "HEALTH_PROF_ACTIVITY_STATUS": "PA"}, {"HEALTH_PROF": "PHYS", "HEALTH_PROF_ACTIVITY_STATUS": "L"}]),
    ("gasto_pib", "Gasto corriente en salud (porcentaje del producto bruto interno)", "DSD_SHA@DF_SHA", "EXP_HEALTH", "PT_B1GQ",
     [{"FINANCING_SCHEME": "_T", "FUNCTION": "_T", "PROVIDER": "_T"}]),
    ("gasto_pc", "Gasto corriente en salud por habitante (dólares a paridad de poder adquisitivo)", "DSD_SHA@DF_SHA", "EXP_HEALTH", "USD_PPP_PS",
     [{"FINANCING_SCHEME": "_T", "FUNCTION": "_T", "PROVIDER": "_T"}]),
    ("bolsillo", "Gasto de bolsillo (porcentaje del gasto corriente en salud)", "DSD_SHA@DF_SHA", "EXP_HEALTH", "PT_EXP_HLTH",
     [{"FINANCING_SCHEME": "HF3", "FUNCTION": "_T", "PROVIDER": "_T"}]),
    ("esperanza", "Esperanza de vida al nacer (años)", "DSD_HEALTH_STAT@DF_LE", "LFEXP", "Y", [{"AGE": "Y0", "SEX": "_T"}]),
    ("mort_infantil", "Mortalidad infantil por 1 000 nacidos vivos", "DSD_HEALTH_STAT@DF_MIM", "INM", "DT_10P3BR_L", [{"GESTATION_THRESHOLD": "NONE"}]),
    ("mort_neonatal", "Mortalidad neonatal por 1 000 nacidos vivos", "DSD_HEALTH_STAT@DF_MIM", "NEOM", "DT_10P3BR_L", [{"GESTATION_THRESHOLD": "NONE"}]),
    ("mort_materna", "Mortalidad materna por 100 000 nacidos vivos", "DSD_HEALTH_STAT@DF_MIM", "MATM", "DT_10P5BR_L", [{}]),
    ("mort_evitable", "Mortalidad evitable por 100 000 habitantes", "DSD_HEALTH_STAT@DF_AM", "AVM", "DT_10P5HB", [{"SEX": "_T"}]),
    ("mort_tratable", "Mortalidad tratable por 100 000 habitantes", "DSD_HEALTH_STAT@DF_AM", "TRTM", "DT_10P5HB", [{"SEX": "_T"}]),
    ("mort_prevenible", "Mortalidad prevenible por 100 000 habitantes", "DSD_HEALTH_STAT@DF_AM", "PREVM", "DT_10P5HB", [{"SEX": "_T"}]),
    ("vac_dtp", "Vacunación contra difteria, tétanos y tos ferina (porcentaje de niños)", "DSD_HEALTH_PROC@DF_IMMUN", "IMMUN", "PT_CH_ELG_IM", [{"DISEASE": "DIPTETPERT"}]),
    ("vac_sarampion", "Vacunación contra el sarampión (porcentaje de niños)", "DSD_HEALTH_PROC@DF_IMMUN", "IMMUN", "PT_CH_ELG_IM", [{"DISEASE": "MEAS"}]),
]
RESULTADOS = ["esperanza", "mort_infantil", "mort_neonatal", "mort_materna", "mort_evitable", "mort_tratable", "mort_prevenible", "vac_dtp", "vac_sarampion"]

mat, anio, nombres = {}, {}, {}
for clave, nombre, fl, med, uni, alts in IND:
    nombres[clave] = nombre
    datos = {}
    for pais, dims, periodo, val in q("select %s, %s, periodo, %s from %s where flujo = ? and medida = ? and unidad = ? and periodo >= '2018'" % (CP, CD, CV, T), (fl, med, uni)):
        try:
            v = float(val)
            y = int(periodo[:4])
        except (TypeError, ValueError):
            continue
        d = json.loads(dims) if dims else {}
        for rango, alt in enumerate(alts):
            if all(d.get(k) == v2 for k, v2 in alt.items()):
                # preferir la alternativa de menor rango y, dentro de ella, el año más reciente; a igualdad, la serie con menos desgloses
                extra = sum(1 for k, x in d.items() if x not in ("_Z", "_T", "A", "OBS") and k not in alt and k not in ("DECIMALS", "UNIT_MULT", "FREQ", "OBS_STATUS2", "PRICE_BASE", "CALC_METHODOLOGY", "CURRENCY", "REF_YEAR_PRICE"))
                clave_orden = (rango, extra, -y)
                if pais not in datos or clave_orden < datos[pais][0]:
                    datos[pais] = (clave_orden, v, y)
                break
    for pais, (_, v, y) in datos.items():
        mat.setdefault(pais, {})[clave] = v
        anio.setdefault(pais, {})[clave] = y
    print("%-16s países con dato: %d | Perú: %s (%s)" % (clave, len(datos), mat.get("PER", {}).get(clave), anio.get("PER", {}).get(clave)), flush=True)

for p in mat:
    if mat[p].get("enf_total") and mat[p].get("medicos"):
        mat[p]["enf_por_medico"] = round(mat[p]["enf_total"] / mat[p]["medicos"], 3)
nombres["enf_por_medico"] = "Personal de enfermería por cada médico (cociente calculado)"
claves = [c[0] for c in IND] + ["enf_por_medico"]
paises = sorted(p for p in mat if len(p) == 3 and p.isalpha() and p not in ("OECD", "EU27", "E22"))
with io.open(os.path.join(OUT, "ocde_matriz_paises.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "miembro_ocde"] + claves + [c + "_anio" for c in claves if c != "enf_por_medico"])
    for p in paises:
        w.writerow([p, int(p in OCDE)] + [mat[p].get(c, "") for c in claves] + [anio[p].get(c, "") for c in claves if c != "enf_por_medico"])


def parcial(x, y, z):
    rx, ry, rz = stats.rankdata(x), stats.rankdata(y), stats.rankdata(z)
    A = np.vstack([rz, np.ones(len(rz))]).T
    ex = rx - A @ np.linalg.lstsq(A, rx, rcond=None)[0]
    ey = ry - A @ np.linalg.lstsq(A, ry, rcond=None)[0]
    r = float(np.corrcoef(ex, ey)[0, 1])
    n = len(x)
    gl = n - 3
    t = r * math.sqrt(gl / max(1e-12, 1 - r * r))
    return r, float(2 * stats.t.sf(abs(t), gl))


sal = []
for grupo, conj in (("todos los países de la base", paises), ("solo miembros de la OCDE", [p for p in paises if p in OCDE])):
    for x in ("enf_total", "enf_prof", "medicos", "enf_por_medico", "gasto_pc"):
        for y in RESULTADOS:
            ps = [p for p in conj if x in mat[p] and y in mat[p]]
            if len(ps) < 12:
                continue
            xv, yv = [mat[p][x] for p in ps], [mat[p][y] for p in ps]
            rs, pv = stats.spearmanr(xv, yv)
            rp, pp = stats.pearsonr(xv, yv)
            fila = {"grupo": grupo, "x": x, "x_nombre": nombres[x], "y": y, "y_nombre": nombres[y], "n": len(ps), "spearman": round(float(rs), 3), "p_spearman": float("%.4g" % pv),
                    "pearson": round(float(rp), 3), "p_pearson": float("%.4g" % pp), "n_parcial": "", "spearman_parcial_descontando_gasto": "", "p_parcial": "", "incluye_peru": int("PER" in ps)}
            if x != "gasto_pc":
                pz = [p for p in ps if "gasto_pc" in mat[p]]
                if len(pz) >= 12:
                    r, pvp = parcial([mat[p][x] for p in pz], [mat[p][y] for p in pz], [mat[p]["gasto_pc"] for p in pz])
                    fila.update({"n_parcial": len(pz), "spearman_parcial_descontando_gasto": round(r, 3), "p_parcial": float("%.4g" % pvp)})
            sal.append(fila)
with io.open(os.path.join(OUT, "ocde_correlaciones.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sal[0].keys()))
    w.writeheader()
    w.writerows(sal)
print("países en la matriz:", len(paises), "| filas de correlación:", len(sal))
for s in sal:
    if s["x"] in ("enf_total", "enf_por_medico", "gasto_pc") and s["grupo"].startswith("todos"):
        print("%-15s x %-16s n=%-3d rho=%6.3f p=%-9.3g | parcial(n=%s) %s p=%s" % (s["x"], s["y"], s["n"], s["spearman"], s["p_spearman"], s["n_parcial"], s["spearman_parcial_descontando_gasto"], s["p_parcial"]))
