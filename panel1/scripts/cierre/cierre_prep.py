# -*- coding: utf-8 -*-
"""Lee los diarios de los cuatro flujos interrumpidos por el límite semanal y separa:
   lo ya verificado (con sus votos), lo pendiente de verificar y lo no hallado."""
import io, json, pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
W = pathlib.Path(r"C:\Users\infor\.claude\projects\C--Users-infor-OneDrive-CARLOS-PEREZ-UNIVERSIDADES-CEP-FORO\a76ee289-0d5f-426a-becc-af42c47fbeaf\subagents\workflows")
RUNS = {"ia": "wf_5056b99a-e5d", "pais": "wf_af7968f2-36b", "niv": "wf_3884fa8e-c1a", "ag": "wf_49d40803-a26", "aut": "wf_38f4707e-7f7"}


def lee(run):
    lab, res = {}, {}
    for l in io.open(W / run / "journal.jsonl", encoding="utf-8"):
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
        return "PENDIENTE"
    ref = sum(1 for v in votos if v.get("verdict") == "REFUTADA")
    if ref * 2 > len(votos):
        return "REFUTADA"
    if ref or any(v.get("verdict") == "MATIZAR" for v in votos):
        return "MATIZAR"
    return "CONFIRMADA"


resumen, ids_pend = {}, []
for corto, run in RUNS.items():
    res = lee(run)
    claims, nf = [], {}
    for etq, r in res.items():
        if etq.startswith("buscar:") and isinstance(r, dict):
            ang = etq.split(":", 1)[1]
            nf[ang] = r.get("notFound", "")
            for i, c in enumerate(r.get("claims", []), 1):
                votos = [v for k, v in res.items() if k.startswith("verif:%s#%d:" % (ang, i)) and isinstance(v, dict) and v.get("verdict")]
                claims.append({"id": "%s:%s#%d" % (corto, ang, i), "angle": ang, "n": i, "status": estado(votos), "votos": len(votos), "claim": c,
                               "corrected": [v.get("corrected") for v in votos if v.get("corrected") and len(v.get("corrected")) > 15],
                               "notes": ["%s: %s" % (v.get("verdict"), v.get("note", "")) for v in votos],
                               "evidence": [v.get("evidence", "") for v in votos]})
    pend = {c["id"]: c["claim"] for c in claims if c["status"] == "PENDIENTE"}
    ids_pend += list(pend)
    json.dump(claims, io.open(HERE / ("claims_%s.json" % corto), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(pend, io.open(HERE / ("pend_%s.json" % corto), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with io.open(HERE / ("usables_%s.md" % corto), "w", encoding="utf-8") as f:
        f.write("# Afirmaciones YA verificadas del flujo %s (%s)\n\n" % (corto, run))
        for c in claims:
            if c["status"] in ("CONFIRMADA", "MATIZAR"):
                k = c["claim"]
                f.write("[%s#%d] (%s; %d voto(s); %s; %s) %s\n   corregido: %s\n   literal: %s\n   fuente: %s | %s\n   límites: %s\n   notas de los verificadores: %s\n\n" % (
                    c["angle"], c["n"], c["status"], c["votos"], k.get("layer"), k.get("country") or k.get("topic") or "", k.get("statement"),
                    " || ".join(c["corrected"]) or "sin corrección", (k.get("literal") or "")[:1200], k.get("source"), k.get("locator"), k.get("limits"), " || ".join(c["notes"])[:1500]))
        f.write("\n# REFUTADAS (no usar)\n\n")
        for c in claims:
            if c["status"] == "REFUTADA":
                f.write("[%s#%d] %s\n   notas: %s\n\n" % (c["angle"], c["n"], c["claim"].get("statement"), " || ".join(c["notes"])[:900]))
        f.write("\n# NO HALLADO POR LOS BUSCADORES\n\n")
        for a, t in nf.items():
            f.write("[%s] %s\n\n" % (a, t))
    with io.open(HERE / ("pendientes_%s.md" % corto), "w", encoding="utf-8") as f:
        f.write("# Afirmaciones PENDIENTES de verificar del flujo %s\n\n" % corto)
        for c in claims:
            if c["status"] == "PENDIENTE":
                k = c["claim"]
                f.write("[%s#%d] (PENDIENTE; %s; %s) %s\n   literal: %s\n   fuente: %s | %s\n   límites: %s\n   cómo se abrió: %s\n\n" % (
                    c["angle"], c["n"], k.get("layer"), k.get("country") or k.get("topic") or "", k.get("statement"), (k.get("literal") or "")[:1200], k.get("source"), k.get("locator"), k.get("limits"), (k.get("openedHow") or "")[:600]))
    extras = {k: v for k, v in res.items() if not k.startswith(("buscar:", "verif:"))}
    json.dump(extras, io.open(HERE / ("extras_%s.json" % corto), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cuenta = {}
    for c in claims:
        cuenta[c["status"]] = cuenta.get(c["status"], 0) + 1
    resumen[corto] = {"buscadores": sorted(nf), "afirmaciones": len(claims), "estado": cuenta, "otros": sorted(extras)[:40]}
print(json.dumps(resumen, ensure_ascii=False, indent=1))
print("PENDIENTES:", len(ids_pend))
print(json.dumps(ids_pend, ensure_ascii=False))
