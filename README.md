# gem_cep — Base OCDE·Salud por indicador, país y año

Base pública de **todos los conjuntos del tema Health de la OCDE**
(agencia `OECD.ELS.HD`, API SDMX `sdmx.oecd.org`), consolidada en un formato
único: un renglón por **indicador × país × año**. Sirve de marco de
comparación externo para **GEM·VigIA**: el Perú frente a Chile, Colombia,
México, Costa Rica, Brasil y Argentina.

**Página publicada:** `https://carlosperez100.github.io/gem_cep/`
(se activa con la primera corrida del workflow).

Es información pública de la OCDE. No contiene datos de SUSALUD ni de
pacientes.

## Qué hay

| Archivo | Contenido |
|---|---|
| `docs/index.html` | Publicación: método, flujos, cobertura por país, 16 indicadores clave con el Perú resaltado, catálogo buscable, descargas |
| `docs/base_ocde_salud.xlsx` | Excel: *Léeme*, *Catálogo*, *Base larga* y una hoja por flujo (indicador × país en filas, años en columnas) |
| `docs/base_larga.csv` | fuente · indicador · unidad · desglose · país · año · valor · estado |
| `docs/catalogo_indicadores.csv` | Un renglón por indicador con su cobertura (países, años, observaciones) |
| `docs/crudo/flujos.json` | Dataflows de `OECD.ELS.HD` el día de la descarga |
| `docs/registro.txt` | Registro completo de la corrida |

Última corrida: 86 flujos listados, 79 con datos, 1 853 indicadores,
7 países, 1960-2025, 140 022 observaciones.

## Cómo se construye

1. `ocde_salud_base.py` descubre los dataflows vigentes de la agencia (no
   usa una lista fija: la OCDE los renombra y versiona).
2. Baja cada flujo en CSV con etiquetas, pidiendo a la API solo los países
   de `--paises` (lee la estructura del flujo para ubicar `REF_AREA`).
3. Si la API rechaza una respuesta por tamaño, parte el rango de años por
   mitades. Si devuelve 429, espera lo que pida `Retry-After` o hasta 15 min.
4. Guarda el **total** de cada desglose (sexo, edad, proveedor…) para que
   un indicador sea una sola serie por país y año; si un desglose no tiene
   total, cada valor se vuelve un indicador aparte, con la etiqueta entre
   corchetes.
5. `publicar_ocde_salud.py` genera `docs/index.html` a partir de los CSV
   reales. Si un indicador clave no está en la base, su gráfico no aparece.

## Correrlo

En GitHub: pestaña **Actions → Actualizar Base OCDE·Salud → Run workflow**.
También corre solo el día 1 de cada mes. El workflow guarda los archivos en
`docs/` y despliega la página en GitHub Pages.

En local:

```bash
pip install -r requirements.txt
python -I ocde_salud_base.py --paises PER CHL COL MEX CRI BRA ARG OECD
python -I publicar_ocde_salud.py --paises PER CHL COL MEX CRI BRA ARG OECD --html docs/index.html
```

## Fuente y licencia de los datos

OECD Data Explorer, tema *Health* (<https://data-explorer.oecd.org>), bajo
las condiciones de uso de la OCDE.
