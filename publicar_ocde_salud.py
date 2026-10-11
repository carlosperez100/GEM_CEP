# -*- coding: utf-8 -*-
"""
publicar_ocde_salud.py — Publicación HTML de la Base OCDE·Salud
================================================================
Lee lo que dejó `ocde_salud_base.py` en `salida/ocde_salud/` y genera UNA
página autocontenida (sin CDN, sin servidor) que cuenta todo el trabajo:
qué se construyó, cómo, qué flujos y cuántos indicadores hay, la cobertura
por país, gráficos de los indicadores clave con el Perú frente a sus pares,
el catálogo completo buscable y los enlaces de descarga.

    python publicar_ocde_salud.py
    python publicar_ocde_salud.py --paises PER CHL COL MEX CRI BRA ARG OECD
    python publicar_ocde_salud.py --salida salida/ocde_salud --html otra.html

Todo lo que la página muestra sale de los CSV reales; si un indicador clave
no está en la base, su gráfico simplemente no aparece. Nada se inventa.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

SALIDA = Path("salida") / "ocde_salud"
PAISES_DEFECTO = ["PER", "CHL", "COL", "MEX", "CRI", "BRA", "ARG", "OECD"]

# Indicadores clave: (título en español, regex sobre el nombre OCDE, regex de
# unidad, regex del flujo o None). Los nombres son los reales del catálogo
# de la corrida de 2026-10-11 (el flujo distingue, p. ej., médicos de
# enfermeras cuando el nombre solo dice "Practicing"). Se elige el que
# mejor cubre al primer país; si no hay ninguno, el gráfico no aparece.
DESTACADOS = [
    ("Esperanza de vida al nacer", r"^life expectancy \[0 years\]", r"^years", r"DF_LE$"),
    ("Mortalidad materna", r"^maternal mortality", r"per 100 000 live births", None),
    ("Mortalidad perinatal", r"^perinatal mortality", r"per 1 000 births", None),
    ("Mortalidad evitable", r"^avoidable mortality", r"per 100 000", r"DF_AM$"),
    ("Mortalidad por todas las causas", r"^mortality \(deaths per 100 000", r"per 100 000", r"DF_HEALTH_STATUS$"),
    ("Años potenciales de vida perdidos", r"^potential years of life lost", r".", r"DF_PYLL$"),
    ("Gasto en salud (% del PIB)", r"^expenditure \(percentage of gdp\)", r"percentage of gdp", r"DF_SHA$"),
    ("Gasto en salud per cápita (USD PPA)", r"^expenditure \(us dollars per person, ppp", r"per person", r"DF_SHA$"),
    ("Cobertura del seguro público u obligatorio (% población)",
     r"^health insurance coverage \[government/compulsory", r"percentage of population", r"DF_HEALTH_PROT$"),
    ("Médicos en ejercicio por 1 000 habitantes", r"^health and social employment \[practicing\]", r"per 1 000", r"DF_PHYS$"),
    ("Enfermeras en ejercicio por 1 000 habitantes", r"^health and social employment \[nurses · practicing\]", r"per 1 000", r"DF_NURSE$"),
    ("Camas hospitalarias por 1 000 habitantes", r"^hospital beds \(per 1 000", r"per 1 000", r"DF_HOSP_REAC$"),
    ("Consultas médicas por persona", r"^consultations \[medical doctors\]|^consultations \[.*medical doctors", r"per person", None),
    ("Estancia media hospitalaria (todas las causas)", r"^hospital average length of stay \[all causes\]", r"days", None),
    ("Vacunación DTP (% de niños elegibles)", r"^immunisation \[diphtheria, tetanus, pertussis\]", r"percentage of children", r"DF_IMMUN$"),
    ("Obesidad medida (% de la población)", r"^share of population who are obese \[measured\]", r"percentage", None),
    ("Consumo de alcohol (litros por persona)", r"^alcohol consumption", r"litres", r"DF_HEALTH_LVNG_AC$"),
]

# Paleta validada (skill dataviz): 8 ranuras categóricas, claro / oscuro.
RANURAS_CLARO = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
RANURAS_OSCURO = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]


def _leer(salida: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], str]:
    cat = pd.read_csv(salida / "catalogo_indicadores.csv", dtype=str, keep_default_na=False)
    for c in ("n_paises", "anio_min", "anio_max", "n_obs"):
        cat[c] = pd.to_numeric(cat[c], errors="coerce").fillna(0).astype(int)
    base_csv = salida / "base_larga.csv"
    if not base_csv.exists() and (salida / "base_larga.csv.gz").exists():
        base_csv = salida / "base_larga.csv.gz"
    base = pd.read_csv(base_csv, dtype=str, keep_default_na=False)
    base["valor"] = pd.to_numeric(base["valor"], errors="coerce")
    base["anio"] = pd.to_numeric(base["anio"], errors="coerce").astype("Int64")
    base = base[base["valor"].notna() & base["anio"].notna()]
    flujos_json = salida / "crudo" / "flujos.json"
    flujos = json.loads(flujos_json.read_text(encoding="utf-8")) if flujos_json.exists() else []
    registro = ""
    if (salida / "registro.txt").exists():
        registro = (salida / "registro.txt").read_text(encoding="utf-8", errors="replace")
    return base, cat, flujos, registro


def _flujos(base: pd.DataFrame, cat: pd.DataFrame, flujos: list[dict], registro: str) -> list[dict]:
    nombres = {f["id"]: f.get("nombre", "") for f in flujos}
    fallidos = set()
    m = re.search(r"Flujos que no se pudieron bajar: (.+)", registro)
    if m:
        fallidos = {x.strip() for x in m.group(1).split(",")}
    g = base.groupby("fuente")
    resumen = []
    for fid, sub in g:
        resumen.append({
            "id": fid,
            "nombre": sub["fuente_nombre"].iloc[0] or nombres.get(fid, ""),
            "indicadores": int(cat[cat["fuente"] == fid].shape[0]),
            "paises": int(sub["pais_codigo"].nunique()),
            "anio_min": int(sub["anio"].min()), "anio_max": int(sub["anio"].max()),
            "obs": int(len(sub)), "estado": "ok",
        })
    vistos = {r["id"] for r in resumen}
    for f in flujos:
        if f["id"] not in vistos:
            resumen.append({"id": f["id"], "nombre": f.get("nombre", ""), "indicadores": 0,
                            "paises": 0, "anio_min": None, "anio_max": None, "obs": 0,
                            "estado": "falló" if f["id"] in fallidos else "sin datos"})
    return sorted(resumen, key=lambda r: r["id"])


def _cobertura(base: pd.DataFrame, paises: list[str]) -> dict:
    piv = base.groupby(["pais_codigo", "fuente"])["indicador_codigo"].nunique().unstack(fill_value=0)
    orden = [p for p in paises if p in piv.index] + sorted(set(piv.index) - set(paises))
    piv = piv.reindex(orden)
    nombres = base.drop_duplicates("pais_codigo").set_index("pais_codigo")["pais"].to_dict()
    return {"flujos": list(piv.columns), "paises": [{"codigo": p, "nombre": nombres.get(p, p),
                                                      "valores": [int(x) for x in piv.loc[p]]} for p in piv.index]}


def _destacados(base: pd.DataFrame, cat: pd.DataFrame, paises: list[str]) -> list[dict]:
    salida = []
    usados = set()
    principal = paises[0] if paises else None
    nombres_pais = base.drop_duplicates("pais_codigo").set_index("pais_codigo")["pais"].to_dict()
    for titulo, rx_nombre, rx_unidad, rx_fuente in DESTACADOS:
        cand = cat[cat["indicador"].str.contains(rx_nombre, case=False, regex=True)]
        if rx_fuente:
            con_fuente = cand[cand["fuente"].str.contains(rx_fuente, case=False, regex=True)]
            cand = con_fuente if not con_fuente.empty else cand
        if cand.empty:
            continue
        con_unidad = cand[cand["unidad"].str.contains(rx_unidad, case=False, regex=True)
                          | cand["indicador"].str.contains(rx_unidad, case=False, regex=True)]
        if not con_unidad.empty:
            cand = con_unidad
        cand = cand[~(cand["fuente"] + "|" + cand["indicador_codigo"]).isin(usados)]
        if cand.empty:
            continue
        # Nombre corto antes que el largo (DF_KEY_INDIC repite los flujos con
        # "Not applicable" por cada desglose vacío); luego más observaciones
        # del país principal, más países y más observaciones.
        def puntaje(fila):
            sub = base[(base["fuente"] == fila["fuente"]) & (base["indicador_codigo"] == fila["indicador_codigo"])]
            n_p = int((sub["pais_codigo"] == principal).sum()) if principal else 0
            return ("not applicable" not in fila["indicador"].lower(), n_p,
                    int(sub["pais_codigo"].nunique()), int(len(sub)))
        mejor = max(cand.to_dict("records"), key=puntaje)
        sub = base[(base["fuente"] == mejor["fuente"]) & (base["indicador_codigo"] == mejor["indicador_codigo"])]
        if sub.empty:
            continue
        usados.add(mejor["fuente"] + "|" + mejor["indicador_codigo"])
        series = {}
        for p in paises:
            s = sub[sub["pais_codigo"] == p].sort_values("anio")
            if not s.empty:
                series[p] = [[int(a), round(float(v), 3)] for a, v in zip(s["anio"], s["valor"])]
        if len(series) < 2:
            continue
        salida.append({"titulo": titulo, "indicador": mejor["indicador"], "codigo": mejor["indicador_codigo"],
                       "fuente": mejor["fuente"], "unidad": mejor["unidad"], "series": series,
                       "paises": {p: nombres_pais.get(p, p) for p in series}})
    return salida


def _paises_meta(base: pd.DataFrame, paises: list[str]) -> list[dict]:
    nombres = base.drop_duplicates("pais_codigo").set_index("pais_codigo")["pais"].to_dict()
    out = []
    for p in paises:
        sub = base[base["pais_codigo"] == p]
        out.append({"codigo": p, "nombre": nombres.get(p, p), "indicadores": int(sub["indicador_codigo"].nunique()),
                    "obs": int(len(sub)), "anio_min": int(sub["anio"].min()) if len(sub) else None,
                    "anio_max": int(sub["anio"].max()) if len(sub) else None})
    return out


def generar(salida: Path, paises: list[str], ruta_html: Path) -> dict:
    base, cat, flujos, registro = _leer(salida)
    if paises:
        base = base[base["pais_codigo"].isin(paises)]
    paises_presentes = [p for p in paises if p in set(base["pais_codigo"])] or sorted(base["pais_codigo"].unique())
    meta = {
        "fecha": time.strftime("%Y-%m-%d"),
        "flujos_total": len(flujos) or int(base["fuente"].nunique()),
        "flujos_con_datos": int(base["fuente"].nunique()),
        "indicadores": int(cat.shape[0]),
        "paises": int(base["pais_codigo"].nunique()),
        "anio_min": int(base["anio"].min()), "anio_max": int(base["anio"].max()),
        "obs": int(len(base)),
        "paises_pedidos": paises,
        "archivos": {
            "xlsx": "base_ocde_salud.xlsx",
            "csv": "base_larga.csv.gz" if (salida / "base_larga.csv.gz").exists() else "base_larga.csv",
            "catalogo": "catalogo_indicadores.csv",
            "flujos": "crudo/flujos.json",
        },
    }
    datos = {
        "meta": meta,
        "flujos": _flujos(base, cat, flujos, registro),
        "cobertura": _cobertura(base, paises_presentes),
        "paises": _paises_meta(base, paises_presentes),
        "destacados": _destacados(base, cat, paises_presentes),
        "catalogo": cat[["fuente", "indicador_codigo", "indicador", "unidad", "n_paises",
                         "anio_min", "anio_max", "n_obs"]].values.tolist(),
        "ranuras": {"claro": RANURAS_CLARO, "oscuro": RANURAS_OSCURO},
        "registro": registro[-6000:],
    }
    pagina = PLANTILLA.replace("__DATOS__", json.dumps(datos, ensure_ascii=False, default=str)
                               .replace("</", "<\\/"))
    pagina = pagina.replace("__FECHA__", html.escape(meta["fecha"]))
    ruta_html.write_text(pagina, encoding="utf-8")
    return meta


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Base OCDE·Salud — GEM·VigIA</title>
<meta name="description" content="Publicación de la base OCDE·Salud por indicador, país y año construida para GEM·VigIA: método, flujos, cobertura, indicadores clave y catálogo.">
<style>
:root{
  color-scheme:light;
  --bg:#f6f5f2;--surface:#fcfcfb;--surface-2:#efeeea;--border:#dedcd5;
  --text:#0b0b0b;--text-2:#52514e;--muted:#7a7873;
  --accent:#1f4e78;--accent-ink:#fff;--grid:#e6e4de;--ref:#8b8984;
  --s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;--s8:#e34948;
  --seq-1:#cde2fb;--seq-2:#9ec5f4;--seq-3:#6da7ec;--seq-4:#3987e5;--seq-5:#1c5cab;--seq-6:#0d366b;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:#121211;--surface:#1a1a19;--surface-2:#242321;--border:#36352f;
    --text:#f0efec;--text-2:#c3c2b7;--muted:#8f8d84;
    --accent:#86b6ef;--accent-ink:#0b0b0b;--grid:#2c2b27;--ref:#a7a59c;
    --s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;
    --seq-1:#184f95;--seq-2:#1c5cab;--seq-3:#256abf;--seq-4:#3987e5;--seq-5:#6da7ec;--seq-6:#9ec5f4;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#121211;--surface:#1a1a19;--surface-2:#242321;--border:#36352f;
  --text:#f0efec;--text-2:#c3c2b7;--muted:#8f8d84;
  --accent:#86b6ef;--accent-ink:#0b0b0b;--grid:#2c2b27;--ref:#a7a59c;
  --s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;
  --seq-1:#184f95;--seq-2:#1c5cab;--seq-3:#256abf;--seq-4:#3987e5;--seq-5:#6da7ec;--seq-6:#9ec5f4;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:0 16px 64px}
header.hero{padding:48px 0 24px;border-bottom:1px solid var(--border)}
.kicker{color:var(--text-2);font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px}
h1{font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.15;margin:0 0 12px}
h2{font-size:1.4rem;margin:48px 0 12px;padding-top:8px}
h3{font-size:1.05rem;margin:24px 0 8px}
p{max-width:72ch}
.lead{font-size:1.1rem;color:var(--text-2)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.tile .n{font-size:1.7rem;font-weight:650;letter-spacing:-.01em;font-variant-numeric:tabular-nums}
.tile .l{color:var(--text-2);font-size:.85rem}
.nav{display:flex;flex-wrap:wrap;gap:8px 16px;padding:12px 0;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg);z-index:5;font-size:.9rem}
.nav a{color:var(--text-2);text-decoration:none}.nav a:hover{color:var(--text)}
.nav .sp{flex:1}
button.tema{background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:4px 10px;cursor:pointer;font:inherit;font-size:.85rem}
table{border-collapse:collapse;width:100%;font-size:.9rem;font-variant-numeric:tabular-nums}
th,td{padding:7px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
th{color:var(--text-2);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;background:var(--surface-2);position:sticky;top:0;z-index:1}
#t-catalogo td:nth-child(3){min-width:260px;max-width:520px}
#t-catalogo code,#t-flujos code{word-break:break-all}
td.num,th.num{text-align:right}
.tabla-wrap{overflow:auto;border:1px solid var(--border);border-radius:10px;background:var(--surface);max-height:70vh}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.75rem;border:1px solid var(--border);color:var(--text-2)}
.pill.ok{border-color:#1baf7a;color:#0a7a52}.pill.falló,.pill.fallo{border-color:#e34948;color:#b23433}
:root[data-theme="dark"] .pill.ok,:root:not([data-theme="light"]) .pill.ok{color:#5ad0a2}
.pasos{counter-reset:p;list-style:none;padding:0;display:grid;gap:10px}
.pasos li{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px 12px 52px;position:relative}
.pasos li::before{counter-increment:p;content:counter(p);position:absolute;left:14px;top:12px;width:26px;height:26px;border-radius:50%;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;font-weight:700;font-size:.85rem}
.pasos b{display:block;margin-bottom:2px}
.heat td.c{text-align:center;color:var(--text);font-size:.8rem;min-width:44px}
.heat td.c span{display:inline-block;min-width:36px;padding:2px 6px;border-radius:4px}
.graficos{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.grafico{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 14px 10px}
.grafico h3{margin:0 0 2px;font-size:1rem}
.grafico .sub{color:var(--text-2);font-size:.8rem;margin:0 0 8px;min-height:2.4em}
.grafico svg{width:100%;height:auto;display:block;overflow:visible}
.grafico .leyenda{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.78rem;color:var(--text-2);margin-top:6px}
.grafico .leyenda span::before{content:"";display:inline-block;width:14px;height:3px;border-radius:2px;background:var(--c);vertical-align:middle;margin-right:5px}
.grafico .leyenda span.ref::before{background:none;border-top:2px dashed var(--ref);height:0}
.grafico .acciones{display:flex;gap:10px;font-size:.78rem;margin-top:6px}
.grafico .acciones button{background:none;border:0;color:var(--accent);cursor:pointer;font:inherit;font-size:.78rem;padding:0;text-decoration:underline}
.grafico table{font-size:.78rem;margin-top:8px}
.grafico table th{position:static;top:auto}
.tip{position:fixed;pointer-events:none;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:.8rem;box-shadow:0 4px 16px rgba(0,0,0,.12);z-index:20;display:none;max-width:280px}
.tip b{display:block;margin-bottom:4px}
.tip .f{display:flex;justify-content:space-between;gap:12px}
.tip .f i{font-style:normal;display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.filtro{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}
.filtro input,.filtro select{font:inherit;font-size:.9rem;padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);min-width:220px}
.filtro .cnt{color:var(--text-2);font-size:.85rem}
.descargas{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.descargas a{display:block;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px;color:var(--text);text-decoration:none}
.descargas a b{display:block;color:var(--accent)}
.descargas a small{color:var(--text-2)}
pre{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px;font-size:.78rem;overflow:auto;max-height:320px;color:var(--text-2)}
footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--border);color:var(--text-2);font-size:.85rem}
code{background:var(--surface-2);padding:1px 5px;border-radius:4px;font-size:.9em}
.nota{border-left:3px solid var(--accent);padding:6px 12px;color:var(--text-2);background:var(--surface);border-radius:0 8px 8px 0}
@media (max-width:640px){.nav{position:static}}
@media print{.nav,.tema,.acciones{display:none}.tabla-wrap{max-height:none}}
</style>
</head>
<body>
<main>
<header class="hero">
  <p class="kicker">GEM·VigIA · Fuente externa de referencia</p>
  <h1>Base OCDE·Salud por indicador, país y año</h1>
  <p class="lead">Todos los conjuntos del tema <em>Health</em> de la OCDE, consolidados en una sola base con tres llaves (indicador, país, año), para comparar al Perú con sus pares de la región y con el promedio OCDE.</p>
  <div class="tiles" id="tiles"></div>
</header>

<nav class="nav">
  <a href="#que">Qué es</a><a href="#metodo">Método</a><a href="#flujos">Flujos</a><a href="#cobertura">Cobertura</a><a href="#clave">Indicadores clave</a><a href="#catalogo">Catálogo</a><a href="#descargas">Descargas</a>
  <span class="sp"></span><button class="tema" id="tema" type="button">Modo oscuro</button>
</nav>

<section id="que">
  <h2>Qué es y para qué sirve</h2>
  <p>GEM·VigIA vigila la calidad de la atención en el Perú a partir de reclamos, denuncias y señales de alerta temprana. Para situar esos hallazgos hace falta un <strong>marco de comparación externo y público</strong>: cuánto gasta el país en salud, cuántos médicos y camas tiene, cómo evolucionan sus resultados sanitarios frente a Chile, Colombia, México, Costa Rica, Brasil, Argentina y el promedio de la OCDE.</p>
  <p>Esta base responde a eso. Toma <strong>todos</strong> los dataflows que publica la División de Salud de la OCDE (agencia <code>OECD.ELS.HD</code>) por su API SDMX y los deja en un formato único: un renglón por indicador × país × año, con su unidad, su desglose y el estado de la observación (estimado, provisional, quiebre de serie).</p>
  <div class="nota">Es información pública de la OCDE. No contiene ni toca datos de SUSALUD ni de pacientes: no está sujeta a la regla del Anexo 3 del proyecto.</div>
</section>

<section id="metodo">
  <h2>Cómo se construyó</h2>
  <ol class="pasos">
    <li><b>Descubrir los flujos, no listarlos a mano.</b> La OCDE renombra y versiona sus dataflows; una lista fija envejece. El script pide a la API los dataflows vigentes de la agencia <code>OECD.ELS.HD</code> y trabaja con lo que haya ese día.</li>
    <li><b>Bajar cada flujo en CSV con etiquetas.</b> Se pide <code>format=csvfilewithlabels</code> con todas las dimensiones en la observación, de modo que cada código viene acompañado de su nombre legible.</li>
    <li><b>Partir por años cuando la API rechaza el tamaño.</b> Los flujos grandes (gasto en salud, farmacia) superan el límite de respuesta. Si falla, se reintenta por mitades del rango de años hasta llegar a un año por petición; lo que aun así falle queda anotado.</li>
    <li><b>Definir "indicador".</b> Cada flujo tiene una dimensión <code>MEASURE</code> y otras de desglose (sexo, edad, tipo de proveedor, esquema de financiamiento…). La base guarda el <strong>total</strong> de cada desglose para que un indicador sea una sola serie por país y año. Si un desglose no tiene total, cada valor pasa a ser un indicador aparte, con la etiqueta entre corchetes.</li>
    <li><b>Consolidar y entregar.</b> Catálogo (un renglón por indicador con su cobertura), base larga en CSV y un Excel con una hoja por flujo (indicador × país en filas, años en columnas).</li>
    <li><b>Automatizar la corrida.</b> La descarga corre en GitHub Actions bajo demanda; el resultado se sube a una rama temporal de datos y esta página se regenera con cada corrida. Nada de datos en la rama principal del código.</li>
  </ol>
</section>

<section id="flujos">
  <h2>Flujos de la OCDE incluidos</h2>
  <p>Cada flujo es un conjunto de datos del OECD Data Explorer. Se muestra cuántos indicadores aportó, cuántos de los países pedidos cubre y su rango de años.</p>
  <div class="tabla-wrap"><table id="t-flujos"></table></div>
</section>

<section id="cobertura">
  <h2>Cobertura por país</h2>
  <p>Número de indicadores con al menos un dato por país y flujo. Más oscuro, más indicadores. El Perú no es miembro de la OCDE y aparece en menos flujos y con menos series que Chile, Colombia, México y Costa Rica, que sí lo son: ese vacío también es un hallazgo. El agregado "OECD" no viene en estos flujos para la selección pedida.</p>
  <div class="tabla-wrap heat"><table id="t-cobertura"></table></div>
</section>

<section id="clave">
  <h2>Indicadores clave: el Perú frente a sus pares</h2>
  <p>Series anuales de los indicadores más usados en comparaciones internacionales, con el Perú resaltado. Cuando el flujo publica el agregado OCDE, va en línea discontinua gris como referencia. Pase el cursor para leer los valores; cada gráfico tiene su tabla.</p>
  <div class="graficos" id="graficos"></div>
</section>

<section id="catalogo">
  <h2>Catálogo completo de indicadores</h2>
  <div class="filtro">
    <input id="q" type="search" placeholder="Buscar indicador, código o unidad…" aria-label="Buscar en el catálogo">
    <select id="f-flujo" aria-label="Filtrar por flujo"><option value="">Todos los flujos</option></select>
    <span class="cnt" id="cnt"></span>
  </div>
  <div class="tabla-wrap"><table id="t-catalogo"></table></div>
</section>

<section id="descargas">
  <h2>Descargas</h2>
  <p>Los archivos viven junto a esta página en la rama de datos. El Excel trae hojas <em>Léeme</em>, <em>Catálogo</em>, <em>Base larga</em> y una por flujo.</p>
  <div class="descargas" id="lista-descargas"></div>
  <h3>Registro de la corrida</h3>
  <pre id="registro"></pre>
</section>

<footer>
  Fuente: OECD Data Explorer, tema Health · API SDMX <code>sdmx.oecd.org/public/rest</code> · agencia <code>OECD.ELS.HD</code>. Datos de la OCDE bajo sus condiciones de uso. Generado el __FECHA__ por <code>publicar_ocde_salud.py</code> para GEM·VigIA.
</footer>
</main>
<div class="tip" id="tip" role="tooltip"></div>

<script id="datos" type="application/json">__DATOS__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('datos').textContent);
const M = D.meta;
const fmt = n => n==null ? '' : Number(n).toLocaleString('es-PE');
const fmtv = v => v==null ? '' : (Math.abs(v)>=1000 ? Math.round(v).toLocaleString('es-PE') : Number(v).toLocaleString('es-PE',{maximumFractionDigits:2}));
const esc = s => String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const corto = f => String(f).replace(/^.*@/,'').replace(/^DF_/,'');   // DSD_SHA@DF_SHA → SHA

// Tema
const root=document.documentElement, bt=document.getElementById('tema');
function modo(){return root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
function pintarTema(){bt.textContent = modo()==='dark' ? 'Modo claro' : 'Modo oscuro'; dibujarTodo();}
bt.onclick=()=>{root.dataset.theme = modo()==='dark'?'light':'dark'; try{localStorage.setItem('ocde-tema',root.dataset.theme)}catch(e){} pintarTema();};
try{const t=localStorage.getItem('ocde-tema'); if(t) root.dataset.theme=t;}catch(e){}

// Tiles
document.getElementById('tiles').innerHTML = [
  [fmt(M.flujos_con_datos)+(M.flujos_total>M.flujos_con_datos?' / '+fmt(M.flujos_total):''),'flujos con datos'],
  [fmt(M.indicadores),'indicadores'],
  [fmt(M.paises),'países y agregados'],
  [M.anio_min+'–'+M.anio_max,'años'],
  [fmt(M.obs),'observaciones'],
  [M.fecha,'fecha de descarga'],
].map(([n,l])=>`<div class="tile"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');

// Flujos
document.getElementById('t-flujos').innerHTML =
 '<thead><tr><th>Flujo</th><th>Nombre</th><th class="num">Indicadores</th><th class="num">Países</th><th>Años</th><th class="num">Obs.</th><th>Estado</th></tr></thead><tbody>' +
 D.flujos.map(f=>`<tr><td><code>${esc(f.id)}</code></td><td>${esc(f.nombre)}</td><td class="num">${fmt(f.indicadores)}</td><td class="num">${fmt(f.paises)}</td><td>${f.anio_min?f.anio_min+'–'+f.anio_max:''}</td><td class="num">${fmt(f.obs)}</td><td><span class="pill ${f.estado==='falló'?'fallo':f.estado}">${esc(f.estado)}</span></td></tr>`).join('') + '</tbody>';

// Cobertura (mapa de calor secuencial, un solo tono)
(function(){
  const C=D.cobertura; const max=Math.max(1,...C.paises.flatMap(p=>p.valores));
  const seq=['--seq-1','--seq-2','--seq-3','--seq-4','--seq-5','--seq-6'];
  const t=document.getElementById('t-cobertura');
  t.innerHTML='<thead><tr><th>País</th>'+C.flujos.map(f=>`<th title="${esc(f)}">${esc(corto(f))}</th>`).join('')+'<th class="num">Total</th></tr></thead><tbody>'+
   C.paises.map(p=>{const tot=p.valores.reduce((a,b)=>a+b,0);
     return `<tr><td><b>${esc(p.codigo)}</b> <span style="color:var(--text-2)">${esc(p.nombre)}</span></td>`+
       p.valores.map(v=>{ if(!v) return '<td class="c"><span style="color:var(--muted)">·</span></td>';
         const i=Math.min(5,Math.floor(Math.log1p(v)/Math.log1p(max)*5.999)); const oscuro=i>=3;
         return `<td class="c"><span style="background:var(${seq[i]});color:${oscuro?'#fff':'#0b0b0b'}" title="${esc(p.nombre)} · ${v} indicadores">${v}</span></td>`}).join('')+
       `<td class="num"><b>${fmt(tot)}</b></td></tr>`}).join('')+'</tbody>';
})();

// Gráficos de líneas en SVG puro
const tip=document.getElementById('tip');
function colores(){const o=modo()==='dark'?D.ranuras.oscuro:D.ranuras.claro; return o;}
function dibujarGrafico(g, idx){
  const ps=Object.keys(g.series).filter(p=>p!=='OECD'); const tieneRef=!!g.series.OECD;
  const cols=colores(); const colorDe={}; ps.forEach((p,i)=>colorDe[p]=cols[i%cols.length]);
  const todos=Object.values(g.series).flat();
  const xs=todos.map(d=>d[0]), ys=todos.map(d=>d[1]);
  const x0=Math.min(...xs), x1=Math.max(...xs); let y0=Math.min(0,...ys), y1=Math.max(...ys);
  if(y1===y0) y1=y0+1; const pad=(y1-y0)*0.08; y1+=pad; if(y0<0) y0-=pad;
  const W=520,H=260,ml=48,mr=12,mt=10,mb=28, pw=W-ml-mr, ph=H-mt-mb;
  const X=a=>ml+(x1===x0?pw/2:(a-x0)/(x1-x0)*pw), Y=v=>mt+ph-(v-y0)/(y1-y0)*ph;
  const ticksY=5, ty=[]; for(let i=0;i<=ticksY;i++) ty.push(y0+(y1-y0)*i/ticksY);
  const span=x1-x0, paso=span>40?10:span>16?5:span>8?2:1; const tx=[]; for(let a=Math.ceil(x0/paso)*paso;a<=x1;a+=paso) tx.push(a);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(g.titulo)}">`;
  ty.forEach(v=>{s+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)" stroke-width="1"/><text x="${ml-6}" y="${Y(v)+3}" text-anchor="end" font-size="10" fill="var(--text-2)">${fmtv(v)}</text>`});
  tx.forEach(a=>{s+=`<text x="${X(a)}" y="${H-8}" text-anchor="middle" font-size="10" fill="var(--text-2)">${a}</text>`});
  s+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(Math.max(0,y0))}" y2="${Y(Math.max(0,y0))}" stroke="var(--border)"/>`;
  const linea=(d)=>d.map((p,i)=>(i?'L':'M')+X(p[0]).toFixed(1)+' '+Y(p[1]).toFixed(1)).join(' ');
  if(tieneRef) s+=`<path d="${linea(g.series.OECD)}" fill="none" stroke="var(--ref)" stroke-width="2" stroke-dasharray="5 4" stroke-linejoin="round"/>`;
  ps.forEach(p=>{const d=g.series[p]; const c=colorDe[p]; const esPrin=p===M.paises_pedidos[0];
    s+=`<path d="${linea(d)}" fill="none" stroke="${c}" stroke-width="${esPrin?3:2}" stroke-linejoin="round" stroke-linecap="round"/>`;
    if(d.length===1) s+=`<circle cx="${X(d[0][0])}" cy="${Y(d[0][1])}" r="4" fill="${c}" stroke="var(--surface)" stroke-width="2"/>`;
    const u=d[d.length-1]; if(esPrin) s+=`<text x="${X(u[0])+5}" y="${Y(u[1])+3}" font-size="10" font-weight="600" fill="var(--text)">${esc(p)}</text>`;
  });
  s+=`<g class="hover"></g><rect class="zona" x="${ml}" y="${mt}" width="${pw}" height="${ph}" fill="transparent"/></svg>`;
  const el=document.createElement('article'); el.className='grafico';
  el.innerHTML=`<h3>${esc(g.titulo)}</h3><p class="sub">${esc(g.indicador)}${g.unidad?' · '+esc(g.unidad):''} · <code>${esc(g.fuente)}</code></p>${s}
   <div class="leyenda">${ps.map(p=>`<span style="--c:${colorDe[p]}" title="${esc(g.paises[p])}">${esc(p)}</span>`).join('')}${tieneRef?'<span class="ref">OCDE (promedio)</span>':''}</div>
   <div class="acciones"><button type="button" data-tabla>Ver tabla</button></div><div class="tabla" hidden></div>`;
  const svg=el.querySelector('svg'), hov=svg.querySelector('.hover'), zona=svg.querySelector('.zona');
  const anios=[...new Set(xs)].sort((a,b)=>a-b);
  zona.addEventListener('mousemove',ev=>{
    const r=svg.getBoundingClientRect(); const px=(ev.clientX-r.left)/r.width*W;
    let a=anios[0]; for(const k of anios){ if(Math.abs(X(k)-px)<Math.abs(X(a)-px)) a=k; }
    let h=`<line x1="${X(a)}" x2="${X(a)}" y1="${mt}" y2="${mt+ph}" stroke="var(--text-2)" stroke-width="1" stroke-dasharray="2 3"/>`;
    const filas=[];
    const orden=[...ps, ...(tieneRef?['OECD']:[])];
    orden.forEach(p=>{const d=g.series[p].find(q=>q[0]===a); if(!d) return; const c=p==='OECD'?'var(--ref)':colorDe[p];
      h+=`<circle cx="${X(a)}" cy="${Y(d[1])}" r="4.5" fill="${c}" stroke="var(--surface)" stroke-width="2"/>`;
      filas.push(`<div class="f"><span><i style="background:${c}"></i>${esc(g.paises[p]||p)}</span><span>${fmtv(d[1])}</span></div>`)});
    hov.innerHTML=h; tip.innerHTML=`<b>${a}</b>${filas.join('')}`; tip.style.display='block';
    const tw=tip.offsetWidth, th=tip.offsetHeight; let L=ev.clientX+14, T=ev.clientY+14;
    if(L+tw>innerWidth-8) L=ev.clientX-tw-14; if(T+th>innerHeight-8) T=ev.clientY-th-14; tip.style.left=L+'px'; tip.style.top=T+'px';
  });
  zona.addEventListener('mouseleave',()=>{hov.innerHTML=''; tip.style.display='none'});
  el.querySelector('[data-tabla]').onclick=(e)=>{const t=el.querySelector('.tabla'); t.hidden=!t.hidden; e.target.textContent=t.hidden?'Ver tabla':'Ocultar tabla';
    if(!t.innerHTML){const orden=[...ps, ...(tieneRef?['OECD']:[])];
      t.innerHTML='<table><thead><tr><th>Año</th>'+orden.map(p=>`<th class="num">${esc(p)}</th>`).join('')+'</tr></thead><tbody>'+
        anios.map(a=>`<tr><td>${a}</td>`+orden.map(p=>{const d=g.series[p].find(q=>q[0]===a); return `<td class="num">${d?fmtv(d[1]):''}</td>`}).join('')+'</tr>').join('')+'</tbody></table>';}};
  return el;
}
function dibujarTodo(){
  const cont=document.getElementById('graficos'); cont.innerHTML='';
  if(!D.destacados.length){cont.innerHTML='<p class="nota">Ninguno de los indicadores clave previstos aparece en esta corrida; revise el catálogo.</p>'; return;}
  D.destacados.forEach((g,i)=>cont.appendChild(dibujarGrafico(g,i)));
}

// Catálogo
const sel=document.getElementById('f-flujo');
[...new Set(D.catalogo.map(r=>r[0]))].sort().forEach(f=>{const o=document.createElement('option'); o.value=f; o.textContent=f; sel.appendChild(o)});
const tc=document.getElementById('t-catalogo'), q=document.getElementById('q'), cnt=document.getElementById('cnt');
function pintarCatalogo(){
  const txt=q.value.trim().toLowerCase(), f=sel.value;
  const filas=D.catalogo.filter(r=>(!f||r[0]===f)&&(!txt||(r[1]+' '+r[2]+' '+r[3]).toLowerCase().includes(txt)));
  cnt.textContent=fmt(filas.length)+' de '+fmt(D.catalogo.length)+' indicadores';
  const lim=filas.slice(0,600);
  tc.innerHTML='<thead><tr><th>Flujo</th><th>Código</th><th>Indicador</th><th>Unidad</th><th class="num">Países</th><th>Años</th><th class="num">Obs.</th></tr></thead><tbody>'+
    lim.map(r=>`<tr><td><code title="${esc(r[0])}">${esc(corto(r[0]))}</code></td><td><code>${esc(r[1])}</code></td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td class="num">${fmt(r[4])}</td><td>${r[5]}–${r[6]}</td><td class="num">${fmt(r[7])}</td></tr>`).join('')+
    (filas.length>lim.length?`<tr><td colspan="7" style="color:var(--text-2)">Se muestran ${lim.length} de ${fmt(filas.length)}; afine la búsqueda para ver el resto.</td></tr>`:'')+'</tbody>';
}
q.oninput=pintarCatalogo; sel.onchange=pintarCatalogo; pintarCatalogo();

// Descargas
const A=M.archivos;
document.getElementById("lista-descargas").innerHTML=[
  [A.xlsx,'Excel completo','Léeme · Catálogo · Base larga · una hoja por flujo'],
  [A.csv,'Base larga (CSV)','fuente · indicador · país · año · valor · estado'],
  [A.catalogo,'Catálogo de indicadores (CSV)','un renglón por indicador con su cobertura'],
  [A.flujos,'Lista de flujos (JSON)','dataflows de OECD.ELS.HD el día de la descarga'],
].map(([h,t,s])=>`<a href="${esc(h)}" download><b>${esc(t)}</b><small>${esc(s)}</small><br><small><code>${esc(h)}</code></small></a>`).join('');
document.getElementById('registro').textContent=D.registro||'(sin registro)';

pintarTema();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{ if(!root.dataset.theme) pintarTema(); });
})();
</script>
</body>
</html>
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--salida", type=Path, default=SALIDA)
    p.add_argument("--paises", nargs="*", default=PAISES_DEFECTO)
    p.add_argument("--html", type=Path, help="ruta del HTML (por defecto salida/publicacion_ocde_salud.html)")
    a = p.parse_args(argv)
    ruta = a.html or (a.salida / "publicacion_ocde_salud.html")
    meta = generar(a.salida, a.paises, ruta)
    print(f"→ {ruta} · {meta['indicadores']:,} indicadores · {meta['paises']} países · "
          f"{meta['anio_min']}-{meta['anio_max']} · {meta['obs']:,} observaciones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
