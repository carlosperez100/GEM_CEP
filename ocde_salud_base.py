# -*- coding: utf-8 -*-
"""
ocde_salud_base.py — Base OCDE·Salud organizada por indicador × país × año
==========================================================================
Baja los conjuntos del tema **Health** del OECD Data Explorer
(https://data-explorer.oecd.org/?fs[0]=Topic,0%7CHealth%23HEA%23) por la API
SDMX pública (`sdmx.oecd.org`) y los deja en UNA base con tres llaves:
indicador, país y año.

    python ocde_salud_base.py                       # todo el tema Salud, totales
    python ocde_salud_base.py --paises PER CHL COL MEX CRI BRA ARG OECD
    python ocde_salud_base.py --flujos DF_HEALTH_STATUS DF_SHA --desde 2010
    python ocde_salud_base.py --completo             # también los desgloses
    python ocde_salud_base.py --solo-consolidar      # no descarga: usa el crudo

Salida (en `salida/ocde_salud/`, carpeta ignorada por git):

    crudo/<flujo>.csv            lo que devolvió la API, tal cual (caché)
    catalogo_indicadores.csv     un renglón por indicador: flujo, código,
                                 nombre, unidad, países, años, observaciones
    base_larga.csv               fuente · indicador · país · año · valor
    base_ocde_salud.xlsx         "Catálogo", "Base larga" y una hoja por
                                 flujo con indicador×país en filas y años en
                                 columnas

QUÉ ES "INDICADOR". Cada flujo OCDE tiene una dimensión MEASURE (el
indicador propiamente) y otras de desglose (sexo, edad, tipo de proveedor,
esquema de financiamiento…). Por defecto la base guarda el TOTAL de cada
desglose (código `_T`, o `_Z` cuando no aplica) para que un indicador sea
una sola serie por país y año. Si un desglose no tiene total, cada valor
se vuelve un indicador distinto (el nombre lleva la etiqueta). Con
`--completo` se guardan todos los desgloses y el nombre del indicador
concatena cada etiqueta.

POR QUÉ SE DESCUBREN LOS FLUJOS EN VEZ DE LISTARLOS A MANO. La OCDE
renombra y versiona los dataflows; la lista fija queda vieja. El script
pide a la API los dataflows de la agencia `OECD.ELS.HD` (la División de
Salud, dueña del tema Health) y filtra los que no son de salud por
palabra clave si se pide (`--filtro`).

POR QUÉ LOS PAÍSES SE PIDEN AL SERVIDOR. Con `--paises` la clave SDMX lleva
los países en la posición de REF_AREA (se lee del DSD de cada flujo), así
que la API devuelve solo esas filas: el gasto en salud (SHA) completo pesa
cientos de MB y tumba un runner por memoria; filtrado por país son unos
MB. La respuesta se escribe a disco y se lee por trozos. Sin `--paises`
se baja todo y hay que tener memoria para ello.

POR QUÉ SE PARTE POR AÑOS CUANDO FALLA. La API corta respuestas enormes
(SHA, PHARMA). Si una descarga falla, se reintenta por mitades del rango
de años hasta llegar a un año por petición; lo que aun así falle se
anota y se sigue.

Los archivos descargados son datos externos: ejecútese con `python -I`
si se corre desde una carpeta compartida.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

API = "https://sdmx.oecd.org/public/rest"
AGENCIA = "OECD.ELS.HD"
SALIDA = Path("salida") / "ocde_salud"
USER_AGENT = "GEM-VigIA/ocde_salud_base (https://github.com/carlosperez100/gem-vigia)"

# Columnas de la respuesta `csvfilewithlabels` que NO son dimensiones.
NO_DIMENSION = {
    "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION", "OBS_VALUE",
    "OBS_STATUS", "OBS_STATUS2", "OBS_STATUS3", "UNIT_MULT", "DECIMALS",
    "BASE_PER", "CONF_STATUS", "COMMENT_OBS", "COMMENT_TS", "OBS_PRE_BREAK",
    "DATA_COMP", "SOURCE", "CURRENCY", "PRICE_BASE", "TRANSFORMATION",
    "TIME_FORMAT", "REF_PERIOD_DETAIL", "COMPILING_ORG", "DISS_ORG",
    "CALC_METHODOLOGY", "ADJUSTMENT", "UNIT_MEASURE", "FREQ",
}
LLAVES = {"REF_AREA", "TIME_PERIOD", "MEASURE"}
CODIGOS_TOTAL = {"_T", "_Z", "TOT", "TOTAL", "ALL"}
# Los 38 miembros de la OCDE (ISO-3). Las tablas de salud no traen el
# agregado "OECD": el promedio se calcula aquí, simple y sin ponderar,
# sobre los miembros con dato, como en Health at a Glance.
MIEMBROS_OCDE = [
    "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST", "FIN",
    "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN", "KOR", "LVA",
    "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN", "ESP",
    "SWE", "CHE", "TUR", "GBR", "USA",
]
CODIGO_PROMEDIO = "OCDE"
NS = {
    "mes": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}


# ── HTTP ──────────────────────────────────────────────────────────────────────
def _abrir(url: str, accept: str, intentos: int = 4, espera: float = 2.0):
    """Abre la URL con reintento. Devuelve la respuesta abierta o None si 404.

    La API de la OCDE limita peticiones (HTTP 429) por ventanas de varios
    minutos: ahí se respeta `Retry-After` si viene y, si no, se espera
    1, 2, 4, 8, 15, 15, 15, 15 min antes de rendirse. Un 413/400 (respuesta
    demasiado grande) se propaga para que el llamador parta la petición.
    """
    ultimo: Exception | None = None
    i = 0
    limites = 0
    while i < intentos:
        req = urllib.request.Request(url, headers={"Accept": accept,
                                                   "User-Agent": USER_AGENT})
        try:
            return urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            ultimo = e
            if e.code in (413, 400):
                raise
            if e.code == 429:
                limites += 1
                if limites > 8:
                    break
                cabecera = e.headers.get("Retry-After") if e.headers else None
                pausa = float(cabecera) if cabecera and cabecera.isdigit() else 0.0
                pausa = max(pausa, min(60.0 * 2 ** (limites - 1), 900.0))
                print(f"    … límite de peticiones (429); espero {pausa/60:.0f} min",
                      flush=True)
                time.sleep(pausa)
                continue            # un 429 no consume intentos ordinarios
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            ultimo = e
        i += 1
        time.sleep(espera * (2 ** i))
    raise RuntimeError(f"{url}: {ultimo}")


def _get(url: str, accept: str) -> bytes:
    r = _abrir(url, accept)
    if r is None:
        return b""
    with r:
        return r.read()


# ── Descubrir flujos ──────────────────────────────────────────────────────────
def listar_flujos(agencia: str = AGENCIA, filtro: str | None = None) -> list[dict]:
    """Dataflows de la agencia: [{id, agencia, version, nombre}]."""
    xml = _get(f"{API}/dataflow/{agencia}", "application/xml")
    raiz = ET.fromstring(xml)
    flujos = []
    for df in raiz.iter(f"{{{NS['str']}}}Dataflow"):
        nombre = ""
        for n in df.findall("com:Name", NS):
            if n.get("{http://www.w3.org/XML/1998/namespace}lang", "en") == "en":
                nombre = n.text or ""
                break
            nombre = nombre or (n.text or "")
        flujos.append({"id": df.get("id"), "agencia": df.get("agencyID"),
                       "version": df.get("version"), "nombre": nombre})
    if filtro:
        f = filtro.lower()
        flujos = [x for x in flujos if f in x["nombre"].lower() or f in x["id"].lower()]
    return sorted(flujos, key=lambda x: x["id"])


def dimensiones_flujo(flujo: dict) -> list[str]:
    """Ids de las dimensiones del DSD del flujo, en el orden de la clave.

    Hace falta para pedir a la API solo los países que interesan: la
    posición de REF_AREA cambia entre DSD, así que la clave se arma
    leyendo la estructura. Si algo falla devuelve [] y se pide todo.
    """
    try:
        xml = _get(f"{API}/dataflow/{flujo['agencia']}/{flujo['id']}/{flujo['version']}"
                   "?references=datastructure", "application/xml")
        raiz = ET.fromstring(xml)
        dims = []
        for lista in raiz.iter(f"{{{NS['str']}}}DimensionList"):
            for d in lista.findall("str:Dimension", NS):
                dims.append((int(d.get("position", len(dims) + 1)), d.get("id")))
        return [d for _, d in sorted(dims)]
    except Exception:  # noqa: BLE001 — estructura ilegible: se pide todo
        return []


# ── Descargar un flujo ────────────────────────────────────────────────────────
def _url_datos(flujo: dict, clave: str, desde: int | None, hasta: int | None) -> str:
    q = {"dimensionAtObservation": "AllDimensions", "format": "csvfilewithlabels"}
    if desde:
        q["startPeriod"] = str(desde)
    if hasta:
        q["endPeriod"] = str(hasta)
    return (f"{API}/data/{flujo['agencia']},{flujo['id']},{flujo['version']}/"
            f"{clave}?{urllib.parse.urlencode(q)}")


def _clave(flujo: dict, paises: list[str] | None) -> str:
    """Clave SDMX: países en la posición de REF_AREA, comodín en el resto."""
    if not paises:
        return "all"
    dims = dimensiones_flujo(flujo)
    if "REF_AREA" not in dims:
        return "all"
    return ".".join("+".join(paises) if d == "REF_AREA" else "" for d in dims)


def _leer_csv(ruta: Path, paises: list[str] | None) -> pd.DataFrame:
    """Lee por trozos para no cargar en memoria lo que no se va a usar."""
    if not ruta.exists() or ruta.stat().st_size == 0:
        return pd.DataFrame()
    partes = []
    for trozo in pd.read_csv(ruta, dtype=str, keep_default_na=False, chunksize=200_000):
        if paises and "REF_AREA" in trozo.columns:
            trozo = trozo[trozo["REF_AREA"].isin(paises)]
        if len(trozo):
            partes.append(trozo)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def descargar_flujo(flujo: dict, desde: int | None, hasta: int | None,
                    paises: list[str] | None, log, destino: Path | None = None,
                    clave: str | None = None) -> pd.DataFrame:
    """CSV con etiquetas a disco (en trozos a memoria); parte por años si
    la API rechaza el tamaño."""
    clave = clave if clave is not None else _clave(flujo, paises)
    destino = destino or (Path("salida") / "ocde_salud" / "crudo" / f"{flujo['id']}.csv")
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".parcial")
    try:
        r = _abrir(_url_datos(flujo, clave, desde, hasta), "text/csv")
    except urllib.error.HTTPError as e:
        if e.code not in (413, 400):
            raise
        d, h = desde or 1960, hasta or time.localtime().tm_year
        if d >= h:
            log(f"    ✗ {flujo['id']} {d}: la API rechaza incluso un año ({e.code})")
            return pd.DataFrame()
        m = (d + h) // 2
        log(f"    ↳ {flujo['id']} demasiado grande; parto {d}-{m} / {m+1}-{h}")
        a = descargar_flujo(flujo, d, m, paises, log, destino.with_name(
            f"{destino.stem}_{d}_{m}.csv"), clave)
        b = descargar_flujo(flujo, m + 1, h, paises, log, destino.with_name(
            f"{destino.stem}_{m+1}_{h}.csv"), clave)
        return pd.concat([a, b], ignore_index=True)
    if r is None:
        destino.write_bytes(b"")
        return pd.DataFrame()
    with r, open(temporal, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    temporal.replace(destino)
    return _leer_csv(destino, paises)


# ── Consolidar ────────────────────────────────────────────────────────────────
def _pares_columna(df: pd.DataFrame) -> dict[str, str]:
    """{código: etiqueta} para columnas que vienen en pares (código, etiqueta).

    En `csvfilewithlabels` cada dimensión/atributo ocupa dos columnas
    contiguas: `REF_AREA`, `Reference area`. La etiqueta es la que sigue
    inmediatamente al código y no es ella misma un código (mayúsculas con _).
    """
    cols = list(df.columns)
    pares = {}
    for i, c in enumerate(cols):
        if c != c.upper() or not c.replace("_", "").isalnum():
            continue
        sig = cols[i + 1] if i + 1 < len(cols) else None
        if sig and sig != sig.upper():
            pares[c] = sig
    return pares


def consolidar_flujo(df: pd.DataFrame, flujo: dict, completo: bool,
                     log) -> pd.DataFrame:
    """Devuelve filas largas: fuente, indicador_codigo, indicador, unidad,
    desglose, pais_codigo, pais, periodo, anio, valor, estado."""
    if df.empty or "OBS_VALUE" not in df.columns:
        return pd.DataFrame()
    pares = _pares_columna(df)

    def et(col):  # etiqueta o el propio código si no hay
        return df[pares[col]] if col in pares else df[col]

    dims = [c for c in pares if c not in NO_DIMENSION and c not in LLAVES]
    base = pd.DataFrame({
        "fuente": flujo["id"],
        "fuente_nombre": flujo.get("nombre", ""),
        "indicador_codigo": df["MEASURE"] if "MEASURE" in df else "",
        "indicador": et("MEASURE") if "MEASURE" in df else flujo.get("nombre", ""),
        "unidad": et("UNIT_MEASURE") if "UNIT_MEASURE" in df else "",
        "pais_codigo": df["REF_AREA"] if "REF_AREA" in df else "",
        "pais": et("REF_AREA") if "REF_AREA" in df else "",
        "periodo": df["TIME_PERIOD"] if "TIME_PERIOD" in df else "",
        "valor": pd.to_numeric(df["OBS_VALUE"], errors="coerce"),
        "estado": et("OBS_STATUS") if "OBS_STATUS" in df else "",
    })
    base["anio"] = pd.to_numeric(base["periodo"].str[:4], errors="coerce").astype("Int64")

    mascara = pd.Series(True, index=df.index)
    sufijo_cod, sufijo_et = [], []
    for d in dims:
        valores = set(df[d].unique())
        totales = valores & CODIGOS_TOTAL
        if totales and not completo:
            mascara &= df[d].isin(totales)
        elif len(valores) > 1 or completo:
            sufijo_cod.append(df[d])
            sufijo_et.append(et(d))
    if sufijo_cod:
        cod = pd.concat(sufijo_cod, axis=1).agg(".".join, axis=1)
        etq = pd.concat(sufijo_et, axis=1).agg(" · ".join, axis=1)
        base["indicador_codigo"] = base["indicador_codigo"] + "." + cod
        base["desglose"] = etq
        base["indicador"] = base["indicador"] + " [" + etq + "]"
    else:
        base["desglose"] = ""
    if "UNIT_MEASURE" in df and df["UNIT_MEASURE"].nunique() > 1:
        base["indicador_codigo"] = base["indicador_codigo"] + "." + df["UNIT_MEASURE"]
        base["indicador"] = base["indicador"] + " (" + base["unidad"] + ")"

    out = base[mascara & base["valor"].notna() & base["anio"].notna()].copy()
    if out.empty and not completo and dims and base["valor"].notna().any():
        # Los totales de cada desglose no coinciden en una misma fila (p. ej.
        # edad total solo por sexo y sexo total solo por edad): se guardan los
        # desgloses con su etiqueta en vez de perder el flujo.
        log(f"    {flujo['id']}: sin fila con todos los totales; guardo desgloses")
        return consolidar_flujo(df, flujo, True, log)
    out = out.drop_duplicates(["fuente", "indicador_codigo", "pais_codigo", "periodo"])
    nota = "" if out.size or base["valor"].notna().any() else " (valores no numéricos)"
    log(f"    {flujo['id']}: {len(df):,} obs crudas → {len(out):,} en base "
        f"({out['indicador_codigo'].nunique()} indicadores, "
        f"{out['pais_codigo'].nunique()} países){nota}")
    out["n_promedio"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    return out[["fuente", "fuente_nombre", "indicador_codigo", "indicador", "unidad",
                "desglose", "pais_codigo", "pais", "periodo", "anio", "valor", "estado",
                "n_promedio"]]


def promedio_ocde(base: pd.DataFrame, miembros: list[str], minimo: int) -> pd.DataFrame:
    """Filas "OCDE": promedio simple por indicador y periodo sobre los
    miembros con dato; `n_promedio` dice cuántos entraron y se exige al
    menos `minimo` para no llamar promedio a dos países."""
    sub = base[base["pais_codigo"].isin(miembros)]
    if sub.empty:
        return pd.DataFrame()
    llaves = ["fuente", "fuente_nombre", "indicador_codigo", "indicador", "unidad",
              "desglose", "periodo"]
    g = (sub.groupby(llaves, as_index=False, sort=False)
            .agg(anio=("anio", "first"), valor=("valor", "mean"),
                 n_promedio=("valor", "size")))
    g = g[g["n_promedio"] >= minimo].copy()
    g["valor"] = g["valor"].round(3)
    g["pais_codigo"] = CODIGO_PROMEDIO
    g["pais"] = "OCDE (promedio simple)"
    g["estado"] = "Promedio simple de miembros OCDE con dato"
    return g


def catalogo(base: pd.DataFrame) -> pd.DataFrame:
    g = base.groupby(["fuente", "fuente_nombre", "indicador_codigo", "indicador", "unidad"],
                     as_index=False)
    cat = g.agg(n_paises=("pais_codigo", "nunique"), anio_min=("anio", "min"),
                anio_max=("anio", "max"), n_obs=("valor", "size"))
    return cat.sort_values(["fuente", "indicador_codigo"]).reset_index(drop=True)


# ── Excel ─────────────────────────────────────────────────────────────────────
def escribir_excel(base: pd.DataFrame, cat: pd.DataFrame, ruta: Path, log) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    MAX_FILAS = 1_000_000
    leeme = pd.DataFrame({"GEM·VigIA — Base OCDE·Salud": [
        "Fuente: OECD Data Explorer, tema Health (https://data-explorer.oecd.org), "
        "API SDMX https://sdmx.oecd.org/public/rest, agencia OECD.ELS.HD.",
        f"Descargado: {time.strftime('%Y-%m-%d')}. Generado por ocde_salud_base.py.",
        "Catálogo: un renglón por indicador (flujo, código, nombre, unidad, cobertura).",
        "Base larga: una fila por indicador × país × año (valor numérico; 'estado' = "
        "OBS_STATUS de la OCDE: E estimado, P provisional, B quiebre de serie…).",
        "Hojas por flujo: filas = indicador × país, columnas = años. Celda vacía = sin dato.",
        "Salvo --completo, cada indicador es el TOTAL de sus desgloses (sexo, edad, etc.). "
        "Si un desglose no tiene total, cada valor aparece como indicador aparte [entre corchetes].",
        "Los códigos de país son ISO-3. La fila 'OCDE (promedio simple)' no viene de la OCDE: "
        "es el promedio sin ponderar de los miembros con dato en ese indicador y periodo "
        "('n_promedio' dice cuántos), como se calcula en Health at a Glance.",
    ]})
    with pd.ExcelWriter(ruta, engine="openpyxl") as xw:
        leeme.to_excel(xw, sheet_name="Léeme", index=False)
        cat.to_excel(xw, sheet_name="Catálogo", index=False)
        if len(base) <= MAX_FILAS:
            base.to_excel(xw, sheet_name="Base larga", index=False)
        else:
            log(f"    base larga de {len(base):,} filas supera Excel; va solo en CSV")
        for fuente, sub in base.groupby("fuente", sort=True):
            piv = (sub.pivot_table(index=["indicador", "unidad", "pais_codigo", "pais"],
                                   columns="anio", values="valor", aggfunc="first")
                   .reset_index())
            piv.columns = [str(c) for c in piv.columns]
            hoja = fuente.replace("DF_", "")[:31]
            if len(piv) > MAX_FILAS:
                log(f"    {fuente}: pivote de {len(piv):,} filas supera Excel; omitido")
                continue
            piv.to_excel(xw, sheet_name=hoja, index=False)

        fuente_base = Font(name="Arial", size=10)
        fuente_enc = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        relleno = PatternFill("solid", fgColor="1F4E78")
        for ws in xw.book.worksheets:
            for fila in ws.iter_rows():
                for c in fila:
                    c.font = fuente_base
            for c in ws[1]:
                c.font = fuente_enc
                c.fill = relleno
                c.alignment = Alignment(vertical="center", wrap_text=True)
            ws.freeze_panes = "A2"
            if ws.title == "Léeme":
                ws.column_dimensions["A"].width = 120
                continue
            ws.auto_filter.ref = ws.dimensions
            for i, col in enumerate(ws.iter_cols(min_row=1, max_row=min(ws.max_row, 200)), 1):
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                ws.column_dimensions[get_column_letter(i)].width = min(max(8, ancho + 2), 60)


# ── Programa ──────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--agencia", default=AGENCIA)
    p.add_argument("--flujos", nargs="*", help="ids de dataflow (DF_…); por defecto todos")
    p.add_argument("--filtro", help="palabra en el nombre/id del flujo")
    p.add_argument("--paises", nargs="*", help="códigos ISO-3 / agregados (OECD, EU27_2020)")
    p.add_argument("--desde", type=int)
    p.add_argument("--hasta", type=int)
    p.add_argument("--completo", action="store_true", help="guardar todos los desgloses")
    p.add_argument("--promedio", nargs="*", metavar="ISO3",
                   help="añadir filas OCDE = promedio simple de estos miembros "
                        "(sin lista: los 38 de la OCDE); se bajan aunque no estén en --paises")
    p.add_argument("--min-promedio", type=int, default=10,
                   help="miembros con dato que exige un promedio (por defecto 10)")
    p.add_argument("--conservar-miembros", action="store_true",
                   help="dejar en la base las filas de los miembros bajados solo para el promedio")
    p.add_argument("--solo-consolidar", action="store_true", help="no descargar; usar crudo/")
    p.add_argument("--forzar", action="store_true", help="volver a bajar aunque exista crudo")
    p.add_argument("--salida", type=Path, default=SALIDA)
    p.add_argument("--pausa", type=float, default=2.0, help="segundos entre peticiones")
    a = p.parse_args(argv)

    crudo = a.salida / "crudo"
    crudo.mkdir(parents=True, exist_ok=True)
    seleccion = list(a.paises) if a.paises else None
    miembros = None
    if a.promedio is not None:
        miembros = a.promedio or MIEMBROS_OCDE
        if a.paises:
            a.paises = sorted(set(a.paises) | set(miembros))
    log = lambda s: print(s, flush=True)  # noqa: E731

    if a.solo_consolidar:
        flujos = [{"id": f.stem, "agencia": a.agencia, "version": "", "nombre": ""}
                  for f in sorted(crudo.glob("*.csv"))]
        meta = crudo / "flujos.json"
        if meta.exists():
            nombres = {x["id"]: x for x in json.loads(meta.read_text(encoding="utf-8"))}
            flujos = [nombres.get(f["id"], f) for f in flujos]
    else:
        log(f"Flujos de {a.agencia}…")
        flujos = listar_flujos(a.agencia, a.filtro)
        (crudo / "flujos.json").write_text(json.dumps(flujos, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    if a.flujos:
        flujos = [f for f in flujos if f["id"] in set(a.flujos)]
    log(f"{len(flujos)} flujos")
    if not flujos:
        return 1

    partes = []
    fallidos: list[dict] = []

    def procesar(f: dict, pasada: int) -> None:
        ruta = crudo / f"{f['id']}.csv"
        if a.solo_consolidar or (ruta.exists() and not a.forzar):
            df = _leer_csv(ruta, a.paises)
        else:
            log(f"  ↓ {f['id']} — {f['nombre']}" + (" (segunda pasada)" if pasada else ""))
            try:
                df = descargar_flujo(f, a.desde, a.hasta, a.paises, log, ruta)
            except Exception as e:  # noqa: BLE001
                log(f"    ✗ {f['id']}: {e}")
                if pasada == 0:
                    fallidos.append(f)
                else:
                    fallidos_final.append(f["id"])
                return
            time.sleep(a.pausa)
        if df.empty:
            log(f"    {f['id']}: sin observaciones para esta selección")
            return
        partes.append(consolidar_flujo(df, f, a.completo, log))

    fallidos_final: list[str] = []
    for f in flujos:
        procesar(f, 0)
    if fallidos:
        # Los 429 llegan en racha: una segunda pasada al final suele bastar.
        log(f"\nSegunda pasada sobre {len(fallidos)} flujos que fallaron…")
        time.sleep(60)
        for f in fallidos:
            procesar(f, 1)
    fallidos = fallidos_final

    base = pd.concat([x for x in partes if not x.empty], ignore_index=True) if partes else pd.DataFrame()
    if base.empty:
        log("Sin datos.")
        return 1
    if miembros:
        prom = promedio_ocde(base, miembros, a.min_promedio)
        log(f"Promedio OCDE: {len(prom):,} filas (mínimo {a.min_promedio} miembros con dato)")
        if seleccion and not a.conservar_miembros:
            # Los miembros bajados solo para promediar no se quedan en la base.
            base = base[base["pais_codigo"].isin(seleccion)]
        base = pd.concat([base, prom], ignore_index=True)
    base = base.sort_values(["fuente", "indicador_codigo", "pais_codigo", "anio"]).reset_index(drop=True)
    cat = catalogo(base)
    base.to_csv(a.salida / "base_larga.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    cat.to_csv(a.salida / "catalogo_indicadores.csv", index=False)
    escribir_excel(base, cat, a.salida / "base_ocde_salud.xlsx", log)
    log(f"\n{len(cat):,} indicadores · {base['pais_codigo'].nunique()} países · "
        f"{int(base['anio'].min())}-{int(base['anio'].max())} · {len(base):,} observaciones")
    log(f"→ {a.salida / 'base_ocde_salud.xlsx'}")
    if fallidos:
        log(f"Flujos que no se pudieron bajar: {', '.join(fallidos)}")
        (a.salida / "flujos_fallidos.txt").write_text("\n".join(fallidos) + "\n",
                                                      encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
