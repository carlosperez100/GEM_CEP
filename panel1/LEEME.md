# Panel I · Foro Nacional «Enfermería con voz y autonomía» (Congreso de la República, 12 de octubre de 2026)

Material de trabajo de Carlos Pérez Pérez. Regla del trabajo: nada se afirma sin fuente verificable; cada afirmación es cita, derivación o juicio del autor, y va rotulada.

**La presentación completa, con guion, fuentes con enlace y datos, está en una sola página: <https://carlosperez100.github.io/GEM_CEP/panel1/>.** La portada del repositorio ([`README.md`](../README.md)) trae el resumen, la lista de láminas y las 26 fuentes con su enlace.

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
