# -*- coding: utf-8 -*-
# Genera la portada del repositorio (README.md) y el indice de la carpeta panel1 (LEEME.md)
# a partir de lo mismo que usa la pagina publica: resumen.json (tomado de las laminas) y fuentes_enlaces.json.
# Uso: python -I gen_readme.py <carpeta_del_repositorio>
import io, json, pathlib, sys

AQUI = pathlib.Path(__file__).resolve().parent
S = AQUI.parent
REPO_DIR = pathlib.Path(sys.argv[1])
PAGINA = "https://carlosperez100.github.io/GEM_CEP/panel1/"
BASE_OCDE = "https://carlosperez100.github.io/GEM_CEP/"
VERSION = "11 de octubre de 2026"

R = json.loads((AQUI / "resumen.json").read_text(encoding="utf-8"))
fe = S / "fuentes_enlaces.json"
FUENTES = json.loads(fe.read_text(encoding="utf-8")) if fe.exists() else []


import re
URL_RE = re.compile(r"https?://[^\s<>»]+")


def limpia(u):
    return u.replace("[", "%5B").replace("]", "%5D").replace("(", "%28").replace(")", "%29")


def celda(t):
    return t.replace("|", "\\|").replace("\n", " ").strip()


def tabla_fuentes(prefijo_uso=True):
    filas = ["| Fuente | Dónde se usa | Enlace |", "|---|---|---|"]
    for f in FUENTES:
        url = (f.get("url") or "").strip()
        enlace = "[abrir](%s)" % limpia(url) if url else "sin enlace público confirmado"
        nota = URL_RE.sub(lambda m: "[enlace](%s)" % limpia(m.group(0).rstrip(".,;:)")), (f.get("nota") or "").strip())
        t = f["fuente"].strip()
        i = t.find("Proposición Legislativa 00091")
        nombre = celda(t[i:] if i > 0 else t) + ((" — " + celda(nota)) if nota else "")
        filas.append("| %s | %s | %s |" % (nombre, celda(R["uso"].get(str(f["n"]), "")), enlace))
    return "\n".join(filas)


def lista(items, num=False):
    return "\n".join(("%d. %s" % (i, t) if num else "- %s" % t) for i, t in enumerate(items, 1))


resultados = "\n".join("%d. **%s.** %s *(%s)*" % (i, r["cab"], r["texto"], r["capa"]) for i, r in enumerate(R["resultados"], 1))
pedidos = "\n".join("- **%s:** %s" % (g["a"], " ".join(g["items"])) for g in R["pedidos"])
laminas = "\n".join("| %d | %s | [ver](%s#l-%s) |" % (l["n"], celda(l["titulo"]), PAGINA, l["id"]) for l in R["laminas"])

README = """# Autonomía profesional de enfermería · Panel I

Material público de **Carlos Pérez Pérez** para el Panel I del Foro Nacional «Enfermería con voz y autonomía» (Congreso de la República del Perú, 12 de octubre de 2026): la presentación, su guion, cada fuente con su enlace, los datos y los programas con que se hizo. Incluye la base de salud de la Organización para la Cooperación y el Desarrollo Económicos (OCDE) con que se compara al Perú.

> Página personal del autor. No es una publicación oficial del Colegio de Enfermeros del Perú, del Congreso de la República ni del Ministerio de Salud, y no expresa la posición de ninguno de ellos. Las láminas usan la plantilla institucional del Colegio, con la que se expone en el foro: su sello no significa aval. Versión del {version}.

## Empiece aquí

| Qué | Dónde |
|---|---|
| **La presentación completa en una sola página**: {n_laminas} láminas, guion, fuentes con enlace y datos | **<{pagina}>** |
| Base OCDE · Salud por indicador, país y año (el Perú y seis países de la región) | <{base}> |
| Figura «El recorrido del paciente» (3840 × 2160) | [abrir]({pagina}figuras/recorrido_paciente_gestion_del_cuidado.png) |
| Figura «Tres brechas» (3840 × 2160) | [abrir]({pagina}figuras/tres_brechas_enfermeria.png) |
| Veredictos por afirmación | [`panel1/investigaciones/`](panel1/investigaciones) |
| Datos | [`panel1/datos/`](panel1/datos) |

## La presentación en una página

**La pregunta.** {pregunta} {metodo}

**Cuatro resultados**

{resultados}

**Lo que estos datos no prueban**

{no_prueban}

**Conclusión**

{conclusion}

**Tres pedidos del autor**

{pedidos}

El texto de esta sección está tomado literalmente de las láminas.

## Las láminas

| Lámina | Título | En la página |
|---|---|---|
{laminas}

Las láminas 1 a 8 son la exposición (diez minutos), la 9 es el remate (tres minutos) de la 10 a la 12 son respaldo y la 13 es el cierre.

## Cómo leer cada afirmación

| Capa | Qué es | Cómo va rotulada |
|---|---|---|
| **Cita** | La fuente lo dice | Con su documento y, si lo tiene, su artículo o página; los estudios, con autor y año |
| **Derivación** | Cálculo, conteo o lectura propia de un texto | «cálculo propio», «lectura propia» o «búsqueda propia» |
| **Juicio del autor** | Lectura, marco, síntesis o propuesta | Con las palabras «del autor» |

Las cifras y las citas se contrastaron con el documento original de cada fuente mediante verificadores automáticos: agentes de inteligencia artificial que debían abrir cada documento antes de dar un veredicto. Los veredictos están en [`panel1/investigaciones/`](panel1/investigaciones); la responsabilidad del contenido es del autor.

{seccion_fuentes}
## Mapa del repositorio

| Carpeta o archivo | Contenido |
|---|---|
| [`docs/panel1/`](docs/panel1) | La página pública (`index.html`, un solo archivo) y las dos figuras en alta definición |
| [`panel1/deck_fuentes/`](panel1/deck_fuentes) | Las láminas en HTML tal como están publicadas (`slides/`) y su orden (`deck.json`). La portada no se versiona porque lleva datos de contacto |
| [`panel1/figuras/`](panel1/figuras) | Figuras en alta definición y su fuente en HTML |
| [`panel1/investigaciones/`](panel1/investigaciones) | Una carpeta por tema: `autonomia`, `tres_niveles`, `paises_direccion_enfermeria`, `primera_lamina_datos_ia`, `agenda_ministro`, `auditoria_deck` y `laminas_de_respaldo`. Cada una trae la afirmación, el texto de la fuente, el enlace y el veredicto. `laminas_de_respaldo` trae además la lista de fuentes con su enlace (`fuentes_enlaces.json`) |
| [`panel1/datos/ocde/`](panel1/datos/ocde) | El Perú frente a los países miembros: `ocde_titulares.csv` (46 indicadores), `ocde_peru_vs_ocde.csv` (1 540 series comparables), `ocde_matriz_paises.csv` (62 países) y `ocde_correlaciones.csv` (90 pares) |
| [`panel1/datos/oms/`](panel1/datos/oms) | Jefatura nacional de enfermería según la Organización Mundial de la Salud: `sown_perfil.csv` (388 perfiles de país de 2020 y 2025, con el enlace de cada uno), `oms_jefatura_enfermeria_paises.csv` (194 países), `oms_jefatura_resumen.csv`, `oms_jefatura_indicadores.csv` y `bm_pais.csv` (grupo de ingreso del Banco Mundial) |
| [`panel1/datos/primer_nivel/`](panel1/datos/primer_nivel) | Quién está en los puestos de salud de categoría I-1 del Ministerio de Salud y los gobiernos regionales: consultas (`q1.sql`, `q2_padron.sql`) y tabla con sus límites (`primer_nivel_datos.md`) |
| [`panel1/documentos/`](panel1/documentos) | Artículos de la revisión bibliográfica |
| [`panel1/scripts/`](panel1/scripts) | Programas que bajan, cargan y analizan los datos, y los que generan las dos láminas de respaldo, la página pública (`pagina/`) y esta portada |
| [`docs/`](docs) | Publicación de la base OCDE · Salud (`index.html`, Excel y archivos de datos) |
| `ocde_salud_base.py`, `publicar_ocde_salud.py` | Programas de la base OCDE · Salud |

### Lo que no está aquí

- **Datos crudos.** Por su tamaño viven en una base local (PostgreSQL, `bases_pais`): 20 020 959 observaciones de los 86 flujos de salud de la OCDE y los 388 perfiles de país de la Organización Mundial de la Salud. Los cargadores están en `panel1/scripts/` (`cargar_ocde.py`, `cargar_oms_sown.py`).
- **Material interno de trabajo, documentos de terceros, datos de contacto y archivos exportados de la presentación.** No se publican.

## Base OCDE · Salud

Base de **todos los conjuntos del tema Salud de la OCDE** (agencia `OECD.ELS.HD`, interfaz de datos `sdmx.oecd.org`), consolidada en un formato único: un renglón por **indicador × país × año**. Compara al Perú con Chile, Colombia, México, Costa Rica, Brasil y Argentina. Es información pública de la OCDE: no contiene datos de pacientes.

| Archivo | Contenido |
|---|---|
| [`docs/index.html`](docs/index.html) | Publicación: método, flujos, cobertura por país, 16 indicadores clave con el Perú resaltado, catálogo buscable y descargas |
| [`docs/base_ocde_salud.xlsx`](docs/base_ocde_salud.xlsx) | Excel: Léeme, Catálogo, Base larga y una hoja por flujo (indicador × país en filas, años en columnas) |
| [`docs/base_larga.csv`](docs/base_larga.csv) | fuente · indicador · unidad · desglose · país · año · valor · estado |
| [`docs/catalogo_indicadores.csv`](docs/catalogo_indicadores.csv) | Un renglón por indicador con su cobertura (países, años, observaciones) |
| [`docs/crudo/flujos.json`](docs/crudo/flujos.json) | Flujos de `OECD.ELS.HD` el día de la descarga |
| [`docs/registro.txt`](docs/registro.txt) | Registro completo de la corrida |

Última corrida: 86 flujos listados, 79 con datos, 1 853 indicadores, 7 países, 1960-2025, 140 022 observaciones.

**Cómo se construye**

1. `ocde_salud_base.py` descubre los flujos vigentes de la agencia (no usa una lista fija: la OCDE los renombra y versiona).
2. Baja cada flujo con etiquetas, pidiendo solo los países de `--paises`.
3. Si la interfaz rechaza una respuesta por tamaño, parte el rango de años por mitades. Si devuelve el código 429, espera lo que pida `Retry-After` o hasta 15 minutos.
4. Guarda el total de cada desglose (sexo, edad, proveedor) para que un indicador sea una sola serie por país y año; si un desglose no tiene total, cada valor se vuelve un indicador aparte, con la etiqueta entre corchetes.
5. `publicar_ocde_salud.py` genera `docs/index.html` a partir de los archivos reales. Si un indicador clave no está en la base, su gráfico no aparece.

**Correrlo.** En GitHub: pestaña *Actions*, flujo «Actualizar Base OCDE·Salud», botón *Run workflow*. También corre solo el día 1 de cada mes. En local:

```bash
pip install -r requirements.txt
python -I ocde_salud_base.py --paises PER CHL COL MEX CRI BRA ARG OECD
python -I publicar_ocde_salud.py --paises PER CHL COL MEX CRI BRA ARG OECD --html docs/index.html
```

**Fuente de los datos.** Explorador de datos de la OCDE, tema Salud (<https://data-explorer.oecd.org>), bajo las condiciones de uso de la OCDE.

## Créditos

Los íconos de las figuras provienen de Tabler Icons (licencia MIT). La plantilla gráfica de las láminas es la del foro.
""".format(
    version=VERSION, pagina=PAGINA, base=BASE_OCDE, n_laminas=len(R["laminas"]),
    pregunta=R["pregunta"], metodo=R["metodo"], resultados=resultados,
    no_prueban=lista(R["no_prueban"]), conclusion=lista(R["conclusion"], True), pedidos=pedidos,
    laminas=laminas, seccion_fuentes=("## Fuentes con enlace\n\n" + tabla_fuentes() + "\n") if FUENTES else "")

LEEME = """# Panel I · Foro Nacional «Enfermería con voz y autonomía» (Congreso de la República, 12 de octubre de 2026)

Material de trabajo de Carlos Pérez Pérez. Regla del trabajo: nada se afirma sin fuente verificable; cada afirmación es cita, derivación o juicio del autor, y va rotulada.

**La presentación completa, con guion, fuentes con enlace y datos, está en una sola página: <{pagina}>.** La portada del repositorio ([`README.md`](../README.md)) trae el resumen, la lista de láminas y las {n_fuentes} fuentes con su enlace.

| Carpeta | Contenido |
|---|---|
| [`deck_fuentes/`](deck_fuentes) | Las láminas en HTML tal como están publicadas (`slides/`, sin la portada, que lleva datos de contacto) y su orden (`deck.json`) |
| [`figuras/`](figuras) | «El recorrido del paciente» y «Tres brechas» en 3840 × 2160, con su fuente en HTML |
| [`investigaciones/`](investigaciones) | Una carpeta por tema, con la afirmación, el texto de la fuente, el enlace y el veredicto de los verificadores. `laminas_de_respaldo/` trae la verificación de las dos láminas de respaldo y la lista de fuentes con su enlace |
| [`datos/ocde/`](datos/ocde) | El Perú frente a los países miembros de la Organización para la Cooperación y el Desarrollo Económicos: 46 indicadores titulares, 1 540 series comparables, matriz de 62 países y 90 correlaciones |
| [`datos/oms/`](datos/oms) | Jefatura nacional de enfermería en 194 países (388 perfiles de 2020 y 2025 de la Organización Mundial de la Salud), con el enlace de cada perfil |
| [`datos/primer_nivel/`](datos/primer_nivel) | Quién está en los puestos de salud de categoría I-1 del Ministerio de Salud y los gobiernos regionales (cálculo sobre datos abiertos de la Superintendencia Nacional de Salud), con las dos consultas |
| [`documentos/`](documentos) | Artículos de la revisión bibliográfica |
| [`scripts/`](scripts) | Programas que bajan, cargan y analizan los datos, y los que generan las dos láminas de respaldo, la página pública (`pagina/`) y la portada del repositorio |

## Dónde están los datos crudos

No están en este repositorio por su tamaño. Viven en la base local `bases_pais` (PostgreSQL):

- esquema `ocde`: 20 020 959 observaciones de los 86 flujos de salud de la Organización para la Cooperación y el Desarrollo Económicos (`https://sdmx.oecd.org/public/rest`, agencia `OECD.ELS.HD`), 79 países o áreas. Vista de consulta `ref.ocde_salud`. Cargador: `scripts/cargar_ocde.py`.
- esquema `oms`: `oms.sown_perfil` (388 perfiles de país) y `oms.gho_obs` (siete indicadores del Observatorio Mundial de la Salud); `bm.pais` (grupo de ingreso del Banco Mundial). Vista `ref.oms_jefatura_enfermeria`. Cargador: `scripts/cargar_oms_sown.py`.

No se publican aquí: material interno de trabajo, documentos de terceros ni datos de contacto.
""".format(pagina=PAGINA, n_laminas=len(R["laminas"]), n_fuentes=len(FUENTES))

(REPO_DIR / "README.md").write_text(README, encoding="utf-8", newline="\n")
(REPO_DIR / "panel1" / "LEEME.md").write_text(LEEME, encoding="utf-8", newline="\n")
print("ok README.md", len(README), "· LEEME.md", len(LEEME), "· fuentes", len(FUENTES))
