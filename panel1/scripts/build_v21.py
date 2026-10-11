# -*- coding: utf-8 -*-
"""Deck del Panel I, versión estratégica aprobada el 11 de octubre de 2026: nueve láminas.
Escribe deck-panel1/project/slides/*.html y deck.json."""
import io, json, pathlib, re, shutil
S = pathlib.Path(__file__).resolve().parent
P = S / "deck-panel1" / "project"
SL = P / "slides"
A, AZ, ORO, TINTA, PANEL, LINEA, CUERPO, GRIS, MAL, BIEN = "#0070C0", "#005A9C", "#B07A10", "#0B1D36", "#F3F6FA", "#D5DEE9", "#2A3B55", "#55657D", "#9A2A63", "#0B6E55"
F = "font-family:'Fraunces', Georgia, serif;"


def lam(id, titulo, kicker, cuerpo, pie, notas, gap=18):
    return ('<section id="%s" data-transition="fade" style="background:#FFFFFF;color:%s;font-family:Arial, Helvetica, sans-serif;padding:222px 128px 200px;display:flex;flex-direction:column;gap:%dpx">\n'
            '<img src="/_blob/49486cf8087824f7aeba26166eb4df35" alt="" style="position:absolute;left:0px;top:0px;width:1920px;height:1080px;object-fit:cover">\n'
            '<div data-banda="1" style="position:absolute;left:196px;top:22px;width:1600px;height:176px;display:flex;flex-direction:column;justify-content:center"><h2 style="font-family:Arial, Helvetica, sans-serif;font-size:56px;font-weight:700;line-height:1.1;color:#FDFDFD">%s</h2></div>\n'
            '<p style="font-size:24px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:%s">%s</p>\n%s\n'
            '<p style="position:absolute;left:128px;right:128px;bottom:96px;font-size:24px;line-height:1.25;color:%s">%s</p>\n<aside>%s</aside>\n</section>\n') % (id, TINTA, gap, titulo, A, kicker, cuerpo, GRIS, pie, notas)


def caja(inner, flex="1", bg=PANEL, borde=LINEA, pad="22px 26px", extra=""):
    return '<div style="flex:%s;min-width:0px;display:flex;flex-direction:column;gap:10px;background:%s;border:1px solid %s;border-radius:20px;padding:%s;%s">%s</div>' % (flex, bg, borde, pad, extra, inner)


def eti(t, color=A):
    return '<p style="font-size:24px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:%s">%s</p>' % (color, t)


def gran(t, color=ORO, tam=72):
    return '<p style="%sfont-size:%dpx;font-weight:600;line-height:1;color:%s;white-space:nowrap">%s</p>' % (F, tam, color, t)


def tx(t, color=CUERPO, peso=400, tam=26, fx=False):
    return '<p style="%sfont-size:%dpx;font-weight:%d;line-height:1.28;color:%s">%s</p>' % ("flex:1;min-width:0px;" if fx else "", tam, peso, color, t)


FLECHA = '<svg aria-hidden="true" viewBox="0 0 24 48" width="24" height="48" xmlns="http://www.w3.org/2000/svg" style="align-self:center;flex:none;width:24px;height:48px"><path d="M4 4 L20 24 L4 44" fill="none" stroke="%s" stroke-width="4"/></svg>' % A
out = {}

# ---------------------------------------------------------------- 1. Apertura
citas = "".join('<p style="%sfont-size:36px;font-weight:600;line-height:1.1;color:#FFFFFF;white-space:nowrap">%s</p>%s' % (F, c, ('<p style="font-size:34px;color:#7FB6E6">→</p>' if i < 2 else "")) for i, c in enumerate(["«controlar todo el sistema»", "«con esa data»", "«empezar a hacer gestión»"]))
min_ = '<div style="display:flex;gap:22px;align-items:center;background:%s;border-radius:18px;padding:20px 28px"><p style="flex:none;width:190px;font-size:24px;line-height:1.25;color:#C9D7EA">El Ministro de Salud, en televisión:</p>%s</div>' % (TINTA, citas)
pasos = [("1", "La enfermera registra", "el cuidado; es obligatorio por norma", A), ("2", "Registro estandarizado", "con diagnóstico e intervención", A), ("3", "Dato", "que los sistemas pueden leer", ORO),
         ("4", "Inteligencia artificial", "alerta, con supervisión humana", ORO), ("5", "Enfermería decide", "y actúa; el indicador se mueve", BIEN)]
circ = '<div style="display:flex;gap:10px;align-items:stretch">' + FLECHA.join(
    '<div style="flex:1;min-width:0px;background:#FFFFFF;border:2px solid %s;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column;gap:8px"><p style="%sfont-size:40px;font-weight:600;line-height:1;color:%s">%s</p><p style="font-size:28px;font-weight:700;line-height:1.15;color:%s">%s</p><p style="font-size:24px;line-height:1.2;color:%s">%s</p></div>' % (c, F, c, n, TINTA, t, CUERPO, d)
    for n, t, d, c in pasos) + "</div>"
datos = '<div style="display:flex;gap:18px;align-items:stretch">' + caja(eti("Dónde llega la conectividad") + gran("88 %", ORO, 60) + tx("de los puestos de salud I-1 que reportan no tiene médico; en 52 % hay enfermera.", TINTA, 600, 24), pad="18px 24px") + \
    caja(eti("Lo que muestra un ensayo") + gran("0.64", ORO, 60) + tx("riesgo de muerte hospitalaria con una alerta que lee el registro de enfermería. Estados Unidos.", TINTA, 600, 24), pad="18px 24px") + \
    caja(eti("Propuesta del autor", MAL) + tx("El control del cuidado, en manos de enfermería: que el registro sea dato y tenga quien responda.", TINTA, 700, 26) + tx("Demostrarlo en el Perú, con medición.", CUERPO, 400, 24), bg="#FBEFF5", borde="#E9BFD4", pad="18px 24px") + "</div>"
out["apertura"] = lam("apertura", "Datos, inteligencia artificial y control del cuidado", "La propuesta de enfermería, en el lenguaje del Ministro", min_ + circ + datos,
    "Fuentes: Panamericana Televisión, 9 de setiembre de 2026; Decreto Supremo 004-2002-SA, artículo 9; Superintendencia Nacional de Salud, 2026 (cálculo propio); Rossetti, Nature Medicine, 2025.",
    "1:45. El Ministro dijo en televisión que, si interconectamos y empezamos a controlar todo el sistema, con esa data se puede empezar a hacer gestión. Lo dijo de hospitales y centros de salud; no habló de enfermería. Yo vengo a completar esa frase. "
    "El registro del cuidado ya es obligatorio: el reglamento de la Ley 27669, artículo 9, dice que el Proceso de Atención de Enfermería será registrado obligatoriamente en la historia clínica. La conectividad va a llegar a postas donde quien está es la enfermera: de los 2 302 puestos de salud públicos I-1 que reportaron sus recursos, 2 021 no reportan médico y en 1 195 hay enfermera y no hay médico. "
    "En Estados Unidos, un ensayo aleatorizado por conglomerados con una alerta que lee los patrones del registro de enfermería halló menor riesgo de muerte hospitalaria: razón de riesgos 0.64, intervalo de confianza al 95 por ciento de 0.53 a 0.78. Es evidencia extranjera, no del Perú; otro ensayo, con un puntaje mostrado sin respuesta obligatoria, no halló cambio. "
    "Mi juicio profesional, y lo digo como juicio: el control del cuidado en manos de enfermería es la forma de que ese dato exista y tenga quien responda por él. Propongo demostrarlo aquí, con medición. No decir que el Ministro respalda esta propuesta: no lo ha dicho.")

# ---------------------------------------------------------------- 2. Presencia
def par(nombre, per, ocde, vmax, lugar, dec=2, unidad=""):
    f = lambda v: (("%." + str(dec) + "f") % v) if dec else format(int(round(v)), ",").replace(",", " ")
    return ('<div style="display:flex;flex-direction:column;gap:6px"><p style="font-size:24px;font-weight:700;line-height:1.2;color:%s">%s <span style="font-weight:400;color:%s">· %s</span></p>'
            '<div style="display:flex;align-items:center;gap:12px"><p style="flex:none;width:76px;font-size:24px;color:%s">Perú</p><div style="width:%dpx;height:22px;border-radius:6px;background:%s"></div><p style="font-size:24px;font-weight:700;color:%s">%s%s</p></div>'
            '<div style="display:flex;align-items:center;gap:12px"><p style="flex:none;width:76px;font-size:24px;color:%s">OCDE</p><div style="width:%dpx;height:22px;border-radius:6px;background:%s"></div><p style="font-size:24px;font-weight:700;color:%s">%s%s</p></div></div>') % (
        TINTA, nombre, MAL, lugar, CUERPO, max(6, int(520 * per / vmax)), ORO, TINTA, f(per), unidad, CUERPO, max(6, int(520 * ocde / vmax)), A, TINTA, f(ocde), unidad)


izq = caja(eti("En el Perú") + gran("71 052") + tx("enfermeros en el sector salud: 18.0 % de su personal y 37 de cada 100 profesionales asistenciales.", TINTA, 600) +
           '<div style="display:flex;gap:14px;align-items:baseline;border-top:1px solid %s;padding:12px 0px 0px">%s%s</div>' % (LINEA, gran("24", A, 60), tx("horas junto al paciente, en todos los turnos y niveles.", TINTA, 600, 26, True)) +
           '<div style="display:flex;gap:14px;align-items:baseline;border-top:1px solid %s;padding:12px 0px 0px">%s%s</div>' % (LINEA, gran("≈22 000", MAL, 60), tx("faltan para el umbral de 27.5 por 10 000 habitantes.", TINTA, 600, 26, True)), flex="0 0 600px")
der = caja(eti("Frente a los países de la OCDE") + par("Enfermeras profesionales por 1 000 habitantes", 2.09, 8.85, 9.5, "lugar 32 de 33") + par("Ingreso anual de una enfermera de hospital, en dólares comparables", 31253, 67428, 72000, "último de 37", 0) +
           par("Gasto en salud, porcentaje del producto bruto interno", 5.4, 9.3, 9.5, "lugar 38 de 39", 1, " %") + par("Mortalidad materna por 100 000 nacidos vivos", 38.4, 8.9, 40, "lugar 37 de 38", 1), pad="20px 26px")
out["presencia"] = lam("presencia", "Presencia: la mayor fuerza del sistema, y la más escasa", "Parte 1 · lo que enfermería ya aporta", '<div style="display:flex;gap:18px;align-items:stretch">' + izq + der + "</div>",
    "Fuentes: Ministerio de Salud, Información de Recursos Humanos en el Sector Salud, 2023; Organización para la Cooperación y el Desarrollo Económicos (OCDE), Data Explorer, tema Salud, datos de 2024 y 2025; el umbral y los lugares son cálculo propio.",
    "1:15. Somos 71 052 enfermeros en el sector salud: el 18 por ciento de todo su personal y 37 de cada 100 profesionales asistenciales. Estamos las 24 horas. Y aun así somos pocos: faltan unos 22 000 para el umbral de 27.5 por 10 000 habitantes que la Organización Mundial de la Salud usa para estimar el déficit; es cálculo mío sobre esa referencia. "
    "Frente a la OCDE, a la que el país quiere ingresar: 2.09 enfermeras profesionales por 1 000 habitantes contra 8.85; solo un país miembro tiene menos. Una enfermera de hospital gana, en dólares comparables, 31 253 al año contra 67 428: el valor más bajo de los 37 países con dato. Gastamos en salud 5.4 por ciento del producto contra 9.3, y la mortalidad materna es 38.4 contra 8.9 por 100 000 nacidos vivos, más de cuatro veces. "
    "Fuente: base completa de salud de la OCDE, 20 millones de observaciones, descargada el 10 de octubre de 2026; promedio simple de los países miembros con dato.")

# ---------------------------------------------------------------- 3. Resultados
def res(num, que, estudio, color=BIEN):
    return caja('<p style="%sfont-size:128px;font-weight:600;line-height:1;color:%s">%s</p>' % (F, color, num) + tx(que, TINTA, 700, 30) + tx(estudio, GRIS, 400, 24), pad="30px 26px")


fila = '<div style="display:flex;gap:16px;align-items:stretch">' + res("0.69", "Reingresos por insuficiencia cardiaca con transición dirigida por enfermeras", "Koontalay, 2025 · metaanálisis · intervalo 0.54 a 0.89") + \
    res("0.56", "Muerte a tres meses en ictus cuando hay enfermera de ictus en el equipo", "Kumar, 2025 · 8 estudios · intervalo 0.37 a 0.85") + \
    res("0.52", "Muerte tras una complicación con vigilancia de enfermería 12 o más veces al día", "Shever, 2011 · observacional · sin intervalo") + \
    res("−0.68", "Puntos de hemoglobina glicosilada en diabetes con cuidado dirigido por enfermeras", "Zhang, 2022 · 13 ensayos · 3 757 personas", A) + "</div>"
barra = '<div style="display:flex;gap:18px;align-items:center;background:%s;border-radius:16px;padding:16px 24px"><p style="font-size:26px;font-weight:700;color:#FFFFFF">Cómo leerlo</p><p style="flex:1;min-width:0px;font-size:26px;line-height:1.25;color:#DCE6F2">Menos de 1 es menos riesgo: 0.69 significa 31 %% menos. Son estudios de otros países; los observacionales muestran asociación, no causa.</p></div>' % TINTA
out["resultados"] = lam("resultados", "Resultados: cuando la enfermera decide en su campo", "Parte 1 · lo que enfermería ya aporta", fila + barra,
    "Fuentes: artículos de la revisión, con su enlace en PubMed: Koontalay 2025, Kumar 2025, Shever 2011 y Zhang 2022. Razones de riesgo o de momios; diferencia de medias en hemoglobina glicosilada.",
    "1:30. Cuando la enfermera decide en su campo, el paciente gana. Transición del hospital a la casa dirigida por enfermeras en insuficiencia cardiaca: 31 por ciento menos reingresos. Enfermera de ictus en el equipo: 44 por ciento menos probabilidad de morir a tres meses. Vigilancia de enfermería doce o más veces al día: la mitad de muertes tras una complicación, en un estudio observacional. "
    "Diabetes con cuidado dirigido por enfermeras: 0.68 puntos menos de hemoglobina glicosilada en 13 ensayos aleatorizados. Honestidad: son estudios de otros países y los observacionales muestran asociación. La revisión Cochrane de 2026, con 82 ensayos en hospitales, encontró que cuando enfermeras asumen tareas habitualmente médicas probablemente hay poca o ninguna diferencia en mortalidad: el paciente no pierde.")

# ---------------------------------------------------------------- 4. Eficiencia
def antes(tit, a, b, ta, tb, ua=""):
    return ('<div style="display:flex;flex-direction:column;gap:10px"><p style="font-size:28px;font-weight:700;color:%s">%s</p>'
            '<div style="display:flex;align-items:center;gap:12px"><p style="flex:none;width:120px;font-size:26px;color:%s">Antes</p><div style="width:%dpx;height:38px;border-radius:6px;background:%s"></div><p style="font-size:32px;font-weight:700;color:%s">%s</p></div>'
            '<div style="display:flex;align-items:center;gap:12px"><p style="flex:none;width:120px;font-size:26px;color:%s">Después</p><div style="width:%dpx;height:38px;border-radius:6px;background:%s"></div><p style="font-size:32px;font-weight:700;color:%s">%s</p></div></div>') % (
        TINTA, tit, CUERPO, a, MAL, TINTA, ta, CUERPO, b, BIEN, TINTA, tb)


c1 = caja(eti("El caso · Instituto Nacional Cardiovascular, 2015") + antes("Formatos de registro de enfermería", 430, 24, "18", "1") + antes("Minutos de registro por paciente en 24 horas", 430, 242, "223.5", "125.8") +
          tx("97.7 minutos menos por paciente al día: tiempo que vuelve al cuidado.", TINTA, 700, 28) + tx("Se logró con enfermería integrada, sin brecha de personal y con apoyo de la alta dirección.", CUERPO, 400, 26), flex="0 0 720px", pad="26px 30px")
c2 = caja(eti("Lo que valió") + gran("S/ 2 009 550", ORO, 104) + tx("en un año, con 95 camas. Es tiempo de enfermería valorizado, más úlceras por presión evitadas y formatos.", TINTA, 600, 28) +
          '<div style="border-top:1px solid %s;padding:12px 0px 0px;display:flex;flex-direction:column;gap:8px">%s<div style="display:flex;gap:26px;align-items:baseline">%s%s</div>%s</div>' % (
              LINEA, eti("Si cada cama del país lograra lo mismo", MAL), gran("S/ 859 millones", MAL, 72), tx("techo al año", TINTA, 600, 28), tx("Escenario prudente, la cuarta parte: S/ 215 millones. Cálculo del autor: es un techo, no un pronóstico.")))
out["eficiencia"] = lam("eficiencia", "Eficiencia: del registro al dato", "Parte 1 · lo que enfermería ya aporta", '<div style="display:flex;gap:18px;align-items:stretch">' + c1 + c2 + "</div>",
    "Fuentes: Instituto Nacional Cardiovascular, postulación al Reconocimiento a la Gestión de Proyectos de Mejora 2016, tablas 13 y 14; Superintendencia Nacional de Salud, camas por establecimiento, 2015 y 2026. Antes y después, sin grupo de control.",
    "1:15. Este caso es nuestro. En 2015, en el Instituto Nacional Cardiovascular, enfermería reemplazó 18 formatos de registro por uno solo, estandarizado, con diagnósticos, intervenciones y resultados de enfermería. El tiempo de registro por paciente en 24 horas bajó de 223.5 a 125.8 minutos: 97.7 minutos que volvieron al cuidado. "
    "La institución valorizó el ahorro en 2 009 550 soles en un año, con 95 camas. Es un estudio de antes y después, sin grupo de control, y se hizo con enfermería integrada, sin brecha de personal y con apoyo de la alta dirección. Si cada una de las 40 593 camas del país lograra lo mismo, el techo sería 859 millones de soles al año; el escenario prudente, la cuarta parte, 215 millones. "
    "Es extrapolación mía: se midió en cuidados críticos, donde registrar toma más tiempo. Ese registro estandarizado es exactamente el dato que la inteligencia artificial necesita.")

# ---------------------------------------------------------------- 5. El mapa
def nivel(ancho, color, nombre, verbo):
    return '<div style="width:%dpx;height:150px;background:%s;clip-path:polygon(%dpx 0px, %dpx 0px, 100%% 100%%, 0px 100%%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px"><p style="font-size:30px;font-weight:700;color:#FFFFFF">%s</p><p style="font-size:26px;color:#FFFFFF">%s</p></div>' % (
        ancho, color, 72, ancho - 72, nombre, verbo)


pir = '<div style="flex:0 0 560px;display:flex;flex-direction:column;align-items:center;gap:6px;justify-content:center">' + nivel(270, MAL, "Estratégico", "decide") + nivel(414, ORO, "Táctico", "conduce") + nivel(558, BIEN, "Operativo", "cuida") + "</div>"


def filam(estado, color, donde, que):
    return ('<div style="display:flex;gap:16px;align-items:center;background:%s;border:1px solid %s;border-left:10px solid %s;border-radius:14px;padding:12px 22px;height:150px">'
            '<p style="flex:none;width:170px;font-size:24px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:%s">%s</p><div style="flex:1;display:flex;flex-direction:column;gap:6px;min-width:0px"><p style="font-size:30px;font-weight:700;line-height:1.15;color:%s">%s</p><p style="font-size:26px;line-height:1.2;color:%s">%s</p></div></div>') % (PANEL, LINEA, color, color, estado, TINTA, donde, CUERPO, que)


lista = '<div style="flex:1;min-width:0px;display:flex;flex-direction:column;gap:6px;justify-content:center">' + \
    filam("Ausente", MAL, "Ministerio de Salud y sede del Seguro Social", "Ningún órgano lleva el nombre de enfermería: ni en los reglamentos de 2017 y 2025 ni en las trece gerencias centrales.") + \
    filam("Presente", ORO, "Unidad Orgánica de Enfermería", "Órgano de línea bajo la máxima dirección del establecimiento. Ley 27669, artículo 13.") + \
    filam("Presente", BIEN, "Servicios, las 24 horas", "Jefas de servicio, supervisoras, coordinadoras y personal: donde el cuidado se ejecuta.") + "</div>"
out["mapa3"] = lam("mapa3", "El mapa: enfermería conduce y ejecuta, pero no decide", "Parte 2 · qué pasaría con respaldo en la alta dirección", '<div style="display:flex;gap:30px;align-items:stretch">' + pir + lista + "</div>" + '<div style="background:' + TINTA + ';border-radius:16px;padding:16px 26px"><p style="font-size:28px;font-weight:700;line-height:1.25;color:#FFFFFF">La profesión que produce el dato del cuidado no tiene silla donde se decide qué hacer con él.</p></div>',
    "Fuentes: Ley 27669, artículo 13; Decretos Supremos 008-2017-SA y 019-2025-SA; Reglamento de Organización y Funciones del Seguro Social de Salud. Los tres niveles: Parsons, según Thompson (1967); Anthony (1965); Mintzberg (1979).",
    "1:15. Toda organización tiene tres niveles: el que decide, el que conduce y el que ejecuta. Lo dicen Parsons, Anthony y Mintzberg con otros nombres. Enfermería está en dos. En el operativo, las 24 horas. En el táctico, por mandato de la Ley 27669, artículo 13: la Unidad Orgánica de Enfermería es órgano de línea, dependiente de la máxima instancia de dirección del establecimiento. "
    "Y en el estratégico, donde se decide oportunidad, calidad, seguridad y costos, no hay ningún órgano con nombre de enfermería: ni en el Ministerio de Salud, en sus reglamentos de 2017 y de 2025, ni en la Alta Dirección ni en las trece gerencias centrales del Seguro Social de Salud. Ojo: digo que no hay órgano; no digo que ninguna enfermera ocupe cargos. La profesión que produce el dato y sostiene el cuidado no tiene silla donde se decide qué hacer con él.")

# ---------------------------------------------------------------- 6. Los países
def chip(t, sub, color):
    return '<div style="background:#FFFFFF;border:2px solid %s;border-radius:14px;padding:12px 18px;display:flex;flex-direction:column;gap:4px"><p style="font-size:28px;font-weight:700;line-height:1.15;color:%s">%s</p><p style="font-size:26px;line-height:1.15;color:%s">%s</p></div>' % (color, TINTA, t, CUERPO, sub)


si = [("Chile", "Dirección Nacional de Enfermería"), ("Panamá", "Dirección Nacional de Enfermería"), ("El Salvador", "Dirección Nacional de Enfermería"), ("Argentina", "Dirección de Enfermería"),
      ("Paraguay", "Dirección de Enfermería"), ("Uruguay", "Unidad de Planificación y Desarrollo Estratégico en Enfermería")]
pi = caja(eti("Lo que reportan los países") + '<div style="display:flex;gap:14px;align-items:baseline">%s%s</div>' % (gran("82 %", BIEN, 110), tx("de los países que respondieron tiene jefatura de enfermería en el gobierno: 98 de 120.", TINTA, 600, 26, True)) +
          '<div style="display:flex;gap:14px;align-items:baseline">%s%s</div>' % (gran("86 %", A, 84), tx("en las Américas: 18 de 21.", TINTA, 600, 26, True)) +
          '<div style="border-top:1px solid %s;padding:12px 0px 0px">%s%s</div>' % (LINEA, eti("El Perú", MAL), tx("Reportó «No» en 2020. En 2025 no reportó.", TINTA, 700, 34)), flex="0 0 560px")
pd_ = caja(eti("Dentro del ministerio de salud, según fuente oficial abierta") + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">%s</div>' % "".join(chip(a, b, BIEN) for a, b in si) +
           tx("Sin órgano encontrado en el ministerio: Colombia, Brasil, Bolivia, Ecuador, Costa Rica, Honduras y el Perú.", TINTA, 600, 28) +
           tx("Tenerla no garantiza mejores indicadores. Es el lugar desde donde se decide.", MAL, 700, 28), pad="20px 24px")
out["paises"] = lam("paises", "Los países: la jefatura nacional de enfermería es el estándar", "Parte 2 · qué pasaría con respaldo en la alta dirección", '<div style="display:flex;gap:18px;align-items:stretch">' + pi + pd_ + "</div>",
    "Fuentes: Organización Mundial de la Salud, State of the world's nursing 2025, página 88 y perfiles de país 2020 y 2025; normas de organización de cada ministerio, abiertas y verificadas; la misma organización no halló correlación significativa (página 90).",
    "1:15. Revisé los 194 perfiles de país de la Organización Mundial de la Salud. De los 120 países que respondieron en 2025, 98 reportan una jefatura de enfermería en el gobierno: 82 por ciento. En las Américas, 18 de 21. El Perú reportó que no en 2020 y en 2025 no reportó. "
    "Con la norma abierta: Chile, Panamá y El Salvador tienen una Dirección Nacional de Enfermería dentro del ministerio; Argentina y Paraguay, una Dirección de Enfermería; Uruguay creó su unidad en enero de 2026. No la encontré en Colombia, Brasil, Bolivia, Ecuador, Costa Rica ni Honduras. "
    "Honestidad: tener la jefatura no garantiza mejores indicadores; la propia Organización Mundial de la Salud no halló correlación significativa, y mi análisis por grupo de ingreso tampoco. No vendo un resultado: señalo el lugar desde donde se decide. La Asamblea Mundial de la Salud, en su resolución 74.15 de 2021, exhorta a los Estados a establecer y fortalecer funciones de liderazgo superior para enfermería.")

# ---------------------------------------------------------------- 7. La ventana
def hito(fecha, tit, txt, color):
    return ('<div style="flex:1;min-width:0px;display:flex;flex-direction:column;gap:8px"><div style="display:flex;align-items:center;gap:0px"><div style="flex:none;width:26px;height:26px;border-radius:13px;background:%s"></div><div style="flex:1;height:4px;background:%s"></div></div>'
            '<p style="font-size:24px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:%s">%s</p><p style="font-size:32px;font-weight:700;line-height:1.15;color:%s">%s</p><p style="font-size:26px;line-height:1.25;color:%s">%s</p></div>') % (color, LINEA, color, fecha, TINTA, tit, CUERPO, txt)


linea = '<div style="display:flex;gap:14px;align-items:stretch">' + hito("2002", "Ley 27669", "Unidad Orgánica de Enfermería en todo establecimiento.", A) + hito("2020", "Propuesta del Colegio", "Una Dirección General de Enfermería en el Ministerio.", A) + \
    hito("8 de setiembre de 2026", "Reorganización", "Decreto Supremo 014-2026-SA: propuesta de nueva estructura orgánica en 90 días.", ORO) + hito("Octubre de 2026", "Datos e inteligencia artificial", "Prioridades del sector y lineamientos que exigen supervisión humana.", ORO) + \
    hito("7 de diciembre de 2026", "Vence el informe", "con la propuesta de nueva estructura del Ministerio.", MAL) + "</div>"
cierre = '<div style="display:flex;gap:18px;align-items:stretch">' + caja('<div style="display:flex;gap:18px;align-items:baseline">%s%s</div>' % (gran("56 días", MAL, 120), tx("quedan, desde hoy, para que la nueva estructura incluya a enfermería.", TINTA, 700, 30, True)), bg="#FBEFF5", borde="#E9BFD4", flex="0 0 760px") + \
    caja(tx("El Ministerio ya decidió reorganizarse y ya decidió gobernarse con datos. Falta decidir quién responde por el dato del cuidado.", TINTA, 700, 34)) + "</div>"
out["ventana"] = lam("ventana", "La ventana: la nueva estructura del Ministerio", "Parte 2 · qué pasaría con respaldo en la alta dirección", linea + cierre,
    "Fuentes: Ley 27669; Colegio de Enfermeros del Perú, informe técnico legal de 2020; Decreto Supremo 014-2026-SA; Resolución Suprema 289-2026-PCM; Resolución Ministerial 903-2026/MINSA. El 7 de diciembre y los 56 días son cálculo propio.",
    "1:00. Hay una ventana, y tiene fecha. El 8 de setiembre de 2026 el Decreto Supremo 014-2026-SA declaró al Ministerio en reorganización y pidió, en 90 días, un informe con la propuesta de una nueva estructura orgánica: eso vence el 7 de diciembre; la fecha es cálculo mío. Quedan 56 días. "
    "En octubre, dos normas firmadas por el Ministro nombran entre las prioridades del sector el uso estratégico de datos y la inteligencia artificial, y la Resolución Ministerial 903-2026 aprueba lineamientos que exigen supervisión humana. El Colegio propuso en 2020 una Dirección General de Enfermería. El Ministerio ya decidió reorganizarse y gobernarse con datos: falta decidir quién responde por el dato del cuidado.")

# ---------------------------------------------------------------- 8. Remate
def pedido(a_quien, color, items):
    return caja('<p style="font-size:24px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:%s">%s</p>' % (color, a_quien) + "".join(
        '<div style="display:flex;gap:12px;align-items:flex-start"><div style="flex:none;width:14px;height:14px;border-radius:7px;background:%s;margin:14px 0px 0px"></div><p style="flex:1;min-width:0px;font-size:34px;line-height:1.26;color:%s">%s</p></div>' % (color, TINTA, i) for i in items), pad="24px 26px", extra="border-top:8px solid %s" % color)


rem = '<div style="display:flex;gap:18px;align-items:stretch">' + pedido("Al Ministro", MAL, ["Una instancia de enfermería en la nueva estructura del Ministerio, antes del 7 de diciembre.", "Que el registro de enfermería sea dato estandarizado en la historia clínica electrónica.", "Un piloto medido: alerta con inteligencia artificial, supervisada, con enfermería al mando del cuidado."]) + \
    pedido("Al Congreso", A, ["Aprobar el texto sustitutorio que nombra la autonomía en la Ley 27669, con su frontera escrita.", "Fiscalizar el artículo 13: cuántos establecimientos tienen su Unidad Orgánica de Enfermería."]) + \
    pedido("A la profesión", BIEN, ["Medir y publicar lo que hacemos: indicadores sensibles al cuidado.", "Producir evidencia peruana: hoy casi toda viene de fuera.", "Decidir en nuestro campo y responder por lo que decidimos."]) + "</div>"
out["remate"] = lam("remate", "No pedimos un campo nuevo: pedimos decidir sobre el cuidado y responder por él", "Remate · tres pedidos", rem,
    "La autonomía ya está en el reglamento: el cuidado «se basa en el juicio crítico y ponderado de la enfermera(o)», que «asume plena responsabilidad» (Decreto Supremo 004-2002-SA, artículo 4).",
    "3:00. Cierro con tres pedidos. Al Ministro: una instancia de enfermería en la nueva estructura del Ministerio, antes del 7 de diciembre; que el registro de enfermería sea dato estandarizado en la historia clínica electrónica; y un piloto medido, con una alerta de inteligencia artificial supervisada y enfermería al mando del cuidado. "
    "Al Congreso: aprobar el texto sustitutorio de las proposiciones 91 y 159, que nombra la autonomía en la Ley 27669 con su frontera escrita, sin tocar los actos reservados a otras profesiones; y fiscalizar el artículo 13. A la profesión: medir, publicar y producir evidencia peruana. "
    "La autonomía no es un campo nuevo: el reglamento ya dice que el cuidado se basa en el juicio crítico y ponderado de la enfermera, que asume plena responsabilidad. Es autonomía dentro del equipo, no contra él: el Código de Ética manda cautelarla respetando las funciones de cada uno. Pedimos decidir sobre el cuidado y responder por él.")

# ---------------------------------------------------------------- 9. Fuentes
fu = [("El Ministro", "Panamericana Televisión, 9 de setiembre de 2026; Radio Programas del Perú, 7 de agosto de 2026; notas del Ministerio de Salud; Resolución Suprema 289-2026-PCM; Resolución Ministerial 903-2026/MINSA."),
      ("OCDE", "Data Explorer, tema Salud (sdmx.oecd.org): 86 flujos, 20 020 959 observaciones, descarga del 10 de octubre de 2026. Promedio simple de países miembros."),
      ("Países", "Organización Mundial de la Salud, State of the world's nursing 2025 y 388 perfiles de país; normas de organización de 26 ministerios."),
      ("Primer nivel", "Superintendencia Nacional de Salud, recursos por establecimiento, junio de 2025 a junio de 2026: 2 302 puestos I-1 que reportan."),
      ("Estudios", "Rossetti 2025 (Nature Medicine); Koontalay 2025; Kumar 2025; Shever 2011; Zhang 2022; Cochrane 2026."),
      ("Normas", "Ley 27669 y Decreto Supremo 004-2002-SA; Decretos Supremos 008-2017-SA, 019-2025-SA y 014-2026-SA; Ley 26842."),
      ("Caso propio", "Instituto Nacional Cardiovascular, postulación al Reconocimiento a la Gestión de Proyectos de Mejora 2016.")]
tabla = '<div style="display:flex;flex-direction:column;gap:8px">' + "".join('<div style="display:flex;gap:18px;align-items:baseline;border-bottom:1px solid %s;padding:0px 0px 8px"><p style="flex:none;width:210px;font-size:24px;font-weight:700;color:%s">%s</p><p style="flex:1;min-width:0px;font-size:24px;line-height:1.22;color:%s">%s</p></div>' % (LINEA, A, a, CUERPO, b) for a, b in fu) + "</div>"
out["fuentes"] = lam("fuentes", "Anexo: de dónde sale cada dato", "Respaldo · todo está en el tablero y en la base", tabla,
    "Detalle, enlaces y veredictos de los verificadores: carpeta del proyecto y repositorio github.com/carlosperez100/GEM_CEP.",
    "Respaldo. Cada cifra tiene su fuente abierta. Las afirmaciones pasaron por verificadores independientes: ninguna fue refutada; las que pidieron matiz se usan con la redacción corregida.", gap=14)

# ---------------------------------------------------------------- portada
po = io.open(SL / "portada.html", encoding="utf-8").read()
if "Ciencia, arte y disciplina</h1>" in po:
    shutil.copy2(SL / "portada.html", S / "portada_v20.html")
    po = po.replace("Ciencia, arte y disciplina</h1>", "Autonomía profesional de enfermería</h1>").replace("font-size:80px;font-weight:700;line-height:1.12", "font-size:68px;font-weight:700;line-height:1.12")
    po = po.replace("El aporte de la enfermería al paciente, a la sociedad y al Estado", "Datos, cuidado y decisión: lo que enfermería ya aporta y lo que el país gana si decide")
    io.open(SL / "portada.html", "w", encoding="utf-8").write(po)

for k, v in out.items():
    io.open(SL / (k + ".html"), "w", encoding="utf-8").write(v)
d = json.load(io.open(P / "deck.json", encoding="utf-8"))
d["title"] = "Panel I: autonomía, datos y decisión"
d["order"] = ["portada", "apertura", "presencia", "resultados", "eficiencia", "mapa3", "paises", "ventana", "remate", "fuentes", "gracias"]
d["sections"] = {"s1": {"description": "Apertura: datos, inteligencia artificial y control del cuidado", "start": "portada"},
                 "s2": {"description": "Parte 1: lo que enfermería ya aporta", "start": "presencia"},
                 "s3": {"description": "Parte 2: qué pasaría con respaldo en la alta dirección", "start": "mapa3"},
                 "s4": {"description": "Remate y respaldo", "start": "remate"}}
json.dump(d, io.open(P / "deck.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("láminas escritas:", list(out), "| orden:", d["order"])
