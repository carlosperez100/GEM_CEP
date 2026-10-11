# -*- coding: utf-8 -*-
# Construye las dos laminas de respaldo: recorrido del paciente y tres brechas.
# Mismo marco de plantilla que el resto del deck (banda, pie, notas).
# Redaccion ajustada a la verificacion del 11 de octubre de 2026 (carpeta investigaciones/laminas_de_respaldo).
import io, re, pathlib

S = pathlib.Path(__file__).resolve().parent
SL = S / "deck-panel1" / "project" / "slides"
if not SL.exists():  # dentro del repositorio
    SL = S.parent / "deck_fuentes" / "slides"
IC = S / "iconos"

TINTA, AZ, ORO, BIEN, MAL = "#0B1D36", "#0070C0", "#B07A10", "#0B6E55", "#9A2A63"
PANEL, LINEA, CUERPO, GRIS = "#F3F6FA", "#D5DEE9", "#2A3B55", "#55657D"
F = "font-family:'Fraunces', Georgia, serif;"


def icono(nombre, lado, color, grosor=1.7):
    """SVG en linea a partir del trazo del icono (Tabler Icons, licencia MIT). Sin <text>."""
    src = io.open(IC / (nombre + ".svg"), encoding="utf-8").read()
    ds = [d for d in re.findall(r'<path[^>]*\sd="([^"]+)"', src) if d != "M0 0h24v24H0z"]
    paths = "".join('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/>' % (d, color, grosor) for d in ds)
    return ('<svg aria-hidden="true" viewBox="0 0 24 24" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg" '
            'style="flex:none;width:%dpx;height:%dpx">%s</svg>') % (lado, lado, lado, lado, paths)


def lam(id, titulo, kicker, cuerpo, pie, notas, gap=18):
    return ('<section id="%s" data-transition="fade" style="background:#FFFFFF;color:%s;font-family:Arial, Helvetica, sans-serif;padding:222px 128px 200px;display:flex;flex-direction:column;gap:%dpx">\n'
            '<img src="/_blob/49486cf8087824f7aeba26166eb4df35" alt="" style="position:absolute;left:0px;top:0px;width:1920px;height:1080px;object-fit:cover">\n'
            '<div data-banda="1" style="position:absolute;left:196px;top:22px;width:1600px;height:176px;display:flex;flex-direction:column;justify-content:center"><h2 style="font-family:Arial, Helvetica, sans-serif;font-size:56px;font-weight:700;line-height:1.1;color:#FDFDFD">%s</h2></div>\n'
            '<p style="font-size:24px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:%s">%s</p>\n'
            '%s\n'
            '<p style="position:absolute;left:128px;right:128px;bottom:96px;font-size:24px;line-height:1.25;color:%s">%s</p>\n'
            '<aside>%s</aside>\n</section>\n') % (id, TINTA, gap, titulo, AZ, kicker, cuerpo, GRIS, pie, notas)


# ---------------------------------------------------------------- recorrido
def estacion(nombre, ico, hogar=False):
    borde, fondo, trazo = ("#8A99AE", PANEL, GRIS) if hogar else (AZ, "#E6F1FB", "#005A9C")
    return ('<div style="flex:1;min-width:0px;display:flex;flex-direction:column;align-items:center;gap:12px">'
            '<div style="flex:none;width:136px;height:136px;border-radius:68px;background:%s;border:5px solid %s;display:flex;align-items:center;justify-content:center">%s</div>'
            '<p style="font-size:26px;font-weight:700;line-height:1.15;text-align:center;white-space:nowrap;color:%s">%s</p></div>') % (fondo, borde, icono(ico, 76, trazo), TINTA, nombre)


SEP = ('<div style="flex:none;width:30px;height:136px;display:flex;align-items:center;justify-content:center">'
       '<svg aria-hidden="true" viewBox="0 0 24 48" width="20" height="40" xmlns="http://www.w3.org/2000/svg" style="flex:none;width:20px;height:40px"><path d="M4 4 L20 24 L4 44" fill="none" stroke="#8A99AE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')

ests = [("Hogar", "home", True), ("Atención<br>prehospitalaria", "ambulance", False), ("Emergencia", "urgent", False),
        ("Centro<br>quirúrgico", "cut", False), ("Cuidados<br>intensivos", "heart-rate-monitor", False),
        ("Hospitalización", "bed", False), ("Consulta<br>externa", "stethoscope", False), ("Hogar", "home", True)]
linea = '<div style="display:flex;align-items:flex-start">' + SEP.join(estacion(n, i, h) for n, i, h in ests) + "</div>"

gestion = ('<div style="display:flex;align-items:center;justify-content:center;gap:18px;background:#FBEFF5;border:4px dashed %s;border-radius:18px;padding:14px 26px">'
           '%s<p style="font-size:30px;font-weight:700;line-height:1.2;white-space:nowrap;color:#7A1F4E">Gestión del cuidado: el proceso que debería conducir el recorrido</p>'
           '<p style="flex:none;font-size:24px;font-weight:700;line-height:1.2;white-space:nowrap;background:%s;color:#FFFFFF;border-radius:999px;padding:6px 20px">no figura en la Ley 27669</p></div>') % (MAL, icono("route", 44, "#7A1F4E", 1.9), MAL)
baja = '<div style="display:flex;justify-content:center;height:34px">%s</div>' % icono("arrow-down", 34, MAL, 2.2)
enf = ('<div style="display:flex;align-items:center;justify-content:center;gap:18px;background:%s;border-radius:18px;padding:16px 26px">'
       '%s<p style="font-size:34px;font-weight:700;line-height:1.2;white-space:nowrap;color:#FFFFFF">Enfermería: presente las 24 horas, en todo el recorrido'
       '<span style="font-size:24px;font-weight:400;color:#CDEBE2"> · lectura del autor</span></p></div>') % (BIEN, icono("nurse", 48, "#FFFFFF", 1.8))
sop = ('<div style="display:flex;align-items:center;justify-content:center;gap:16px;border:3px dashed #B9C8D8;border-radius:18px;padding:12px 26px">'
       '%s<p style="font-size:26px;line-height:1.2;white-space:nowrap;color:%s">36 unidades de soporte: patología clínica, diagnóstico por imágenes, farmacia, banco de sangre y 32 más</p></div>') % (icono("microscope", 40, GRIS, 1.8), CUERPO)

recorrido = lam(
    "recorrido",
    "El recorrido del paciente: dónde está enfermería",
    "Respaldo · elaboración del autor sobre la Norma Técnica de Salud 249",
    gestion + baja + linea + enf + sop,
    "Fuentes: Norma Técnica de Salud 249 (Resolución Ministerial 625-2026/MINSA), Anexo 04: 8 unidades de atención directa, de las que se muestran 6, y 36 de soporte (conteo propio). "
    "La expresión «gestión del cuidado» no aparece en la Ley 27669 ni en su reglamento (búsqueda propia). "
    "Chappel y colaboradores (2017) dicen, como contexto, que las enfermeras están presentes las 24 horas del día. El orden del recorrido y el proceso propuesto son del autor.",
    "Respaldo, 0:30. El recorrido del paciente, del hogar al hogar: atención prehospitalaria, emergencia, centro quirúrgico, cuidados intensivos, hospitalización y consulta externa. "
    "Son seis de las ocho unidades de atención directa de la Norma Técnica de Salud 249; las otras dos son centro obstétrico y docencia e investigación, y la norma lista 36 de soporte. "
    "Enfermería está en todo el recorrido: es mi lectura, no un dato de la norma, que lista unidades y no personal. Una revisión sistemática dice, como contexto, que las enfermeras están presentes las 24 horas del día. "
    "Mi propuesta, como juicio profesional: que un proceso conduzca todo el recorrido, la gestión del cuidado. La expresión «gestión del cuidado» no figura en la Ley 27669 ni en su reglamento; sí aparece en normas del Colegio de Enfermeros del Perú y en guías técnicas institucionales. "
    "El orden de las estaciones y el proceso propuesto son elaboración mía, no de la norma.",
    gap=14)

# ------------------------------------------------------------------ brechas
def tarjeta(color, ico, titulo, numero, texto, hay, falta, a, b, nota):
    return ('<div style="flex:1;min-width:0px;display:flex;flex-direction:column;gap:8px;background:%s;border:1px solid %s;border-radius:20px;padding:14px 24px;border-top:8px solid %s">'
            '<div style="display:flex;gap:14px;align-items:center"><div style="flex:none;width:64px;height:64px;border-radius:32px;background:%s;display:flex;align-items:center;justify-content:center">%s</div>'
            '<p style="flex:1;min-width:0px;font-size:30px;font-weight:700;line-height:1.12;color:%s">%s</p></div>'
            '<p style="%sfont-size:60px;font-weight:600;line-height:1;white-space:nowrap;color:%s">%s</p>'
            '<p style="font-size:24px;font-weight:600;line-height:1.28;color:%s">%s</p>'
            '<div style="display:flex;height:46px">'
            '<div style="flex:%d 1 0px;min-width:0px;background:%s;border-radius:12px 0px 0px 12px;display:flex;align-items:center;justify-content:center"><p style="font-size:24px;font-weight:700;line-height:1;white-space:nowrap;color:#FFFFFF">%s</p></div>'
            '<div style="flex:%d 1 0px;min-width:0px;background:#FFFFFF;border:3px dashed %s;border-radius:0px 12px 12px 0px;display:flex;align-items:center;justify-content:center"><p style="font-size:24px;font-weight:700;line-height:1;white-space:nowrap;color:%s">%s</p></div>'
            '</div>'
            '<p style="font-size:24px;font-weight:400;line-height:1.28;color:%s">%s</p></div>') % (
        PANEL, LINEA, color, color, icono(ico, 38, "#FFFFFF", 1.9), TINTA, titulo, F, color, numero, TINTA, texto,
        a, AZ, hay, b, color, color, falta, GRIS, nota)


fila = '<div style="display:flex;gap:18px;align-items:stretch">' + \
    tarjeta(ORO, "wifi-off", "Brecha digital", "42 a 43 %",
            "de los establecimientos de salud no tiene conexión a internet, según declaró el Ministro de Salud.",
            "con conexión", "sin conexión", 57, 43,
            "Declaración oral del 8 de setiembre de 2026, no una estadística publicada. En agosto había dicho 54 % de los establecimientos que administra el Ministerio.") + \
    tarjeta(MAL, "sitemap", "Brecha de toma de decisiones", "82 %",
            "de los países que respondieron reporta un jefe nacional de enfermería o cargo equivalente: 98 de 120; el resto respondió «no» o «parcial».",
            "82 % sí", "18 %", 82, 18,
            "El Perú no está entre los 120: «No» en 2020 y «no reportado» en 2025. En el reglamento de su Ministerio de Salud no figura un órgano de enfermería (lectura propia).") + \
    tarjeta("#005A9C", "database-off", "Brecha de información", "46 %",
            "de los puestos de salud de categoría I-1 del Ministerio de Salud y los gobiernos regionales no tiene reporte de recursos en doce meses: 1 948 de 4 250.",
            "reporta", "no reporta", 54, 46,
            "No se halló una estadística pública de cuántos cargos directivos ocupa enfermería.") + "</div>"

cierre = ('<div style="display:flex;gap:18px;align-items:center;background:%s;border-radius:16px;padding:16px 26px">'
          '<p style="flex:1;min-width:0px;font-size:28px;font-weight:700;line-height:1.25;color:#FFFFFF">Propuesta del autor:'
          '<span style="font-weight:400;color:#C9D7EA"> nombrar la gestión del cuidado en la ley y medirla, frente a las tres brechas.</span></p></div>') % TINTA

brechas = lam(
    "brechas",
    "Tres brechas: digital, de toma de decisiones y de información",
    "Respaldo · síntesis del autor, con un dato por brecha · las cifras no se suman",
    fila + cierre,
    "Fuentes: Agencia Peruana de Noticias Andina, 8 de setiembre de 2026, y diario Gestión, 6 de agosto de 2026; Organización Mundial de la Salud, State of the world's nursing 2025, página 88, y perfiles del Perú de 2020 y 2025; "
    "Decretos Supremos 008-2017-SA, 011-2017-SA y 019-2025-SA; Superintendencia Nacional de Salud, junio de 2025 a junio de 2026 (cálculo propio).",
    "Respaldo, 0:30. Tres brechas, que son mi marco para ordenar los resultados, con un dato cada una. "
    "Digital: el Ministro declaró ante la Comisión de Salud de la Cámara de Diputados que entre 42 y 43 por ciento de los establecimientos de salud no tiene conexión a internet. Un mes antes había dicho 54 por ciento de los establecimientos que administra el Ministerio: son declaraciones orales, no estadísticas publicadas, y por eso presento la cifra como declaración. "
    "De toma de decisiones: 98 de los 120 países que respondieron a la Organización Mundial de la Salud reportan un jefe nacional de enfermería o un cargo equivalente, con datos de 2018 a 2023; el resto respondió que no o que parcialmente. El Perú no está entre los 120: figuró con un «No» en el perfil de 2020 y como «no reportado» en el de 2025. "
    "En el Reglamento de Organización y Funciones del Ministerio de Salud no figura ningún órgano ni unidad orgánica de enfermería, y tampoco en la Sección Primera del reglamento aprobado en 2025: es lectura mía de esos textos; sus hospitales e institutos sí tienen departamento de enfermería. "
    "De información: de los 4 250 puestos de salud de categoría I-1 del Ministerio de Salud y los gobiernos regionales que figuran en el padrón, 1 948 no tienen reporte de recursos en doce meses, 46 por ciento; mide falta de reporte, no falta de recursos, y es cálculo mío. "
    "Tampoco hallé una estadística pública de cuántos cargos directivos ocupa enfermería; el registro nacional de establecimientos muestra, uno por uno, el colegio profesional del responsable, pero no publica la suma. "
    "Las tres cifras miden cosas distintas y no se suman. Mi propuesta: nombrar la gestión del cuidado en la ley y medirla.",
    gap=16)

for nombre, html in (("recorrido", recorrido), ("brechas", brechas)):
    assert "<text" not in html
    io.open(SL / (nombre + ".html"), "w", encoding="utf-8", newline="\n").write(html)
    print("ok", nombre, len(html))
