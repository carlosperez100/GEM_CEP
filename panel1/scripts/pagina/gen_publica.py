# -*- coding: utf-8 -*-
# Genera la pagina publica unica del Panel I (un solo archivo HTML autocontenido):
# laminas tal como estan publicadas en el deck + guion + resumen + fuentes con enlace + datos.
# Uso: python -I gen_publica.py   -> escribe publica/index.html
import base64, html as H, io, json, pathlib, re

AQUI = pathlib.Path(__file__).resolve().parent
S = AQUI.parent
PROJ = S / "deck-panel1" / "project"
PNG = S / "plantilla_png"
REPO = "https://github.com/carlosperez100/GEM_CEP/tree/main/panel1"
SITIO = "https://carlosperez100.github.io/GEM_CEP/panel1/"
VERSION = "11 de octubre de 2026"

deck = json.loads((PROJ / "deck.json").read_text(encoding="utf-8"))
ORDEN = deck["order"]

# ------------------------------------------------------------------ imagenes
def jpg_uri(nombre, calidad=86):
    from PIL import Image
    im = Image.open(PNG / nombre).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=calidad, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

FONDOS = {
    "/_blob/49486cf8087824f7aeba26166eb4df35": ("fondo-interna", jpg_uri("fondo_interna.png", 88)),
    "/_blob/7980c71054d8346a4975940bcc3e4aea": ("fondo-portada", None),
    "/_blob/f310a222aa9836148fb61507e0b6585e": ("fondo-gracias", None),
}

# ------------------------------------------------------------------- laminas
def texto(inner):
    t = re.sub(r"<br\s*/?>", " ", inner)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", H.unescape(t)).strip()


def parrafos(src):
    return [(m.group(1), texto(m.group(2))) for m in re.finditer(r'<p\b[^>]*?style="([^"]*)"[^>]*>(.*?)</p>', src, re.S)]


CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TELEFONO = re.compile(r"(?<!\d)9\d{8}(?!\d)")


def limpia_contacto(src):
    """La pagina publica no lleva correo ni telefono personales."""
    src = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+\s*(?:&nbsp;|\s)*-\s*9\d{8}\s*<br\s*/?>", "", src)
    src = CORREO.sub("", src)
    src = TELEFONO.sub("", src)
    return src


LAMINAS = []
for i, sid in enumerate(ORDEN, 1):
    src = (PROJ / "slides" / (sid + ".html")).read_text(encoding="utf-8")
    src = limpia_contacto(src)
    assert not CORREO.search(src) and not TELEFONO.search(src), sid
    m = re.search(r"<aside>(.*?)</aside>", src, re.S)
    guion = texto(m.group(1)) if m else ""
    src = re.sub(r"<aside>.*?</aside>", "", src, flags=re.S)
    clase = ""
    for blob, (cl, _uri) in FONDOS.items():
        patron = re.compile(r'<img\b[^>]*src="%s"[^>]*>\s*' % re.escape(blob))
        if patron.search(src):
            src = patron.sub("", src)
            clase = cl
    assert "/_blob/" not in src, sid
    assert clase, sid
    src = re.sub(r'<section id="[^"]*"\s*(data-transition="[^"]*")?', '<section class="%s" data-lamina="%s"' % (clase, sid), src, count=1)
    src = re.sub(r'\sid="[0-9a-f]{8}"', "", src)  # ids internos del editor
    mt = re.search(r"<h2\b[^>]*>(.*?)</h2>", src, re.S)
    titulo = texto(mt.group(1)) if mt else ""
    if sid == "portada":
        titulo = "Portada"
    if sid == "gracias":
        titulo = "Cierre"
    src = re.sub(r"<(h[1-6])\b", r'<\1 role="presentation"', src)  # los titulos internos no entran al esquema de la pagina
    LAMINAS.append({"n": i, "id": sid, "titulo": titulo, "html": src.strip(), "guion": guion})

POR_ID = {l["id"]: l for l in LAMINAS}


def crudo(sid):
    return limpia_contacto((PROJ / "slides" / (sid + ".html")).read_text(encoding="utf-8"))


# ------------------------------------------------- resumen tomado de las laminas
def titulo_h2(sid):
    return texto(re.search(r"<h2\b[^>]*>(.*?)</h2>", crudo(sid), re.S).group(1))


def kicker(sid):
    for st, tx in parrafos(crudo(sid)):
        if "letter-spacing:3px" in st:
            return tx
    return ""


RESULTADOS = []
for sid in ("resultados", "piramide", "mundo", "datos"):
    t = titulo_h2(sid)
    assert t.startswith("Resultado "), t
    cab, cuerpo = t.split(":", 1)
    RESULTADOS.append((cab.strip(), cuerpo.strip(), kicker(sid), sid))

lim = parrafos(crudo("limites"))
NO_PRUEBAN = [tx for st, tx in lim if "font-size:34px" in st or "font-size:32px" in st]
CONCLUSION = [tx for st, tx in lim if "font-size:38px" in st]
assert len(NO_PRUEBAN) == 4 and len(CONCLUSION) == 3, (len(NO_PRUEBAN), len(CONCLUSION))

PEDIDOS, grupo = [], None
for st, tx in parrafos(crudo("remate")):
    if "letter-spacing:2px" in st and "text-transform:uppercase" in st:
        grupo = [tx, []]
        PEDIDOS.append(grupo)
    elif "font-size:34px" in st and grupo is not None:
        grupo[1].append(tx)
assert [len(g[1]) for g in PEDIDOS] == [2, 2, 3], PEDIDOS

preg = [tx for st, tx in parrafos(crudo("pregunta")) if "font-size:28px;font-weight:700" in st]
assert len(preg) == 1 and preg[0].startswith("¿"), preg
PREGUNTA, METODO = preg[0].split("?", 1)
PREGUNTA += "?"
METODO = METODO.strip()

# -------------------------------------------------------------------- fuentes
USO = {
    1: "Autonomía clínica; Resultado 2 (artículo 13)", 2: "La pregunta (artículo 4); autonomía clínica (artículo 9)",
    3: "Autonomía clínica: la frontera (artículo 26)", 4: "Autonomía clínica: la frontera (artículo 5)",
    5: "Autonomía clínica (artículo 49)", 6: "Autonomía clínica; remate. Es propuesta, no norma",
    7: "Anexo de fuentes. Es propuesta, no norma", 8: "Resultado 1", 9: "Resultado 1", 10: "Resultado 1", 11: "Resultado 1",
    12: "Resultado 4", 13: "Resultado 2", 14: "Resultado 2", 15: "Resultado 2; brecha de toma de decisiones",
    16: "Remate", 17: "Resultado 3", 18: "Resultado 3; brecha de toma de decisiones",
    19: "Resultado 3; brecha de toma de decisiones", 20: "Resultado 4", 21: "Brecha digital",
    22: "Resultado 4; brecha de información", 23: "Recorrido del paciente", 24: "Recorrido del paciente",
    25: "Resultado 3 (órganos de enfermería en otros ministerios)", 26: "Resultado 4 (caso propio)",
}
fe = S / "fuentes_enlaces.json"
FUENTES = json.loads(fe.read_text(encoding="utf-8")) if fe.exists() else []


def e(t):
    return H.escape(t, quote=True)


def nb(t):
    """Espacio de no separacion en miles, porcentajes y soles (solo texto corrido, nunca el HTML de las laminas)."""
    t = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", "\u00a0", t)
    return re.sub(r"(?<=\d) (?=%)|(?<=S/) (?=\d)", "\u00a0", t)


URL_RE = re.compile(r"https?://[^\s<>»]+")


def url_limpia(u):
    return u.replace("[", "%5B").replace("]", "%5D")


def nombre_fuente(f):
    """Nombre tal como lo dio el verificador; la proposicion 91 se cita por su numero, sin nombres de personas."""
    t = f["fuente"].strip()
    i = t.find("Proposición Legislativa 00091")
    return t[i:] if i > 0 else t


def nota_html(nota):
    partes, ult = [], 0
    for m in URL_RE.finditer(nota):
        u = m.group(0).rstrip(".,;:)")
        partes.append(e(nota[ult:m.start()]))
        partes.append('<a href="%s" rel="noopener">enlace</a>' % e(url_limpia(u)))
        ult = m.start() + len(u)
    partes.append(e(nota[ult:]))
    return "".join(partes)


def fila_fuente(f):
    n = int(f["n"])
    url = (f.get("url") or "").strip()
    if url:
        dominio = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        enlace = '<a href="%s" rel="noopener">%s</a>' % (e(url_limpia(url)), e(dominio))
    else:
        enlace = '<span class="sin">sin enlace público confirmado</span>'
    nota = f.get("nota", "").strip()
    return ('<tr><td><span class="f-nom">%s</span>%s</td><td class="c-uso">%s</td><td class="c-enl">%s</td></tr>'
            % (e(nb(nombre_fuente(f))), ('<span class="f-nota">%s</span>' % nota_html(nb(nota))) if nota else "", e(USO.get(n, "")), enlace))


TABLA_FUENTES = "\n".join(fila_fuente(f) for f in FUENTES) or '<tr><td colspan="3">Lista de enlaces en preparación.</td></tr>'

# ----------------------------------------------------------------------- html

def li(items):
    return "".join("<li>%s</li>" % e(t) for t in items)


res_html = "".join(
    '<li><a class="res" href="#l-%s"><span class="res-n">%s</span><span class="res-t">%s</span><span class="res-k">%s</span></a></li>'
    % (sid, e(cab), e(cuerpo[0].upper() + cuerpo[1:]), e(k)) for cab, cuerpo, k, sid in RESULTADOS)

ped_html = "".join('<div class="ped"><h3>%s</h3><ul>%s</ul></div>' % (e(g[0]), li(g[1])) for g in PEDIDOS)

lam_html = []
for l in LAMINAS:
    lam_html.append(
        '<figure class="lam" id="l-%s">'
        '<figcaption><span class="lam-n">%d</span><h3 class="lam-t">%s</h3>'
        '<button class="lam-z" type="button" aria-pressed="false">Ampliar</button></figcaption>'
        '<div class="visor"><div class="marco"><div class="lienzo">%s</div></div></div>'
        '%s</figure>'
        % (l["id"], l["n"], e(l["titulo"]), l["html"],
           ('<details class="guion"><summary>Guion del expositor</summary><p>%s</p></details>' % e(nb(l["guion"]))) if l["guion"] else ""))

indice = "".join('<a href="#l-%s" aria-label="Lámina %d: %s" title="%s">%d</a>' % (l["id"], l["n"], e(l["titulo"]), e(l["titulo"]), l["n"]) for l in LAMINAS)

CSS_FONDOS = "".join(".lienzo section.%s{background-image:url(%s) !important}\n" % (cl, uri) for cl, uri in FONDOS.values() if uri)

# imagen para compartir el enlace (1200 x 630), a partir de la figura de las tres brechas
def imagen_compartir():
    from PIL import Image
    origen = S / "figura" / "tres_brechas_enfermeria.png"
    if not origen.exists():
        return
    (AQUI / "figuras").mkdir(exist_ok=True)
    im = Image.open(origen).convert("RGB")
    im.thumbnail((1120, 630), Image.LANCZOS)
    lz = Image.new("RGB", (1200, 630), "#FFFFFF")
    lz.paste(im, ((1200 - im.width) // 2, (630 - im.height) // 2))
    lz.save(AQUI / "figuras" / "compartir.jpg", "JPEG", quality=86, optimize=True, progressive=True)


imagen_compartir()
PLANTILLA = (AQUI / "plantilla.html").read_text(encoding="utf-8")
BLOQUE_FUENTES = (AQUI / "bloque_fuentes.html").read_text(encoding="utf-8") if FUENTES else ""
NAV_FUENTES = '<a href="#fuentes">Fuentes con enlace</a>' if FUENTES else ""
PLANTILLA = PLANTILLA.replace("{{SECCION_FUENTES}}", BLOQUE_FUENTES).replace("{{NAV_FUENTES}}", NAV_FUENTES)
pagina = (PLANTILLA
          .replace("{{CSS_FONDOS}}", CSS_FONDOS)
          .replace("{{VERSION}}", VERSION)
          .replace("{{SITIO}}", SITIO)
          .replace("{{REPO}}", REPO)
          .replace("{{N_LAMINAS}}", str(len(LAMINAS)))
          .replace("{{PREGUNTA}}", e(PREGUNTA))
          .replace("{{METODO}}", e(METODO))
          .replace("{{RESULTADOS}}", res_html)
          .replace("{{NO_PRUEBAN}}", li(NO_PRUEBAN))
          .replace("{{CONCLUSION}}", li(CONCLUSION))
          .replace("{{PEDIDOS}}", ped_html)
          .replace("{{INDICE}}", indice)
          .replace("{{LAMINAS}}", "\n".join(lam_html))
          .replace("{{TABLA_FUENTES}}", TABLA_FUENTES)
          .replace("{{N_FUENTES}}", str(len(FUENTES))))
assert "{{" not in pagina, re.findall(r"\{\{[A-Z_]+\}\}", pagina)
visible = re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", "", pagina)
assert not CORREO.search(visible), CORREO.search(visible).group(0)
assert not TELEFONO.search(visible), TELEFONO.search(visible).group(0)
(AQUI / "index.html").write_text(pagina, encoding="utf-8", newline="\n")
resumen = {
    "pregunta": PREGUNTA, "metodo": METODO,
    "resultados": [{"cab": cab, "texto": cuerpo[0].upper() + cuerpo[1:], "capa": k, "id": sid} for cab, cuerpo, k, sid in RESULTADOS],
    "no_prueban": NO_PRUEBAN, "conclusion": CONCLUSION,
    "pedidos": [{"a": g[0], "items": g[1]} for g in PEDIDOS],
    "laminas": [{"n": l["n"], "id": l["id"], "titulo": l["titulo"]} for l in LAMINAS],
    "uso": {str(k): v for k, v in USO.items()},
}
(AQUI / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print("ok index.html", round(len(pagina.encode("utf-8")) / 1024), "KB ·", len(LAMINAS), "laminas ·", len(FUENTES), "fuentes")
