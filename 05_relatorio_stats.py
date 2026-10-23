import math
import re
from collections import Counter

import pandas as pd

docs = pd.read_csv("dados/derivados/documentos_processaveis.csv").sort_values("ano")
trechos = pd.read_csv("dados/derivados/discursos_trechos.csv")
coo = pd.read_csv("dados/derivados/coocorrencias.csv")

TOKEN = re.compile(r"[a-záàâãéêíóôõúüçñ]+")
docs["tokens"] = [TOKEN.findall(open(f"dados/brutos/{a}", encoding="utf-8").read().lower())
                  for a in docs["arquivo_bruto"]]

print("== centro e dispersão (palavras)")
x = docs["palavras"]
print(x.describe().round(1).to_string())
print("mediana", x.median(), "var ddof=1", round(x.var(ddof=1), 1), "dp", round(x.std(ddof=1), 1))

print("\n== frequência/proporção: discursos que mencionam o termo")
docs["menciona"] = docs["ocorrencias_liberdade"].gt(0).map({True: "menciona", False: "não menciona"})
print(docs["menciona"].value_counts().to_string())
print(docs["menciona"].value_counts(normalize=True).round(3).to_string())

print("\n== contingência período × menção")
docs["periodo"] = docs["ano"].map(lambda a: "1985-1995" if a <= 1995 else "1999-2023")
print(pd.crosstab(docs["periodo"], docs["menciona"]).to_string())
print(pd.crosstab(docs["periodo"], docs["menciona"], normalize="index").round(3).to_string())

print("\n== frequências textuais: total de tokens")
todos = [t for ts in docs["tokens"] for t in ts]
print("N total tokens:", len(todos), "| formas:", len(set(todos)))
print("liberdade(s):", sum(1 for t in todos if t in {"liberdade", "liberdades"}),
      "| relativa por mil:", round(sum(1 for t in todos if t in {"liberdade","liberdades"})/len(todos)*1000, 3))

print("\n== bigramas com 'liberdade' (freq mínima 2), PMI")
bigr, esq, dir_ = Counter(), Counter(), Counter()
for ts in docs["tokens"]:
    pares = list(zip(ts, ts[1:]))
    bigr.update(pares); esq.update(a for a, _ in pares); dir_.update(b for _, b in pares)
N = sum(bigr.values())
linhas = []
for (a, b), f in bigr.items():
    if f >= 2 and (a in {"liberdade", "liberdades"} or b in {"liberdade", "liberdades"}):
        linhas.append((f"{a} {b}", f, math.log2(f * N / (esq[a] * dir_[b]))))
print(pd.DataFrame(sorted(linhas, key=lambda l: -l[2]),
                   columns=["bigrama", "frequencia", "pmi"]).round(2).head(12).to_string(index=False))

print("\n== TTR bruta e padronizada")
m = int(docs["tokens"].map(len).min())
docs["ttr_padronizada"] = docs["tokens"].map(lambda ts: len(set(ts[:m])) / m)
print("m =", m)
print(docs[["ano", "presidente", "palavras", "ttr", "ttr_padronizada"]].round(3).to_string(index=False))

print("\n== trechos de 2023")
for r in trechos[trechos.id_doc == "DISCURSO_2023_LULA"].itertuples():
    print("-", r.sentenca_alvo[:160])
