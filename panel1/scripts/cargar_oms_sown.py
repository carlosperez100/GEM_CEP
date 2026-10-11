# -*- coding: utf-8 -*-
r"""Jefatura nacional de enfermería en el gobierno, país por país, según la Organización Mundial de la Salud.

Qué baja
  1. Los perfiles de país de «State of the world's nursing» 2020 y 2025 (una página por país, 194 países).
     Cada perfil marca con un ícono (Yes / Partial / No / NR) si el país reporta «Chief Nursing Officer position»
     (2020) o «Chief nursing position» (2025) y un programa de desarrollo de liderazgo en enfermería.
       2020: https://apps.who.int/nhwaportal/Sown/Files?name=<ISO3>
       2025: enlaces de la tabla «tbNP_SoWN25» del informe público del portal https://apps.who.int/nhwaportal/
             (guardados en descargas\oms_sown\enlaces_2025.txt)
  2. Siete indicadores del Observatorio Mundial de la Salud (https://ghoapi.azureedge.net/api/<código>), todos los países.
  3. La clasificación de países del Banco Mundial (https://api.worldbank.org/v2/country): región y grupo de ingreso.

Dónde lo deja (bases_pais)
  oms.sown_perfil     crudo: un país y una edición por fila, con el enlace del perfil y el sha256 del archivo
  oms.gho_obs         crudo: observaciones de los siete indicadores
  bm.pais             crudo: clasificación del Banco Mundial
  ref.oms_jefatura_enfermeria   una fila por país: jefatura 2020 y 2025, último valor de cada indicador, región e ingreso

Cómo se lee el ícono: se convierte la página a imagen (110 puntos por pulgada) y se clasifica por color el recuadro
del rubro (verde = Yes, rojo = No, morado = Partial, gris = NR). Lo dudoso queda como «??» para revisión manual.

Uso:
    python pais\scripts\cargar_oms_sown.py                 baja lo que falte, lee y carga
    python pais\scripts\cargar_oms_sown.py --local         no descarga; usa lo que hay en descargas\oms_sown\
    python pais\scripts\cargar_oms_sown.py --sin-base      no carga a PostgreSQL; solo deja los CSV
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import _entorno  # noqa: F401
except Exception:
    pass

import ast, colorsys, csv, datetime, hashlib, io, json, re, subprocess, time, urllib.request  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"T:\BASES SISOL\pais")
D = RAIZ / "descargas" / "oms_sown"
PDFTOPPM = r"equipo del autor/AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftoppm.exe"
PDFTOTEXT = r"C:\Program Files\Git\mingw64\bin\pdftotext.exe"
CURL = r"C:\Windows\System32\curl.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
URL20 = "https://apps.who.int/nhwaportal/Sown/Files?name=%s"
CAJAS = {"2020": {"jefatura": (246, 781, 271, 803), "liderazgo": (246, 808, 271, 830)},
         "2025": {"jefatura": (280, 765, 305, 787), "liderazgo": (280, 790, 305, 812)}}
GHO = [("UHC_INDEX_REPORTED", "Índice de cobertura de servicios de la cobertura sanitaria universal (0 a 100)", None),
       ("WHOSIS_000001", "Esperanza de vida al nacer, ambos sexos (años)", "SEX_BTSX"),
       ("MDG_0000000026", "Razón de mortalidad materna (por 100 000 nacidos vivos)", None),
       ("MDG_0000000007", "Tasa de mortalidad de menores de cinco años, ambos sexos (por 1 000 nacidos vivos)", "SEX_BTSX"),
       ("WHOSIS_000003", "Tasa de mortalidad neonatal, ambos sexos (por 1 000 nacidos vivos)", "SEX_BTSX"),
       ("HWF_0006", "Personal de enfermería y partería (por 10 000 habitantes)", None),
       ("GHED_CHE_pc_US_SHA2011", "Gasto corriente en salud por habitante (dólares de los Estados Unidos)", None)]


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def es_pdf(p):
    try:
        return p.exists() and p.stat().st_size > 20000 and open(p, "rb").read(5) == b"%PDF-"
    except Exception:
        return False


def baja(url, dest, jar):
    for intento in (1, 2, 3):
        subprocess.run([CURL, "-s", "-L", "-m", "150", "-A", UA, "-c", str(jar), "-b", str(jar), "-o", str(dest), url], capture_output=True)
        if es_pdf(dest):
            return True
        time.sleep(4 * intento)
    return False


def enlaces():
    out = []
    for l in io.open(D / "enlaces_2025.txt", encoding="utf-8"):
        l = l.strip()
        if l.startswith("["):
            r = ast.literal_eval(l)
            out.append({"iso3": r[0], "pais": r[1], "url25": r[2], "url25_es": r[3]})
    return out


def color(im, caja):
    from PIL import Image  # noqa: F401
    g = r = p = k = 0
    for (R, G, B) in im.crop(caja).convert("RGB").getdata():
        mx, mn = max(R, G, B), min(R, G, B)
        if mx - mn < 25:
            if 120 < mx < 215:
                k += 1
            continue
        h, s, v = colorsys.rgb_to_hsv(R / 255, G / 255, B / 255)
        if s < 0.25:
            continue
        hd = h * 360
        if 55 <= hd <= 110:
            g += 1
        elif hd >= 320 or hd <= 15:
            r += 1
        elif 220 <= hd <= 280:
            p += 1
    d = {"Yes": g, "No": r, "Partial": p, "NR": k}
    mejor = max(d, key=d.get)
    return (mejor if d[mejor] >= 6 else "??"), d


def lee_perfil(pdf, ed):
    from PIL import Image
    base = pdf.with_suffix("")
    png = Path(str(base) + "-1.png")
    alt = Path(str(base) + "-01.png")
    if not png.exists() and not alt.exists():
        subprocess.run([PDFTOPPM, "-r", "110", "-png", "-f", "1", "-l", "1", str(pdf), str(base)], capture_output=True)
    if not png.exists() and alt.exists():
        png = alt
    txt = pdf.with_suffix(".txt")
    if not txt.exists():
        subprocess.run([PDFTOTEXT, str(pdf), str(txt)], capture_output=True)
    out = {"jefatura": "??", "liderazgo": "??", "conteo": {}}
    if png.exists():
        im = Image.open(png).convert("RGB")
        out["tam"] = im.size
        for k, caja in CAJAS[ed].items():
            out[k], out["conteo"][k] = color(im, caja)
    t = txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""
    if ed == "2025":
        lines = t.split("\n")
        for i, l in enumerate(lines):
            m = re.search(r"points, (\d{4})\)", l)
            if m and i + 1 < len(lines):
                out["anio_indice"] = m.group(1)
                partes = lines[i + 1].strip().split()
                if len(partes) > 1:
                    out["poblacion"], out["indice"] = partes[0], partes[1]
        mp = re.search(r"Personnel\s*\n?Density\s*\n?([\d,]+)\s+([\d.]+)", t)
        if mp:
            out["personal"], out["densidad"] = mp.group(1), mp.group(2)
        else:
            md = re.search(r"([\d.,]+)\s*\n?per 10,000", t)
            if md:
                out["densidad"] = md.group(1)
    return out


def trae_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8-sig"))


def main():
    local = "--local" in sys.argv
    sin_base = "--sin-base" in sys.argv
    for s in ("pdf2020", "pdf2025"):
        (D / s).mkdir(parents=True, exist_ok=True)
    paises = enlaces()
    log("países en la tabla de enlaces:", len(paises))

    # 1) perfiles
    faltan = []
    for k, p in enumerate(paises, 1):
        for ed, url in (("2020", URL20 % p["iso3"]), ("2025", (p["url25"] or "") + "&download=1")):
            dest = D / ("pdf" + ed) / (p["iso3"] + ".pdf")
            if not es_pdf(dest) and not local and url.startswith("http"):
                ok = baja(url, dest, D / ("jar%s.txt" % ed))
                time.sleep(0.6)
                if not ok:
                    faltan.append((p["iso3"], ed))
            elif not es_pdf(dest):
                faltan.append((p["iso3"], ed))
        if k % 20 == 0:
            log("  perfiles revisados: %d de %d; sin archivo: %d" % (k, len(paises), len(faltan)))
    log("perfiles sin archivo:", faltan)

    filas, dudas = [], []
    for p in paises:
        for ed in ("2020", "2025"):
            pdf = D / ("pdf" + ed) / (p["iso3"] + ".pdf")
            if not es_pdf(pdf):
                continue
            r = lee_perfil(pdf, ed)
            if "??" in (r["jefatura"], r["liderazgo"]):
                dudas.append((p["iso3"], ed, r["conteo"], r.get("tam")))
            filas.append({"iso3": p["iso3"], "pais": p["pais"], "edicion": ed, "jefatura_enfermeria": r["jefatura"], "programa_liderazgo": r["liderazgo"],
                          "indice_cobertura": r.get("indice", ""), "anio_indice": r.get("anio_indice", ""), "poblacion": r.get("poblacion", ""),
                          "personal_enfermeria": r.get("personal", ""), "densidad_por_10000": r.get("densidad", ""),
                          "url_perfil": (URL20 % p["iso3"]) if ed == "2020" else p["url25"], "url_perfil_es": "" if ed == "2020" else (p["url25_es"] or ""),
                          "archivo": pdf.name, "sha256": sha256(pdf), "bytes": pdf.stat().st_size,
                          "pixeles_jefatura": json.dumps(r["conteo"].get("jefatura", {}))})
    log("perfiles leídos:", len(filas), "| dudosos:", len(dudas))
    for d in dudas:
        log("   REVISAR", d)
    cab = list(filas[0].keys())
    with io.open(D / "sown_perfil.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cab)
        w.writeheader()
        w.writerows(filas)

    # 2) indicadores del Observatorio Mundial de la Salud
    gho = []
    for cod, nom, dim in GHO:
        p = D / ("gho_%s.json" % cod)
        if not p.exists() and not local:
            try:
                d = trae_json("https://ghoapi.azureedge.net/api/%s" % cod)
                p.write_text(json.dumps(d), encoding="utf-8")
                time.sleep(1)
            except Exception as ex:
                log("  no se pudo bajar", cod, ex)
        if not p.exists():
            continue
        for v in json.loads(p.read_text(encoding="utf-8")).get("value", []):
            if v.get("SpatialDimType") != "COUNTRY":
                continue
            if dim and v.get("Dim1") != dim:
                continue
            gho.append({"indicador": cod, "nombre": nom, "iso3": v.get("SpatialDim"), "anio": v.get("TimeDim"), "dim1": v.get("Dim1") or "",
                        "valor": v.get("NumericValue"), "valor_txt": v.get("Value") or "", "url": "https://ghoapi.azureedge.net/api/%s" % cod})
    with io.open(D / "gho_obs.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["indicador", "nombre", "iso3", "anio", "dim1", "valor", "valor_txt", "url"])
        w.writeheader()
        w.writerows(gho)
    log("observaciones del Observatorio Mundial de la Salud:", len(gho))

    # 3) Banco Mundial
    bm = []
    p = D / "bm_paises.json"
    if not p.exists() and not local:
        try:
            p.write_text(json.dumps(trae_json("https://api.worldbank.org/v2/country?format=json&per_page=400")), encoding="utf-8")
        except Exception as ex:
            log("  no se pudo bajar la clasificación del Banco Mundial", ex)
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d[1]:
            if c.get("region", {}).get("value") == "Aggregates":
                continue
            bm.append({"iso3": c["id"], "nombre": c["name"], "region": c["region"]["value"], "grupo_ingreso": c["incomeLevel"]["value"], "capital": c.get("capitalCity", ""),
                       "url": "https://api.worldbank.org/v2/country?format=json&per_page=400"})
    with io.open(D / "bm_pais.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iso3", "nombre", "region", "grupo_ingreso", "capital", "url"])
        w.writeheader()
        w.writerows(bm)
    log("países del Banco Mundial:", len(bm))

    if sin_base:
        return
    import psycopg
    cfg = {}
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if l and not l.startswith("#") and "=" in l:
            a, b = l.split("=", 1)
            cfg[a.strip()] = b.strip()
    cx = psycopg.connect(host=cfg["PGHOST"], port=cfg["PGPORT"], user=cfg["PGUSER"], password=cfg["PGPASSWORD"], dbname=cfg.get("PGDATABASE", "bases_pais"))
    with cx.cursor() as cur:
        for f in (dict(fuente_id="oms", nombre="Organización Mundial de la Salud: perfiles de «State of the world's nursing» y Observatorio Mundial de la Salud",
                       organismo="Organización Mundial de la Salud", portal="https://apps.who.int/nhwaportal/", api="https://ghoapi.azureedge.net/api",
                       licencia="Ver condiciones de uso de la Organización Mundial de la Salud: https://www.who.int/about/policies/publishing/copyright",
                       notas="Los perfiles son archivos PDF de una página; el valor de cada rubro es un ícono que se clasifica por color. Los enlaces de 2025 salen de la tabla tbNP_SoWN25 del informe público del portal."),
                  dict(fuente_id="bm", nombre="Banco Mundial: clasificación de países", organismo="Banco Mundial", portal="https://data.worldbank.org/",
                       api="https://api.worldbank.org/v2", licencia="Ver condiciones de uso del Banco Mundial: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
                       notas="Región y grupo de ingreso de cada país, vigentes a la fecha de descarga.")):
            cur.execute("""INSERT INTO meta.fuente (fuente_id, nombre, organismo, portal, api, licencia, notas)
                           VALUES (%(fuente_id)s, %(nombre)s, %(organismo)s, %(portal)s, %(api)s, %(licencia)s, %(notas)s)
                           ON CONFLICT (fuente_id) DO UPDATE SET nombre = EXCLUDED.nombre, organismo = EXCLUDED.organismo, portal = EXCLUDED.portal,
                               api = EXCLUDED.api, licencia = EXCLUDED.licencia, notas = EXCLUDED.notas""", f)
        for ds in (("oms_sown_perfil", "oms", "Perfiles de país de «State of the world's nursing» 2020 y 2025: jefatura nacional de enfermería y programa de liderazgo", "oms", "sown_perfil", ["iso3", "edicion"]),
                   ("oms_gho_obs", "oms", "Observatorio Mundial de la Salud: siete indicadores, todos los países y años", "oms", "gho_obs", ["indicador", "iso3", "anio", "dim1"]),
                   ("bm_pais", "bm", "Banco Mundial: región y grupo de ingreso por país", "bm", "pais", ["iso3"])):
            cur.execute("""INSERT INTO meta.dataset (dataset_id, fuente_id, nombre, esquema, tabla, ckan_id, filtro_recurso, periodicidad, personales, clave_negocio, notas)
                           VALUES (%s,%s,%s,%s,%s, NULL, NULL, 'manual', false, %s, 'Se carga con pais\\scripts\\cargar_oms_sown.py')
                           ON CONFLICT (dataset_id) DO UPDATE SET nombre = EXCLUDED.nombre, esquema = EXCLUDED.esquema, tabla = EXCLUDED.tabla, clave_negocio = EXCLUDED.clave_negocio, notas = EXCLUDED.notas""",
                        (ds[0], ds[1], ds[2], ds[3], ds[4], ds[5]))
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS oms;
            CREATE SCHEMA IF NOT EXISTS bm;
            DROP VIEW IF EXISTS ref.oms_jefatura_enfermeria;
            DROP TABLE IF EXISTS oms.sown_perfil;
            CREATE TABLE oms.sown_perfil (iso3 text, pais text, edicion text, jefatura_enfermeria text, programa_liderazgo text, indice_cobertura text, anio_indice text,
                poblacion text, personal_enfermeria text, densidad_por_10000 text, url_perfil text, url_perfil_es text, archivo text, sha256 text, bytes text, pixeles_jefatura text,
                PRIMARY KEY (iso3, edicion));
            DROP TABLE IF EXISTS oms.gho_obs;
            CREATE TABLE oms.gho_obs (indicador text, nombre text, iso3 text, anio text, dim1 text, valor text, valor_txt text, url text);
            DROP TABLE IF EXISTS bm.pais;
            CREATE TABLE bm.pais (iso3 text PRIMARY KEY, nombre text, region text, grupo_ingreso text, capital text, url text);
            COMMENT ON SCHEMA oms IS 'Crudo de la Organización Mundial de la Salud: todo texto, tal como lo publica.';
            COMMENT ON SCHEMA bm IS 'Crudo del Banco Mundial: todo texto, tal como lo publica.';
            COMMENT ON TABLE oms.sown_perfil IS 'Perfiles de país de «State of the world''s nursing» 2020 y 2025 de la Organización Mundial de la Salud. jefatura_enfermeria: Yes / Partial / No / NR (no reportado), leído del ícono del rubro «Chief Nursing Officer position» (2020) o «Chief nursing position» (2025). url_perfil es el enlace del archivo original.';
            COMMENT ON TABLE oms.gho_obs IS 'Observatorio Mundial de la Salud (Organización Mundial de la Salud): observaciones por país y año de siete indicadores. url es la consulta de origen.';
            COMMENT ON TABLE bm.pais IS 'Banco Mundial: región y grupo de ingreso por país.';
        """)
        with cur.copy("COPY oms.sown_perfil FROM STDIN") as cp:
            for r in filas:
                cp.write_row([str(r[c]) for c in cab])
        with cur.copy("COPY oms.gho_obs FROM STDIN") as cp:
            for r in gho:
                cp.write_row([None if r[c] is None else str(r[c]) for c in ("indicador", "nombre", "iso3", "anio", "dim1", "valor", "valor_txt", "url")])
        with cur.copy("COPY bm.pais FROM STDIN") as cp:
            for r in bm:
                cp.write_row([r[c] for c in ("iso3", "nombre", "region", "grupo_ingreso", "capital", "url")])
        ult = lambda cod: "(SELECT DISTINCT ON (iso3) iso3, valor::numeric AS v, anio::int AS a FROM oms.gho_obs WHERE indicador = '%s' AND valor ~ '^-?[0-9.]+$' ORDER BY iso3, anio::int DESC)" % cod
        cur.execute("""
            CREATE VIEW ref.oms_jefatura_enfermeria AS
            SELECT p.iso3, coalesce(a.pais, b.pais) AS pais, w.region AS region_banco_mundial, w.grupo_ingreso,
                   a.jefatura_enfermeria AS jefatura_2020, a.programa_liderazgo AS liderazgo_2020,
                   b.jefatura_enfermeria AS jefatura_2025, b.programa_liderazgo AS liderazgo_2025,
                   uhc.v AS indice_cobertura, uhc.a AS indice_cobertura_anio, le.v AS esperanza_vida, le.a AS esperanza_vida_anio,
                   mm.v AS mortalidad_materna, mm.a AS mortalidad_materna_anio, u5.v AS mortalidad_menores5, u5.a AS mortalidad_menores5_anio,
                   nn.v AS mortalidad_neonatal, nn.a AS mortalidad_neonatal_anio, enf.v AS enfermeria_por_10000, enf.a AS enfermeria_anio,
                   gs.v AS gasto_salud_por_habitante, gs.a AS gasto_salud_anio,
                   a.url_perfil AS url_perfil_2020, b.url_perfil AS url_perfil_2025
            FROM (SELECT DISTINCT iso3 FROM oms.sown_perfil) p
            LEFT JOIN oms.sown_perfil a ON a.iso3 = p.iso3 AND a.edicion = '2020'
            LEFT JOIN oms.sown_perfil b ON b.iso3 = p.iso3 AND b.edicion = '2025'
            LEFT JOIN bm.pais w ON w.iso3 = p.iso3
            LEFT JOIN %s uhc ON uhc.iso3 = p.iso3
            LEFT JOIN %s le ON le.iso3 = p.iso3
            LEFT JOIN %s mm ON mm.iso3 = p.iso3
            LEFT JOIN %s u5 ON u5.iso3 = p.iso3
            LEFT JOIN %s nn ON nn.iso3 = p.iso3
            LEFT JOIN %s enf ON enf.iso3 = p.iso3
            LEFT JOIN %s gs ON gs.iso3 = p.iso3;
        """ % tuple(ult(c[0]) for c in GHO))
        cur.execute("COMMENT ON VIEW ref.oms_jefatura_enfermeria IS 'Una fila por país: jefatura nacional de enfermería en el gobierno según los perfiles 2020 y 2025 de la Organización Mundial de la Salud, último valor de siete indicadores del Observatorio Mundial de la Salud, y región y grupo de ingreso del Banco Mundial. Comparar grupos muestra asociación, no causa.'")
        for ds, n in (("oms_sown_perfil", len(filas)), ("oms_gho_obs", len(gho)), ("bm_pais", len(bm))):
            cur.execute("INSERT INTO meta.carga (dataset_id, destino, inicio, fin, estado, filas, mensaje) VALUES (%s, %s, now(), now(), 'ok', %s, %s)",
                        (ds, {"oms_sown_perfil": "oms.sown_perfil", "oms_gho_obs": "oms.gho_obs", "bm_pais": "bm.pais"}[ds], n, "cargar_oms_sown.py; archivos en " + str(D)))
    cx.commit()
    cx.close()
    log("LISTO: oms.sown_perfil %d filas, oms.gho_obs %d, bm.pais %d; vista ref.oms_jefatura_enfermeria" % (len(filas), len(gho), len(bm)))


if __name__ == "__main__":
    main()
