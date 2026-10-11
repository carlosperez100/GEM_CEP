# -*- coding: utf-8 -*-
# Arma inventario.json, autonomia_estado.json, niveles.json y paises.json a partir de los diarios de los flujos.
import json, sys, collections, pathlib
sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
W = pathlib.Path(r"C:\Users\infor\.claude\projects\C--Users-infor-OneDrive-CARLOS-PEREZ-UNIVERSIDADES-CEP-FORO\a76ee289-0d5f-426a-becc-af42c47fbeaf\subagents\workflows")


def resultados(wf):
    out = []
    p = W / wf / "journal.jsonl"
    if not p.exists():
        return out
    for line in open(p, encoding="utf-8"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "result" and isinstance(o.get("result"), dict):
            out.append(o["result"])
    return out


MAPEO = [("Demanda", "demanda"), ("imagen", "imagen_auditorias"), ("publicada", "deck"), ("Marco normativo", "normativa"), ("Producción científica", "bibliometria_modelo"), ("GEMSES", "gemses_caso"),
         ("Autonomía", "autonomia"), ("Valor del cuidado", "valor_programas")]
inv = []
for r in resultados("wf_579be73d-848"):
    if "tema" not in r:
        continue
    key = next((k for pat, k in MAPEO if pat.lower() in r["tema"].lower()), "primeros_temas")
    inv.append({"key": key, "r": r})
json.dump(inv, open(HERE / "inventario.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("inventario:", [(x["key"], len(x["r"].get("tenemos", []))) for x in inv])

c = collections.Counter(); claims = 0; busc = 0
for r in resultados("wf_38f4707e-7f7"):
    if "claims" in r:
        busc += 1; claims += len(r["claims"])
    elif "verdict" in r:
        c[r["verdict"]] += 1
json.dump({"claims": claims, "buscadores": busc, "CONFIRMADA": c["CONFIRMADA"], "MATIZAR": c["MATIZAR"], "REFUTADA": c["REFUTADA"]}, open(HERE / "autonomia_estado.json", "w"), indent=1)
print("autonomia:", claims, busc, dict(c))

for wf, nombre, campo in (("wf_3884fa8e-c1a", "niveles.json", "fundamento"), ("wf_af7968f2-36b", "paises.json", "paises")):
    s = [r for r in resultados(wf) if campo in r]
    if s:
        json.dump(s[-1], open(HERE / nombre, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(nombre, "listo")
    else:
        est = collections.Counter(("claims" if "claims" in r else r.get("verdict", "otro")) for r in resultados(wf))
        print(nombre, "aun no; avance:", dict(est))
