# -*- coding: utf-8 -*-
# Secciones nuevas del tablero (11 de octubre): OCDE, países del mundo, Ministro y primer nivel, primera lámina, autonomía.
# Se ejecuta dentro de gen_tablero.py (usa sus funciones: e, num, fig, seccion, chip_estado, chip_capa, stack, leyenda, svg, tx, carga).
import csv as _csv

OC = S / "ocde" / "salidas_pg"


def _csvr(p):
    return list(_csv.DictReader(io.open(p, encoding="utf-8-sig"))) if p.exists() else []


TIT = _csvr(OC / "ocde_titulares.csv")
COR = _csvr(OC / "ocde_correlaciones.csv")
MATP = _csvr(OC / "ocde_matriz_paises.csv")
OMS_P = _csvr(OC / "oms_jefatura_enfermeria_paises.csv")
OMS_R = _csvr(OC / "oms_jefatura_resumen.csv")
OMS_I = _csvr(OC / "oms_jefatura_indicadores.csv")
PRI = carga("primera.json", None)
AGE = carga("agenda.json", None)
AUTC = carga("autonomia_critica.json", None)
INVR = carga("investigaciones_resumen.json", None)
PLAN3 = carga("plan3.json", None)


def _fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _n(v):
    v = float(v)
    return num(v, 0 if abs(v) >= 1000 else (1 if abs(v) >= 20 else 2))


def _a(url, texto="abrir"):
    return ' <a href="%s" rel="noopener">%s</a>' % (html.escape(url, quote=True), e(texto)) if url and str(url).startswith("http") else ""


def _tit(prefijo):
    return next((r for r in TIT if r["indicador"].startswith(prefijo)), None)


def _kpi(titulo, prefijo, texto):
    r = _tit(prefijo)
    if not r:
        return ""
    return fig(titulo, "", '<figcaption>Fuente: OCDE, Data Explorer, tema Salud%s. Perú %s; promedio simple de %s países miembros con dato.</figcaption>' % (_a(r.get("enlace")), r["peru_anio"], r["paises_ocde_con_dato"]),
               gran='%s <small>en el Perú · %s en la OCDE</small>' % (e(_n(r["peru"])), e(_n(r["ocde_media"]))), txt=texto % {"lugar": r["lugar_del_peru_1_es_el_mejor"], "de": r["de"], "veces": num(float(r["peru_sobre_media"]), 1)})


def sec_ocde(local):
    if not TIT:
        return ""
    k = '<div class="figs">%s%s%s%s</div>' % (
        _kpi("Enfermeras profesionales por 1 000 habitantes", "Enfermeras profesionales", "Lugar %(lugar)s de %(de)s países con dato: solo un miembro de la OCDE tiene menos."),
        _kpi("Mortalidad materna por 100 000 nacidos vivos", "Mortalidad materna", "%(veces)s veces el promedio de la OCDE. Lugar %(lugar)s de %(de)s."),
        _kpi("Gasto en salud, porcentaje del producto bruto interno", "Gasto corriente en salud", "Lugar %(lugar)s de %(de)s."),
        _kpi("Ingreso anual de una enfermera de hospital, en dólares comparables", "Ingreso anual de enfermeras", "El más bajo de los %(de)s países con dato."))
    filas, notas = [], []
    for r in TIT:
        if r["nota"]:
            notas.append("%s: %s" % (r["indicador"], r["nota"]))
            continue
        if r["mejor_si"] not in ("alto", "bajo") or not r["lugar_del_peru_1_es_el_mejor"]:
            continue
        lugar, de = int(r["lugar_del_peru_1_es_el_mejor"]), int(r["de"])
        filas.append((100.0 * (lugar - 1) / max(1, de - 1), lugar, de, r))
    filas.sort(key=lambda t: -t[0])
    cuerpo = "".join('<span class="rk-l">%s</span><span class="rk-t" title="lugar %d de %d"><i class="%s" style="left:%.1f%%"></i></span><span class="rk-v">lugar <b>%d</b> de %d</span><span class="rk-x">Perú %s · OCDE %s</span>' % (
        e(r["indicador"]), lugar, de, "mal" if pct >= 75 else ("med" if pct >= 40 else "bien"), pct, lugar, de, e(_n(r["peru"])), e(_n(r["ocde_media"]))) for pct, lugar, de, r in filas)
    peores = sum(1 for t in filas if t[0] >= 75)
    f1 = ('<figure class="fig ancha"><h4>Dónde queda el Perú entre los países de la OCDE, indicador por indicador</h4>'
          '<p class="rk-eje"><span>◀ mejor lugar</span><span>peor lugar ▶</span></p><div class="rk" role="img" aria-label="Lugar del Perú entre los países miembros de la OCDE en %d indicadores de salud">%s</div>'
          '<p class="txt">En %d de %d indicadores el Perú queda en la cuarta parte más rezagada. El lugar 1 es el mejor; «mejor» depende del indicador (más enfermeras, menos mortalidad).</p>'
          '<figcaption>Fuente: OCDE, Data Explorer, tema Salud <a href="https://data-explorer.oecd.org/?fs[0]=Topic%%2C0%%7CHealth%%23HEA%%23&pg=0&fc=Topic&bp=true&snb=86" rel="noopener">abrir</a>; interfaz de datos https://sdmx.oecd.org/public/rest. '
          'Último dato del Perú frente al dato más cercano en el tiempo de cada país miembro. Cálculo del autor sobre la base bases_pais, esquema ocde.</figcaption></figure>') % (len(filas), cuerpo, peores, len(filas))
    # dispersión: enfermería y esperanza de vida
    pts = [(r["iso3"], _fl(r["enf_total"]), _fl(r["esperanza"]), r["miembro_ocde"] == "1") for r in MATP]
    pts = [p for p in pts if p[1] is not None and p[2] is not None]
    disp = ""
    if pts:
        W_, H_, x0, x1, y0, y1 = 760, 400, 70, 730, 350, 24
        xmax = max(20.0, max(p[1] for p in pts) * 1.05)
        ymin, ymax = min(64.0, min(p[2] for p in pts) - 1), 86.0
        X = lambda v: x0 + (x1 - x0) * v / xmax
        Y = lambda v: y0 - (y0 - y1) * (v - ymin) / (ymax - ymin)
        o = []
        for g in range(0, int(xmax) + 1, 4):
            o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" class="s-line" stroke-width="1"/>' % (X(g), y0, X(g), y1) + tx(X(g), y0 + 18, str(g), "ts", "middle"))
        for g in range(int(ymin) + 1, 87, 4):
            o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" class="s-line" stroke-width="1"/>' % (x0, Y(g), x1, Y(g)) + tx(x0 - 8, Y(g) + 4, str(g), "ts", "end"))
        o.append(tx((x0 + x1) / 2, H_ - 6, "personal de enfermería por 1 000 habitantes", "t", "middle"))
        o.append('<text x="16" y="%d" class="t" text-anchor="middle" transform="rotate(-90 16 %d)">esperanza de vida al nacer, en años</text>' % ((y0 + y1) / 2, (y0 + y1) / 2))
        nom = {"PER": "Perú", "CHL": "Chile", "COL": "Colombia", "MEX": "México", "CRI": "Costa Rica", "BRA": "Brasil", "USA": "Estados Unidos", "JPN": "Japón", "NOR": "Noruega", "CHE": "Suiza", "ESP": "España", "ZAF": "Sudáfrica", "IND": "India"}
        for iso, xv, yv, miem in pts:
            if iso == "PER":
                continue
            o.append('<circle cx="%.1f" cy="%.1f" r="5.5" class="%s" opacity="0.75"/>' % (X(xv), Y(yv), "f-acc" if miem else "f-wait"))
            if iso in nom:
                o.append(tx(X(xv) + 8, Y(yv) + 4, nom[iso], "ts"))
        for iso, xv, yv, miem in pts:
            if iso == "PER":
                o.append('<circle cx="%.1f" cy="%.1f" r="9" class="f-ask s-surf" stroke-width="2"/>' % (X(xv), Y(yv)) + tx(X(xv) + 13, Y(yv) + 5, "Perú", "tb task"))
        c1 = next((c for c in COR if c["grupo"].startswith("todos") and c["x"] == "enf_total" and c["y"] == "esperanza"), None)
        disp = fig("Más enfermería, más esperanza de vida: asociación entre países", svg(W_, H_, "".join(o), "Diagrama de dispersión de %d países: personal de enfermería por 1 000 habitantes frente a esperanza de vida al nacer; el Perú aparece resaltado" % len(pts), 560) +
                   leyenda([("sg-acc", "País miembro de la OCDE"), ("sg-wait", "Otro país de la base"), ("sg-ask", "Perú")]),
                   '<figcaption>Fuente: OCDE, Data Explorer, tema Salud; último dato de 2018 a 2025 por país. Correlación de Spearman %s entre %s países; al descontar el gasto en salud por habitante baja a %s y deja de ser significativa. Es asociación, no causa.</figcaption>' % (
                       e(c1["spearman"]) if c1 else "", e(c1["n"]) if c1 else "", e(c1["spearman_parcial_descontando_gasto"]) if c1 else ""), ancha=True)
    tr = "".join('<tr><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % (e(c["y_nombre"]), e(c["n"]), e(c["spearman"]), e(c["spearman_parcial_descontando_gasto"]), e("%.3f" % float(c["p_parcial"]) if c["p_parcial"] else ""))
                 for c in COR if c["grupo"].startswith("todos") and c["x"] == "enf_total")
    f3 = ('<figure class="fig ancha"><h4>Correlaciones entre países: personal de enfermería por 1 000 habitantes y resultados</h4><div class="scroll"><table class="lam"><thead><tr><th>Resultado</th><th>Países</th><th>Spearman</th><th>Descontando el gasto en salud</th><th>Valor p</th></tr></thead><tbody>%s</tbody></table></div>'
          '<p class="txt">Lectura honesta: la asociación bruta es fuerte, pero casi desaparece al descontar el gasto en salud por habitante. Los países con más enfermeras también gastan más y son más ricos. Estos datos no prueban que más enfermeras causen mejores resultados; para eso están los estudios de la sección «Valor del cuidado».</p>'
          '<figcaption>Cálculo del autor con la base de la OCDE. Correlación de rangos de Spearman; la columna «descontando» correlaciona los residuos tras ajustar por el gasto corriente en salud por habitante.</figcaption></figure>') % tr
    det = "".join('<tr><td>%s</td><td><b>%s</b></td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s de %s</td><td class="cf">%s</td></tr>' % (
        e(r["grupo"]), e(r["indicador"]), e(_n(r["peru"]) + " (" + r["peru_anio"] + ")"), e(_n(r["ocde_media"])), e(_n(r["chile"]) if r["chile"] else ""), e(r["lugar_del_peru_1_es_el_mejor"] or "—"), e(r["de"]), e(r["nota"])) for r in TIT)
    tabla = '<details class="datos"><summary>Ver los %d indicadores titulares con sus valores</summary><div><div class="scroll"><table class="lam"><thead><tr><th>Grupo</th><th>Indicador</th><th>Perú</th><th>Promedio OCDE</th><th>Chile</th><th>Lugar</th><th>Advertencia</th></tr></thead><tbody>%s</tbody></table></div></div></details>' % (len(TIT), det)
    aviso = '<div class="aviso"><h3>Datos que no conviene citar todavía</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(x) for x in notas[:8]) if notas else ""
    base = ('<div class="pedidos"><h3>Dónde quedó la data</h3><ul><li>Base única <b>bases_pais</b> (PostgreSQL, T:\\BASES SISOL), esquema <b>ocde</b>: 20 020 959 observaciones, 86 flujos de datos y 79 países o áreas, tal como las publica la OCDE. El Perú tiene dato en 56 flujos (73 886 observaciones).</li>'
            '<li>Se consulta por la vista <b>ref.ocde_salud</b>. Los archivos originales están en T:\\BASES SISOL\\pais\\descargas\\ocde_salud y el cargador en pais\\scripts\\cargar_ocde.py.</li>'
            '<li>Interfaz de integración: https://sdmx.oecd.org/public/rest, la misma que alimenta el Data Explorer. No pide clave.</li></ul></div>')
    return seccion("ocde", "El Perú frente a la OCDE: toda la data de salud, en su base", "HECHO",
                   "Su pedido: bajar todos los indicadores de salud de la OCDE, de todos los países, en datos crudos, para reconstruir, analizar y correlacionar.", k + '<div class="figs">' + f1 + disp + f3 + "</div>" + aviso + base + tabla)


def _oms(ed, nivel, grupo):
    return next((r for r in OMS_R if r["edicion"] == ed and r["nivel"] == nivel and r["grupo"] == grupo), None)


def sec_mundo(local):
    if not OMS_R:
        return ""
    def barra(r):
        return stack([(int(r["si"]), "sg-ok", "Sí: %s" % r["si"]), (int(r["parcial"]), "sg-gold", "Parcial: %s" % r["parcial"]), (int(r["no"]), "sg-ask", "No: %s" % r["no"]), (int(r["no_reportado"]), "sg-wait", "No reportado: %s" % r["no_reportado"])], cap=70)
    m20, m25 = _oms("2020", "Mundo", "Todos"), _oms("2025", "Mundo", "Todos")
    a20, a25 = _oms("2020", "Región", "América Latina y el Caribe"), _oms("2025", "Región", "América Latina y el Caribe")
    b = '<div class="barras"><div><b>Mundo, edición 2020 (194 países)</b>%s</div><div><b>Mundo, edición 2025 (194 países)</b>%s</div>' % (barra(m20), barra(m25))
    if a20 and a25:
        b += '<div><b>América Latina y el Caribe, 2020 (%s países)</b>%s</div><div><b>América Latina y el Caribe, 2025 (%s países)</b>%s</div>' % (a20["paises"], barra(a20), a25["paises"], barra(a25))
    b += "</div>" + leyenda([("sg-ok", "Sí reporta jefatura"), ("sg-gold", "Parcial"), ("sg-ask", "No"), ("sg-wait", "No reportado")])
    per = next((r for r in OMS_P if r["iso3"] == "PER"), {})
    f1 = fig("Jefatura nacional de enfermería en el gobierno: lo que reporta cada país a la Organización Mundial de la Salud", b,
             '<figcaption>Fuente: Organización Mundial de la Salud, perfiles de país de «State of the world\'s nursing» 2020 <a href="https://apps.who.int/nhwaportal/Sown/Index" rel="noopener">abrir</a> y 2025 <a href="https://apps.who.int/nhwaportal/" rel="noopener">abrir</a>; rubros «Chief Nursing Officer position» y «Chief nursing position». '
             'Lectura propia de los 388 perfiles (el dato es un ícono). En 2025 respondieron 120 países, igual que en el informe; mi conteo de «Sí» es %s y el informe publica 98: un país de diferencia, por determinar.</figcaption>' % e(m25["si"]),
             ancha=True, gran='%s %% <small>de los países que respondieron en 2025 reporta tenerla (%s de %s)</small>' % (e(m25["porcentaje_si_entre_los_que_respondieron"]), e(m25["si"]), e(m25["respondieron"])),
             txt="El Perú: en 2020 reportó «%s»; en 2025 figura como «%s». En América Latina y el Caribe, en 2025 la reportan %s de los %s países que respondieron." % (per.get("jefatura_enfermeria_2020", ""), per.get("jefatura_enfermeria_2025", "").lower(), a25["si"] if a25 else "", a25["respondieron"] if a25 else ""))
    sel = [r for r in OMS_I if r["edicion"] == "2025" and r["estrato"] == "Ingreso mediano alto"]
    tr = "".join('<tr><td>%s</td><td class="n">%s <span class="cf">(%s países)</span></td><td class="n">%s <span class="cf">(%s países)</span></td><td class="n">%s</td></tr>' % (
        e(r["indicador"]), e(r["mediana_si"]), e(r["n_si"]), e(r["mediana_no_o_parcial"]), e(r["n_no_o_parcial"]), e(("%.3f" % float(r["p_mann_whitney_si_frente_a_no"])) if r["p_mann_whitney_si_frente_a_no"] else "")) for r in sel)
    f2 = ('<figure class="fig ancha"><h4>¿Tienen mejores indicadores los países con jefatura? Países de ingreso mediano alto, como el Perú, 2025</h4><div class="scroll"><table class="lam"><thead><tr><th>Indicador (mediana)</th><th>Con jefatura</th><th>Sin jefatura o parcial</th><th>Valor p</th></tr></thead><tbody>%s</tbody></table></div>'
          '<p class="txt">Lectura honesta: no. Entre países del mismo nivel de ingreso, tener la jefatura no se asocia con mejores indicadores; en esperanza de vida la diferencia incluso favorece a los que no la tienen. El argumento sólido no es «tienen mejores indicadores», sino «es el estándar: cuatro de cada cinco países que responden la tienen, y el Perú reportó que no».</p>'
          '<figcaption>Fuente: jefatura, perfiles 2025 de la Organización Mundial de la Salud; indicadores, Observatorio Mundial de la Salud <a href="https://ghoapi.azureedge.net/api/Indicator" rel="noopener">abrir</a>; grupo de ingreso, Banco Mundial <a href="https://api.worldbank.org/v2/country?format=json&per_page=400" rel="noopener">abrir</a>. '
          'Prueba de Mann-Whitney. La propia Organización Mundial de la Salud informa que no halló correlación estadísticamente significativa (informe 2025, página impresa 90).</figcaption></figure>') % tr
    am = [r for r in OMS_P if r["region_banco_mundial"] in ("América Latina y el Caribe", "América del Norte")]
    am.sort(key=lambda r: r["pais"] or "")
    cls = {"Sí": "si", "No": "no", "Parcial": "qd", "No reportado": "qd"}
    det = "".join('<tr><td>%s</td><td class="%s">%s</td><td class="%s">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s%s</td></tr>' % (
        e(r["pais"]), cls.get(r["jefatura_enfermeria_2020"], "qd"), e(r["jefatura_enfermeria_2020"]), cls.get(r["jefatura_enfermeria_2025"], "qd"), e(r["jefatura_enfermeria_2025"]),
        e(r["enfermeria_por_10000"]), e(r["indice_cobertura"]), _a(r["fuente_2020"], "perfil 2020"), _a(r["fuente_2025"], "perfil 2025")) for r in am)
    tabla = ('<details class="datos"><summary>Ver país por país: las Américas (%d países; la base tiene los 194)</summary><div><div class="scroll"><table class="lam matriz"><thead><tr><th>País</th><th>Jefatura 2020</th><th>Jefatura 2025</th><th>Enfermería por 10 000</th><th>Índice de cobertura</th><th>Fuente</th></tr></thead><tbody>%s</tbody></table></div></div></details>') % (len(am), det)
    base = ('<div class="pedidos"><h3>Dónde quedó la base</h3><ul><li><b>bases_pais</b>, esquema <b>oms</b>: tabla oms.sown_perfil (194 países, dos ediciones, con el enlace y la huella de cada perfil) y oms.gho_obs (siete indicadores, todos los países y años). Clasificación de ingreso en bm.pais.</li>'
            '<li>Vista de consulta: <b>ref.oms_jefatura_enfermeria</b>, una fila por país. Archivo plano: datos/oms/oms_jefatura_enfermeria_paises.csv.</li>'
            '<li>Límite de esta fuente: dice si el país reporta la jefatura, no su nombre ni su rango. El nombre oficial y la base legal, país por país, están en la sección siguiente.</li></ul></div>')
    return seccion("mundo", "Qué países tienen jefatura nacional de enfermería: la base de 194 países", "HECHO",
                   "Su pedido: buscar una base de datos de qué países tienen una dirección nacional de enfermería en el ministerio y bajarla con su fuente.", '<div class="figs">' + f1 + f2 + "</div>" + base + tabla)


def sec_ministro(local):
    if not (PRI or AGE):
        return ""
    cuerpo = ""
    if PRI and PRI.get("ministro"):
        m = PRI["ministro"]
        it = "".join('<li><p class="dato">%s</p><p class="meta">%s<span class="donde">%s</span><span class="fu">%s%s</span></p></li>' % (e(d.get("cita")), chip_capa("CITA"), e(d.get("fecha")), e(d.get("ocasion")), _a(d.get("enlace"))) for d in m.get("dichos", []))
        cuerpo += '<h3>Lo que el Ministro ha dicho sobre datos, control e inteligencia artificial</h3><p class="nota">%s, en el cargo desde %s.</p><ul class="hechos">%s</ul><div class="aviso"><h3>Lo que no dijo</h3><ul><li>%s</li></ul></div>' % (
            e(m.get("nombreOficial")), e(m.get("desde")), it, e(m.get("advertencia")))
    if AGE and AGE.get("agenda"):
        marca = {"CONFIRMADA": ("si", "● Confirmada"), "MATIZAR": ("qd", "◐ Con matiz"), "REFUTADA": ("no", "✕ Refutada"), "NO_ABIERTA": ("qd", "○ No se pudo abrir")}
        tr = "".join('<tr><td>%s</td><td class="%s">%s</td><td>%s<span class="cf">%s · %s%s</span></td><td class="cf">%s</td></tr>' % (
            e(a.get("tema")), marca.get(a.get("veredicto"), ("qd", ""))[0], marca.get(a.get("veredicto"), ("qd", a.get("veredicto")))[1], e(a.get("fraseSegura")), e(a.get("quienLoDice")), e(a.get("fecha")), _a(a.get("enlace")), e(a.get("advertencia"))) for a in AGE["agenda"])
        cuerpo += ('<h3>El resumen que usted pegó, contrastado con las notas originales</h3><div class="scroll"><table class="vist matriz"><thead><tr><th>Tema</th><th>Veredicto</th><th>Frase segura, quién lo dice y cuándo</th><th>Advertencia</th></tr></thead><tbody>%s</tbody></table></div>'
                   '<p class="nota">Un resumen hecho por un buscador no es fuente: cada afirmación se abrió en su página original.</p>') % tr
    pn = stack([(1195, "sg-ok", "Enfermera, sin médico: 1 195"), (826, "sg-wait", "Sin enfermera ni médico: 826"), (281, "sg-acc", "Con médico: 281")], cap=80)
    f = fig("Quién está en los puestos de salud públicos de categoría I-1", pn + leyenda([("sg-ok", "Hay enfermera y no hay médico: 1 195 (52 %)"), ("sg-wait", "Sin enfermera ni médico (obstetra o técnico): 826 (36 %)"), ("sg-acc", "Con médico: 281 (12 %)")]),
            '<figcaption>Fuente: Superintendencia Nacional de Salud, «Consulta de recursos de salud por IPRESS» <a href="http://datos.susalud.gob.pe/dataset/consulta-recursos-de-salud-por-ipress" rel="noopener">abrir</a>; último reporte de cada establecimiento entre junio de 2025 y junio de 2026; Ministerio de Salud y gobiernos regionales. Cálculo del autor en la base bases_pais. '
            'Límite: reportaron 2 302 de los 4 250 puestos públicos I-1 del padrón; describe a los que reportan.</figcaption>',
            ancha=True, gran='88 % <small>de los puestos de salud I-1 que reportan no tiene médico (2 021 de 2 302)</small>',
            txt="La conectividad llegará a postas donde, en la mitad de los casos, la profesional presente es la enfermera. Si el dato se va a producir ahí, lo va a producir ella.")
    cuerpo += '<h3>El puente: a quién le llega la conectividad</h3><div class="figs">%s</div>' % f
    if AGE and AGE.get("puente"):
        cuerpo += '<ul class="hechos">%s</ul>' % "".join('<li><p class="dato">%s</p><p class="meta">%s<span class="fu">%s%s</span></p></li>' % (e(p.get("dato")), chip_capa(p.get("capa")), e(p.get("fuente")), _a(p.get("enlace"))) for p in AGE["puente"])
    for titulo, clave, src in (("Lo que sí se puede decir", "paraLaPrimeraLamina", AGE), ("Lo que no conviene decir", "queNoDecir", AGE)):
        if src and src.get(clave):
            cuerpo += '<h3>%s</h3><ul class="pd">%s</ul>' % (titulo, "".join("<li>%s</li>" % e(x) for x in src[clave]))
    return seccion("ministro", "El Ministro: lo que dijo, su agenda y a quién le llega", "HECHO", "Su indicación: el Ministro habla de control con datos e inteligencia artificial, y esa debe ser la primera lámina. Esto es lo que las fuentes abiertas permiten atribuirle.", cuerpo)


def sec_primera(local):
    if not PRI:
        return ""
    L = PRI.get("primeraLamina", {})
    datos = "".join('<li><p class="dato">%s</p><p class="meta">%s<span class="fu">%s</span></p></li>' % (e(d.get("dato")), chip_capa(d.get("capa")), e(d.get("ref"))) for d in L.get("datos", []))
    cad = "".join('<li class="%s"><b>%s</b><span>%s</span><span class="tag">%s</span></li>' % ({"CITA": "", "DERIVACION": "oro", "JUICIO": "ask"}.get(c.get("capa"), ""), e(c.get("paso")), e(c.get("texto")), e({"CITA": "cita", "DERIVACION": "derivación", "JUICIO": "juicio del autor"}.get(c.get("capa"), c.get("capa")))) for c in PRI.get("cadena", []))
    cuerpo = ('<figure class="fig ancha"><h4>%s</h4><p class="txt"><b>Mensaje único:</b> %s</p><h3>Los datos de la lámina</h3><ul class="hechos">%s</ul><h3>El esquema</h3><p class="txt">%s</p><h3>Guion oral de un minuto</h3><p class="txt">%s</p>'
              '<figcaption>Propuesta elaborada solo con afirmaciones verificadas. La tesis es juicio del autor y así está rotulada.</figcaption></figure>') % (e(L.get("titulo")), e(L.get("mensaje")), datos, e(L.get("esquema")), e(L.get("guionOral")))
    cuerpo += '<h3>La cadena lógica, paso por paso y con su capa</h3><ol class="flujo c3">%s</ol>' % cad
    if PRI.get("indicadoresCriticos"):
        marca = {"SI_POR_NORMA": "Sí, por norma", "SI_POR_EVIDENCIA": "Sí, por evidencia", "PARCIAL": "En parte", "NO": "No", "POR_DETERMINAR": "Por determinar"}
        tr = "".join('<tr><td><b>%s</b><span class="cf">%s</span></td><td class="n">%s</td><td class="n">%s</td><td>%s</td><td>%s<span class="cf">%s</span></td></tr>' % (e(i.get("indicador")), e(i.get("fuente")), e(i.get("peru")), e(i.get("comparador")), e(i.get("anio")), e(marca.get(i.get("sensibleAEnfermeria"), "")), e(i.get("base"))) for i in PRI["indicadoresCriticos"])
        cuerpo += '<h3>Indicadores críticos y qué tiene que ver enfermería</h3><div class="scroll"><table class="vist"><thead><tr><th>Indicador</th><th>Perú</th><th>Comparador</th><th>Año</th><th>¿Depende de enfermería?</th></tr></thead><tbody>%s</tbody></table></div>' % tr
    if PRI.get("evidenciaIA"):
        tr = "".join('<tr><td><b>%s</b>%s</td><td>%s</td><td>%s</td><td class="cf">%s</td></tr>' % (e(x.get("estudio")), _a(x.get("enlace")), e(x.get("diseno")), e(x.get("efecto")), e(x.get("limite"))) for x in PRI["evidenciaIA"])
        cuerpo += '<h3>Inteligencia artificial con datos de enfermería: qué muestran los estudios</h3><div class="scroll"><table class="vist"><thead><tr><th>Estudio</th><th>Diseño</th><th>Efecto</th><th>Límite</th></tr></thead><tbody>%s</tbody></table></div>' % tr
    for titulo, clave, k1, k2 in (("Cuando enfermería comanda la gestión del cuidado", "gestionDelCuidado", "hecho", "capa"), ("Qué permite y qué exige la norma peruana", "baseNormativa", "norma", "dice")):
        if PRI.get(clave):
            if clave == "gestionDelCuidado":
                cuerpo += '<h3>%s</h3><ul class="hechos">%s</ul>' % (titulo, "".join('<li><p class="dato">%s</p><p class="meta">%s<span class="fu">%s%s</span></p></li>' % (e(x.get("hecho")), chip_capa(x.get("capa")), e(x.get("ref")), _a(x.get("enlace"))) for x in PRI[clave]))
            else:
                cuerpo += '<h3>%s</h3><ul class="hechos">%s</ul>' % (titulo, "".join('<li><p class="dato"><b>%s.</b> %s</p><p class="meta"><span class="fu">%s%s</span></p></li>' % (e(x.get("norma")), e(x.get("dice")), e(x.get("ref")), _a(x.get("enlace"))) for x in PRI[clave]))
    if PRI.get("gobernanza"):
        cuerpo += '<div class="pedidos"><h3>Gobernanza de la inteligencia artificial: el marco del autor</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(x) for x in PRI["gobernanza"])
    if PRI.get("queNoDecir"):
        cuerpo += '<div class="aviso"><h3>Lo que no conviene decir</h3><ul>%s</ul></div>' % "".join("<li>%s</li>" % e(x) for x in PRI["queNoDecir"])
    if PRI.get("porDeterminar"):
        cuerpo += '<h3>Por determinar</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in PRI["porDeterminar"])
    return seccion("primera2", "La primera lámina, con su sustento verificado", "HECHO", "Enfermería, datos e inteligencia artificial, y el control del cuidado: qué puede afirmarse con fuente y qué es tesis del autor.", cuerpo)


def sec_autonomia2(local):
    if not AUTC:
        return ""
    par = "".join("<p class=\"txt\">%s</p>" % e(p) for p in (AUTC.get("answerOutline") or "").split("\n\n") if p.strip())
    cuerpo = '<figure class="fig ancha"><h4>La respuesta en cuatro pasos, con lo que cada fuente permite decir</h4>%s<figcaption>Elaborada por el crítico de la investigación a partir de 43 afirmaciones; todas pidieron algún matiz y ninguna fue refutada.</figcaption></figure>' % par
    if AUTC.get("strongest"):
        cuerpo += '<h3>Las cinco afirmaciones más fuertes</h3><ul class="pd">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in AUTC["strongest"])
    for titulo, clave in (("Vacíos que quedan", "gaps"), ("Riesgos ante un público médico", "risks")):
        if AUTC.get(clave):
            cuerpo += '<details class="datos"><summary>%s (%d)</summary><div><ul class="pd">%s</ul></div></details>' % (titulo, len(AUTC[clave]), "".join("<li>%s</li>" % e(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)) for x in AUTC[clave]))
    return seccion("autonomia2", "Autonomía: la respuesta verificada", "HECHO", "Su pregunta: cómo demostramos la autonomía de enfermería frente al equipo de salud.", cuerpo)


def sec_plan3(local):
    if not PLAN3:
        return ""
    tar = []
    for l in PLAN3["laminas"]:
        datos = "".join("<li>%s %s</li>" % (chip_capa(d[0]), e(d[1])) for d in l.get("datos", []))
        tar.append('<li class="p3 %s"><div class="p3-h"><span class="num">%s</span><div><b>%s</b><span class="tag">%s · %s</span></div></div><p class="txt"><b>Mensaje:</b> %s</p><p class="txt"><b>Visual:</b> %s</p><ul class="p3-d">%s</ul>%s</li>' % (
            l.get("clase", ""), e(l["n"]), e(l["titulo"]), e(l.get("parte", "")), e(l.get("tiempo", "")), e(l.get("mensaje", "")), e(l.get("visual", "")), datos, ('<p class="nota">%s</p>' % e(l["nota"])) if l.get("nota") else ""))
    cuerpo = '<ol class="plan3">%s</ol><p class="nota">%s</p>' % ("".join(tar), e(PLAN3.get("pie", "")))
    return seccion("plan3", "El plan, lámina por lámina, con los datos ya verificados", "POR_DECIDIR", PLAN3.get("lead", ""), cuerpo)
