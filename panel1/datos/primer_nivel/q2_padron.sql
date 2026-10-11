-- Padrón de puestos de salud de categoría I-1 (Registro Nacional de Instituciones Prestadoras de Servicios de Salud),
-- por institución. Denominador de «1 948 de 4 250 sin reporte de recursos en doce meses».
-- Resultado del 11 de octubre de 2026: gobiernos regionales 4 233 (2 de ellos inoperativos) + Ministerio de Salud 17 = 4 250.
select sector, institucion, condicion, count(*) as establecimientos
from ref.ipress
where categoria = 'I-1'
group by 1, 2, 3
order by establecimientos desc;
