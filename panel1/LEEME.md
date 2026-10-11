# Panel I · Foro Nacional «Enfermería con voz y autonomía» (Congreso de la República, 12 de octubre de 2026)

Material de trabajo de Mg. Carlos Pérez Pérez. Regla del trabajo: nada se afirma sin fuente verificable; cada afirmación es CITA, DERIVACIÓN o JUICIO del autor.

| Carpeta | Contenido |
|---|---|
| `TABLERO_PANEL1.html` | Tablero visual con todo lo trabajado: estrategia, datos, gráficos y fuentes. Se abre en el navegador |
| `deck_fuentes/` | Fuentes del deck de nueve láminas (versión estratégica aprobada el 11 de octubre de 2026) |
| `documentos/` | Plan anterior, dossier de evidencia, artículos de la revisión y auditoría |
| `investigaciones/` | Cinco investigaciones: cada una con `afirmaciones.md` (afirmación, texto de la fuente, enlace, veredicto de los verificadores) y `sintesis.md` |
| `datos/ocde/` | El Perú frente a los 38 países miembros de la OCDE: 46 indicadores titulares, 1 540 series comparables, matriz de países y correlaciones |
| `datos/oms/` | Jefatura nacional de enfermería en el gobierno en 194 países (perfiles 2020 y 2025 de la Organización Mundial de la Salud), con su enlace de origen |
| `datos/primer_nivel/` | Quién está en los puestos de salud públicos de categoría I-1 (cálculo sobre datos abiertos de la Superintendencia Nacional de Salud) |
| `scripts/` | Programas que bajan, cargan y analizan los datos, y los que generan el tablero y el deck |

## Dónde están los datos crudos

No están en este repositorio por su tamaño. Viven en la base local `bases_pais` (PostgreSQL):

- esquema `ocde`: 20 020 959 observaciones de los 86 flujos de salud de la OCDE (`https://sdmx.oecd.org/public/rest`, agencia `OECD.ELS.HD`), 79 países o áreas. Vista de consulta `ref.ocde_salud`. Cargador: `scripts/cargar_ocde.py`.
- esquema `oms`: `oms.sown_perfil` (388 perfiles de país) y `oms.gho_obs` (siete indicadores del Observatorio Mundial de la Salud); `bm.pais` (grupo de ingreso del Banco Mundial). Vista `ref.oms_jefatura_enfermeria`. Cargador: `scripts/cargar_oms_sown.py`.

## Cuatro lecturas honestas

1. El Perú tiene 2.09 enfermeras profesionales por 1 000 habitantes; el promedio de la OCDE es 8.85 (lugar 32 de 33 países con dato, 2025).
2. La asociación entre más enfermería y mejores resultados entre países casi desaparece al descontar el gasto en salud: es asociación, no causa.
3. El 82 % de los países que respondieron a la Organización Mundial de la Salud reporta una jefatura nacional de enfermería; el Perú reportó «No» en 2020. Tenerla no se asocia con mejores indicadores.
4. De los 2 302 puestos de salud públicos I-1 que reportan recursos, el 88 % no reporta médico y en el 52 % hay enfermera y no hay médico.

No se publican aquí: documentos de terceros, datos de contacto ni la fotografía descartada por privacidad.
