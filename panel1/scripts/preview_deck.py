# -*- coding: utf-8 -*-
# Genera vistas previas locales de cada lamina del deck (lienzo 1920x1080 escalado a 0.5).
import json, re, pathlib

BASE = pathlib.Path(r"C:\Users\infor\AppData\Local\Temp\claude\C--Users-infor-OneDrive-CARLOS-PEREZ-UNIVERSIDADES-CEP-FORO\a76ee289-0d5f-426a-becc-af42c47fbeaf\scratchpad")
PROJ = BASE / "deck-panel1" / "project"
OUT = BASE / "preview"
OUT.mkdir(exist_ok=True)
FORO = pathlib.Path(r"C:\Users\infor\OneDrive\CARLOS PEREZ\UNIVERSIDADES\CEP\FORO\mapas_enfermeria_ampliada")
import shutil
(OUT / "img").mkdir(exist_ok=True)
SRC = {
    "/_blob/49486cf8087824f7aeba26166eb4df35": BASE / "plantilla_png" / "fondo_interna.png",
    "/_blob/7980c71054d8346a4975940bcc3e4aea": BASE / "plantilla_png" / "fondo_portada.png",
    "/_blob/f310a222aa9836148fb61507e0b6585e": BASE / "plantilla_png" / "fondo_gracias.png",
    "/_blob/92bc4e90200224ea9298bd19c3e8ad76": BASE.parent / "images" / "1.webp",
    "/_blob/4b1b8d6061aaf2ea7a345a6528a58610": BASE / "slides-src" / "cover.png",
    "/_blob/c895ac2b1c9a169f6b8853f35b4f1a83": BASE / "foto_arte_out" / "arte_foto.jpg",
    "/_blob/541f9c5068545a4b4dee4509feddd1cb": BASE / "slides-src" / "logo.png",
    "/_blob/419b0b9283435563a99dc0ab51b8ff86": FORO / "02_departamento_por_10000.png",
    "/_blob/d9a2335cea91fdbf3b0344af3bcce6be": FORO / "06_distrito_por_10000.png",
}
BLOBS = {}
for k, src in SRC.items():
    shutil.copyfile(src, OUT / "img" / src.name)
    BLOBS[k] = "img/" + src.name
deck = json.loads((PROJ / "deck.json").read_text(encoding="utf-8"))
links = "".join('<link rel="stylesheet" href="%s">' % f["href"] for f in deck["faces"].values())
CSS = """
html,body{margin:0;background:#2a2a2a}
body{width:960px;height:540px;overflow:hidden}
.canvas{position:relative;width:1920px;height:1080px;overflow:hidden;transform:scale(0.5);transform-origin:0 0}
section{position:absolute;left:0;top:0;width:1920px;height:1080px;box-sizing:border-box;display:flex;flex-direction:column}
section *{box-sizing:border-box;margin:0}
section > *{flex-shrink:0}
section div > *{flex-shrink:0}
section div:not([style*="display:"]){display:flex;flex-direction:column}
section > :not([style*="position:absolute"]){position:relative}
h1{font-size:96px;font-weight:600;line-height:1.1}
h2{font-size:64px;font-weight:600;line-height:1.15}
h3{font-size:44px;font-weight:600;line-height:1.2}
p{font-size:32px;font-weight:400;line-height:1.4}
aside{display:none}
hr{border:0;height:0}
x-shape[kind=arrow-right]{display:block;flex:none;clip-path:polygon(0 30%,60% 30%,60% 0,100% 50%,60% 100%,60% 70%,0 70%)}
x-icon{display:block;flex:none;border-radius:50%;background:currentColor;opacity:.85}
.guide{position:absolute;left:128px;top:128px;width:1664px;height:824px;border:1px dashed rgba(255,0,0,.35);pointer-events:none}
.y920{position:absolute;left:0;top:920px;width:1920px;height:0;border-top:1px dashed rgba(255,0,0,.35);pointer-events:none}
"""
for sid in deck["order"]:
    html = (PROJ / "slides" / (sid + ".html")).read_text(encoding="utf-8")
    for k, v in BLOBS.items():
        html = html.replace(k, v)
    page = ("<!doctype html><html><head><meta charset='utf-8'>%s<style>%s</style></head>"
            "<body><div class='canvas'>%s<div class='guide'></div><div class='y920'></div></div></body></html>" % (links, CSS, html))
    (OUT / (sid + ".html")).write_text(page, encoding="utf-8")
    print("ok", sid)
