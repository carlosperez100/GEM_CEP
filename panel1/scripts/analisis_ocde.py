# -*- coding: utf-8 -*-
r"""El Perú frente a los países de la OCDE, serie por serie, con los datos de salud de la OCDE.

Lee las observaciones (SQLite intermedio o PostgreSQL bases_pais, esquema ocde) y, para cada serie
(flujo + medida + unidad + resto de dimensiones) en la que el Perú tiene dato, compara el último valor
del Perú con el último valor de cada país miembro de la OCDE en una ventana de años cercana.

Uso:  python -I analisis_ocde.py [sqlite|pg] [carpeta_salida]
Salida: ocde_peru_vs_ocde.csv (todas las series comparables)
"""
import csv, io, json, math, os, statistics, sys
sys.stdout.reconfigure(encoding="utf-8")
MODO = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "salidas")
os.makedirs(OUT, exist_ok=True)

OCDE = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
VECINOS = ["CHL", "COL", "CRI", "MEX", "BRA", "ARG"]
FLUJOS = ["DSD_HEALTH_STAT@DF_HEALTH_STATUS", "DSD_HEALTH_STAT@DF_AM", "DSD_HEALTH_EMP_REAC@DF_REAC", "DSD_HEALTH_REAC_EMP@DF_NURSE", "DSD_HEALTH_REAC_EMP@DF_MIDWIFE",
          "DSD_HEALTH_REAC_EMP@DF_REMUN", "DSD_HEALTH_REAC_EMP@DF_HOSP_EMP", "DSD_HEALTH_REAC_HOSP@DF_HOSP_REAC", "DSD_HEALTH_REAC_HOSP@DF_BEDS_ICU",
          "DSD_HEALTH_PROC@DF_KEY_INDIC", "DSD_HEALTH_PROC@DF_WAITING", "DSD_HEALTH_PROT@DF_HEALTH_PROT", "DSD_HEALTH_LVNG@DF_HEALTH_LVNG",
          "DSD_HCQO@DF_HCQO", "DSD_HCQO@DF_PSC", "HEALTH_PHMC@DF_KEY_INDIC", "DSD_SHA@DF_SHA"]
OMITE = {"FREQ", "DECIMALS", "UNIT_MULT", "OBS_STATUS2", "OBS_STATUS3", "OBS_STATUS4", "REF_YEAR_PRICE", "PRICE_BASE", "CURRENCY", "CONVERSION_TYPE"}
RELATIVA = ("per ", "percentage", "years", "days", "ratio", "factor", "minutes", "hours", "kilogram", "litre", "gram", "index", "share", "rate", "calories", "us dollars per", "ppp", "salary")

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
    T_OBS, C_PAIS, C_VAL, T_COD, C_DIMS = "ocde.salud_obs", "ref_area", "valor", "ocde.salud_codigo", "dims::text"
    T_FL, C_FLID = "ocde.salud_flujo", "flujo"
else:
    import sqlite3
    con = sqlite3.connect(r"file:T:\OCDE_SALUD\ocde_salud.db?mode=ro", uri=True)

    def q(sql, par=()):
        return con.execute(sql, par).fetchall()
    T_OBS, C_PAIS, C_VAL, T_COD, C_DIMS = "obs", "pais", "valor_txt", "codigos", "dims"
    T_FL, C_FLID = "flujos", "id"

lab = {(d, c): e for d, c, e in q("select dim, codigo, etiqueta from %s" % T_COD)}
nomfl = dict(q("select %s, nombre from %s" % (C_FLID, T_FL)))


def norm(d):
    """Clave canónica de dimensiones (independiente del orden y del motor)."""
    j = json.loads(d) if d else {}
    return json.dumps({k: j[k] for k in sorted(j) if k not in OMITE}, separators=(",", ":"), ensure_ascii=False)


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


filas = []
for fl in FLUJOS:
    per = {}
    for med, uni, dims, periodo, val in q("select medida, unidad, %s, periodo, %s from %s where flujo = ? and %s = 'PER'" % (C_DIMS, C_VAL, T_OBS, C_PAIS), (fl,)):
        v = num(val)
        if v is None or not periodo or not periodo[:4].isdigit():
            continue
        k = (med, uni, norm(dims))
        y = int(periodo[:4])
        if k not in per or y > per[k][0]:
            per[k] = (y, v)
    if fl == "DSD_SHA@DF_SHA":
        # solo totales de función y de proveedor, para no comparar miles de celdas
        per = {k: v for k, v in per.items() if json.loads(k[2]).get("FUNCTION", "_T") == "_T" and json.loads(k[2]).get("PROVIDER", "_T") == "_T"}
    if not per:
        continue
    paises = OCDE + [p for p in VECINOS if p not in OCDE]
    otros = {}
    marca = ",".join("?" * len(paises))
    for pais, med, uni, dims, periodo, val in q("select %s, medida, unidad, %s, periodo, %s from %s where flujo = ? and %s in (%s) and periodo >= '2012'" % (C_PAIS, C_DIMS, C_VAL, T_OBS, C_PAIS, marca), (fl, *paises)):
        k = (med, uni, norm(dims))
        if k not in per:
            continue
        v = num(val)
        if v is None or not periodo[:4].isdigit():
            continue
        otros.setdefault(k, {}).setdefault(pais, {})[int(periodo[:4])] = v
    for k, (y0, vper) in per.items():
        vals = {}
        for pais, serie in otros.get(k, {}).items():
            cand = [y for y in serie if y0 - 4 <= y <= y0 + 1]
            if cand:
                y = min(cand, key=lambda t: (abs(t - y0), -t))
                vals[pais] = (serie[y], y)
        miem = [vals[p][0] for p in OCDE if p in vals]
        if len(miem) < 12:
            continue
        media, mediana = statistics.mean(miem), statistics.median(miem)
        sd = statistics.pstdev(miem)
        menores = sum(1 for x in miem if x < vper)
        d = json.loads(k[2])
        uni_l = lab.get(("UNIT_MEASURE", k[1]), k[1]) or ""
        filas.append({
            "flujo": fl, "flujo_nombre": nomfl.get(fl, ""), "medida": k[0], "medida_nombre": lab.get(("MEASURE", k[0]), ""), "unidad": k[1], "unidad_nombre": uni_l,
            "dimensiones": ";".join("%s=%s" % (a, b) for a, b in d.items() if b not in ("_Z",)),
            "dimensiones_nombre": "; ".join("%s" % (lab.get((a, b), b)) for a, b in d.items() if b not in ("_Z", "_T", "OBS", "A")),
            "relativa": int(any(s in uni_l.lower() for s in RELATIVA)),
            "peru": vper, "peru_anio": y0, "ocde_n": len(miem), "ocde_media": round(media, 4), "ocde_mediana": round(mediana, 4), "ocde_min": min(miem), "ocde_max": max(miem),
            "peru_sobre_media": round(vper / media, 4) if media else "", "z": round((vper - media) / sd, 3) if sd else "",
            "miembros_por_debajo_del_peru": menores, "posicion_peru_de_menor_a_mayor": menores + 1, "de": len(miem) + 1,
            **{p.lower(): (vals[p][0] if p in vals else "") for p in VECINOS},
        })
    print(fl, "series del Perú:", len(per), "| comparables:", sum(1 for f in filas if f["flujo"] == fl), flush=True)

cab = list(filas[0].keys())
with io.open(os.path.join(OUT, "ocde_peru_vs_ocde.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cab)
    w.writeheader()
    w.writerows(filas)
print("TOTAL series comparables:", len(filas), "->", os.path.join(OUT, "ocde_peru_vs_ocde.csv"))
