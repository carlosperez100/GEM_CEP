# -*- coding: utf-8 -*-
# Tablero visual de todo lo trabajado para el Panel I (Foro del 12 de octubre de 2026).
# Entradas: tablero/inventario.json (nueve lectores), tablero/niveles.json (sintesis del fundamento teorico, si existe),
#           el deck local (deck-panel1/project) y el plan (FORO/PLAN_LAMINAS_PANEL1.md).
# Salidas:  tablero/tablero_artefacto.html (fragmento para publicar) y FORO/TABLERO_PANEL1.html (archivo completo).
import json, html, re, pathlib, sys, math, base64, csv, io
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
S = HERE.parent
FORO = pathlib.Path(r"C:\Users\infor\OneDrive\CARLOS PEREZ\UNIVERSIDADES\CEP\FORO")
NB = "\u00a0"
DECK_URL = "https://claude.ai/artifact/DHEjbVAbeB1pEYK8meoiuE"


def carga(nombre, defecto):
    p = HERE / nombre
    if p.exists():
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception as ex:
            print("no se pudo leer", nombre, ex)
    return defecto


INV = {x["key"]: x["r"] for x in carga("inventario.json", []) if x and x.get("r")}
NIV = carga("niveles.json", None)
AUT = carga("autonomia_estado.json", None)
PAI = carga("paises.json", None)

# ------------------------------------------------------------------ utilidades


def e(s):
    s = html.escape(str(s if s is not None else ""), quote=True)
    return re.sub(r"(?<=\d) (?=\d{3}(?!\d))", NB, s)


def num(v, dec=0):
    s = ("%." + str(dec) + "f") % v
    ent, _, fr = s.partition(".")
    neg = ent.startswith("-")
    ent = ent.lstrip("-")
    grupos = []
    while len(ent) > 3:
        grupos.insert(0, ent[-3:])
        ent = ent[:-3]
    grupos.insert(0, ent)
    out = NB.join(grupos) if len("".join(grupos)) > 4 else "".join(grupos)
    return ("-" if neg else "") + out + (("." + fr) if fr else "")


FUENTES = {
    "censo": ("Instituto Nacional de Estadística e Informática, Censos Nacionales 2025, nota del 29 de mayo de 2026", "https://www.gob.pe/institucion/inei/noticias/1399446-inei-poblacion-del-peru-totalizo-34-millones-157-mil-732-habitantes-al-2025"),
    "censo2": ("Instituto Nacional de Estadística e Informática, Censos Nacionales 2025, nota del 10 de julio de 2026", "https://www.gob.pe/institucion/inei/noticias/1417313"),
    "ent": ("Instituto Nacional de Estadística e Informática, Perú: Enfermedades no transmisibles y transmisibles, 2025, páginas 23 y 24", "https://cdn.www.gob.pe/uploads/document/file/10182873/8284033-principales-indicadores-peru-enfermedades-no-transmisibles-y-transmisibles-2025.pdf"),
    "minsa": ("Ministerio de Salud, Información de Recursos Humanos en el Sector Salud, Perú 2023, páginas 11, 12 y 21", "https://bvs.minsa.gob.pe/local/MINSA/7355.pdf"),
    "oms": ("Organización Mundial de la Salud, State of the world's nursing 2025", "https://iris.who.int/handle/10665/381329"),
    "gho": ("Organización Mundial de la Salud, Observatorio Mundial de la Salud, enfermería y partería por 10 000 habitantes", "https://ghoapi.azureedge.net/api/HWF_0006"),
    "susalud": ("Superintendencia Nacional de Salud, Recursos de Salud por establecimiento, 2015 y 2026", "http://datos.susalud.gob.pe/dataset/consulta-recursos-de-salud-por-ipress"),
    "pubmed": ("PubMed, Biblioteca Nacional de Medicina de Estados Unidos, consulta del 9 de octubre de 2026", "https://pubmed.ncbi.nlm.nih.gov/?term=nursing%5Btiab%5D+AND+leadership%5Btiab%5D"),
    "ley": ("Ley 27669, Ley del Trabajo de la Enfermera(o)", "https://leyes.congreso.gob.pe/Documentos/Leyes/27669.pdf"),
    "ds004": ("Decreto Supremo 004-2002-SA, reglamento de la Ley 27669", "https://cdn.www.gob.pe/uploads/document/file/283049/254821_DS004-2002.pdf20190110-18386-1ktrq99.pdf"),
    "ds014": ("Decreto Supremo 014-2026-SA", "https://www.gob.pe/institucion/minsa/normas-legales/8582202-014-2026-sa"),
    "ds019": ("Decreto Supremo 019-2025-SA", "https://www.gob.pe/institucion/minsa/normas-legales/7348479-019-2025-sa"),
    "incor": ("Instituto Nacional Cardiovascular, postulación al Reconocimiento a la Gestión de Proyectos de Mejora 2016, tablas 13 y 14; fuente de las tablas: Oficina de Planeamiento y Calidad", ""),
    "dossier": ("Dossier de evidencia del Panel I, con el enlace de cada estudio", ""),
    "articulos": ("Artículos de la revisión, con enlace a PubMed de cada uno", ""),
    "congreso": ("Congreso de la República, nota del 30 de septiembre de 2026", "https://comunicaciones.congreso.gob.pe/noticias/comision-de-trabajo-aprueba-fortalecer-funciones-de-los-profesionales-de-enfermeria/"),
    "nts249": ("Norma Técnica de Salud 249, Resolución Ministerial 625-2026/MINSA, Anexo 04", "https://busquedas.elperuano.pe/dispositivo/NL/2535379-1"),
    "inforhus": ("Registro Nacional del Personal de la Salud, agosto de 2020, y Censo 2025; elaboración propia", ""),
    "autor": ("Elaboración del autor", ""),
}


def cap(*ks, extra=""):
    partes = []
    for k in ks:
        n, u = FUENTES[k]
        partes.append('%s%s' % (e(n), (' <a href="%s" rel="noopener">abrir</a>' % html.escape(u, quote=True)) if u else ""))
    return '<figcaption>Fuente: %s.%s</figcaption>' % ("; ".join(partes), (" " + e(extra)) if extra else "")


def svg(w, h, body, label, minw=0):
    st = (' style="min-width:%dpx"' % minw) if minw else ""
    return '<div class="svgw"><svg viewBox="0 0 %d %d" role="img" aria-label="%s"%s>%s</svg></div>' % (w, h, e(label), st, body)


def tx(x, y, s, cls="t", a="start"):
    return '<text x="%.1f" y="%.1f" class="%s" text-anchor="%s">%s</text>' % (x, y, cls, a, e(s))


def hbar(rows, vmax, label, w=600, lw=200, rowh=27, refs=(), dec=1, minw=0):
    """rows: (etiqueta, valor, clase de relleno, texto del valor o None, resaltar). Barras en HTML para que el texto no se encoja."""
    marcas = "".join('<em class="%s" style="left:%.2f%%"></em>' % (cls, 100.0 * v / vmax) for v, lab, cls in refs)
    o = []
    for r in rows:
        lab, v, cls = r[0], r[1], r[2]
        vt = r[3] if len(r) > 3 and r[3] else num(v, dec)
        fu = " fu" if len(r) > 4 and r[4] else ""
        o.append('<span class="hb-l%s">%s</span><span class="hb-t"><i class="%s" style="width:%.2f%%"></i>%s</span><span class="hb-v%s">%s</span>' % (fu, e(lab), cls, max(0.8, 100.0 * v / vmax), marcas, fu, e(vt)))
    pie = "".join('<p class="hb-ref"><em class="%s"></em>%s</p>' % (cls, e("Línea punteada: " + lab)) for v, lab, cls in refs)
    return '<div class="hb" role="img" aria-label="%s">%s</div>%s' % (e(label), "".join(o), pie)


def vbar(items, vmax, label, w=300, h=190, dec=1):
    """items: (etiqueta, valor, clase, texto)."""
    n = len(items)
    gap = 26
    bw = (w - 40 - gap * (n - 1)) / n
    base = h - 34
    o = ['<line x1="14" y1="%d" x2="%d" y2="%d" class="s-line" stroke-width="1.5"/>' % (base, w - 14, base)]
    for i, (lab, v, cls, vt) in enumerate(items):
        x = 20 + i * (bw + gap)
        bh = (base - 30) * v / vmax
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4" class="%s"/>' % (x, base - bh, bw, bh, cls))
        o.append(tx(x + bw / 2, base - bh - 8, vt or num(v, dec), "tb", "middle"))
        o.append(tx(x + bw / 2, base + 18, lab, "ts", "middle"))
    return svg(w, h, "".join(o), label)


def forest(rows, label, w=820, lw=370, lo=0.3, hi=1.3):
    x0, x1 = lw + 16, w - 150
    rowh, top = 34, 34

    def X(v):
        return x0 + (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) * (x1 - x0)

    h = top + len(rows) * rowh + 34
    o = []
    for t in (0.4, 0.5, 0.7, 1.0, 1.2):
        o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" class="%s" stroke-width="%s"/>' % (X(t), top - 6, X(t), h - 30, "s-ink" if t == 1.0 else "s-line", "2" if t == 1.0 else "1"))
        o.append(tx(X(t), h - 14, ("%.1f" % t), "ts", "middle"))
    o.append(tx(X(1.0) - 8, 16, "menos riesgo", "ts tok", "end"))
    o.append(tx(X(1.0) + 8, 16, "más riesgo", "ts task", "start"))
    for i, (lab, est, a, b, sub) in enumerate(rows):
        y = top + i * rowh + 14
        cls = "ok" if est < 1 else "ask"
        o.append(tx(lw, y - 1, lab, "tb", "end"))
        o.append(tx(lw, y + 13, sub, "ts", "end"))
        if a and b:
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="s-%s" stroke-width="3" stroke-linecap="round"/>' % (X(a), y + 3, X(b), y + 3, cls))
        o.append('<rect x="%.1f" y="%.1f" width="12" height="12" rx="2" class="f-%s"/>' % (X(est) - 6, y - 3, cls))
        o.append(tx(x1 + 14, y + 7, ("%s (%s a %s)" % (num(est, 2 if est < 1 or est > 1.1 else 3), num(a, 2), num(b, 2))) if a else ("%s, sin intervalo" % num(est, 2)), "t"))
    return svg(w, h, "".join(o), label, 620)


def lineas(serie_a, serie_b, label, w=640, h=250):
    x0, x1, y0, y1 = 64, w - 16, h - 40, 18
    vmax = 450000.0
    n = len(serie_a)

    def P(i, v):
        return (x0 + (x1 - x0) * i / (n - 1), y0 - (y0 - y1) * v / vmax)

    o = []
    for g in (0, 100000, 200000, 300000, 400000):
        y = y0 - (y0 - y1) * g / vmax
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="s-line" stroke-width="1"/>' % (x0, y, x1, y))
        o.append(tx(x0 - 8, y + 4, num(g / 1000) + " mil", "ts", "end"))
    for i in range(n):
        o.append(tx(P(i, 0)[0], y0 + 18, str(i + 1), "ts", "middle"))
    o.append(tx((x0 + x1) / 2, h - 4, "mes de 2015, de enero (1) a diciembre (12)", "ts", "middle"))
    area = "M%.1f,%.1f " % P(0, serie_a[0]) + " ".join("L%.1f,%.1f" % P(i, v) for i, v in enumerate(serie_a)) + " " + " ".join("L%.1f,%.1f" % P(i, serie_b[i]) for i in range(n - 1, -1, -1)) + " Z"
    o.append('<path d="%s" class="f-okbg"/>' % area)
    for serie, cls in ((serie_a, "s-ask"), (serie_b, "s-ok")):
        o.append('<polyline points="%s" class="%s f-none" stroke-width="3" stroke-linejoin="round"/>' % (" ".join("%.1f,%.1f" % P(i, v) for i, v in enumerate(serie)), cls))
        for i, v in enumerate(serie):
            o.append('<circle cx="%.1f" cy="%.1f" r="3.5" class="%s"/>' % (P(i, v)[0], P(i, v)[1], "f-ask" if cls == "s-ask" else "f-ok"))
    o.append(tx(P(n - 1, serie_a[-1])[0], P(n - 1, serie_a[-1])[1] - 12, "18 formatos", "tb task", "end"))
    o.append(tx(P(n - 1, serie_b[-1])[0], P(n - 1, serie_b[-1])[1] + 22, "1 formato estandarizado", "tb tok", "end"))
    o.append(tx(P(5, 290000)[0], P(5, 290000)[1], "ahorro", "ts tok", "middle"))
    return svg(w, h, "".join(o), label, 520)


def anidadas(rows, vmax, label, w=820, lw=350):
    x0 = lw + 10
    bw = w - x0 - 190
    rowh = 40
    h = 26 + len(rows) * rowh + 8
    o = [tx(x0, 14, "barra clara: todo · media: la mitad · oscura: la cuarta parte", "ts")]
    for i, (lab, camas, v) in enumerate(rows):
        y = 26 + i * rowh
        o.append(tx(lw, y + 15, lab, "tb", "end"))
        o.append(tx(lw, y + 29, num(camas) + " camas", "ts", "end"))
        for f, op in ((1.0, "0.28"), (0.5, "0.55"), (0.25, "1")):
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="22" rx="3" class="f-acc" opacity="%s"/>' % (x0, y + 5, bw * v * f / vmax, op))
        o.append(tx(x0 + bw * v / vmax + 8, y + 15, "S/ " + num(v) + " millones", "tb"))
        o.append(tx(x0 + bw * v / vmax + 8, y + 29, "prudente: S/ " + num(v * 0.25) + " millones", "ts"))
    return svg(w, h, "".join(o), label, 640)


def picto(n, k, label, cols=7):
    o = []
    for i in range(n):
        x, y = 16 + (i % cols) * 30, 16 + (i // cols) * 30
        o.append('<circle cx="%d" cy="%d" r="11" class="%s"/>' % (x, y, "f-acc" if i < k else "f-line"))
    return svg(16 + cols * 30 - 8, 16 + ((n - 1) // cols + 1) * 30 - 8, "".join(o), label)


def piramide():
    o = ['<polygon points="100,14 66,96 134,96" class="f-askbg"/>', '<polygon points="66,96 35,172 165,172 134,96" class="f-runbg"/>', '<polygon points="35,172 18,214 182,214 165,172" class="f-okbg"/>',
         '<polygon points="100,14 18,214 182,214" class="f-none s-ink" stroke-width="2"/>',
         '<line x1="66" y1="96" x2="134" y2="96" class="s-ink" stroke-width="1.5"/>', '<line x1="35" y1="172" x2="165" y2="172" class="s-ink" stroke-width="1.5"/>',
         '<line x1="124" y1="60" x2="196" y2="60" class="s-ask" stroke-width="1.5"/>', '<line x1="152" y1="134" x2="196" y2="134" class="s-gold" stroke-width="1.5"/>', '<line x1="176" y1="194" x2="196" y2="194" class="s-ok" stroke-width="1.5"/>',
         tx(202, 58, "Estratégico", "tB"), tx(202, 76, "decide", "tS"),
         tx(202, 132, "Táctico", "tB"), tx(202, 150, "conduce", "tS"),
         tx(202, 192, "Operativo", "tB"), tx(202, 210, "ejecuta el cuidado", "tS")]
    return svg(340, 226, "".join(o), "Pirámide de tres niveles de gestión: estratégico, táctico y operativo")


def triada():
    o = ['<line x1="170" y1="70" x2="74" y2="196" class="s-line" stroke-width="3"/>', '<line x1="170" y1="70" x2="266" y2="196" class="s-line" stroke-width="3"/>', '<line x1="74" y1="196" x2="266" y2="196" class="s-line" stroke-width="3"/>',
         '<circle cx="170" cy="70" r="60" class="f-acc"/>', '<circle cx="74" cy="196" r="60" class="f-gold"/>', '<circle cx="266" cy="196" r="60" class="f-ask"/>',
         tx(170, 66, "Enfoque", "tW", "middle"), tx(170, 85, "la persona", "tV", "middle"),
         tx(74, 192, "Modelo", "tW", "middle"), tx(74, 211, "la evidencia", "tV", "middle"),
         tx(266, 192, "Equipo", "tW", "middle"), tx(266, 211, "tres niveles", "tV", "middle")]
    return svg(340, 262, "".join(o), "Marco GEMSES: enfoque centrado en la persona, modelo basado en la evidencia y equipo en tres niveles")


def radial():
    un = ["Atención prehospitalaria", "Emergencia", "Consulta externa", "Centro obstétrico", "Hospitalización", "Centro quirúrgico", "Cuidados intensivos", "Docencia e investigación"]
    cx, cy = 350, 170
    o = ['<circle cx="%d" cy="%d" r="62" class="f-acc"/>' % (cx, cy), '<circle cx="%d" cy="%d" r="46" class="f-ink"/>' % (cx, cy),
         tx(cx, cy - 6, "Persona, familia", "tw", "middle"), tx(cx, cy + 11, "y comunidad", "tw", "middle")]
    pos = [(150, 40), (106, 125), (106, 215), (150, 300), (550, 40), (594, 125), (594, 215), (550, 300)]
    for (x, y), u in zip(pos, un):
        o.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" class="s-acc" stroke-width="2" stroke-dasharray="6 5"/>' % (x, y, cx + (x - cx) * 0.25, cy + (y - cy) * 0.36))
        o.append('<rect x="%d" y="%d" width="200" height="30" rx="15" class="f-surf s-acc" stroke-width="1.5"/>' % (x - 100, y - 15))
        o.append(tx(x, y + 5, u, "t", "middle"))
    o.append(tx(cx, cy - 74, "Enfermería", "tb tacc", "middle"))
    o.append(tx(cx, cy + 88, "las 24 horas", "tb tacc", "middle"))
    return svg(700, 340, "".join(o), "La persona al centro, rodeada por enfermería y por ocho unidades de atención directa", 560)


def stack(partes, cap=34):
    tot = float(sum(p[0] for p in partes)) or 1.0

    def rot(n, t):
        if not t:
            return ""
        lim = cap * n / tot
        if len(t) <= lim:
            return t
        corto = t.split(": ")[-1]
        return corto if len(corto) <= lim else ""

    return '<div class="stack">%s</div>' % "".join('<span class="%s" style="flex:%s" title="%s">%s</span>' % (c, n, e(t), e(rot(n, t))) for n, c, t in partes if n)


def leyenda(items):
    return '<p class="leyenda">%s</p>' % "".join('<span><i class="%s"></i>%s</span>' % (c, e(t)) for c, t in items)


def fig(titulo, cuerpo, caption="", ancha=False, gran=None, txt=None):
    return '<figure class="fig%s"><h4>%s</h4>%s%s%s%s</figure>' % (" ancha" if ancha else "", e(titulo), ('<p class="gran">%s</p>' % gran) if gran else "", cuerpo, ('<p class="txt">%s</p>' % e(txt)) if txt else "", caption)


ESTADOS = {"HECHO": ("hecho", "Hecho"), "EN_CURSO": ("curso", "En curso"), "PENDIENTE": ("pend", "Pendiente"), "POR_DECIDIR": ("decidir", "Por decidir")}
CAPAS = {"CITA": ("cita", "Cita"), "DERIVACION": ("deriv", "Derivación"), "JUICIO": ("juicio", "Juicio del autor"), "ESTADO": ("est", "Estado del trabajo")}


def chip_estado(k):
    c, t = ESTADOS.get(k, ("pend", k))
    return '<span class="chip st-%s"><i aria-hidden="true"></i>%s</span>' % (c, t)


def chip_capa(k):
    c, t = CAPAS.get(str(k).upper().replace("Ó", "O"), ("est", str(k).capitalize()))
    return '<span class="capa capa-%s">%s</span>' % (c, t)


def fuente(d):
    f, u = d.get("fuente", ""), (d.get("enlace") or "").strip()
    if u.startswith("http"):
        return '%s <a class="src" href="%s" rel="noopener">abrir fuente</a>' % (e(f), html.escape(u.split(" ")[0], quote=True))
    return e(f)


def hechos(lista):
    grupos, orden = {}, []
    for d in lista:
        g = (d.get("subtitulo") or "").strip() or "Datos"
        if g not in grupos:
            grupos[g] = []
            orden.append(g)
        grupos[g].append(d)
    out = []
    for g in orden:
        out.append('<h4>%s</h4><ul class="hechos">' % e(g))
        for d in grupos[g]:
            donde = (d.get("enDeck") or "").strip()
            out.append('<li><p class="dato">%s</p><p class="meta">%s%s<span class="fu">%s</span></p></li>' % (e(d.get("dato")), chip_capa(d.get("capa")), ('<span class="donde">%s</span>' % e(donde)) if donde else "", fuente(d)))
        out.append("</ul>")
    return "\n".join(out)


def corto(u):
    u = (u or "").replace("\\", "/")
    for a, b in (("C:/Users/infor/OneDrive/CARLOS PEREZ/UNIVERSIDADES/CEP/FORO", "carpeta FORO"),
                 (str(S).replace("\\", "/"), "carpeta de trabajo de la sesión"),
                 ("C:/Users/infor/OneDrive/CARLOS PEREZ", "OneDrive de Carlos"), ("C:/Users/infor/.claude/projects/C--Users-infor/memory", "memoria del proyecto")):
        if u.startswith(a):
            u = b + u[len(a):]
    return u


def archivo(nombre, ubic, local):
    u = (ubic or "").strip()
    if u.startswith("http"):
        return '<a href="%s" rel="noopener">%s</a>' % (html.escape(u, quote=True), e(nombre))
    if local and u:
        try:
            rel = pathlib.Path(u.replace("\\", "/")).resolve().relative_to(FORO.resolve())
            if (FORO / rel).exists():
                return '<a href="%s">%s</a>' % (html.escape(str(rel).replace("\\", "/"), quote=True), e(nombre))
        except Exception:
            pass
    return e(nombre)


def detalles(key, local, titulo="Ver los datos y sus fuentes"):
    r = INV.get(key)
    if not r:
        return ""
    o = ['<details class="datos"><summary>%s (%d)</summary><div>' % (e(titulo), len(r.get("tenemos", [])))]
    if r.get("pedidos"):
        o.append('<div class="pedidos"><h3>Lo que pidió</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(p) for p in r["pedidos"]))
    o.append(hechos(r.get("tenemos", [])))
    if r.get("advertencias"):
        o.append('<div class="aviso"><h3>Advertencias</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(a) for a in r["advertencias"]))
    if r.get("pendientes"):
        o.append('<h3>Pendientes de este tema</h3><ul class="pend">%s</ul>' % "".join('<li><p class="dato">%s</p><p class="meta"><span class="quien">%s</span><span class="fu">Siguiente paso: %s</span></p></li>' % (e(p.get("que")), e(p.get("quien")), e(p.get("siguientePaso"))) for p in r["pendientes"]))
    if r.get("entregables"):
        o.append('<h3>Archivos de este tema</h3><ul class="files">%s</ul>' % "".join('<li><b>%s</b><span>%s</span><span class="ruta">%s</span></li>' % (archivo(x.get("nombre"), x.get("ubicacion"), local), e(x.get("descripcion")), e(corto(x.get("ubicacion")))) for x in r["entregables"]))
    o.append("</div></details>")
    return "\n".join(o)


def seccion(anchor, titulo, estado, lead, cuerpo):
    return '<section id="%s" class="tema"><div class="tema-h"><h2>%s</h2>%s</div><p class="lead">%s</p>%s</section>' % (anchor, e(titulo), chip_estado(estado) if estado else "", e(lead), cuerpo)


def estado_de(key, defecto):
    return (INV.get(key) or {}).get("estado") or defecto

# ------------------------------------------------------------------ datos del deck y del plan


def lee_deck():
    P = S / "deck-panel1" / "project"
    d = json.load(open(P / "deck.json", encoding="utf-8"))
    sec = {}
    actual = "s1"
    starts = {v["start"]: k for k, v in d["sections"].items()}
    out = []
    for i, sid in enumerate(d["order"], 1):
        actual = starts.get(sid, actual)
        t = (P / "slides" / (sid + ".html")).read_text(encoding="utf-8")
        m = re.search(r"<h2[^>]*>(.*?)</h2>", t, re.S) or re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        tit = re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else sid
        tm = re.search(r"<aside>(\d+:\d\d)", t)
        resp = sid in ("anexo", "anexo2", "gracias")
        out.append({"n": i, "id": sid, "titulo": html.unescape(tit), "tiempo": tm.group(1) if tm else "", "sec": actual, "resp": resp})
    return out


def lee_plan():
    t = (FORO / "PLAN_LAMINAS_PANEL1.md").read_text(encoding="utf-8")
    filas = []
    for ln in t.splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) == 7 and re.match(r"^\d+$", c[0]):
            lam = re.sub(r"\*\*", "", c[1])
            filas.append({"n": int(c[0]), "lamina": lam, "dira": c[2], "cambio": re.sub(r"\*\*", "", c[5]), "tiempo": c[6]})
    return filas


DECK = lee_deck()
PLAN = lee_plan()


def story_deck():
    its = []
    for x in DECK:
        cls = "resp" if x["resp"] else x["sec"]
        its.append('<li class="%s"><span class="num">%d</span><span class="tit">%s</span><span class="tie">%s</span></li>' % (cls, x["n"], e(x["titulo"]), e(x["tiempo"] or "respaldo")))
    return '<ol class="story">%s</ol>' % "".join(its)


def story_plan():
    its = []
    for x in PLAN:
        c = x["cambio"].lower()
        tag = "nueva" if c.startswith("nueva") else "rehecha" if c.startswith("rehecha") else "fusión" if c.startswith("fusión") else "ajuste" if c.startswith("ajuste") else ""
        its.append('<li class="%s"><span class="num">%d</span><span class="tit">%s</span>%s<span class="tie">%s</span></li>' % ("nuevo" if tag in ("nueva", "rehecha", "fusión") else "", x["n"], e(x["lamina"]), ('<span class="tag">%s</span>' % tag) if tag else "", e(x["tiempo"])))
    return '<ol class="story">%s</ol>' % "".join(its)

# ------------------------------------------------------------------ secciones


def sec_vistazo():
    temas = [
        ("deck", "El deck publicado", estado_de("deck", "HECHO"), "20", "láminas en la versión 20; 9 minutos 55 segundos más 3 de remate"),
        ("estrategia", "La nueva estrategia", "POR_DECIDIR", "9", "láminas con más datos, pensadas para el Ministro de Salud: una apertura y dos partes"),
        ("primera2" if PRI else "primera", "La primera lámina: datos e inteligencia artificial", "POR_DECIDIR" if PRI else "EN_CURSO", "6", "pasos del circuito del control del cuidado en manos de enfermería" + ("; sustento ya verificado" if PRI else "; sustento en verificación")),
        ("plan3", "El plan, lámina por lámina", "POR_DECIDIR", "9", "láminas con su mensaje, su visual y sus datos ya verificados"),
        ("ministro", "El Ministro y su agenda", "HECHO", "88 %", "de los puestos de salud públicos I-1 que reportan no tiene médico; en la mitad hay enfermera"),
        ("ocde", "El Perú frente a la OCDE", "HECHO", "32 de 33", "lugar del Perú en enfermeras profesionales por habitante; toda la data de salud está en su base"),
        ("mundo", "Jefatura de enfermería en 194 países", "HECHO", "82.5 %", "de los países que respondieron en 2025 la reportan; el Perú reportó que no en 2020"),
        ("plan", "El plan anterior", "HECHO", "17", "láminas: 2 nuevas, 1 fusión y 1 rehecha; lo reemplaza la nueva estrategia si usted la aprueba"),
        ("encargo", "Encargo y primeros análisis", estado_de("primeros_temas", "HECHO"), "18.0 %", "del personal del sector salud son enfermeros"),
        ("demanda", "Demanda, oferta y brecha", estado_de("demanda", "HECHO"), "22 000", "enfermeros faltan para el umbral de la Organización Mundial de la Salud"),
        ("normas", "Marco normativo", estado_de("normativa", "HECHO"), "6", "frentes, cada uno con su artículo literal"),
        ("valor", "Valor del cuidado y programas", estado_de("valor_programas", "HECHO"), "24", "artículos científicos verificados"),
        ("investigacion", "Investigación y modelo de cuidado", estado_de("bibliometria_modelo", "HECHO"), "8", "de 11 374 registros de PubMed tienen afiliación peruana"),
        ("gemses", "Marco GEMSES y caso del registro", estado_de("gemses_caso", "POR_DECIDIR"), "S/ 2.0 M", "de ahorro en un año con 95 camas"),
        ("niveles", "El mapa de tres niveles", "EN_CURSO" if not NIV else "HECHO", "3", "niveles: enfermería está en dos y falta en el que decide"),
        ("paises", "Países con dirección de enfermería", "HECHO" if PAI else "EN_CURSO", "18 de 21", "países de las Américas informan tener jefatura de enfermería en el gobierno"),
        ("autonomia2" if AUTC else "autonomia", "Autonomía frente al equipo", "HECHO" if AUTC else "EN_CURSO", "4", "pasos verificados: decide, responde, dentro del equipo y con frontera escrita"),
        ("rigor", "Imagen, auditorías y rigor", estado_de("imagen_auditorias", "POR_DECIDIR"), "205", "hallazgos confirmados en el dossier"),
    ]
    cuenta = {}
    for t in temas:
        cuenta[t[2]] = cuenta.get(t[2], 0) + 1
    tiles = "".join('<a class="tile" href="#%s">%s<b>%s</b><span class="kpi">%s</span><span class="d">%s</span></a>' % (a, chip_estado(st), e(n), e(k), e(d)) for a, n, st, k, d in temas)
    barra = stack([(cuenta.get("HECHO", 0), "sg-ok", "Hecho: %d" % cuenta.get("HECHO", 0)), (cuenta.get("EN_CURSO", 0), "sg-run", "En curso: %d" % cuenta.get("EN_CURSO", 0)), (cuenta.get("POR_DECIDIR", 0), "sg-ask", "Por decidir: %d" % cuenta.get("POR_DECIDIR", 0)), (cuenta.get("PENDIENTE", 0), "sg-wait", "Pendiente: %d" % cuenta.get("PENDIENTE", 0))], cap=110)
    hilo = '<ol class="flujo c4">%s</ol>' % "".join("<li><b>%s</b><span>%s</span></li>" % (e(a), e(b)) for a, b in [
        ("Datos e inteligencia artificial", "el control del cuidado en manos de enfermería"), ("Presencia", "el país que cuidamos"), ("Resultados", "cuando la enfermera decide en su campo"), ("Eficiencia", "del registro al dato"),
        ("El mapa", "conduce y ejecuta, pero no decide"), ("Los países", "dirección nacional de enfermería"), ("La ventana", "la nueva estructura del Ministerio"), ("Remate", "tres pedidos")])
    cuerpo = '<h3>Los temas y su estado</h3>%s<div class="tiles">%s</div><h3>El hilo de la exposición que propone la nueva estrategia</h3>%s' % (barra, tiles, hilo)
    return seccion("vistazo", "Estado de un vistazo", None, "Cada recuadro lleva a su tema. El color y la forma del estado dicen si está hecho, en curso o esperando su decisión.", cuerpo)


def sec_decisiones():
    dec = [
        ("Aprobar la nueva estrategia", "Nueve láminas con más datos. Abre con datos, inteligencia artificial y control del cuidado en manos de enfermería; sigue con lo que enfermería ya aporta y con qué pasaría con respaldo en la alta dirección. Reemplaza al plan anterior de 17 láminas. Nada se construye hasta su visto bueno.", "Aprobarla. Las investigaciones ya cerraron: el deck puede construirse en cuanto usted dé el visto bueno."),
        ("Imagen de la lámina «Arte»", "La ilustración propia está publicada. La foto real se descargó, pero su página pública muestra el documento de identidad y la tarjeta de historia clínica de un paciente.", "Quedarse con la ilustración."),
        ("Qué escenario de extrapolación mostrar", "Techo: S/ 859 millones al año si cada cama del país lograra lo del Instituto. Prudente: S/ 215 millones, la cuarta parte.", "Mostrar los dos, rotulados como cálculo del autor."),
        ("Nombrar al Instituto Nacional Cardiovascular en el caso", "El caso tiene un artículo publicado en la revista de enfermería del propio Instituto, en 2018.", "Nombrarlo, después de leer la cifra en el artículo publicado."),
        ("Descargar los artículos de acceso libre", "Quince de los artículos de la revisión tienen texto completo libre en PubMed Central. Hoy solo están los enlaces.", "Descargarlos a la carpeta si los quiere a mano."),
    ]
    pd = ["Qué significa «OGCE» en su indicación: lo leo como la Organización para la Cooperación y el Desarrollo Económicos.", "La cita literal del Ministro de Salud sobre control con datos e inteligencia artificial, con fecha y enlace.", "Cuántos establecimientos cumplen el artículo 13 de la Ley 27669.", "Cumplimiento de las 85 horas de capacitación por empleador.", "Etapa del texto sustitutorio después del 30 de septiembre de 2026.",
          "Vigencia del reglamento de organización del Ministerio de Salud de 2025: falta ubicar la resolución de su Sección Segunda.", "Camas de cuidados críticos del Instituto Nacional Cardiovascular en 2015, para extrapolar solo sobre camas críticas.",
          "La cifra del ahorro tal como aparece en el artículo publicado de 2018, que está escaneado.", "Consentimiento de las personas retratadas en la foto real."]
    if PRI:
        pd = [x for x in pd if "OGCE" not in x and "cita literal del Ministro" not in x]
    it = "".join('<li><div><b>%s</b><p>%s</p></div><p class="rec"><span>Recomendación</span>%s</p></li>' % (e(a), e(b), e(c)) for a, b, c in dec)
    cuerpo = '<ol class="dec">%s</ol><h3>Por determinar</h3><ul class="pd">%s</ul>' % (it, "".join("<li>%s</li>" % e(x) for x in pd))
    return seccion("decisiones", "Lo que espera su decisión", "POR_DECIDIR", "Cinco decisiones, en orden de urgencia, y los datos que todavía nadie ha podido sustentar. Lo que está por determinar no entra al deck como afirmación.", cuerpo)


def sec_deck(local):
    tot = sum(int(x["tiempo"].split(":")[0]) * 60 + int(x["tiempo"].split(":")[1]) for x in DECK if x["tiempo"] and x["id"] not in ("normas", "conclusiones"))
    cuerpo = ('<p><a class="btn" href="%s" rel="noopener">Abrir el deck, versión 20</a></p><h3>Guion gráfico: las 20 láminas</h3>%s%s%s' % (
        DECK_URL, story_deck(),
        leyenda([("sg-acc", "Punto de partida, pilares y áreas"), ("sg-gold", "Ciencia, arte y disciplina"), ("sg-ok", "Las cuatro áreas"), ("sg-ask", "Tecnología y quién decide"), ("sg-wait", "Remate y respaldo")]),
        detalles("deck", local, "Ver estado, versiones y pedidos sobre la forma")))
    return seccion("deck", "El deck publicado", estado_de("deck", "HECHO"), "Versión 20, con la plantilla institucional del Colegio de Enfermeros del Perú. La exposición suma %d minutos %d segundos; el remate, 3 minutos." % (tot // 60, tot % 60), cuerpo)


def sec_plan(local):
    cuerpo = '<h3>Guion gráfico del plan: 17 láminas a presentar</h3>%s%s<p class="nota">El detalle de cada lámina, con su fuente y su capa, está en el archivo PLAN_LAMINAS_PANEL1.md de la carpeta FORO.</p>' % (
        story_plan(), leyenda([("sg-run", "Fondo ámbar: lámina nueva, rehecha o fusionada"), ("sg-panel", "Fondo blanco: sin cambio o con ajuste menor")]))
    return seccion("plan", "El plan anterior, de 17 láminas", "POR_DECIDIR", "Lo propuse antes de su indicación de ser más estratégicos. Ordena la exposición según el Modelo GEMSES. Queda como referencia: la nueva estrategia lo reemplaza si usted la aprueba.", cuerpo)


NOMBRES = {"Apurimac": "Apurímac", "Madre De Dios": "Madre de Dios", "Junin": "Junín", "Huanuco": "Huánuco", "San Martin": "San Martín", "Ancash": "Áncash"}


def sec_encargo(local):
    prof = [("Enfermero", 71052, "f-acc", None, True), ("Médico", 57110, "f-wait"), ("Obstetra", 21599, "f-wait"), ("Tecnólogo médico", 8879, "f-wait"), ("Psicólogo", 7432, "f-wait"), ("Odontólogo", 7289, "f-wait"),
            ("Químico farmacéutico", 5594, "f-wait"), ("Biólogo", 4165, "f-wait"), ("Nutricionista", 3209, "f-wait"), ("Trabajadora social", 2662, "f-wait")]
    f1 = fig("El equipo de salud por profesión, 2023", hbar([(a, b, c, num(b), len(r) > 4) for r in prof for a, b, c in [r[:3]]], 80000, "Profesionales asistenciales del sector salud por profesión en 2023", dec=0),
             cap("minsa", extra="Cuadro 01. Además hay 107 686 técnicos asistenciales, que el informe no separa por profesión."), txt="De cada 100 profesionales asistenciales, 37 son enfermeros (71 052 de 190 316; cálculo del autor).")
    depto = []
    try:
        for r in csv.DictReader(io.open(FORO / "mapas_enfermeria_ampliada" / "tabla_departamentos.csv", encoding="utf-8-sig")):
            depto.append((NOMBRES.get(r["departamento"].title(), r["departamento"].title()), float(r["por_10000"])))
    except Exception as ex:
        print("sin tabla de departamentos", ex)
    depto.sort(key=lambda x: -x[1])
    sel = depto[:5] + depto[-5:]
    f2 = fig("Enfermería ampliada por cada 10 000 habitantes: los cinco más altos y los cinco más bajos",
             hbar([(a, b, "f-acc" if i < 5 else "f-gold") for i, (a, b) in enumerate(sel)], 65, "Enfermeras y técnicos en enfermería por cada 10 000 habitantes, departamentos extremos", dec=2),
             cap("inforhus", extra="Enfermería ampliada suma enfermeras y técnicos en enfermería. Los conteos son de 2020 y la población de 2025."))
    img = ""
    p = HERE / "mapa_sin_leyenda.jpg"
    if p.exists():
        img = fig("Mapa por departamento", '<img class="mapaimg" alt="Mapa del Perú por departamento: enfermeras y técnicos en enfermería por cada 10 000 habitantes; los tonos más oscuros están en la sierra sur y Madre de Dios" src="data:image/jpeg;base64,%s">' % base64.b64encode(p.read_bytes()).decode() + '<p class="leyenda mapal"><b>Por cada 10 000 habitantes</b><span><i style="background:#F2F7FD"></i>19.8 a 23.4</span><span><i style="background:#C4E1F1"></i>23.4 a 31.7</span><span><i style="background:#85B1D8"></i>31.7 a 33.4</span><span><i style="background:#3080C5"></i>33.4 a 43.9</span><span><i style="background:#0C3E6F"></i>43.9 a 59.2</span></p>', cap("inforhus"))
    cuerpo = '<div class="figs">%s%s%s</div>%s' % (f1, f2, img, detalles("primeros_temas", local))
    return seccion("encargo", "El encargo y los primeros análisis", estado_de("primeros_temas", "HECHO"), "El organizador pidió mostrar a la enfermería como ciencia, arte y disciplina en sus cuatro áreas. Los primeros análisis midieron su peso en el equipo de salud y su distribución en el territorio.", cuerpo)


def sec_demanda(local):
    f1 = fig("Demanda: la población", vbar([("60 años o más, 2017", 11.7, "f-wait", "11.7 %"), ("60 años o más, 2025", 14.8, "f-acc", "14.8 %")], 18, "Población de 60 años o más: 11.7 por ciento en 2017 y 14.8 por ciento en 2025"),
             cap("censo"), gran="34 157 732 <small>habitantes en el Censo 2025</small>")
    f2 = fig("Demanda: enfermedades crónicas en personas de 15 años o más, 2025",
             hbar([("Exceso de peso", 63.8, "f-gold", "63.8 %"), ("Al menos una de tres condiciones", 41.8, "f-acc", "41.8 %", True), ("Hipertensión", 20.8, "f-gold", "20.8 %"), ("Diabetes diagnosticada", 5.2, "f-gold", "5.2 %")], 80, "Prevalencia de enfermedades crónicas en 2025", lw=230),
             cap("ent", extra="Las tres condiciones son obesidad, diabetes e hipertensión."),
             txt="Además, el 19.4 % de la población vive en el área rural.")
    reg = [("Apurímac", 38.36), ("Moquegua", 37.81), ("Huancavelica", 33.12), ("Callao", 31.18), ("Ayacucho", 27.09), ("Huánuco", 26.47), ("Lima", 21.70), ("Perú", 21.00), ("Cajamarca", 18.37), ("La Libertad", 16.94), ("Ucayali", 15.89), ("San Martín", 14.93), ("Loreto", 13.91), ("Piura", 12.34)]
    f3 = fig("Oferta: enfermeros por cada 10 000 habitantes, por región, 2023",
             hbar([(a, b, "f-ink" if a == "Perú" else ("f-acc" if b >= 27.5 else "f-gold"), num(b, 2), a == "Perú") for a, b in reg], 42, "Densidad de enfermeros por región frente al umbral de 27.5", lw=120, refs=[(27.5, "umbral 27.5", "s-ask")], dec=2),
             cap("minsa", "oms", extra="Se muestran las seis regiones más altas, las seis más bajas, Lima y el país."), ancha=False, gran="71 052 <small>enfermeros, 18.0 % del sector</small>")
    f4 = fig("Brecha: cuánto falta para el umbral",
             hbar([("Perú hoy", 21.00, "f-gold", "21.00"), ("Umbral de la Organización Mundial de la Salud", 27.5, "f-ask", "27.5")], 34, "Densidad actual de 21.00 frente al umbral de 27.5 enfermeros por 10 000 habitantes", lw=290, dec=2),
             cap("minsa", "oms", extra="Cálculo del autor: (27.5 − 21.00) × 71 052 ÷ 21.00 = 21 992."), gran="≈ 22 000 <small>enfermeros faltan</small>",
             txt="El umbral es la mediana de 2013 en 194 Estados Miembros. La Organización Mundial de la Salud lo usa para estimar el déficit; no es una meta legal.")
    am = [("Estados Unidos", 123.92), ("Canadá", 116.18), ("Cuba", 71.94), ("Argentina", 64.87), ("Brasil", 58.32), ("Chile", 47.16), ("México", 30.48), ("Perú", 27.38), ("Ecuador", 26.30), ("Colombia", 15.73)]
    f5 = fig("Comparación en las Américas: enfermería y partería por cada 10 000 habitantes",
             hbar([(a, b, "f-acc" if a == "Perú" else "f-wait", num(b, 2), a == "Perú") for a, b in am], 135, "Enfermería y partería por 10 000 habitantes en diez países de las Américas", lw=130, dec=2),
             cap("gho", extra="Último dato de cada país, entre 2020 y 2024. El Perú ocupa el puesto 22 de 35; el puesto es cálculo del autor."))
    f6 = fig("Oferta: régimen laboral de los enfermeros del Ministerio de Salud y los gobiernos regionales",
             stack([(54.8, "sg-acc", "Régimen 276: 54.8 %"), (43.3, "sg-gold", "Contratación Administrativa de Servicios: 43.3 %"), (1.9, "sg-wait", "Otros: 1.9 %")]) + leyenda([("sg-acc", "Régimen 276: 54.8 %"), ("sg-gold", "Contratación Administrativa de Servicios: 43.3 %"), ("sg-wait", "Terceros y régimen 728: 1.9 %")]),
             cap("minsa", extra="Sobre 48 990 enfermeros."))
    flujo = '<ol class="flujo"><li><b>Demanda</b><span>un país que envejece y vive con enfermedades crónicas</span></li><li class="oro"><b>Oferta</b><span>71 052 enfermeros, mal repartidos entre regiones</span></li><li class="ask"><b>Brecha</b><span>unos 22 000 para llegar al umbral</span></li></ol>'
    cuerpo = '%s<div class="figs">%s%s%s%s%s%s</div>%s' % (flujo, f1, f2, f3, f4, f5, f6, detalles("demanda", local))
    return seccion("demanda", "Demanda, oferta y brecha", estado_de("demanda", "HECHO"), "Es la lámina 2 del deck. Parte del país que cuidamos antes de hablar de la profesión.", cuerpo)


def sec_normas(local):
    hitos = [("1978", "Decreto Ley 22315", "crea el Colegio de Enfermeros del Perú"), ("2002", "Ley 27669 y su reglamento", "cuatro áreas, unidad orgánica de enfermería, registro obligatorio, 85 horas"),
             ("2015", "Decretos Supremos 012 y 031", "concurso de jefaturas y residentado en enfermería"), ("2016", "Ley 30459", "consultorios de profesionales de enfermería"),
             ("2025", "Decreto Supremo 019-2025-SA", "nuevo reglamento del Ministerio de Salud, sin órgano de enfermería"), ("Enero de 2026", "Decreto Supremo 001-2026-SA", "esos consultorios son establecimientos de salud"),
             ("Agosto y septiembre de 2026", "Proposiciones 91 y 159", "autonomía en la Ley 27669; texto sustitutorio aprobado en comisión el 30 de septiembre"),
             ("8 de septiembre de 2026", "Decreto Supremo 014-2026-SA", "Ministerio de Salud en reorganización por 90 días"), ("7 de diciembre de 2026", "Vence el informe", "con la propuesta de nueva estructura orgánica; fecha calculada por el autor")]
    linea = '<ol class="crono">%s</ol>' % "".join('<li><span class="cuando">%s</span><div><b>%s</b><p>%s</p></div></li>' % (e(a), e(b), e(c)) for a, b, c in hitos)
    fr = [("Colegio", "«entidad autónoma y normativa que vela y regula el ejercicio profesional de Enfermería»", "Ley 27669, Segunda Disposición Final", "Actualizar el artículo 2"),
          ("Formación", "cada vacante de residentado «debe contar con el financiamiento correspondiente»", "Decreto Supremo 031-2015-SA, artículo 10", "Vacantes según la brecha de cada especialidad"),
          ("Asistencial", "el proceso de atención «será registrado obligatoriamente en la historia clínica del paciente y/o en la ficha familiar»", "Decreto Supremo 004-2002-SA, artículo 9, literal a", "Que el registro llegue como dato"),
          ("Gestión", "Unidad Orgánica de Enfermería «como órgano de línea» en todo establecimiento", "Ley 27669, artículo 13", "Una instancia de enfermería en el nivel estratégico"),
          ("Docencia", "las horas de capacitación «deberán ser por lo menos de ochenta y cinco (85) horas al año»", "Decreto Supremo 004-2002-SA, artículo 15", "Medir su cumplimiento por empleador"),
          ("Investigación", "«Realizar investigación en el campo de Enfermería y de salud»", "Ley 27669, artículo 7, literal i", "Producir evidencia propia")]
    tabla = '<div class="scroll"><table class="vist matriz"><thead><tr><th>Frente</th><th>Lo que ya dice la norma</th><th>Dónde</th><th>Lo que falta, lectura del autor</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td class="no">%s</td></tr>' % (e(a), e(b), e(c), e(d)) for a, b, c, d in fr)
    cuerpo = '<div class="figs"><figure class="fig ancha"><h4>Seis frentes: lo que ya es norma y lo que falta</h4>%s%s</figure><figure class="fig ancha"><h4>Línea de tiempo normativa</h4>%s%s</figure></div>%s' % (
        tabla, cap("ley", "ds004"), linea, cap("ley", "ds019", "ds014", "congreso"), detalles("normativa", local))
    return seccion("normas", "Marco normativo por frente", estado_de("normativa", "HECHO"), "Cada frente tiene su artículo literal, abierto en el texto oficial. La columna de lo que falta es lectura del autor.", cuerpo)


def sec_valor(local):
    fo = [("Vigilancia de enfermería 12 o más veces al día", 0.52, None, None, "Shever 2011 · muerte tras complicación"),
          ("Enfermera de ictus en el equipo", 0.56, 0.37, 0.85, "Kumar 2025 · muerte a tres meses"),
          ("Transición dirigida por enfermeras", 0.69, 0.54, 0.89, "Koontalay 2025 · reingreso en insuficiencia cardiaca"),
          ("Más enfermeras en cuidados intensivos", 0.91, 0.86, 0.96, "Kane 2007 · mortalidad hospitalaria"),
          ("10 % más de enfermeras con bachiller", 0.929, 0.886, 0.973, "Aiken 2014 · muerte a 30 días"),
          ("Un paciente más por enfermera", 1.07, 1.03, 1.12, "Aiken 2002 · muerte a 30 días")]
    f1 = fig("Lo que cambia cuando hay más y mejor enfermería", forest(fo, "Efecto de seis intervenciones o condiciones de enfermería, como razón de riesgo o de momios con su intervalo de confianza"),
             cap("articulos", extra="Cada cuadro es el efecto estimado y la línea su intervalo de confianza al 95 %. Los estudios de dotación son observacionales: muestran asociación, no causa."), ancha=True)
    f2 = fig("Cáncer: días de hospitalización", vbar([("Con enfermeras navegadoras", 2.82, "f-ok", "2.82"), ("Cuidado habitual", 4.44, "f-wait", "4.44")], 5.2, "Días de hospitalización: 2.82 con enfermeras navegadoras frente a 4.44 con cuidado habitual", dec=2),
             cap("articulos", extra="Mir 2022, ensayo aleatorizado de fase 3 con 559 pacientes."))
    f3 = fig("Ictus: minutos de puerta a aguja", '<p class="gran">−19.7 <small>minutos con enfermera de ictus</small></p>', cap("articulos", extra="Kumar 2025, revisión sistemática y metaanálisis de 8 estudios."), txt="Además, la razón de momios de muerte a tres meses es 0.56.")
    f4 = fig("Diabetes tipo 2: hemoglobina glucosilada", '<p class="gran">−0.68 <small>con cuidado dirigido por enfermeras</small></p>', cap("articulos", extra="Zhang 2022, metaanálisis de 13 ensayos aleatorizados con 3 757 participantes."), txt="Es la prueba del pilar Ciencia en el mapa del deck.")
    f5 = fig("Jefatura de enfermería en el gobierno, países de las Américas", picto(21, 18, "18 de 21 países de las Américas que respondieron informan tener una jefatura de enfermería en el gobierno"),
             cap("oms", extra="Página impresa 88, tabla 8.1. Datos de 2018 a 2023."), gran="18 de 21 <small>países que respondieron</small>", txt="En el mundo, 82 %. El informe no dice si el Perú está entre los 18.")
    f6 = fig("Trasplante: coordinación", '<p class="gran">Obligatorio</p>', cap("articulos", extra="Código de Regulaciones Federales de Estados Unidos, título 42, sección 482.98."), txt="En Estados Unidos, el coordinador clínico de trasplante debe ser una enfermera registrada o un clínico con licencia. En España la coordinación la hace un médico o personal de enfermería bajo su supervisión.")
    cuerpo = '<div class="figs">%s%s%s%s%s%s</div>%s' % (f1, f2, f3, f4, f5, f6, detalles("valor_programas", local))
    return seccion("valor", "Valor del cuidado y programas que coordina enfermería", estado_de("valor_programas", "HECHO"), "Veinticuatro artículos verificados sostienen el mapa de pilares y áreas y la lámina de gestión. No se sostiene decir que todos los programas exitosos los coordina enfermería; sí que, donde enfermería los dirige, hay resultados medidos.", cuerpo)


def sec_investigacion(local):
    f1 = fig("Registros de PubMed sobre liderazgo en enfermería, por afiliación del autor",
             hbar([("Brasil", 143, "f-wait", "143"), ("Chile", 28, "f-wait", "28"), ("Colombia", 25, "f-wait", "25"), ("Perú", 8, "f-acc", "8", True), ("México", 8, "f-wait", "8")], 160, "Registros de PubMed con las palabras nursing y leadership, por país de afiliación", lw=110, dec=0),
             cap("pubmed", extra="Son 11 374 registros en total. Es una búsqueda por palabras: uno de los 8 registros peruanos no trata de enfermería."), gran="8 de 11 374")
    f2 = fig("La persona al centro: ocho unidades de atención directa", radial(), cap("nts249", extra="Además hay 36 unidades de soporte. El anillo y las flechas son propuesta del autor."), ancha=True)
    mom = '<ol class="flujo">%s</ol>' % "".join("<li><b>%s</b><span>%s</span></li>" % (e(a), e(b)) for a, b in [("Periodo prenatal", ""), ("Niña y niño", "hasta los 11 años"), ("Adolescente", "12 a 17 años"), ("Adulto joven", "18 a 29 años"), ("Adulto", "30 a 59 años"), ("Adulto mayor", "60 años o más")])
    f3 = '<figure class="fig ancha"><h4>Los seis momentos del curso de vida</h4>%s<figcaption>Fuente: Ministerio de Salud, Modelo de Cuidado Integral de Salud por Curso de Vida para la Persona, Familia y Comunidad, Resolución Ministerial 030-2020/MINSA. El curso de vida va «desde la preconcepción hasta la muerte».</figcaption></figure>' % mom
    cuerpo = '<div class="figs">%s%s%s</div>%s' % (f1, f2, f3, detalles("bibliometria_modelo", local))
    return seccion("investigacion", "Producción científica, unidades de servicio y modelo de cuidado", estado_de("bibliometria_modelo", "HECHO"), "Tres verificaciones que sostienen las láminas de investigación y de la persona al centro.", cuerpo)


def sec_gemses(local):
    antes = [370770.40, 337885.77, 387443.58, 382940.78, 364771.00, 367568.91, 375526.38, 380101.84, 364420.46, 355294.51, 352368.00, 354171.78]
    desp = [207020.52, 190984.92, 212352.00, 211068.48, 201849.48, 201818.40, 212049.60, 214045.44, 201269.04, 198804.48, 190566.60, 194361.72]
    f0 = fig("El marco GEMSES", triada(), cap("autor", extra="Los tres niveles de gestión constan en la buena práctica de EsSalud publicada por la Asociación Internacional de la Seguridad Social en 2020."), txt="Enfoque centrado en la persona, modelo basado en la evidencia científica y equipo en tres niveles: estratégico, táctico y operativo.")
    f1 = fig("El caso: costo mensual del registro de enfermería, 2015", lineas(antes, desp, "Costo mensual asociado al registro de enfermería en 2015 con 18 formatos y con 1 formato estandarizado"),
             cap("incor", extra="Soles por mes. La franja entre las dos líneas es el ahorro."), ancha=True, gran="S/ 2 009 550 <small>de ahorro institucional en 2015</small>")
    f2 = fig("Formatos de registro", vbar([("Antes", 18, "f-ask", "18"), ("Después", 1, "f-ok", "1")], 21, "Formatos de registro: de 18 a 1", dec=0), cap("incor"))
    f3 = fig("Minutos de registro por paciente en 24 horas", vbar([("Antes", 223.5, "f-ask", "223.5"), ("Después", 125.8, "f-ok", "125.8")], 260, "Minutos de registro por paciente en 24 horas: de 223.5 a 125.8"), cap("incor", extra="Son 97.7 minutos menos por paciente al día."))
    f4 = fig("De qué está hecho el ahorro", stack([(1957073, "sg-acc", "Tiempo de enfermería: 97.4 %"), (51586, "sg-gold", ""), (891, "sg-wait", "")]) + leyenda([("sg-acc", "Tiempo de enfermería: S/ 1 957 073"), ("sg-gold", "Úlceras por presión evitadas: S/ 51 586"), ("sg-wait", "Formatos: S/ 891")]),
             cap("incor"), txt="Es tiempo devuelto al cuidado, valorizado con la remuneración. No es presupuesto que sobra.")
    esc = [("Todas las camas reportadas", 40593), ("Sin el sector privado", 33225), ("Ministerio de Salud y gobiernos regionales", 21774), ("Solo tercer nivel", 16800), ("Seguro Social de Salud", 9537)]
    u = 2009550.0 / 95
    f5 = fig("Extrapolación a las camas del país: ahorro anual por escenario", anidadas([(a, b, u * b / 1e6) for a, b in esc], 900, "Ahorro anual extrapolado por escenario de camas, al cien, cincuenta y veinticinco por ciento"),
             cap("incor", "susalud", extra="Cálculo del autor: S/ 2 009 550 ÷ 95 camas = S/ 21 153 por cama al año. El Instituto reportó entre 94 y 97 camas en 2015; el país, 40 593 en mayo de 2026, tras excluir un registro anómalo."), ancha=True,
             txt="Es un techo, no un pronóstico: el ahorro se midió en cuidados críticos, donde registrar toma más tiempo que en hospitalización general.")
    cond = '<ol class="flujo sin"><li class="ok"><b>Enfermería integrada</b><span>un solo registro para todo el proceso</span></li><li class="ok"><b>Sin brecha de personal</b><span>dotación completa</span></li><li class="ok"><b>Apoyo de la alta dirección</b><span>equipo de mejora con los directivos</span></li><li class="oro"><b>Resultado medido</b><span>en calidad, en tiempo y en soles</span></li></ol>'
    cuerpo = '<div class="figs">%s%s%s%s%s%s</div><h3>Las condiciones del caso</h3>%s%s' % (f0, f1, f2, f3, f4, f5, cond, detalles("gemses_caso", local))
    return seccion("gemses", "Marco GEMSES, caso del registro estandarizado y extrapolación", estado_de("gemses_caso", "POR_DECIDIR"), "El marco del autor ordena la exposición. El caso del Instituto Nacional Cardiovascular es la prueba: cuando enfermería trabaja integrada y con apoyo de la alta dirección, el resultado se mide.", cuerpo)


MAPA_BASE = [
    {"escalera": "Ministerio de Salud", "nivel": "ESTRATEGICO", "peldano": "Alta Dirección y direcciones generales", "enfermeria": "AUSENTE", "comoEsta": "Sin órgano de enfermería en los reglamentos de 2017 y de 2025", "prueba": "Decretos Supremos 008-2017-SA y 019-2025-SA", "capa": "DERIVACION"},
    {"escalera": "Establecimiento de salud", "nivel": "ESTRATEGICO", "peldano": "Máxima instancia de dirección", "enfermeria": "AUSENTE", "comoEsta": "La unidad de enfermería depende de la dirección; no la integra", "prueba": "Ley 27669, artículo 13", "capa": "DERIVACION"},
    {"escalera": "Establecimiento de salud", "nivel": "TACTICO", "peldano": "Unidad Orgánica de Enfermería", "enfermeria": "PRESENTE", "comoEsta": "Órgano de línea; lo dirige una enfermera por concurso de méritos", "prueba": "Ley 27669, artículos 13 y 14", "capa": "CITA"},
    {"escalera": "Establecimiento de salud", "nivel": "OPERATIVO", "peldano": "Servicios", "enfermeria": "PRESENTE", "comoEsta": "Jefas de servicio, supervisoras, coordinadoras y personal", "prueba": "Decreto Supremo 012-2015-SA", "capa": "CITA"},
    {"escalera": "Seguro Social de Salud", "nivel": "ESTRATEGICO", "peldano": "Alta Dirección y gerencias centrales", "enfermeria": "POR_DETERMINAR", "comoEsta": "En verificación", "prueba": "Reglamento de organización de la institución", "capa": "ESTADO"},
    {"escalera": "Seguro Social de Salud", "nivel": "TACTICO", "peldano": "Gerencias de red y departamentos", "enfermeria": "POR_DETERMINAR", "comoEsta": "En verificación", "prueba": "Reglamentos de las redes", "capa": "ESTADO"},
]


def sec_niveles(local):
    filas = (NIV or {}).get("mapa") or MAPA_BASE
    esc = []
    for r in filas:
        if r["escalera"] not in esc:
            esc.append(r["escalera"])
    marca = {"PRESENTE": ("si", "● Presente"), "AUSENTE": ("no", "✕ Ausente"), "POR_DETERMINAR": ("qd", "○ Por determinar")}
    tr = []
    for niv, nom in (("ESTRATEGICO", "Estratégico: donde se decide"), ("TACTICO", "Táctico: donde se conduce"), ("OPERATIVO", "Operativo: donde se cuida")):
        celdas = []
        for es in esc:
            its = [r for r in filas if r["escalera"] == es and r["nivel"] == niv]
            if not its:
                celdas.append("<td></td>")
                continue
            peor = "AUSENTE" if any(x["enfermeria"] == "AUSENTE" for x in its) else ("POR_DETERMINAR" if any(x["enfermeria"] == "POR_DETERMINAR" for x in its) else "PRESENTE")
            celdas.append('<td class="%s">%s</td>' % (marca[peor][0], "".join('<b>%s · %s</b><span>%s</span><span class="ruta">%s</span>' % (marca[x["enfermeria"]][1], e(x["peldano"]), e(x["comoEsta"]), e(x["prueba"])) for x in its)))
        tr.append('<tr><td>%s</td>%s</tr>' % (e(nom), "".join(celdas)))
    tabla = '<div class="scroll"><table class="vist matriz"><thead><tr><th>Nivel</th>%s</tr></thead><tbody>%s</tbody></table></div>' % ("".join("<th>%s</th>" % e(x) for x in esc), "".join(tr))
    f1 = fig("La pirámide", piramide(), cap("autor", extra="Diagrama de Carlos Pérez: estrategias, tácticas y operaciones."), txt="Estrategias: oportunidad, calidad, seguridad y costos. Tácticas: operación con proyección estratégica. Operaciones: acciones de los ejes de calidad.")
    f2 = '<figure class="fig ancha"><h4>Dónde está enfermería en cada nivel</h4>%s<figcaption>Verde con círculo lleno: presente. Morado con aspa: ausente. Gris con círculo vacío: por determinar. Debajo de cada dato va la norma que lo prueba.</figcaption></figure>' % tabla
    extra = ""
    if NIV:
        fu = "".join('<li><p class="dato"><b>%s.</b> %s</p><p class="meta">%s<span class="fu">Apoya: %s</span></p></li>' % (e(x.get("autorObra")), e(x.get("idea")), chip_capa(x.get("capa")), e(x.get("apoya"))) for x in NIV.get("fundamento", []))
        extra += '<h3>Fundamento teórico</h3><p class="lead">%s</p><ul class="hechos">%s</ul>' % (e(NIV.get("parrafoTeorico")), fu)
        extra += '<h3>Respuesta: cómo está enfermería en este mapa</h3><p class="lead">%s</p>' % e(NIV.get("respuesta"))
        if NIV.get("comparadores"):
            extra += '<h3>Dónde la ley sí la pone en la dirección</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in NIV["comparadores"])
        if NIV.get("evidencia"):
            extra += '<h3>Qué muestra la investigación cuando enfermería participa en el nivel estratégico</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in NIV["evidencia"])
        if NIV.get("objeciones"):
            extra += '<div class="aviso"><h3>Lo que le van a objetar</h3><ul>%s</ul></div>' % "".join("<li><b>%s</b> %s</li>" % (e(x["objecion"]), e(x["respuesta"])) for x in NIV["objeciones"])
        if NIV.get("porDeterminar"):
            extra += '<h3>Por determinar</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in NIV["porDeterminar"])
    else:
        extra = '<div class="aviso"><h3>Fundamento teórico en investigación</h3><ul><li>Cinco buscadores revisan la teoría de los tres niveles, la norma peruana de organización del Estado, la estructura real del Seguro Social de Salud y del Ministerio de Salud, los estándares de la disciplina de enfermería y la evidencia. Cada afirmación pasa por dos verificadores.</li><li>Lo que ya está verificado aparece en la tabla; lo demás figura como por determinar.</li></ul></div>'
    cuerpo = '<div class="figs">%s%s</div>%s' % (f1, f2, extra)
    return seccion("niveles", "El mapa de tres niveles: dónde está enfermería", "HECHO" if NIV else "EN_CURSO", "Su pregunta: cómo está enfermería en este mapa. La tesis: existe en lo operativo y lo táctico, y falta en lo estratégico, donde se toman las decisiones.", cuerpo)


def sec_autonomia(local):
    pasos = '<ol class="flujo"><li><b>Ya está en la norma</b><span>el cuidado «se basa en el juicio crítico y ponderado de la enfermera(o) así como en la toma de decisiones que competen a su labor, por lo cual asume plena responsabilidad»</span></li><li class="oro"><b>Da resultados</b><span>cuando la enfermera decide en su campo, los resultados igualan o mejoran</span></li><li class="ask"><b>Es dentro del equipo</b><span>«sin perjuicio de la coordinación interdisciplinaria»; no comprende actos reservados a otras profesiones</span></li></ol>'
    est = ""
    if AUT:
        est = fig("Investigación en curso: afirmaciones nuevas", stack([(AUT.get("CONFIRMADA", 0), "sg-ok", "Confirmadas: %d" % AUT.get("CONFIRMADA", 0)), (AUT.get("MATIZAR", 0), "sg-run", "A matizar: %d" % AUT.get("MATIZAR", 0)), (AUT.get("REFUTADA", 0), "sg-ask", "Refutadas: %d" % AUT.get("REFUTADA", 0))]) +
                  leyenda([("sg-ok", "Veredictos que confirman: %d" % AUT.get("CONFIRMADA", 0)), ("sg-run", "Veredictos que piden matizar: %d" % AUT.get("MATIZAR", 0)), ("sg-ask", "Veredictos que refutan: %d" % AUT.get("REFUTADA", 0))]),
                  '<figcaption>Corte del 10 de octubre de 2026. %d afirmaciones encontradas por %d buscadores; cada una recibe dos veredictos. Son veredictos, no afirmaciones cerradas.</figcaption>' % (AUT.get("claims", 0), AUT.get("buscadores", 0)), ancha=True)
    cuerpo = '<h3>La demostración en tres pasos</h3>%s<p class="nota">Paso 1: Decreto Supremo 004-2002-SA, artículo 4. Paso 2: Yang 2025, Zhang 2022, Koontalay 2025, Kumar 2025 y Shever 2011. Paso 3: iniciativa del Colegio de Enfermeros del Perú, Proposición Legislativa 159/2026-2031-CD.</p><div class="figs">%s</div>%s' % (pasos, est, detalles("autonomia", local, "Ver las afirmaciones en verificación"))
    return seccion("autonomia", "Autonomía de enfermería frente al equipo de salud", "EN_CURSO", "Su pregunta: cómo demostramos la autonomía. La respuesta tiene tres pasos; los dos primeros ya descansan en fuentes verificadas y el tercero se está reforzando.", cuerpo)


def sec_rigor(local):
    dos = [("Marco normativo", 58, 2, 20), ("Demanda, oferta y brecha", 42, 2, 12), ("Valor del cuidado", 40, 0, 31), ("Programas y liderazgo", 33, 3, 2), ("Actualización y modelo de cuidado", 32, 2, 0)]
    barras = '<div class="barras">%s</div>' % "".join('<div><b>%s</b>%s</div>' % (e(a), stack([(c, "sg-ok", "%d" % c), (r, "sg-ask", "%d" % r), (s, "sg-wait", "%d" % s)])) for a, c, r, s in dos)
    f1 = fig("Dossier de evidencia: qué pasó con cada hallazgo", barras + leyenda([("sg-ok", "Confirmados: 205"), ("sg-ask", "Refutados: 9"), ("sg-wait", "Sin verificar: 65")]),
             cap("dossier", extra="Cada hallazgo confirmado fue abierto por un buscador y revisado por tres verificadores. Lo refutado y lo no verificado no entra al deck."), ancha=True)
    ilus = ""
    p = S / "arte_img" / "final_r1.svg"
    if p.exists():
        sv = re.sub(r"<\?xml[^>]*\?>", "", p.read_text(encoding="utf-8")).strip()
        ilus = fig("Imagen publicada en la lámina «Arte»", '<div class="ilus">%s</div>' % sv, '<figcaption>Ilustración de elaboración propia, elegida entre cuatro propuestas por un jurado de tres revisores.</figcaption>',
                   txt="Una enfermera de uniforme turquesa toma el pulso y sostiene la mano de un adulto mayor.")
    foto = fig("Foto real: descargada, no publicada", '<ol class="flujo sin"><li class="ok"><b>Licencia verificada</b><span>Creative Commons Atribución 2.0</span></li><li class="ask"><b>Bloqueo de privacidad</b><span>la página pública muestra el documento de identidad y la historia clínica de un paciente</span></li><li class="oro"><b>Decisión pendiente</b><span>recomendación: mantener la ilustración</span></li></ol>',
               '<figcaption>Fuente: Wikimedia Commons, serie «Plataformas Itinerantes de Ayuda Social (PIAS)», Galería del Ministerio de Defensa del Perú, 2015 <a href="#" rel="noopener">abrir</a>. Control de tres revisores: licencia, privacidad y encaje.</figcaption>')
    fuera = '<ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in [
        "Quintiles, anemia y correlación: la correlación bruta se diluye al ajustar por ruralidad.", "Anemia 2025 de la prensa (34.9 %): compara dos criterios de medición distintos.",
        "El ensayo de cuidados paliativos tempranos: no es un programa dirigido solo por enfermería.", "«Todos los programas exitosos los coordina enfermería»: no hay fuente que lo sostenga.",
        "La reserva del investigador principal en ensayos clínicos como barrera general: el reglamento solo cubre ensayos con productos en investigación."])
    cuerpo = '<div class="figs">%s%s%s</div><h3>Decisiones de rigor: lo que se dejó fuera y por qué</h3>%s%s' % (f1, ilus, foto, fuera, detalles("imagen_auditorias", local, "Ver auditorías, controles y pendientes"))
    return seccion("rigor", "Imagen de «Arte», auditorías y decisiones de rigor", estado_de("imagen_auditorias", "POR_DECIDIR"), "La regla del trabajo: nada se afirma sin fuente verificable. Aquí está lo que se verificó, lo que se corrigió y lo que quedó fuera.", cuerpo)


ESTRATEGIA = [
    (0, "Portada", "con el título oficial del panel", "0:15", ""),
    (1, "Datos, inteligencia artificial y control del cuidado, en manos de enfermería", "el circuito: cuidado las 24 horas, registro estandarizado, dato, alerta, decisión de enfermería e indicador; sustento en verificación", "1:45", "Apertura"),
    (2, "Presencia: el país que cuidamos", "34 157 732 habitantes; 41.8 % con una condición crónica; 71 052 enfermeros, 18.0 % del sector; faltan unos 22 000", "1:15", "Parte 1"),
    (3, "Resultados: cuando la enfermera decide en su campo", "reingresos 0.69; muerte a tres meses en ictus 0.56; muerte tras complicación 0.52", "1:30", "Parte 1"),
    (4, "Eficiencia: del registro al dato", "de 18 formatos a 1; 97.7 minutos menos de registro por paciente al día; S/ 2 009 550 en un año; hasta S/ 859 millones en el país", "1:15", "Parte 1"),
    (5, "El mapa: conduce y ejecuta, pero no decide", "presente en lo operativo y lo táctico; ausente en lo estratégico", "1:15", "Parte 2"),
    (6, "Los países que tienen dirección nacional de enfermería", "18 de 21 países de las Américas; sus indicadores, en investigación", "1:15", "Parte 2"),
    (7, "La ventana: la nueva estructura del Ministerio", "informe con la propuesta al 7 de diciembre de 2026; propuesta del Colegio de 2020", "1:00", "Parte 2"),
    (8, "Remate: tres pedidos", "al Ministro, al Congreso y a la profesión", "3:00", "Remate"),
]

CIRCUITO = [
    ("Cuidado las 24 horas", "enfermería junto al paciente, en todos los turnos", ""),
    ("Registro estandarizado", "un solo formato, con el Proceso de Atención de Enfermería", ""),
    ("Dato", "lenguaje común que los sistemas pueden leer", "oro"),
    ("Inteligencia artificial", "lee patrones del registro y da alerta temprana", "oro"),
    ("Decisión de enfermería", "actúa sobre la alerta, en su campo", "ok"),
    ("Indicador", "seguridad, oportunidad y costo, a la vista", "ok"),
]


def sec_estrategia(local):
    prog = '<ol class="flujo sin"><li><b>15:00 · Inauguración</b><span>Ministro de Salud, Luis Dyer Fernández, en modo virtual</span></li><li class="oro"><b>15:30 · Conferencia inaugural</b><span>Decana Nacional del Colegio de Enfermeros del Perú: desafíos regulatorios, autonomía y competencia</span></li><li class="ask"><b>15:45 a 16:30 · Panel I</b><span>un abogado constitucionalista, Mg. Carlos Pérez Pérez y Mg. Sugely Carpio Borja</span></li></ol>'
    circ = '<ol class="flujo c3">%s</ol>' % "".join('<li class="%s"><b>%s</b><span>%s</span></li>' % (c, e(a), e(b)) for a, b, c in CIRCUITO)
    quien = ('<div class="tres"><div><h5>Lo que pone enfermería</h5><ul><li>Presencia las 24 horas</li><li>El registro del cuidado</li><li>El juicio clínico</li><li>La decisión y la responsabilidad</li></ul></div>'
             '<div class="oro"><h5>Lo que pone la inteligencia artificial</h5><ul><li>Lectura de patrones en el registro</li><li>Alerta temprana</li><li>Tablero en tiempo real</li></ul></div>'
             '<div class="ask"><h5>Lo que no se delega</h5><ul><li>La alianza terapéutica</li><li>El juicio clínico ante el paciente singular</li><li>La seguridad psicológica del equipo</li></ul></div></div>')
    gob = '<p class="banda"><b>Gobernanza de la inteligencia artificial</b><span>validación clínica</span><span>privacidad</span><span>supervisión humana</span><span>auditoría</span></p>'
    sust = ('<div class="scroll"><table class="vist"><thead><tr><th>Lo que la lámina necesita</th><th>Qué tenemos</th><th>Estado</th></tr></thead><tbody>'
            '<tr><td>Lo que el Ministro ha dicho sobre control con datos e inteligencia artificial</td><td>Su indicación del 10 de octubre. Falta la cita literal, con fecha y enlace.</td><td>%s</td></tr>'
            '<tr><td>Los indicadores críticos del país frente a la Organización para la Cooperación y el Desarrollo Económicos</td><td>En búsqueda en las fuentes de esa organización. Leo así su «OGCE»: confírmelo.</td><td>%s</td></tr>'
            '<tr><td>Que enfermería produce el registro y está las 24 horas</td><td>71 052 enfermeros, 18.0 %% del sector; ocho unidades de atención directa.</td><td>%s</td></tr>'
            '<tr><td>Que un registro estandarizado se vuelve dato y ahorro</td><td>Caso de 2015: de 18 formatos a 1; de 223.5 a 125.8 minutos por paciente en 24 horas; S/ 2 009 550 en un año.</td><td>%s</td></tr>'
            '<tr><td>Que la inteligencia artificial sobre registros de enfermería mejora resultados</td><td>Ensayos y revisiones en búsqueda en PubMed, con sus límites.</td><td>%s</td></tr>'
            '<tr><td>Qué exige la norma peruana a la inteligencia artificial en salud</td><td>Ley 31814 y su reglamento, historia clínica electrónica y datos personales: en lectura.</td><td>%s</td></tr>'
            '</tbody></table></div>') % (chip_estado("EN_CURSO"), chip_estado("EN_CURSO"), chip_estado("HECHO"), chip_estado("HECHO"), chip_estado("EN_CURSO"), chip_estado("EN_CURSO"))
    if PRI:
        sust = '<p class="nota">El sustento ya está verificado: está en «La primera lámina, con su sustento verificado» y en «El plan, lámina por lámina».</p>'
    primera = ('<figure class="fig ancha" id="primera"><h4>La primera lámina: el circuito del control del cuidado</h4>%s%s%s'
               '<figcaption>Esquema propuesto por el autor: es su tesis y su marco profesional, no una cita. La evidencia que lo respalda se está verificando; nada entra a la lámina sin fuente abierta.</figcaption></figure>') % (circ, quien, gob)
    p1 = '<figure class="fig"><h4>Parte 1 · Lo que enfermería ya aporta</h4><ol class="flujo"><li><b>Presencia</b><span>71 052 enfermeros, 18.0 % del sector, las 24 horas</span></li><li><b>Resultados</b><span>menos reingresos y menos muertes donde la enfermera decide en su campo</span></li><li><b>Eficiencia</b><span>del registro al dato: 97.7 minutos menos por paciente al día; S/ 2 009 550 en un año</span></li></ol><figcaption>Cada dato tiene su fuente en las secciones de este tablero.</figcaption></figure>'
    p2 = '<figure class="fig"><h4>Parte 2 · Qué pasaría con respaldo en la alta dirección</h4><ol class="flujo"><li class="ask"><b>El mapa</b><span>enfermería conduce y ejecuta, pero no está donde se decide</span></li><li class="ask"><b>Los países</b><span>qué países tienen dirección nacional de enfermería y cómo están sus indicadores</span></li><li class="ask"><b>La ventana</b><span>la nueva estructura del Ministerio de Salud, con informe al 7 de diciembre de 2026</span></li></ol><figcaption>La comparación de países está en investigación; muestra asociación, no causa.</figcaption></figure>'
    its = []
    for n, tit, dato, tie, parte in ESTRATEGIA:
        cls = "s3" if parte == "Apertura" else "s2" if parte == "Parte 1" else "s4" if parte == "Parte 2" else "s5" if parte == "Remate" else ""
        its.append('<li class="%s"><span class="num">%s</span><span class="tit"><b>%s</b></span><span class="tit">%s</span>%s<span class="tie">%s</span></li>' % (cls, n, e(tit), e(dato), ('<span class="tag">%s</span>' % e(parte)) if parte else "", e(tie)))
    story = '<ol class="story grande">%s</ol>' % "".join(its)
    tesis = '<div class="pedidos"><h3>La tesis para el Ministro, en palabras de Carlos</h3><ul><li>Enfermería, con la inteligencia artificial y con el control del cuidado del paciente en sus manos, es la solución para que el país salga de sus indicadores críticos.</li><li>Si la enfermera comanda la gestión del cuidado, los procesos son más ágiles.</li><li>Enfermería con autonomía no compite con el equipo: lo hace rendir más.</li><li>Lo que falta no es capacidad, es un lugar en la alta dirección.</li></ul></div>'
    aviso = '<div class="aviso"><h3>Tres avisos</h3><ul><li>La lámina no pondrá palabras en boca del Ministro: se busca su cita literal sobre control con datos e inteligencia artificial, con fecha y enlace. Si no aparece, la lámina hablará de «la agenda de datos» sin atribuirle una frase.</li><li>El título oficial del panel es «Autonomía profesional de enfermería: PAE, diagnóstico y delimitación de competencias profesionales», donde PAE es el Proceso de Atención de Enfermería. La portada del deck publicado habla de ciencia, arte y disciplina: hay que alinearla.</li><li>Los otros dos panelistas cubren el frente legal y el Proceso de Atención de Enfermería. El espacio propio de Carlos es la gestión, la calidad, los datos y la estrategia.</li></ul></div>'
    cuerpo = ('<h3>El programa del foro</h3>%s<h3>La apertura: hablar el lenguaje del Ministro</h3><div class="figs">%s</div><h3>Qué sustenta la primera lámina</h3>%s'
              '<h3>Después, la exposición en dos partes</h3><div class="figs">%s%s</div><h3>Guion gráfico propuesto: nueve láminas con más datos</h3>%s%s%s%s<p class="nota">Exposición: 9 minutos 30 segundos. Remate: 3 minutos. Nada de esto está construido.</p>') % (
        prog, primera, sust, p1, p2, story, leyenda([("sg-ok", "Apertura: datos e inteligencia artificial"), ("sg-gold", "Parte 1: lo que ya aporta"), ("sg-ask", "Parte 2: con respaldo en la alta dirección"), ("sg-wait", "Remate")]), tesis, aviso)
    return seccion("estrategia", "La nueva estrategia: abrir con datos e inteligencia artificial y seguir en dos partes", "POR_DECIDIR", "Sus indicaciones del 10 de octubre: ser más estratégicos, porque estará el Ministro de Salud, y abrir con enfermería, la inteligencia artificial y el control del cuidado del paciente en manos de enfermería.", cuerpo)


def _numero(txt):
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(txt or "").replace(" ", "").replace(" ", ""))
    return float(m.group(0).replace(",", ".")) if m else None


def sec_paises(local):
    base = fig("Jefatura de enfermería en el gobierno", picto(21, 18, "18 de 21 países de las Américas que respondieron informan tener una jefatura de enfermería en el gobierno"),
               cap("oms", extra="Página impresa 88, tabla 8.1; datos de 2018 a 2023. En el mundo, 98 de 120 países: 82 %."), gran="18 de 21 <small>países de las Américas que respondieron</small>",
               txt="El mismo informe advierte que no halló una correlación estadísticamente significativa entre tener esa jefatura y mejores regulaciones.")
    peru = fig("El Perú hoy", '<ol class="flujo sin"><li class="ask"><b>Ministerio de Salud</b><span>sin órgano de enfermería en sus reglamentos de 2017 y de 2025</span></li><li class="oro"><b>2020</b><span>el Colegio propuso una Dirección General de Enfermería</span></li><li class="ok"><b>2026</b><span>el Ministerio está en reorganización; informe al 7 de diciembre</span></li></ol>', cap("ds019", "ds014"))
    if not PAI:
        extra = '<div class="aviso"><h3>En investigación</h3><ul><li>Seis buscadores revisan, país por país, el organigrama oficial de 25 ministerios de salud y siete indicadores del Observatorio Mundial de la Salud. Cada afirmación pasa por dos verificadores.</li><li>La comparación mostrará asociación, no causa: los países difieren en ingreso y en gasto.</li></ul></div>'
        return seccion("paises", "Países con dirección nacional de enfermería y sus indicadores", "EN_CURSO", "Su pedido: revisar qué países tienen esta dirección en su ministerio de salud y cómo están sus indicadores.", '<div class="figs">%s%s</div>%s' % (base, peru, extra))
    marca = {"SI": ("si", "● Sí"), "NO": ("no", "✕ No"), "POR_DETERMINAR": ("qd", "○ Por determinar")}
    filas = "".join('<tr><td>%s</td><td class="%s">%s</td><td><b>%s</b><span>%s</span></td><td>%s</td><td>%s</td></tr>' % (e(p["pais"]), marca.get(p["tieneOrgano"], ("qd", "○"))[0], marca.get(p["tieneOrgano"], ("qd", "○ Por determinar"))[1], e(p.get("nombreOficial")), e(p.get("nivel")), e(p.get("baseLegal")), e(p.get("segunOMS"))) for p in PAI.get("paises", []))
    tabla = '<figure class="fig ancha"><h4>Órgano de enfermería dentro del ministerio de salud, país por país</h4><div class="scroll"><table class="vist matriz"><thead><tr><th>País</th><th>¿Tiene?</th><th>Nombre oficial y nivel</th><th>Base legal</th><th>Según la Organización Mundial de la Salud</th></tr></thead><tbody>%s</tbody></table></div><figcaption>Fuente: organigramas y normas oficiales de cada ministerio, abiertos y verificados uno por uno.</figcaption></figure>' % filas
    nom = {p["iso3"]: p for p in PAI.get("paises", [])}
    graf = []
    for campo, titulo, mejor_alto, vmax_min in (("coberturaUniversal", "Índice de cobertura universal de servicios de salud", True, 100), ("esperanzaVida", "Esperanza de vida al nacer, en años", True, 90), ("mortalidadMaterna", "Muertes maternas por cada 100 000 nacidos vivos", False, 0), ("enfermeriaPor10000", "Enfermería y partería por cada 10 000 habitantes", True, 0)):
        rows = []
        for x in PAI.get("indicadores", []):
            v = _numero(x.get(campo))
            if v is None:
                continue
            p = nom.get(x["iso3"], {})
            tt = p.get("tieneOrgano", "POR_DETERMINAR")
            rows.append((p.get("pais", x["iso3"]), v, "f-ok" if tt == "SI" else "f-ask" if tt == "NO" else "f-wait", str(x.get(campo)), x["iso3"] == "PER"))
        if len(rows) >= 4:
            rows.sort(key=lambda r: -r[1] if mejor_alto else r[1])
            graf.append(fig(titulo, hbar(rows, max(vmax_min, max(r[1] for r in rows) * 1.12), titulo + ", por país", lw=150), cap("gho", extra="Verde: tiene órgano de enfermería en el ministerio. Morado: no tiene. Gris: por determinar. Último año disponible de cada país.")))
    extra = '<div class="aviso"><h3>Lectura honesta</h3><ul><li>%s</li></ul></div>' % e(PAI.get("lecturaHonesta"))
    if PAI.get("paraElMinistro"):
        extra += '<div class="pedidos"><h3>Lo que sí se puede decir al Ministro</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(x) for x in PAI["paraElMinistro"])
    if PAI.get("queNoDecir"):
        extra += '<h3>Lo que la evidencia no permite decir</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in PAI["queNoDecir"])
    if PAI.get("porDeterminar"):
        extra += '<h3>Por determinar</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in PAI["porDeterminar"])
    return seccion("paises", "Países con dirección nacional de enfermería y sus indicadores", "HECHO", "Su pedido: revisar qué países tienen esta dirección en su ministerio de salud y cómo están sus indicadores.", '<div class="figs">%s%s%s%s</div>%s' % (base, peru, tabla, "".join(graf), extra))


ARCHIVOS = [
    ("Deck del Panel I, versión 20", DECK_URL, "20 láminas con la plantilla institucional; privado, se comparte desde el menú Compartir"),
    ("PLAN_LAMINAS_PANEL1.md", str(FORO / "PLAN_LAMINAS_PANEL1.md"), "Plan lámina por lámina, caso del registro y extrapolación; no construido"),
    ("DOSSIER_EVIDENCIA_PANEL1.md", str(FORO / "DOSSIER_EVIDENCIA_PANEL1.md"), "Seis secciones con cada hallazgo, su cita literal, su enlace y el voto de los verificadores"),
    ("ARTICULOS_REVISION_PANEL1.md", str(FORO / "ARTICULOS_REVISION_PANEL1.md"), "10 artículos del deck, 14 de respaldo, 8 registros peruanos y los artículos de norma literales"),
    ("AUDITORIA_PANEL1_2026-10-09.md", str(FORO / "AUDITORIA_PANEL1_2026-10-09.md"), "Auditoría del deck: qué refleja lo conversado, qué se corrigió y qué falta"),
    ("TABLERO_PANEL1.html", str(FORO / "TABLERO_PANEL1.html"), "Esta página, como archivo"),
    ("imagen_arte", str(FORO / "imagen_arte" / "LICENCIA_Y_CREDITO.txt"), "Ilustración propia, foto descargada, recorte y nota de licencia con la advertencia de privacidad"),
    ("mapas_enfermeria_ampliada", str(FORO / "mapas_enfermeria_ampliada" / "02_departamento_por_10000.png"), "Nueve mapas y tres tablas por departamento, provincia y distrito"),
    ("PLANTILLA INSTITUCIONAL DE PPT.pptx", str(FORO / "PLANTILLA INSTITUCIONAL DE PPT.pptx"), "Plantilla del Colegio de Enfermeros del Perú usada en el deck"),
    ("PROYECTO DE LEY-00091-2026-2031-CD.pdf", str(FORO / "PROYECTO DE LEY-00091-2026-2031-CD.pdf"), "Proposición Legislativa 91"),
    ("pdf.pdf", str(FORO / "pdf.pdf"), "Oficio 1795-2026-CN/CEP e iniciativa del Colegio, Proposición Legislativa 159"),
    ("cuadro comparativo.pdf", str(FORO / "cuadro comparativo.pdf"), "Cuadro de trabajo que compara la proposición con el texto sustitutorio"),
]


def sec_archivos(local):
    it = "".join('<li><b>%s</b><span>%s</span><span class="ruta">%s</span></li>' % (archivo(a, b, local), e(c), e(corto(b))) for a, b, c in ARCHIVOS)
    return seccion("archivos", "Entregables y archivos", None, "Todo está en la carpeta FORO, salvo el deck, que vive en su enlace.", '<ul class="files">%s</ul>' % it)


CRONO = [
    ("8 de octubre, noche", "El encargo", "Presentación de 10 minutos más 3 de remate, con datos concretos y actualizados. Mensaje y audios del organizador: ciencia, arte y disciplina; cuatro áreas."),
    ("8 y 9 de octubre", "Enfermería en el equipo y en el territorio", "Presencia en el mundo, proporción dentro del equipo de salud, técnicos y auxiliares como enfermería ampliada, mapas, anemia y correlación."),
    ("9 de octubre", "La forma del deck", "Cambio de estilo, fondo blanco, imagen de fondo y plantilla institucional de la carpeta."),
    ("9 de octubre", "Cómo demostramos cada pilar y cada área", "El mapa con siete pruebas, tras «está muy flojo». Valor del cuidado, 24 horas, especialidades y programas coordinados por enfermería."),
    ("9 de octubre", "Investigaciones completas antes de presentar", "Demanda, oferta y brecha; cuántas enfermeras deciden; documentación normativa por frente; la persona al centro; verificación de normas vigentes."),
    ("9 de octubre, noche", "Terminar y auditar", "Deck terminado como para presentar, auditado contra lo conversado. Luego: otra imagen para «Arte» y los artículos de la revisión."),
    ("10 de octubre", "Foto, autonomía y marco GEMSES", "Descarga de la foto real y su control. Cómo demostrar la autonomía frente al equipo de salud. Enfoque, modelo y equipo, con la brecha en el nivel estratégico."),
    ("10 de octubre", "Plan, extrapolación y este tablero", "Plan lámina por lámina sin construir. Extrapolación del ahorro a las camas del país. Fundamento teórico del mapa de tres niveles. Página visual con todo lo trabajado."),
    ("10 de octubre, noche", "Ser más estratégicos", "Estará el Ministro de Salud. Menos láminas y más datos, en dos partes: lo que enfermería ya aporta y qué pasaría con una dirección nacional de enfermería, como la tienen otros países."),
    ("10 de octubre, noche", "La primera lámina", "Su indicación: el Ministro habla de control con datos e inteligencia artificial. La primera lámina debe ser enfermería, la inteligencia artificial y el control del cuidado del paciente en manos de enfermería, como salida a los indicadores críticos."),
]


def sec_crono():
    it = "".join('<li><span class="cuando">%s</span><div><b>%s</b><p>%s</p></div></li>' % (e(a), e(b), e(c)) for a, b, c in CRONO)
    return seccion("cronologia", "Cronología de pedidos", None, "El recorrido del trabajo, en el orden en que usted lo pidió.", '<ol class="crono">%s</ol>' % it)


exec((HERE / "extra.py").read_text(encoding="utf-8"), globals())
CSS = (HERE / "tablero.css").read_text(encoding="utf-8")
NAV = [("vistazo", "Estado de un vistazo"), ("decisiones", "Lo que espera su decisión"), ("estrategia", "La nueva estrategia"), ("plan3", "El plan, lámina por lámina"),
       ("primera2", "La primera lámina, con su sustento"), ("ministro", "El Ministro y su agenda"), ("ocde", "El Perú frente a la OCDE"), ("mundo", "Jefatura de enfermería en 194 países"),
       ("paises", "Países: nombre y base legal"), ("niveles", "El mapa de tres niveles"), ("autonomia2", "Autonomía: respuesta verificada"), ("autonomia", "Autonomía: primeros pasos"),
       ("deck", "El deck publicado"), ("plan", "El plan anterior"), ("encargo", "Encargo y primeros análisis"), ("demanda", "Demanda, oferta y brecha"), ("normas", "Marco normativo"),
       ("valor", "Valor del cuidado y programas"), ("investigacion", "Investigación y modelo de cuidado"), ("gemses", "Marco GEMSES y caso del registro"), ("rigor", "Imagen, auditorías y rigor"),
       ("archivos", "Entregables y archivos"), ("cronologia", "Cronología de pedidos")]
CAPAS_TXT = {"CITA": "la fuente lo dice, con página o artículo", "DERIVACION": "se sigue de premisas citadas", "JUICIO": "criterio profesional del autor", "ESTADO": "un hecho sobre el propio trabajo"}


def pagina(local):
    orden = [sec_vistazo(), sec_decisiones(), sec_estrategia(local), sec_plan3(local), sec_primera(local), sec_ministro(local), sec_ocde(local), sec_mundo(local), sec_paises(local), sec_niveles(local),
             sec_autonomia2(local), sec_autonomia(local), sec_deck(local), sec_plan(local), sec_encargo(local), sec_demanda(local), sec_normas(local), sec_valor(local), sec_investigacion(local),
             sec_gemses(local), sec_rigor(local), sec_archivos(local), sec_crono()]
    todo = "\n".join(x for x in orden if x)
    r1 = _tit("Enfermeras profesionales") or {}
    body = ['<div class="wrap">',
            '<header class="top"><p class="eyebrow">Foro Nacional «Enfermería con voz y autonomía» · Congreso de la República · 12 de octubre de 2026</p><h1>Panel I: todo lo trabajado y lo que tenemos</h1>'
            '<p class="sub">Tablero de trabajo de Mg. Carlos Pérez Pérez. Cada tema abre con sus gráficos y esquemas; los datos, con su fuente y su enlace, se despliegan debajo. Corte: 11 de octubre de 2026.</p>',
            '<dl class="resumen"><div><dt>Deck publicado</dt><dd>versión 20</dd></div><div><dt>Estrategia nueva</dt><dd>9 láminas, por aprobar</dd></div><div><dt>Data de la OCDE en su base</dt><dd>20 020 959 datos</dd></div>'
            '<div><dt>Países con perfil leído</dt><dd>194</dd></div><div><dt>Enfermeras por 1 000 habitantes</dt><dd>%s <small>Perú</small> · %s <small>OCDE</small></dd></div></dl></header>' % (e(r1.get("peru", "")), e(_n(r1["ocde_media"])) if r1 else ""),
            '<div class="cuerpo"><nav class="toc" aria-label="Contenido"><p>Contenido</p><ol>%s</ol><div class="ley"><p>Capas de evidencia</p>%s</div></nav><main>' % (
                "".join('<li><a href="#%s">%s</a></li>' % (a, e(t)) for a, t in NAV if ('id="%s"' % a) in todo), "".join('<p>%s<span>%s</span></p>' % (chip_capa(k), e(v)) for k, v in CAPAS_TXT.items())),
            todo,
            '<footer><p>Regla del trabajo: nada se afirma sin fuente verificable. Las cifras de los gráficos provienen de las fuentes citadas al pie de cada figura; los cálculos del autor están rotulados.</p></footer>', "</main></div></div>"]
    head = '<title>Tablero del Panel I</title>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Public+Sans:wght@400;500;600;700&display=swap">\n<style>\n%s\n</style>\n' % CSS
    return head, "\n".join(x for x in body if x)


head, body = pagina(False)
(HERE / "tablero_artefacto.html").write_text(head + body + "\n", encoding="utf-8")
head2, body2 = pagina(True)
full = '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + head2 + '</head>\n<body>\n' + body2 + '\n</body>\n</html>\n'
(FORO / "TABLERO_PANEL1.html").write_text(full, encoding="utf-8")
print("ok: artefacto %d bytes; local %d bytes; inventario: %s; niveles: %s; autonomia: %s" % (len((head + body).encode("utf-8")), len(full.encode("utf-8")), sorted(INV), bool(NIV), bool(AUT)))
