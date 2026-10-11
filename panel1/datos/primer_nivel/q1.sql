with v as (
  select r.*, coalesce(medicos,0)+coalesce(medicos_serum,0)+coalesce(medicos_residentes,0) as med
  from ref.recurso_vigente r
  where vigente and categoria in ('I-1','I-2','I-3','I-4')
)
select sector, categoria,
       count(*) as reportan,
       sum((coalesce(enfermeras,0) > 0)::int) as con_enfermera,
       sum((med = 0)::int) as sin_medico,
       sum((coalesce(enfermeras,0) > 0 and med = 0)::int) as enfermera_sin_medico,
       sum((coalesce(enfermeras,0) = 0 and med = 0)::int) as sin_enfermera_ni_medico,
       sum(coalesce(enfermeras,0)) as enfermeras, sum(med) as medicos,
       max(periodo) as ultimo_periodo, min(periodo) as periodo_min
from v group by rollup (sector, categoria) order by 1, 2
