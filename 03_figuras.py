import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SAIDA = Path("figuras"); SAIDA.mkdir(exist_ok=True)
docs = pd.read_csv("dados/derivados/documentos_processaveis.csv")
coo = pd.read_csv("dados/derivados/coocorrencias.csv")
docs = docs.sort_values("ano")
CURTO = {"José Sarney": "Sarney", "Fernando Collor de Mello": "Collor",
         "Itamar Franco": "Itamar", "Fernando Henrique Cardoso": "FHC",
         "Luiz Inácio Lula da Silva": "Lula", "Dilma Rousseff": "Dilma",
         "Michel Temer": "Temer", "Jair Bolsonaro": "Bolsonaro"}
docs["curto"] = docs["presidente"].map(CURTO)
rot = docs["ano"].astype(str) + "\n" + docs["curto"]

# 1 barras
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(rot, docs["ocorrencias_liberdade"], color="#3b6ea5")
ax.set_title('Ocorrências de "liberdade/liberdades" por discurso de posse (n = 11 discursos)')
ax.set_xlabel("Discurso de posse"); ax.set_ylabel("Ocorrências (contagem absoluta)")
ax.tick_params(axis="x", labelsize=8)
fig.tight_layout(); fig.savefig(SAIDA / "fig1_barras.png", dpi=130); plt.close(fig)

# 2 histograma + boxplot
q1, q3 = docs["palavras"].quantile(.25), docs["palavras"].quantile(.75)
iqr = q3 - q1; li, ls = q1 - 1.5 * iqr, q3 + 1.5 * iqr
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
a1.hist(docs["palavras"], bins=range(0, 7000, 1000), color="#3b6ea5", edgecolor="white")
a1.set_title("Extensão dos discursos"); a1.set_xlabel("Palavras (tokens)"); a1.set_ylabel("Discursos")
a2.boxplot(docs["palavras"], vert=False, widths=.5)
a2.set_title("Boxplot (regra 1,5·IQR)"); a2.set_xlabel("Palavras (tokens)"); a2.set_yticks([])
fig.tight_layout(); fig.savefig(SAIDA / "fig2_distribuicao.png", dpi=130); plt.close(fig)

# 3 série temporal
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(docs["ano"], docs["taxa_liberdade_mil"], marker="o", color="#3b6ea5")
for _, r in docs.iterrows():
    ax.annotate(r["curto"], (r["ano"], r["taxa_liberdade_mil"]),
                textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
ax.set_title('Taxa de "liberdade" por 1.000 palavras (1 discurso por ano de posse)')
ax.set_xlabel("Ano da posse"); ax.set_ylabel("Ocorrências por 1.000 palavras")
ax.set_ylim(-.3, 5.6)
fig.tight_layout(); fig.savefig(SAIDA / "fig3_serie.png", dpi=130); plt.close(fig)

# 4 coocorrentes por período
coo["periodo"] = coo["ano"].map(lambda a: "1985-1995" if a <= 1995 else "1999-2023")
tab = (coo.groupby(["periodo", "termo_coocorrente"])["frequencia"].sum()
         .reset_index().sort_values("frequencia", ascending=False))
top = {p: tab[tab.periodo == p].head(8) for p in ["1985-1995", "1999-2023"]}
tot = coo.groupby("periodo")["frequencia"].sum()
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
for ax, p in zip(axes, top):
    d = top[p].iloc[::-1]
    ax.barh(d["termo_coocorrente"], d["frequencia"], color="#3b6ea5")
    ax.set_title(f"{p} (N={int(tot[p])} tokens de conteúdo na janela)", fontsize=10)
    ax.set_xlabel("Frequência na janela ±5")
fig.suptitle('Termos de conteúdo mais frequentes no entorno de "liberdade"', fontsize=11)
fig.tight_layout(); fig.savefig(SAIDA / "fig4_coocorrentes.png", dpi=130); plt.close(fig)

print("IQR:", q1, q3, iqr, "limites:", round(li), round(ls))
print(docs[docs.palavras.lt(li) | docs.palavras.gt(ls)][["id_doc", "palavras"]])
print(docs[["ano","presidente","palavras","ocorrencias_liberdade","taxa_liberdade_mil","n_trechos","ttr"]].round(3).to_string(index=False))
print("\nTOP 1985-1995:\n", top["1985-1995"].to_string(index=False))
print("\nTOP 1999-2019:\n", top["1999-2023"].to_string(index=False))
print("\ntotais janela:", tot.to_dict())
