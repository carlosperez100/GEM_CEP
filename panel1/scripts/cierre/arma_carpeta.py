# -*- coding: utf-8 -*-
"""Arma la carpeta T:\\CEP\\panel1 con todo lo trabajado para el Panel I:
investigaciones (afirmaciones con su veredicto y su fuente, y síntesis), datos y programas.
También deja en scratchpad/tablero los JSON que consume gen_tablero.py."""
import io, json, pathlib, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
S = HERE.parent
W = pathlib.Path(r"C:\Users\infor\.claude\projects\C--Users-infor-OneDrive-CARLOS-PEREZ-UNIVERSIDADES-CEP-FORO\a76ee289-0d5f-426a-becc-af42c47fbeaf\subagents\workflows")
FORO = pathlib.Path(r"C:\Users\infor\OneDrive\CARLOS PEREZ\UNIVERSIDADES\CEP\FORO")
DEST = pathlib.Path(r"T:\CEP\panel1")
TAB = S / "tablero"
CIERRE = "wf_fc5b28c9-7e7"

TEMAS = {
    "aut": ("autonomia", "Cómo demostrar la autonomía de enfermería frente al equipo de salud", "wf_38f4707e-7f7"),
    "niv": ("tres_niveles", "Fundamento teórico de los niveles estratégico, táctico y operativo, y dónde está enfermería", "wf_3884fa8e-c1a"),
    "pais": ("paises_direccion_enfermeria", "Países con dirección o jefatura nacional de enfermería en su ministerio de salud", "wf_af7968f2-36b"),
    "ia": ("primera_lamina_datos_ia", "Sustento de la primera lámina: datos, inteligencia artificial y control del cuidado", "wf_5056b99a-e5d"),
    "ag": ("agenda_ministro", "Agenda de conectividad del Ministro de Salud y puente con enfermería", "wf_49d40803-a26"),
}


def journal(run):
    lab, res = {}, {}
    p = W / run / "journal.jsonl"
    if not p.exists():
        return res
    for l in io.open(p, encoding="utf-8"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("type") == "started":
            lab[d["key"]] = d.get("label")
        elif d.get("type") == "result":
            res[lab.get(d["key"], "?")] = d.get("result")
    return res


def estado(votos):
    if not votos:
        return "SIN_VERIFICAR"
    ref = sum(1 for v in votos if v.get("verdict") == "REFUTADA")
    if ref * 2 > len(votos):
        return "REFUTADA"
    if ref or any(v.get("verdict") == "MATIZAR" for v in votos):
        return "MATIZAR"
    return "CONFIRMADA"


def md(v, nivel=2):
    """Convierte un dict o lista en Markdown legible."""
    out = []
    if isinstance(v, dict):
        for k, x in v.items():
            if isinstance(x, (dict, list)):
                out.append("\n%s %s\n" % ("#" * min(nivel, 5), k))
                out.append(md(x, nivel + 1))
            else:
                out.append("- **%s:** %s" % (k, x))
    elif isinstance(v, list):
        for x in v:
            if isinstance(x, dict):
                partes = ["**%s:** %s" % (k, y if not isinstance(y, (dict, list)) else json.dumps(y, ensure_ascii=False)) for k, y in x.items()]
                out.append("- " + "\n  ".join(partes) + "\n")
            else:
                out.append("- %s" % x)
    else:
        out.append(str(v))
    return "\n".join(out)


cie = journal(CIERRE)
nuevos_v = {k.split("verif:", 1)[1]: v for k, v in cie.items() if k.startswith("verif:") and isinstance(v, dict)}
sint = {"niv": cie.get("sintesis:mapa"), "pais": cie.get("sintesis:paises"), "ia": cie.get("sintesis:primera_lamina"), "ag": cie.get("sintesis:agenda_y_puente")}
aut = journal("wf_38f4707e-7f7").get("critico:vacios")
sint["aut"] = aut

resumen = {}
for corto, (carpeta, titulo, run) in TEMAS.items():
    d = DEST / "investigaciones" / carpeta
    d.mkdir(parents=True, exist_ok=True)
    claims = json.load(io.open(HERE / ("claims_%s.json" % corto), encoding="utf-8"))
    # afirmaciones halladas en el cierre (solo agenda): se agregan
    if corto == "ag":
        for etq, r in cie.items():
            if etq.startswith("buscar:") and isinstance(r, dict):
                ang = etq.split(":", 1)[1]
                for i, c in enumerate(r.get("claims", []), 1):
                    claims.append({"id": "ag:%s#%d" % (ang, i), "angle": ang, "n": i, "status": "PENDIENTE", "votos": 0, "claim": c, "corrected": [], "notes": [], "evidence": []})
    cuenta = {}
    for c in claims:
        v = nuevos_v.get(c["id"])
        if c["status"] == "PENDIENTE":
            if v:
                c["status"] = estado([v])
                c["votos"] = 1
                if v.get("corrected") and len(v["corrected"]) > 15:
                    c["corrected"] = [v["corrected"]]
                c["notes"] = ["%s: %s" % (v.get("verdict"), v.get("note", ""))]
                c["evidence"] = [v.get("evidence", "")]
                c["enlace"] = v.get("sourceUrl", "")
            else:
                c["status"] = "SIN_VERIFICAR"
        cuenta[c["status"]] = cuenta.get(c["status"], 0) + 1
    json.dump(claims, io.open(d / "afirmaciones.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with io.open(d / "afirmaciones.md", "w", encoding="utf-8") as f:
        f.write("# %s\n\nAfirmaciones halladas por los buscadores, con el veredicto de los verificadores. Capas: CITA (la fuente lo dice), DERIVACION (se sigue de premisas citadas), JUICIO (criterio del autor).\n\n" % titulo)
        f.write("Resumen: %s.\n\n" % ", ".join("%s %d" % (k, n) for k, n in sorted(cuenta.items())))
        f.write("Regla de uso: solo las CONFIRMADA y las MATIZAR (con su redacción corregida) pueden pasar a un documento. Las REFUTADA y las SIN_VERIFICAR no.\n\n")
        for c in claims:
            k = c["claim"]
            f.write("## [%s#%d] %s · %s\n\n" % (c["angle"], c["n"], c["status"], k.get("layer", "")))
            if c["corrected"]:
                f.write("**Redacción segura (corregida por los verificadores):** %s\n\n" % c["corrected"][0])
                f.write("Redacción original del buscador: %s\n\n" % k.get("statement"))
            else:
                f.write("%s\n\n" % k.get("statement"))
            f.write("- **Texto de la fuente:** %s\n- **Fuente:** %s\n- **Dónde:** %s\n" % ((k.get("literal") or "").replace("\n", " "), k.get("source"), k.get("locator")))
            if c.get("enlace"):
                f.write("- **Enlace para comprobar:** %s\n" % c["enlace"])
            f.write("- **Límites:** %s\n- **Verificadores (%d):** %s\n\n" % (k.get("limits"), c["votos"], " | ".join(c["notes"]) or "sin verificación"))
    if sint.get(corto):
        json.dump(sint[corto], io.open(d / "sintesis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        io.open(d / "sintesis.md", "w", encoding="utf-8").write("# %s — síntesis\n\nElaborada solo con las afirmaciones verificadas de este tema.\n\n%s\n" % (titulo, md(sint[corto])))
    resumen[corto] = {"carpeta": carpeta, "titulo": titulo, "afirmaciones": len(claims), "estado": cuenta, "sintesis": bool(sint.get(corto))}

# resumen pegado (agenda): votos originales
ext = json.load(io.open(HERE / "extras_ag.json", encoding="utf-8"))
json.dump(ext, io.open(DEST / "investigaciones" / "agenda_ministro" / "verificacion_del_resumen_pegado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with io.open(DEST / "investigaciones" / "agenda_ministro" / "verificacion_del_resumen_pegado.md", "w", encoding="utf-8") as f:
    f.write("# Verificación del resumen pegado sobre la agenda de conectividad del Ministro de Salud\n\nCada afirmación del resumen fue abierta en sus páginas originales por dos verificadores.\n\n")
    for k, v in ext.items():
        if not isinstance(v, dict):
            continue
        f.write("## %s · %s\n\n- **Quién lo dice:** %s\n- **Fecha:** %s\n- **Texto de la fuente:** %s\n- **Frase segura:** %s\n- **Nota:** %s\n- **Páginas abiertas:** %s\n\n" % (
            k.replace("pegado:", ""), v.get("verdict"), v.get("whoSaysIt"), v.get("date"), v.get("literal"), v.get("corrected"), v.get("note"), " ; ".join(v.get("opened") or [])))

# JSON para el tablero
TAB.mkdir(exist_ok=True)
for corto, nombre in (("niv", "niveles.json"), ("pais", "paises.json"), ("ia", "primera.json"), ("ag", "agenda.json"), ("aut", "autonomia_critica.json")):
    if sint.get(corto):
        json.dump(sint[corto], io.open(TAB / nombre, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(resumen, io.open(TAB / "investigaciones_resumen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# datos
for sub, origen, nombres in (
    ("datos/ocde", S / "ocde" / "salidas_pg", ["ocde_titulares.csv", "ocde_peru_vs_ocde.csv", "ocde_correlaciones.csv", "ocde_matriz_paises.csv", "oms_jefatura_enfermeria_paises.csv", "oms_jefatura_resumen.csv", "oms_jefatura_indicadores.csv"]),
    ("datos/primer_nivel", HERE, ["primer_nivel_datos.md"]),
    ("datos/primer_nivel", S / "ocde", ["q1.sql"]),
    ("scripts", S / "ocde", ["cargar_ocde.py", "cargar_oms_sown.py", "analisis_ocde.py", "titulares.py", "correlaciones.py", "analisis_oms.py", "descarga_ocde.py"]),
    ("scripts/tablero", TAB, ["gen_tablero.py", "tablero.css", "arma_datos.py"]),
    ("scripts/cierre", HERE, ["cierre_prep.py", "arma_carpeta.py"]),
):
    (DEST / sub).mkdir(parents=True, exist_ok=True)
    for n in nombres:
        if (origen / n).exists():
            destino = DEST / sub / n
            if n.startswith("oms_"):
                destino = DEST / "datos" / "oms" / n
                destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen / n, destino)
        else:
            print("  falta", origen / n)
for n in ("sown_perfil.csv", "bm_pais.csv"):
    p = pathlib.Path(r"T:\BASES SISOL\pais\descargas\oms_sown") / n
    if p.exists():
        (DEST / "datos" / "oms").mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, DEST / "datos" / "oms" / n)

# documentos propios de la carpeta FORO
(DEST / "documentos").mkdir(parents=True, exist_ok=True)
for n in ("PLAN_LAMINAS_PANEL1.md", "DOSSIER_EVIDENCIA_PANEL1.md", "ARTICULOS_REVISION_PANEL1.md", "AUDITORIA_PANEL1_2026-10-09.md"):
    if (FORO / n).exists():
        shutil.copy2(FORO / n, DEST / "documentos" / n)
print(json.dumps(resumen, ensure_ascii=False, indent=1))
print("verificaciones nuevas:", len(nuevos_v), "| síntesis:", {k: bool(v) for k, v in sint.items()})
