# -*- coding: utf-8 -*-
"""Deck del Panel I, versión científica y directa (aprobada el 11 de octubre de 2026):
una pregunta, cuatro resultados y una conclusión sobre la autonomía profesional de enfermería."""
import io, json, pathlib
S = pathlib.Path(__file__).resolve().parent
exec(io.open(S / "build_v21.py", encoding="utf-8").read())   # trae las funciones (lam, caja, eti, gran, tx, par, res…) y los colores
n = {}


def barra(t, sub=""):
    return ('<div style="display:flex;gap:18px;align-items:center;background:' + TINTA + ';border-radius:16px;padding:16px 26px"><p style="flex:1;min-width:0px;font-size:28px;font-weight:700;line-height:1.25;color:#FFFFFF">' + t +
            ('<span style="font-weight:400;color:#C9D7EA"> ' + sub + '</span>' if sub else "") + '</p></div>')


def cita(t, fuente, color=TINTA):
    return ('<p style="font-size:32px;font-weight:700;line-height:1.28;color:' + color + '">' + t + '</p><p style="font-size:24px;line-height:1.25;color:' + GRIS + '">' + fuente + '</p>')


def fila(a, b):
    return '<div style="display:flex;gap:18px;align-items:stretch">' + a + b + "</div>"


# ---------------------------------------------------------------- 1. Pregunta y definición
izq = ('<div style="flex:0 0 900px;min-width:0px;display:flex;flex-direction:column;gap:14px;background:' + TINTA + ';border-radius:20px;padding:28px 32px">'
       '<p style="font-size:24px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#7FB6E6">Lo que ya dice el reglamento</p>'
       '<p style="' + F + 'font-size:40px;font-weight:500;line-height:1.3;color:#FFFFFF">El cuidado integral de enfermería «se basa en el juicio crítico y ponderado de la enfermera(o) así como en la toma de decisiones que competen a su labor, por lo cual asume plena responsabilidad por los efectos y consecuencias que de ellas se originen».</p>'
       '<p style="font-size:24px;line-height:1.25;color:#C9D7EA">Decreto Supremo 004-2002-SA, reglamento de la Ley 27669, artículo 4</p></div>')


def nv(t, d, c):
    return ('<div style="background:' + PANEL + ';border:1px solid ' + LINEA + ';border-left:10px solid ' + c + ';border-radius:14px;padding:20px 24px;display:flex;flex-direction:column;gap:6px">'
            '<p style="font-size:36px;font-weight:700;line-height:1.15;color:' + TINTA + '">' + t + '</p><p style="font-size:28px;line-height:1.2;color:' + CUERPO + '">' + d + '</p></div>')


der = ('<div style="flex:1;min-width:0px;display:flex;flex-direction:column;gap:10px">' + eti("Tres niveles de autonomía · marco del autor", MAL) +
       nv("Clínica", "decide el cuidado del paciente", BIEN) + nv("Organizativa", "conduce su propio servicio", ORO) + nv("Estratégica", "participa donde se decide", MAL) + "</div>")
n["pregunta"] = lam("pregunta", "Autonomía: decidir en el propio campo y responder por lo decidido", "La pregunta", fila(izq, der) +
    barra("¿Tiene enfermería esa autonomía en el Perú, y qué pasa cuando la ejerce?", "Método: normas vigentes abiertas, ensayos aleatorizados y datos oficiales de 2023 a 2026."),
    "Fuente: Decreto Supremo 004-2002-SA, artículo 4. El reglamento no usa la palabra «autonomía»: llamar así a decidir y responder, y los tres niveles, son lectura del autor.",
    "1:00. Empiezo por un texto que no es mío: es del reglamento de nuestra ley. El cuidado de enfermería se basa en el juicio crítico y ponderado de la enfermera y en la toma de decisiones que competen a su labor, por lo cual asume plena responsabilidad. El reglamento no usa la palabra autonomía; yo llamo autonomía a eso: decidir en el propio campo y responder por lo decidido. "
    "Para ordenar la evidencia la miro en tres niveles, que son mi marco de trabajo: clínica, organizativa y estratégica. Mi pregunta es directa: ¿tiene enfermería esa autonomía en el Perú, y qué pasa cuando la ejerce? Respondo con normas vigentes, ensayos aleatorizados y datos oficiales.")

# ---------------------------------------------------------------- 2. Autonomía clínica, con frontera
campo = caja(eti("El campo propio", BIEN) + cita("El Proceso de Atención de Enfermería «incluye la valoración, el diagnóstico, la planificación, la ejecución y la evaluación» y «será registrado obligatoriamente en la historia clínica».", "Decreto Supremo 004-2002-SA, artículo 9, literal a") +
             cita("Al técnico y al auxiliar se les encomiendan actividades «que no implican toma de decisiones».", "El mismo artículo, literal b"), extra="border-top:8px solid " + BIEN, pad="24px 28px")
front = caja(eti("La frontera", MAL) + cita("«Sólo los médicos pueden prescribir medicamentos».", "Ley 26842, Ley General de Salud, artículo 26") +
             cita("El diagnóstico, la terapéutica y el pronóstico que realiza el médico «son de exclusivo ejercicio del profesional médico».", "Decreto Supremo 024-2001-SA, artículo 5"), extra="border-top:8px solid " + MAL, pad="24px 28px")
n["clinica"] = lam("clinica", "Autonomía clínica: el campo propio y su frontera ya están escritos", "Nivel clínico · delimitación de competencias", fila(campo, front) +
    barra("Dentro del equipo, no contra él:", "el Código de Ética manda «cautelar su autonomía profesional» respetando «las funciones que a cada uno le compete» (artículo 49)."),
    "Ni la Ley 27669 ni su reglamento usan la palabra «autonomía»: el reglamento describe su contenido y el Código de Ética y Deontología del Colegio de Enfermeros del Perú la nombra. La Proposición Legislativa 159 la nombra y mantiene la frontera; es propuesta, no norma.",
    "1:30. En el nivel clínico la autonomía ya está delimitada. El campo propio: el Proceso de Atención de Enfermería, que incluye valoración, diagnóstico, planificación, ejecución y evaluación, y que debe registrarse obligatoriamente en la historia clínica. El mismo artículo dice que al técnico y al auxiliar se les encomiendan actividades que no implican toma de decisiones: la decisión es de la enfermera. "
    "La frontera también está escrita: solo los médicos prescriben medicamentos, y el diagnóstico, la terapéutica y el pronóstico médicos son de su exclusivo ejercicio. La iniciativa del Colegio no propone moverla: la Proposición 159 dice que el diagnóstico de enfermería no comprende los diagnósticos ni los demás actos reservados por ley a otros profesionales; es propuesta, no norma. "
    "Y es autonomía dentro del equipo: el Código de Ética manda cautelarla respetando las funciones de cada uno. Lo que falta es que la ley la llame por su nombre.")

# ---------------------------------------------------------------- 3. Resultado 1
fila3 = '<div style="display:flex;gap:16px;align-items:stretch">' + res("1.03", "Mortalidad cuando enfermeras asumen tareas habitualmente médicas: poca o ninguna diferencia", "Cochrane, 2026 · 82 ensayos · 28 041 personas · intervalo 0.87 a 1.21", A) + \
    res("0.69", "Reingresos por cualquier causa en insuficiencia cardiaca con transición dirigida por enfermeras", "Koontalay, 2025 · metaanálisis · intervalo 0.54 a 0.89") + \
    res("0.56", "Muerte a tres meses en ictus con enfermera de ictus en el equipo: asociación", "Kumar, 2025 · 8 estudios · razón de momios · intervalo 0.37 a 0.85") + \
    res("−0.68", "Diferencia de medias en hemoglobina glicosilada en diabetes con cuidado dirigido por enfermeras", "Zhang, 2022 · 13 ensayos · 3 757 personas") + "</div>"
n["resultados"] = lam("resultados", "Resultado 1: en ensayos de otros países, cuando la enfermera asume más, el paciente no pierde", "Nivel clínico · evidencia de resultado", fila3 +
    barra("Cómo leerlo:", "1 es igual; menos de 1 es menos riesgo. Son estudios de otros países; asumir tareas no equivale a autonomía: es la evidencia más cercana disponible."),
    "Fuentes: revisión Cochrane de 2026 (hospitales); Koontalay 2025, Kumar 2025 y Zhang 2022, con su enlace en PubMed. Razones de riesgo o de momios; diferencia de medias en hemoglobina glicosilada.",
    "1:45. Primer resultado. La pregunta que hace todo médico es si el paciente pierde. La revisión Cochrane de 2026 reunió 82 ensayos aleatorizados en hospitales, con 28 041 participantes: cuando enfermeras asumen tareas habitualmente médicas, la mortalidad probablemente no cambia; razón de riesgos 1.03, intervalo de 0.87 a 1.21, certeza moderada. El paciente no pierde. "
    "Y en su campo hay indicios de que gana: transición del hospital a la casa dirigida por enfermeras, 31 por ciento menos reingresos por cualquier causa en insuficiencia cardiaca; enfermera de ictus en el equipo, asociada a menos muertes a tres meses, razón de momios 0.56 en ocho estudios, y es asociación; cuidado dirigido por enfermeras en diabetes, diferencia de medias de menos 0.68 en hemoglobina glicosilada en 13 ensayos. "
    "Límite que declaro: son estudios de otros países, y asumir tareas con protocolo no es lo mismo que autonomía. No hay un estudio peruano que mida autonomía y resultados clínicos.")


# ---------------------------------------------------------------- 4. Resultado 2: la pirámide
def niv2(ancho, color, nombre, verbo):
    return ('<div style="width:%dpx;height:170px;background:%s;clip-path:polygon(%dpx 0px, %dpx 0px, 100%% 100%%, 0px 100%%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px">'
            '<p style="font-size:30px;font-weight:700;color:#FFFFFF">%s</p><p style="font-size:26px;color:#FFFFFF">%s</p></div>') % (ancho, color, 72, ancho - 72, nombre, verbo)


def fil2(estado, color, donde, que):
    return ('<div style="display:flex;gap:16px;align-items:center;background:' + PANEL + ';border:1px solid ' + LINEA + ';border-left:10px solid ' + color + ';border-radius:14px;padding:10px 22px;height:170px">'
            '<p style="flex:none;width:170px;font-size:24px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:' + color + '">' + estado + '</p>'
            '<div style="flex:1;display:flex;flex-direction:column;gap:6px;min-width:0px"><p style="font-size:30px;font-weight:700;line-height:1.15;color:' + TINTA + '">' + donde + '</p><p style="font-size:24px;line-height:1.22;color:' + CUERPO + '">' + que + '</p></div></div>')


pir2 = '<div style="flex:0 0 560px;display:flex;flex-direction:column;align-items:center;gap:6px;justify-content:center">' + niv2(270, MAL, "Estratégico", "decide") + niv2(414, ORO, "Táctico", "conduce") + niv2(558, BIEN, "Operativo", "cuida") + "</div>"
lis2 = '<div style="flex:1;min-width:0px;display:flex;flex-direction:column;gap:6px;justify-content:center">' + \
    fil2("Sin órgano", MAL, "Seguro Social: perfiles que piden médico", "Gerente de Red Prestacional y Director del Instituto Nacional Cardiovascular (perfil de 2024) requieren «Médico Cirujano». Ministerio: sin órgano de enfermería, aunque su clasificador admite a la enfermera como directora.") + \
    fil2("Presente por ley", ORO, "Unidad Orgánica de Enfermería", "Órgano de línea por mandato de la Ley 27669, artículo 13. Cuántos establecimientos la tienen: sin dato nacional.") + \
    fil2("Presente", BIEN, "48 990 enfermeras", "36.8 % de los profesionales de la salud y 138 por cada 100 médicos, entre 279 712 trabajadores del Ministerio de Salud y los gobiernos regionales (2023). Además, 82 748 técnicos asistenciales.") + "</div>"
n["piramide"] = lam("piramide", "Resultado 2: a mayor nivel de gestión, menos enfermería", "Lectura del autor sobre normas y datos · órgano propio donde se cuida y se conduce, no donde se decide", '<div style="display:flex;gap:30px;align-items:stretch">' + pir2 + lis2 + "</div>" +
    barra("No existe un registro nacional de cargos directivos por profesión."),
    "Fuentes: Ministerio de Salud, Información de Recursos Humanos en el Sector Salud, Perú 2023; Ley 27669, artículo 13; Manual de Perfiles de Puestos del Seguro Social de Salud (Resolución de Presidencia Ejecutiva 925-PE-ESSALUD-2024); Decreto Supremo 008-2017-SA.",
    "1:45. Segundo resultado: dónde está enfermería en la organización. En la base, donde se cuida: 48 990 enfermeras en el Ministerio de Salud y los gobiernos regionales; son el 36.8 por ciento de los profesionales de la salud y 138 por cada 100 médicos, junto a 82 748 técnicos asistenciales. "
    "En el medio, donde se conduce: la ley manda una Unidad Orgánica de Enfermería como órgano de línea en todo establecimiento; cuántos la tienen, no hay dato nacional. "
    "Arriba, donde se decide: en el Ministerio no hay ningún órgano con nombre de enfermería, y en el Seguro Social de Salud el perfil de 2024 del Gerente de Red Prestacional y el del Director del Instituto Nacional Cardiovascular, cargo que desde julio de 2026 se denomina Gerente, requieren título profesional de médico cirujano. Precisión: en el Ministerio el clasificador de cargos sí admite a la enfermera como directora; lo que no existe es un registro de cuántas lo son. No afirmo que arriba solo haya médicos: afirmo que no hay órgano, que hay perfiles que la excluyen y que nadie lo mide.", gap=14)

# ---------------------------------------------------------------- 5. Resultado 3: el Perú frente al mundo
ocde = caja(eti("Frente a los países de la OCDE") + par("Enfermeras profesionales por 1 000 habitantes", 2.09, 8.85, 9.5, "lugar 32 de 33") +
            par("Ingreso anual de una enfermera de hospital, en dólares comparables", 31253, 67428, 72000, "último de 37", 0) +
            par("Gasto en salud, porcentaje del producto bruto interno", 5.4, 9.3, 9.5, "lugar 38 de 39", 1, " %") +
            tx("Promedio simple de los países miembros con dato, 2024 y 2025.", GRIS, 400, 24), pad="22px 26px")
oms = caja(eti("Jefatura de enfermería en el gobierno") + '<div style="display:flex;gap:16px;align-items:baseline">' + gran("82 %", BIEN, 110) + tx("de los países que respondieron la declara: 98 de 120 (informe, página 88).", TINTA, 600, 28, True) + "</div>" +
           tx("En el perfil de 2020 el Perú figura con «No»; en el de 2025, sin respuesta.", TINTA, 700, 32) +
           tx("Con un órgano de enfermería creado por norma en su ministerio, de rangos distintos: Chile, Panamá, El Salvador, Argentina, Paraguay y Uruguay.", CUERPO, 400, 26) +
           tx("Tenerla no se asoció con mejor regulación ni protección laboral: es gobernanza, no resultado.", MAL, 700, 26), flex="0 0 700px", pad="22px 26px")
n["mundo"] = lam("mundo", "Resultado 3: menos enfermeras, menor ingreso y sin órgano de enfermería en el Ministerio", "Nivel estratégico · el Perú frente al mundo", fila(ocde, oms),
    "Fuentes: Organización para la Cooperación y el Desarrollo Económicos (OCDE), Data Explorer, tema Salud; Organización Mundial de la Salud, State of the world's nursing 2025, página 88, y perfiles de país 2020 y 2025; normas de cada ministerio.",
    "1:15. Tercer resultado: la comparación. En la OCDE, a la que el país quiere ingresar, el promedio es 8.85 enfermeras profesionales por 1 000 habitantes; el Perú tiene 2.09: solo un país miembro tiene menos. Una enfermera de hospital gana aquí 31 253 dólares comparables al año contra 67 428: el valor más bajo de los 37 países con dato. "
    "Y en el gobierno: de los 120 países que respondieron a la Organización Mundial de la Salud, 98 reportan una jefatura nacional de enfermería, 82 por ciento. El Perú figura con que no en el perfil de 2020 y sin respuesta en el de 2025. Chile, Panamá, El Salvador, Argentina, Paraguay y Uruguay tienen un órgano de enfermería creado por norma en su ministerio, de rangos distintos. "
    "Honestidad: el informe de la Organización Mundial de la Salud no halló correlación significativa entre tener ese cargo y mejor regulación educativa o mejores protecciones laborales; y en mi comparación descriptiva de países tampoco vi mejores indicadores. No es un resultado: es gobernanza.")

# ---------------------------------------------------------------- 6. Resultado 4: autonomía con datos
citas2 = "".join('<p style="%sfont-size:36px;font-weight:600;line-height:1.1;color:#FFFFFF;white-space:nowrap">%s</p>%s' % (F, c, ('<p style="font-size:34px;color:#7FB6E6">→</p>' if i < 2 else "")) for i, c in enumerate(["«controlar todo el sistema»", "«con esa data»", "«empezar a hacer gestión»"]))
min2 = '<div style="display:flex;gap:22px;align-items:center;background:' + TINTA + ';border-radius:18px;padding:20px 28px"><p style="flex:none;width:190px;font-size:24px;line-height:1.25;color:#C9D7EA">El Ministro de Salud, en televisión:</p>' + citas2 + "</div>"
tres = '<div style="display:flex;gap:18px;align-items:stretch">' + \
    caja(eti("El registro ya es obligatorio") + gran("18 → 1", ORO, 60) + tx("formatos: 97.7 minutos menos de registro por paciente en 24 horas; ahorro valorizado en S/ 2 009 550 al año.", TINTA, 600, 24) + tx("Instituto Nacional Cardiovascular, 2015. Antes y después, sin grupo de control.", GRIS, 400, 24), pad="16px 24px") + \
    caja(eti("Con inteligencia artificial") + gran("0.64", ORO, 60) + tx("razón de riesgos de muerte hospitalaria con una alerta que lee el registro de enfermería, mostrada a todo el equipo.", TINTA, 600, 24) + tx("Ensayo en Estados Unidos; intervalo 0.53 a 0.78. No es evidencia sobre el Perú.", GRIS, 400, 24), pad="16px 24px") + \
    caja(eti("Sola en el primer nivel") + gran("52 %", ORO, 60) + tx("de los 2 302 puestos de salud públicos I-1 que reportaron tiene enfermera y no reporta médico.", TINTA, 600, 24) + tx("Reportó el 54 % del padrón; el 88 % no reporta médico. Lectura del autor.", GRIS, 400, 24), pad="16px 24px") + "</div>"
n["datos"] = lam("datos", "Resultado 4: el registro de enfermería puede ser la data que la gestión necesita", "Propuesta del autor · datos e inteligencia artificial", min2 + tx("Lo dijo en condicional, sobre hospitales y centros de salud, y no mencionó a enfermería: el vínculo con el registro de enfermería es del autor.", GRIS, 400, 24) + tres +
    barra("Propuesta del autor:", "que ese registro sea dato estandarizado y que enfermería responda por él."),
    "Fuentes: Panamericana Televisión, «Esta Noche», nota del 9 de setiembre de 2026 (transcripción del canal); Instituto Nacional Cardiovascular, 2016; Rossetti, Nature Medicine, 2025; Superintendencia Nacional de Salud, 2026 (cálculo propio).",
    "1:15. Cuarto resultado. El Ministro dijo en televisión que, si se interconecta y se empieza a controlar todo el sistema, con esa data se puede empezar a hacer gestión. Lo dijo de hospitales y centros de salud; no habló de enfermería. Yo completo la frase con tres datos. "
    "Uno: el registro del cuidado ya es obligatorio, y cuando enfermería lo estandarizó en el Instituto Nacional Cardiovascular pasó de 18 formatos a uno, liberó 97.7 minutos por paciente al día y la institución valorizó el ahorro en 2 009 550 soles en un año; es un estudio de antes y después, sin grupo de control. "
    "Dos: en Estados Unidos, un ensayo aleatorizado con una alerta de inteligencia artificial que lee el registro de enfermería mostrada a todo el equipo, halló menor riesgo de muerte hospitalaria, razón de riesgos 0.64, con más traslados a cuidados intensivos; otro ensayo, sin respuesta obligatoria, no halló cambio. No es evidencia sobre el Perú. "
    "Tres: en el 52 por ciento de los puestos de salud públicos que reportan se reporta enfermera y no se reporta médico: ahí la enfermera decide sin médico presente; si eso es autonomía ejercida o solo ausencia de médico, nadie lo ha medido, y es mi lectura. Mi propuesta, como juicio profesional: que ese registro sea dato estandarizado y que enfermería responda por él.", gap=14)


# ---------------------------------------------------------------- 7. Límites y conclusión
def lista(items, color):
    return "".join('<div style="display:flex;gap:12px;align-items:flex-start"><div style="flex:none;width:14px;height:14px;border-radius:7px;background:' + color + ';margin:15px 0px 0px"></div><p style="flex:1;min-width:0px;font-size:34px;line-height:1.28;color:' + TINTA + '">' + i + '</p></div>' for i in items)


def numerada(items):
    return "".join('<div style="display:flex;gap:16px;align-items:flex-start"><p style="flex:none;width:56px;' + F + 'font-size:64px;font-weight:600;line-height:1;color:' + BIEN + '">' + str(k) + '</p><p style="flex:1;min-width:0px;font-size:38px;font-weight:700;line-height:1.24;color:' + TINTA + '">' + i + '</p></div>' for k, i in enumerate(items, 1))


lim = caja(eti("Lo que estos datos no prueban", MAL) + lista(["Los ensayos son de otros países: no hay estudio peruano.", "Asociación no es causa.", "La jefatura nacional no se asocia con mejores indicadores.", "No hay registro de cuántas enfermeras dirigen."], MAL), flex="0 0 640px", pad="30px 30px", extra="border-top:8px solid " + MAL)
con = caja(eti("Conclusión", BIEN) + numerada(["El contenido de la autonomía clínica ya está en la norma; en ensayos de otros países, ejercerla no perjudicó al paciente.", "En la norma llega hasta el nivel táctico: arriba no hay órgano de enfermería ni registro de quién dirige.", "Falta nombrarla en la ley, darle lugar en la estructura y medirla en el Perú."]), pad="30px 30px", extra="border-top:8px solid " + BIEN)
n["limites"] = lam("limites", "Límites y conclusión", "Lo que se puede afirmar y lo que no", fila(lim, con),
    "Las cifras y las citas de esta presentación fueron contrastadas con su fuente por verificadores independientes; los títulos y las propuestas son lectura del autor.",
    "1:15. Antes de concluir, los límites, para que los diga yo y no el público. Los ensayos son de otros países. Varias cifras muestran asociación, no causa. Tener una jefatura nacional no se asocia con mejores indicadores. Y no existe un registro de cuántas enfermeras ocupan cargos directivos. "
    "Con esos límites, la conclusión es tres frases. Uno: el contenido de la autonomía clínica ya está en la norma, y en ensayos de otros países ejercerla no perjudicó al paciente. Dos: en la norma llega hasta el nivel táctico; arriba no hay órgano de enfermería ni registro de quién dirige. Tres: falta nombrarla en la ley, darle lugar en la estructura y medirla en el Perú.")

# ---------------------------------------------------------------- remate: tres pedidos (aparte, 3 minutos)
rem2 = '<div style="display:flex;gap:18px;align-items:stretch">' + pedido("Al Congreso", A, ["Nombrar la autonomía en la Ley 27669, con su frontera escrita, como propone la Proposición Legislativa 159.", "Fiscalizar el artículo 13: cuántos establecimientos tienen su Unidad Orgánica de Enfermería."]) + \
    pedido("Al Ministro", MAL, ["Una instancia de enfermería en la propuesta de nueva estructura del Ministerio, que vence hacia el 7 de diciembre.", "Que el registro de enfermería sea dato estandarizado en la historia clínica electrónica."]) + \
    pedido("A la profesión", BIEN, ["Medir y publicar lo que hacemos.", "Producir evidencia peruana: hoy casi toda viene de fuera.", "Decidir en nuestro campo y responder por lo que decidimos."]) + "</div>"
n["remate"] = lam("remate", "No pedimos un campo nuevo: pedimos decidir sobre el cuidado y responder por él", "Remate · tres pedidos", rem2,
    "El Ministerio está en reorganización (Decreto Supremo 014-2026-SA): el informe con la propuesta de nueva estructura vence hacia el 7 de diciembre de 2026 (90 días calendario; la fecha es cálculo propio).",
    "3:00. Remate, con tres pedidos. Al Congreso, que es donde estamos: nombrar la autonomía en la Ley 27669, con su frontera escrita, como propone la Proposición 159, iniciativa del Colegio. La Comisión de Trabajo aprobó el 30 de setiembre un texto sustitutorio de las proposiciones 91 y 159; su dictamen no estaba publicado cuando preparé esta presentación y no afirmo su contenido: pido que conserve el nombre y la frontera. Y fiscalizar el artículo 13. "
    "Al Ministro: una instancia de enfermería en la propuesta de nueva estructura del Ministerio, que debe presentarse hacia el 7 de diciembre; quedan menos de dos meses. Y que el registro de enfermería sea dato estandarizado en la historia clínica electrónica. "
    "A la profesión: medir, publicar y producir evidencia peruana; decidir en nuestro campo y responder por lo que decidimos. No pedimos un campo nuevo: el reglamento ya dice que decidimos y respondemos. Pedimos que la ley lo llame por su nombre.")

# ---------------------------------------------------------------- fuentes
fu2 = [("Autonomía", "Ley 27669 y Decreto Supremo 004-2002-SA, artículos 4 y 9; Ley 26842, artículo 26; Decreto Supremo 024-2001-SA, artículo 5; Código de Ética y Deontología, artículo 49."),
       ("Resultados", "Cochrane 2026 (82 ensayos); Koontalay 2025; Kumar 2025; Zhang 2022; Rossetti 2025 (Nature Medicine)."),
       ("Pirámide", "Ministerio de Salud, Información de Recursos Humanos en el Sector Salud, Perú 2023; Manual de Perfiles de Puestos del Seguro Social de Salud, 2024."),
       ("OCDE", "Data Explorer, tema Salud (sdmx.oecd.org): 86 flujos, 20 020 959 observaciones, descarga del 10 de octubre de 2026."),
       ("Países", "Organización Mundial de la Salud, State of the world's nursing 2025 y 388 perfiles de país; normas de organización de 26 ministerios."),
       ("Primer nivel", "Superintendencia Nacional de Salud, recursos por establecimiento, junio de 2025 a junio de 2026: 2 302 puestos I-1 que reportan."),
       ("Caso propio", "Instituto Nacional Cardiovascular, postulación al Reconocimiento a la Gestión de Proyectos de Mejora 2016.")]
tabla2 = '<div style="display:flex;flex-direction:column;gap:8px">' + "".join('<div style="display:flex;gap:18px;align-items:baseline;border-bottom:1px solid ' + LINEA + ';padding:0px 0px 8px"><p style="flex:none;width:210px;font-size:24px;font-weight:700;color:' + A + '">' + a + '</p><p style="flex:1;min-width:0px;font-size:24px;line-height:1.22;color:' + CUERPO + '">' + b + '</p></div>' for a, b in fu2) + "</div>"
n["fuentes"] = lam("fuentes", "Anexo: de dónde sale cada dato", "Respaldo", tabla2, "Detalle, enlaces y veredictos de los verificadores: repositorio github.com/carlosperez100/GEM_CEP, carpeta panel1.",
                   "Respaldo. Cada cifra tiene su fuente abierta.", gap=14)

for k, v in n.items():
    io.open(SL / (k + ".html"), "w", encoding="utf-8").write(v)
po = io.open(SL / "portada.html", encoding="utf-8").read()
viejo = "Datos, cuidado y decisión: lo que enfermería ya aporta y lo que el país gana si decide"
if viejo in po:
    po = po.replace(viejo, "Qué dice la norma, qué muestran los datos y qué falta decidir")
    io.open(SL / "portada.html", "w", encoding="utf-8").write(po)
d = json.load(io.open(P / "deck.json", encoding="utf-8"))
d["title"] = "Panel I: autonomía profesional de enfermería"
d["order"] = ["portada", "pregunta", "clinica", "resultados", "piramide", "mundo", "datos", "limites", "remate", "fuentes", "gracias"]
d["sections"] = {"s1": {"description": "La pregunta y la autonomía clínica", "start": "portada"},
                 "s2": {"description": "Cuatro resultados", "start": "resultados"},
                 "s3": {"description": "Límites, conclusión y remate", "start": "limites"},
                 "s4": {"description": "Respaldo", "start": "fuentes"}}
json.dump(d, io.open(P / "deck.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("v22:", list(n), "| orden:", d["order"])
