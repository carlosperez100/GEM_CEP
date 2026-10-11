# -*- coding: utf-8 -*-
r"""Baja TODOS los flujos de datos de salud de la OCDE y los aterriza en bases_pais.

Fuente  : interfaz pública SDMX de la OCDE, https://sdmx.oecd.org/public/rest
          (la misma que alimenta https://data-explorer.oecd.org, tema Health; agencia OECD.ELS.HD).
          No pide clave. Trae a todos los países que la OCDE publica, incluido el Perú.
Destino : esquema `ocde` (crudo, todo texto, tal como lo publicó la OCDE)
              ocde.salud_obs      una fila por observación, con TODAS sus dimensiones
              ocde.salud_flujo    el catálogo de flujos (86)
              ocde.salud_codigo   el diccionario código -> etiqueta de cada dimensión
          y, para consultar, la vista tipada  ref.ocde_salud
Registro: meta.fuente, meta.dataset, meta.archivo (sha256) y meta.carga, igual que etl.py.

Uso:
    python pais\scripts\cargar_ocde.py            baja lo que falte y carga
    python pais\scripts\cargar_ocde.py --local    no descarga: carga lo que ya está en descargas\ocde_salud\
    python pais\scripts\cargar_ocde.py --rehacer  vuelve a bajar y a cargar todo

Correrlo dos veces no duplica nada: cada archivo se identifica por su sha256.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _entorno  # noqa: F401,E402

import csv, datetime, gzip, hashlib, io, json, re, time, urllib.error, urllib.request  # noqa: E402
import psycopg  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10 ** 9)

RAIZ = Path(__file__).resolve().parent.parent            # T:\BASES SISOL\pais
DESC = RAIZ / "descargas" / "ocde_salud"
API = "https://sdmx.oecd.org/public/rest"
AGENCIA = "OECD.ELS.HD"
DATASET = "ocde_salud"
PAUSA = 10          # segundos entre pedidos, para no cargar el servidor
ESPERA_429 = 900    # si el servidor pide bajar el ritmo
UA = {"User-Agent": "Mozilla/5.0 (investigacion academica; descarga unica)"}
ACEPTA_CSV = "application/vnd.sdmx.data+csv; charset=utf-8; labels=both"
FIJAS = {"DATAFLOW", "REF_AREA", "MEASURE", "UNIT_MEASURE", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"}

FUENTE = dict(
    fuente_id="ocde",
    nombre="OCDE Data Explorer (interfaz SDMX)",
    organismo="Organización para la Cooperación y el Desarrollo Económicos",
    portal="https://data-explorer.oecd.org/",
    api=API,
    licencia="Ver términos y condiciones de la OCDE: https://www.oecd.org/en/about/terms-conditions.html",
    notas="No pide clave. Se consulta flujo por flujo: /data/OECD.ELS.HD,<flujo>,<versión>/all con Accept "
          "application/vnd.sdmx.data+csv; labels=both. El catálogo de flujos sale de /dataflow/OECD.ELS.HD?detail=allstubs.",
)
DS = dict(
    dataset_id=DATASET, fuente_id="ocde", nombre="OCDE: estadísticas de salud, todos los flujos y todos los países",
    esquema="ocde", tabla="salud_obs", ckan_id=None, filtro=None, periodicidad="anual", personales=False,
    clave_negocio=["flujo", "ref_area", "medida", "unidad", "periodo", "dims"],
    notas="Una fila por observación, sin agregar ni filtrar. Varios flujos son recortes de otro mayor "
          "(por ejemplo, DF_LE es parte de DF_HEALTH_STATUS): al analizar, elegir un flujo por indicador. "
          "Se consulta por ref.ocde_salud.",
)


def log(*a):
    print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def env():
    d = {}
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if l and not l.startswith("#") and "=" in l:
            k, v = l.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def nombre_archivo(fid):
    return re.sub(r"[^A-Za-z0-9]+", "_", fid) + ".csv.gz"


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pide(url, destino, accept):
    """Descarga url a destino, comprimido. Devuelve el estado HTTP."""
    intentos = 0
    while True:
        intentos += 1
        req = urllib.request.Request(url, headers=dict(UA, Accept=accept))
        tmp = Path(str(destino) + ".tmp")
        try:
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as crudo, \
                    gzip.GzipFile(fileobj=crudo, mode="wb", compresslevel=5, mtime=0) as g:
                for b in iter(lambda: r.read(1 << 20), b""):
                    g.write(b)
            tmp.replace(destino)
            return 200
        except urllib.error.HTTPError as ex:
            if ex.code == 429 and intentos <= 10:
                ra = ex.headers.get("Retry-After")
                esp = max(ESPERA_429, int(ra)) if ra and ra.isdigit() else ESPERA_429
                log("   429: el servidor pide esperar; se duerme", esp, "s")
                time.sleep(esp)
                continue
            if ex.code in (500, 502, 503, 504) and intentos <= 3:
                time.sleep(60)
                continue
            return ex.code
        except Exception as ex:
            if intentos <= 3:
                log("   error de red (%s); reintento %d" % (type(ex).__name__, intentos))
                time.sleep(45)
                continue
            return -1


def catalogo(local):
    p = DESC / "flujos.json"
    if not p.exists() or not local:
        req = urllib.request.Request("%s/dataflow/%s?detail=allstubs" % (API, AGENCIA),
                                     headers=dict(UA, Accept="application/vnd.sdmx.structure+json;version=1.0"))
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                p.write_bytes(r.read())
            time.sleep(PAUSA)
        except Exception as ex:
            if not p.exists():
                raise
            log("no se pudo refrescar el catálogo (%s); se usa el guardado" % type(ex).__name__)
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for f in d["data"]["dataflows"]:
        n = f.get("name")
        if isinstance(n, dict):
            n = n.get("en")
        out.append((f["id"], f["version"], n or f.get("names", {}).get("en", "")))
    return out


def parte(v):
    """'PER: Peru' -> ('PER', 'Peru'); '2022' -> ('2022', '')."""
    i = v.find(": ")
    if i > 0 and " " not in v[:i]:
        return v[:i], v[i + 2:]
    return v, ""


SQL_BASE = """
CREATE SCHEMA IF NOT EXISTS ocde;
CREATE TABLE IF NOT EXISTS ocde.salud_flujo (
    flujo text PRIMARY KEY, version text, nombre text, url text, filas bigint, columnas text, cargado_en timestamptz);
CREATE TABLE IF NOT EXISTS ocde.salud_codigo (
    dim text, codigo text, etiqueta text, PRIMARY KEY (dim, codigo));
CREATE TABLE IF NOT EXISTS ocde.salud_obs (
    flujo text NOT NULL, ref_area text, medida text, unidad text, periodo text,
    valor text, estado text, dims jsonb, archivo_id bigint);
COMMENT ON SCHEMA ocde IS 'Crudo de la OCDE (Organización para la Cooperación y el Desarrollo Económicos): todo texto, tal como lo publica su interfaz SDMX.';
COMMENT ON TABLE ocde.salud_obs IS 'Estadísticas de salud de la OCDE: una fila por observación de cada flujo de OECD.ELS.HD, todos los países. Fuente: https://sdmx.oecd.org/public/rest. Se consulta por ref.ocde_salud.';
COMMENT ON TABLE ocde.salud_flujo IS 'Catálogo de flujos de datos de salud de la OCDE (agencia OECD.ELS.HD).';
COMMENT ON TABLE ocde.salud_codigo IS 'Diccionario código -> etiqueta en inglés de cada dimensión de los flujos de salud de la OCDE.';
"""

SQL_REF = r"""
CREATE INDEX IF NOT EXISTS i_ocde_obs_area  ON ocde.salud_obs (ref_area);
CREATE INDEX IF NOT EXISTS i_ocde_obs_flujo ON ocde.salud_obs (flujo, medida, unidad);
ANALYZE ocde.salud_obs;
CREATE OR REPLACE VIEW ref.ocde_salud AS
SELECT o.flujo,
       f.nombre                                   AS flujo_nombre,
       o.ref_area                                 AS pais_iso3,
       cp.etiqueta                                AS pais,
       o.medida,
       cm.etiqueta                                AS medida_nombre,
       o.unidad,
       cu.etiqueta                                AS unidad_nombre,
       o.periodo,
       CASE WHEN o.periodo ~ '^\d{4}$' THEN o.periodo::int END                          AS anio,
       CASE WHEN o.valor ~ '^-?\d+(\.\d+)?([eE][-+]?\d+)?$' THEN o.valor::numeric END    AS valor,
       o.estado,
       o.dims
FROM   ocde.salud_obs o
LEFT   JOIN ocde.salud_flujo  f  ON f.flujo = o.flujo
LEFT   JOIN ocde.salud_codigo cp ON cp.dim = 'REF_AREA'     AND cp.codigo = o.ref_area
LEFT   JOIN ocde.salud_codigo cm ON cm.dim = 'MEASURE'      AND cm.codigo = o.medida
LEFT   JOIN ocde.salud_codigo cu ON cu.dim = 'UNIT_MEASURE' AND cu.codigo = o.unidad;
COMMENT ON VIEW ref.ocde_salud IS 'OCDE, estadísticas de salud de todos los países, tipadas. dims trae el resto de dimensiones (sexo, edad, profesión…) como jsonb; sus etiquetas están en ocde.salud_codigo. Varios flujos son recortes de otro mayor: elegir un flujo por indicador.';
"""


def aterriza(cx, fid, ruta, archivo_id):
    """Carga un CSV comprimido del flujo fid. Devuelve (filas, cabecera)."""
    cod, filas, cab = {}, 0, ""
    with cx.cursor() as cur:
        cur.execute("DELETE FROM ocde.salud_obs WHERE flujo = %s", (fid,))
        with gzip.open(ruta, "rt", encoding="utf-8", newline="") as f:
            rd = csv.reader(f)
            head = next(rd, None)
            if not head:
                return 0, ""
            cols = [parte(h)[0] for h in head]
            cab = " | ".join(head)
            ix = {c: i for i, c in enumerate(cols)}
            otros = [(c, i) for i, c in enumerate(cols) if c not in FIJAS]

            def g(row, c):
                i = ix.get(c)
                if i is None or row[i] == "":
                    return None
                k, lab = parte(row[i])
                if lab:
                    cod[(c, k)] = lab
                return k

            with cur.copy("COPY ocde.salud_obs (flujo, ref_area, medida, unidad, periodo, valor, estado, dims, archivo_id) FROM STDIN") as cp:
                for row in rd:
                    if len(row) < len(cols):
                        continue
                    d = {}
                    for c, i in otros:
                        if row[i] == "":
                            continue
                        k, lab = parte(row[i])
                        if lab:
                            cod[(c, k)] = lab
                        d[c] = k
                    cp.write_row((fid, g(row, "REF_AREA"), g(row, "MEASURE"), g(row, "UNIT_MEASURE"),
                                  row[ix["TIME_PERIOD"]] if "TIME_PERIOD" in ix else None,
                                  row[ix["OBS_VALUE"]] if "OBS_VALUE" in ix else None,
                                  g(row, "OBS_STATUS"), json.dumps(d, ensure_ascii=False, separators=(",", ":")), archivo_id))
                    filas += 1
        if cod:
            cur.executemany("INSERT INTO ocde.salud_codigo (dim, codigo, etiqueta) VALUES (%s,%s,%s) ON CONFLICT (dim, codigo) DO UPDATE SET etiqueta = EXCLUDED.etiqueta",
                            [(a, b, c) for (a, b), c in cod.items()])
    return filas, cab


def main():
    local = "--local" in sys.argv
    rehacer = "--rehacer" in sys.argv
    DESC.mkdir(parents=True, exist_ok=True)
    e = env()
    t0 = time.time()
    cx = psycopg.connect(host=e["PGHOST"], port=e["PGPORT"], user=e["PGUSER"], password=e["PGPASSWORD"], dbname=e.get("PGDATABASE", "bases_pais"))
    with cx.cursor() as cur:
        cur.execute(SQL_BASE)
        cur.execute("""INSERT INTO meta.fuente (fuente_id, nombre, organismo, portal, api, licencia, notas)
                       VALUES (%(fuente_id)s, %(nombre)s, %(organismo)s, %(portal)s, %(api)s, %(licencia)s, %(notas)s)
                       ON CONFLICT (fuente_id) DO UPDATE SET nombre = EXCLUDED.nombre, organismo = EXCLUDED.organismo,
                           portal = EXCLUDED.portal, api = EXCLUDED.api, licencia = EXCLUDED.licencia, notas = EXCLUDED.notas""", FUENTE)
        cur.execute("""INSERT INTO meta.dataset (dataset_id, fuente_id, nombre, esquema, tabla, ckan_id, filtro_recurso, periodicidad, personales, clave_negocio, notas)
                       VALUES (%(dataset_id)s, %(fuente_id)s, %(nombre)s, %(esquema)s, %(tabla)s, %(ckan_id)s, %(filtro)s, %(periodicidad)s, %(personales)s, %(clave_negocio)s, %(notas)s)
                       ON CONFLICT (dataset_id) DO UPDATE SET nombre = EXCLUDED.nombre, esquema = EXCLUDED.esquema, tabla = EXCLUDED.tabla,
                           periodicidad = EXCLUDED.periodicidad, personales = EXCLUDED.personales, clave_negocio = EXCLUDED.clave_negocio, notas = EXCLUDED.notas""", DS)
    cx.commit()

    flujos = catalogo(local)
    log("flujos de salud de la OCDE:", len(flujos), "| descargas en", DESC)
    ok = err = salt = 0
    for k, (fid, ver, nom) in enumerate(flujos, 1):
        url = "%s/data/%s,%s,%s/all?dimensionAtObservation=AllDimensions" % (API, AGENCIA, fid, ver)
        ruta = DESC / nombre_archivo(fid)
        try:
            if (rehacer or not ruta.exists()) and not local:
                http = pide(url, ruta, ACEPTA_CSV)
                time.sleep(PAUSA)
                if http != 200:
                    raise RuntimeError("la OCDE respondió HTTP %s" % http)
            if not ruta.exists():
                raise RuntimeError("no está el archivo en descargas y se pidió --local")
            huella, tam = sha256(ruta), ruta.stat().st_size
            with cx.cursor() as cur:
                cur.execute("SELECT archivo_id FROM meta.archivo WHERE dataset_id = %s AND sha256 = %s", (DATASET, huella))
                ya = cur.fetchone()
            if ya and not rehacer:
                salt += 1
                continue
            with cx.cursor() as cur:
                cur.execute("""INSERT INTO meta.archivo (dataset_id, url, nombre, formato, periodo, sha256, bytes, ruta_local)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING archivo_id""",
                            (DATASET, url, ruta.name, "csv.gz", datetime.date.today().strftime("%Y%m"), huella, tam, str(ruta)))
                archivo_id = cur.fetchone()[0]
                cur.execute("INSERT INTO meta.carga (archivo_id, dataset_id, destino) VALUES (%s,%s,%s) RETURNING carga_id",
                            (archivo_id, DATASET, "ocde.salud_obs  [%s]" % fid))
                carga_id = cur.fetchone()[0]
            cx.commit()
            try:
                n, cab = aterriza(cx, fid, ruta, archivo_id)
                with cx.cursor() as cur:
                    cur.execute("UPDATE meta.carga SET filas = %s, columnas = %s, fin = now(), estado = 'ok' WHERE carga_id = %s", (n, cab.count("|") + 1 if cab else 0, carga_id))
                    cur.execute("""INSERT INTO ocde.salud_flujo (flujo, version, nombre, url, filas, columnas, cargado_en) VALUES (%s,%s,%s,%s,%s,%s, now())
                                   ON CONFLICT (flujo) DO UPDATE SET version = EXCLUDED.version, nombre = EXCLUDED.nombre, url = EXCLUDED.url,
                                       filas = EXCLUDED.filas, columnas = EXCLUDED.columnas, cargado_en = now()""", (fid, ver, nom, url, n, cab))
                cx.commit()
                ok += 1
                log("[%d/%d] + %s  ->  %s filas" % (k, len(flujos), fid, format(n, ",").replace(",", " ")))
            except Exception as ex:
                cx.rollback()
                with cx.cursor() as cur:
                    cur.execute("UPDATE meta.carga SET fin = now(), estado = 'error', mensaje = %s, archivo_id = NULL WHERE carga_id = %s", (str(ex)[:2000], carga_id))
                    cur.execute("DELETE FROM meta.archivo WHERE archivo_id = %s", (archivo_id,))
                cx.commit()
                err += 1
                log("[%d/%d] ! %s  ERROR al cargar: %s" % (k, len(flujos), fid, ex))
        except Exception as ex:
            cx.rollback()
            with cx.cursor() as cur:
                cur.execute("INSERT INTO meta.carga (dataset_id, destino, inicio, fin, estado, mensaje) VALUES (%s,%s, now(), now(), 'error', %s)",
                            (DATASET, "ocde.salud_obs  [%s]" % fid, ("no se pudo procesar: %s" % ex)[:1500]))
            cx.commit()
            err += 1
            log("[%d/%d] ! %s  %s" % (k, len(flujos), fid, ex))

    log("índices y vista ref.ocde_salud…")
    with cx.cursor() as cur:
        cur.execute(SQL_REF)
    cx.commit()
    with cx.cursor() as cur:
        cur.execute("SELECT count(*), count(DISTINCT flujo), count(DISTINCT ref_area) FROM ocde.salud_obs")
        tot = cur.fetchone()
        cur.execute("SELECT count(*), count(DISTINCT flujo) FROM ocde.salud_obs WHERE ref_area = 'PER'")
        per = cur.fetchone()
        cur.execute("SELECT pg_size_pretty(pg_total_relation_size('ocde.salud_obs'))")
        peso = cur.fetchone()[0]
    log("LISTO en %d s: %d cargados, %d sin cambios, %d con error." % (time.time() - t0, ok, salt, err))
    log("ocde.salud_obs: %s observaciones, %d flujos, %d áreas, %s. Perú: %s observaciones en %d flujos." % (
        format(tot[0], ",").replace(",", " "), tot[1], tot[2], peso, format(per[0], ",").replace(",", " "), per[1]))
    cx.close()


if __name__ == "__main__":
    main()
