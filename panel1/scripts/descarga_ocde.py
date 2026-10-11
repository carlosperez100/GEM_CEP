# -*- coding: utf-8 -*-
"""Descarga TODOS los flujos de datos de salud de la OCDE (agencia OECD.ELS.HD) por su interfaz
pública SDMX y los carga en SQLite, observación por observación, sin agregar ni filtrar.

Fuente: https://sdmx.oecd.org/public/rest  (la misma que alimenta https://data-explorer.oecd.org)
Uso:    python -I descarga_ocde.py [carpeta_destino]
Reanudable: un flujo ya descargado y cargado no se vuelve a pedir.
"""
import csv, datetime, gzip, io, json, os, re, shutil, sqlite3, sys, time, urllib.error, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://sdmx.oecd.org/public/rest"
AGENCIA = "OECD.ELS.HD"
OUT = sys.argv[1] if len(sys.argv) > 1 else r"T:\OCDE_SALUD"
CRUDO = os.path.join(OUT, "crudo")
DB = os.path.join(OUT, "ocde_salud.db")
LOG = os.path.join(OUT, "descarga.log")
PAUSA = 10          # segundos entre pedidos
ESPERA_429 = 900    # segundos si el servidor pide bajar el ritmo
UA = {"User-Agent": "Mozilla/5.0 (investigacion academica; descarga unica)"}
os.makedirs(CRUDO, exist_ok=True)
csv.field_size_limit(10 ** 9)


def log(*a):
    s = "%s  %s" % (datetime.datetime.now().strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    print(s, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def pide(url, destino, accept):
    """Descarga url a destino (gzip). Devuelve (estado_http, bytes_sin_comprimir)."""
    intentos = 0
    while True:
        intentos += 1
        req = urllib.request.Request(url, headers=dict(UA, Accept=accept))
        try:
            with urllib.request.urlopen(req, timeout=300) as r, gzip.open(destino + ".tmp", "wb", compresslevel=5) as g:
                n = 0
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    g.write(b)
                    n += len(b)
            os.replace(destino + ".tmp", destino)
            return 200, n
        except urllib.error.HTTPError as ex:
            if ex.code == 429 and intentos <= 10:
                ra = ex.headers.get("Retry-After")
                esp = max(ESPERA_429, int(ra)) if ra and ra.isdigit() else ESPERA_429
                log("   429: el servidor pide esperar; duermo %d s (intento %d)" % (esp, intentos))
                time.sleep(esp)
                continue
            if ex.code in (500, 502, 503, 504) and intentos <= 3:
                time.sleep(60)
                continue
            return ex.code, 0
        except Exception as ex:
            if intentos <= 3:
                log("   error de red (%s); reintento %d" % (type(ex).__name__, intentos))
                time.sleep(45)
                continue
            return -1, 0


def lista_flujos():
    p = os.path.join(OUT, "flujos.json")
    if not os.path.exists(p):
        req = urllib.request.Request("%s/dataflow/%s?detail=allstubs" % (BASE, AGENCIA), headers=dict(UA, Accept="application/vnd.sdmx.structure+json;version=1.0"))
        with urllib.request.urlopen(req, timeout=120) as r, io.open(p, "wb") as f:
            shutil.copyfileobj(r, f)
        time.sleep(PAUSA)
    d = json.load(io.open(p, encoding="utf-8"))
    out = []
    for f in d["data"]["dataflows"]:
        n = f.get("name")
        if isinstance(n, dict):
            n = n.get("en")
        out.append((f["id"], f["version"], n or f.get("names", {}).get("en", "")))
    return out


def base():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=OFF")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS flujos (id TEXT PRIMARY KEY, version TEXT, nombre TEXT, url TEXT, http INTEGER, bytes INTEGER, filas INTEGER, partes INTEGER, descargado TEXT, columnas TEXT);
    CREATE TABLE IF NOT EXISTS obs (flujo TEXT, pais TEXT, medida TEXT, unidad TEXT, periodo TEXT, valor REAL, valor_txt TEXT, estado TEXT, dims TEXT);
    CREATE TABLE IF NOT EXISTS codigos (dim TEXT, codigo TEXT, etiqueta TEXT, PRIMARY KEY (dim, codigo));
    """)
    return con


FIJAS = {"DATAFLOW", "REF_AREA", "MEASURE", "UNIT_MEASURE", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"}


def parte(v):
    """'PER: Peru' -> ('PER', 'Peru'); '2022' -> ('2022', '')."""
    i = v.find(": ")
    if i > 0 and " " not in v[:i]:
        return v[:i], v[i + 2:]
    return v, ""


def carga(con, fid, archivos):
    """Carga uno o más CSV comprimidos del flujo fid en la tabla obs. Devuelve (filas, columnas)."""
    con.execute("DELETE FROM obs WHERE flujo = ?", (fid,))
    filas, cols_txt = 0, ""
    cod = {}
    for a in archivos:
        with gzip.open(a, "rt", encoding="utf-8", newline="") as f:
            rd = csv.reader(f)
            try:
                head = next(rd)
            except StopIteration:
                continue
            cols = [parte(h)[0] for h in head]
            cols_txt = " | ".join(head)
            ix = {c: i for i, c in enumerate(cols)}
            otros = [(c, i) for i, c in enumerate(cols) if c not in FIJAS]
            lote = []
            for row in rd:
                if len(row) < len(cols):
                    continue

                def g(c):
                    i = ix.get(c)
                    if i is None:
                        return "", ""
                    k, lab = parte(row[i])
                    if lab:
                        cod[(c, k)] = lab
                    return k, lab

                pais = g("REF_AREA")[0]
                med = g("MEASURE")[0]
                uni = g("UNIT_MEASURE")[0]
                est = g("OBS_STATUS")[0]
                per = row[ix["TIME_PERIOD"]] if "TIME_PERIOD" in ix else ""
                vt = row[ix["OBS_VALUE"]] if "OBS_VALUE" in ix else ""
                try:
                    v = float(vt)
                except ValueError:
                    v = None
                d = {}
                for c, i in otros:
                    if row[i] == "":
                        continue
                    k, lab = parte(row[i])
                    if lab:
                        cod[(c, k)] = lab
                    d[c] = k
                lote.append((fid, pais, med, uni, per, v, vt, est, json.dumps(d, ensure_ascii=False, separators=(",", ":"))))
                if len(lote) >= 50000:
                    con.executemany("INSERT INTO obs VALUES (?,?,?,?,?,?,?,?,?)", lote)
                    filas += len(lote)
                    lote = []
            if lote:
                con.executemany("INSERT INTO obs VALUES (?,?,?,?,?,?,?,?,?)", lote)
                filas += len(lote)
    con.executemany("INSERT OR IGNORE INTO codigos VALUES (?,?,?)", [(a, b, c) for (a, b), c in cod.items()])
    con.commit()
    return filas, cols_txt


def nombre(fid):
    return re.sub(r"[^A-Za-z0-9]+", "_", fid)


def main():
    con = base()
    fl = lista_flujos()
    log("flujos de salud en la interfaz de la OCDE:", len(fl), "| destino:", OUT)
    acc = "application/vnd.sdmx.data+csv; charset=utf-8; labels=both"
    for k, (fid, ver, nom) in enumerate(fl, 1):
        ya = con.execute("SELECT http, filas FROM flujos WHERE id = ?", (fid,)).fetchone()
        if ya and ya[0] == 200 and ya[1] is not None:
            continue
        url = "%s/data/%s,%s,%s/all?dimensionAtObservation=AllDimensions" % (BASE, AGENCIA, fid, ver)
        dest = os.path.join(CRUDO, nombre(fid) + ".csv.gz")
        log("[%d/%d] %s — %s" % (k, len(fl), fid, nom))
        http, n = pide(url, dest, acc)
        time.sleep(PAUSA)
        archivos, partes = [dest], 1
        if http != 200:
            # reintento por ventanas de cinco años, por si el flujo completo excede el límite del servidor
            log("   pedido completo devolvió", http, "-> pruebo por ventanas de cinco años")
            archivos, tot, alguno = [], 0, False
            for y in range(1960, 2030, 5):
                d2 = os.path.join(CRUDO, "%s__%d_%d.csv.gz" % (nombre(fid), y, y + 4))
                h2, n2 = pide(url + "&startPeriod=%d&endPeriod=%d" % (y, y + 4), d2, acc)
                time.sleep(PAUSA)
                if h2 == 200:
                    archivos.append(d2)
                    tot += n2
                    alguno = True
                elif h2 != 404:
                    log("   ventana %d-%d devolvió %s" % (y, y + 4, h2))
            if alguno:
                http, n, partes = 200, tot, len(archivos)
        filas, cols = (0, "")
        if http == 200:
            try:
                filas, cols = carga(con, fid, archivos)
            except Exception as ex:
                log("   ERROR al cargar:", type(ex).__name__, ex)
                http = -2
        con.execute("INSERT OR REPLACE INTO flujos VALUES (?,?,?,?,?,?,?,?,?,?)", (fid, ver, nom, url, http, n, filas, partes, datetime.datetime.now().isoformat(timespec="seconds"), cols))
        con.commit()
        log("   http %s | %.1f MB | %d filas | %d parte(s)" % (http, n / 1e6, filas, partes))
    log("creo índices…")
    con.executescript("""
    CREATE INDEX IF NOT EXISTS i_obs_pais ON obs (pais);
    CREATE INDEX IF NOT EXISTS i_obs_fm ON obs (flujo, medida, unidad);
    CREATE INDEX IF NOT EXISTS i_obs_med ON obs (medida);
    """)
    con.commit()
    r = con.execute("SELECT COUNT(*), SUM(http = 200), SUM(filas), SUM(bytes) FROM flujos").fetchone()
    per = con.execute("SELECT COUNT(*), COUNT(DISTINCT flujo) FROM obs WHERE pais = 'PER'").fetchone()
    pa = con.execute("SELECT COUNT(DISTINCT pais) FROM obs").fetchone()[0]
    log("FIN: %d flujos, %d descargados, %d observaciones, %.1f MB sin comprimir; %d áreas; Perú: %d observaciones en %d flujos" % (r[0], r[1] or 0, r[2] or 0, (r[3] or 0) / 1e6, pa, per[0], per[1]))
    mal = con.execute("SELECT id, http FROM flujos WHERE http != 200").fetchall()
    if mal:
        log("flujos que NO se pudieron descargar:", mal)
    con.close()


if __name__ == "__main__":
    main()
