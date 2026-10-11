# Quién está en los establecimientos públicos del primer nivel de atención (cálculo del analista principal)

Capa: DERIVACIÓN. Fuente de los datos: Superintendencia Nacional de Salud (SUSALUD), datos abiertos «Consulta de recursos de salud por IPRESS» (http://datos.susalud.gob.pe/dataset/consulta-recursos-de-salud-por-ipress), cargados en la base `bases_pais` (vista `ref.recurso_vigente`: último reporte de cada establecimiento, solo si es de los últimos 12 meses; periodos de junio de 2025 a junio de 2026). Padrón: Registro Nacional de Instituciones Prestadoras de Servicios de Salud (RENIPRESS), vista `ref.ipress`.

Método: se toma el último reporte vigente de cada establecimiento de categoría I-1, I-2, I-3 e I-4 de los sectores «GOBIERNO REGIONAL» y «MINSA». Médicos = médicos + médicos del Servicio Rural y Urbano Marginal de Salud + médicos residentes. Se cuenta cuántos establecimientos reportan al menos una enfermera, cuántos reportan cero médicos y cuántos reportan enfermera y cero médicos.

| Categoría (Ministerio de Salud y gobiernos regionales) | Reportaron | Con enfermera | Sin médico | Con enfermera y sin médico | Sin enfermera ni médico |
|---|---:|---:|---:|---:|---:|
| I-1 (puesto de salud) | 2 302 | 1 432 (62.2 %) | 2 021 (87.8 %) | 1 195 (51.9 %) | 826 (35.9 %) |
| I-2 | 1 156 | 1 021 (88.3 %) | 154 (13.3 %) | 59 (5.1 %) | 95 (8.2 %) |
| I-3 | 936 | 907 (96.9 %) | 37 (4.0 %) | 11 (1.2 %) | 26 (2.8 %) |
| I-4 | 239 | 234 (97.9 %) | 5 (2.1 %) | 0 | 5 (2.1 %) |
| Total primer nivel | 4 633 | 3 594 (77.6 %) | 2 217 (47.9 %) | 1 265 (27.3 %) | 952 (20.5 %) |

Frase segura: «De los 2 302 puestos de salud públicos de categoría I-1 que reportaron sus recursos a la Superintendencia Nacional de Salud en los últimos doce meses, 2 021 (88 %) no reportan médico; en 1 195 (52 %) hay enfermera y no hay médico».

Límites que deben decirse: (1) es lo que cada establecimiento reporta, no una verificación en campo; (2) el padrón registra 4 250 establecimientos públicos de categoría I-1 y solo 2 302 (54 %) reportaron recursos en los últimos doce meses: el resultado describe a los que reportan; (3) «sin enfermera ni médico» incluye puestos a cargo de obstetra o de técnico de enfermería; (4) el plan de conectividad del Ministerio habla de «postas» sin precisar categoría: la correspondencia con I-1 e I-2 es lectura del autor.

## Denominador del padrón (consulta `q2_padron.sql`, 11 de octubre de 2026)

El padrón registra 4 250 establecimientos de categoría I-1 del Ministerio de Salud y los gobiernos regionales: 4 233 de gobiernos regionales (2 de ellos en condición «inoperativo») y 17 del Ministerio de Salud. Son las mismas dos instituciones del cálculo anterior. De esos 4 250, reportaron recursos en los últimos doce meses 2 302; no tienen reporte 1 948 (45.8 %). Mide falta de reporte, no falta de recursos.
