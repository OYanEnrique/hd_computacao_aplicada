import nbformat as nbf

ORIG = "/mnt/user-data/uploads/unidade_04_03_visualizacao_exploratoria__1_.ipynb"
nb = nbf.read(ORIG, as_version=4)
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

celulas = [
md("""---

## Aplicação ao projeto — discursos de posse presidencial, 1985–2023

Base construída nas Unidades 2 e 3 (não o corpus fictício da unidade). Entradas em
`dados/derivados/`:

| Arquivo | Unidade da linha | n |
|---|---|---|
| `documentos_processaveis.csv` | um discurso de posse | 12 |
| `discursos_trechos.csv` | um trecho com ocorrência de `liberdade(s)` | 49 |
| `coocorrencias.csv` | termo de conteúdo na janela ±5 do alvo, por discurso | 225 |
| `motivos_exclusao.csv` | documento descartado | 2 |

**Proveniência.** Onze transcrições vêm do repositório `estadao/discurso-de-posse-presidentes`
(até 2003 derivado de *Palavra de Presidente*, de João Bosco Bezerra Bonfim; depois, acervo
do Estadão e Biblioteca da Presidência). O discurso de 2023 foi fornecido pelo autor do
projeto.

**Desvios em relação ao protocolo**, registrados em `log_transformacoes.csv`:

1. só o arquivo de 2023 preserva quebras de parágrafo; para manter a unidade comparável,
   todos os documentos foram segmentados por **sentença**, e o trecho é a sentença-alvo
   mais uma sentença à esquerda e uma à direita (`posicao_sentenca` permite recompor);
2. `partido` permanece nulo, com `razao_partido_ausente` — não verificado em fonte documental;
3. Sarney (1985) e Temer (2016) entram como **casos limítrofes**: nenhum proferiu o texto
   na sessão solene de posse no Congresso. Tancredo Neves (1985) foi excluído por não ter
   tomado posse."""),

code("""import pandas as pd
import matplotlib.pyplot as plt

docs = pd.read_csv("dados/derivados/documentos_processaveis.csv").sort_values("ano")
trechos = pd.read_csv("dados/derivados/discursos_trechos.csv")
coocorrencias = pd.read_csv("dados/derivados/coocorrencias.csv")

CURTO = {"José Sarney": "Sarney", "Fernando Collor de Mello": "Collor",
         "Itamar Franco": "Itamar", "Fernando Henrique Cardoso": "FHC",
         "Luiz Inácio Lula da Silva": "Lula", "Dilma Rousseff": "Dilma",
         "Michel Temer": "Temer", "Jair Bolsonaro": "Bolsonaro"}
docs["curto"] = docs["presidente"].map(CURTO)
rotulos = docs["ano"].astype(str) + "\\n" + docs["curto"]

docs[["ano", "presidente", "palavras", "ocorrencias_liberdade",
      "taxa_liberdade_mil", "n_trechos", "ttr"]].round(3)"""),

md("""### Figura 1 — barras: ocorrências por discurso

**Pergunta:** em quais discursos o termo aparece, e em quais não aparece?"""),
code("""fig, ax = plt.subplots(figsize=(9.5, 4))
ax.bar(rotulos, docs["ocorrencias_liberdade"], color="#3b6ea5")
ax.set_title('Ocorrências de "liberdade/liberdades" por discurso de posse (n = 12)')
ax.set_xlabel("Discurso de posse"); ax.set_ylabel("Ocorrências (contagem absoluta)")
ax.tick_params(axis="x", labelsize=8)
plt.show()

docs[["ano", "curto", "ocorrencias_liberdade", "n_trechos", "razao_ausencia"]]"""),
md("""| Item | Conteúdo |
|---|---|
| **Por que barras** | a pergunta compara unidades discretas; a barra de altura zero torna a ausência visível, o que uma linha interpolaria |
| **Escala** | `ocorrencias_liberdade` é numérica de razão (zero = ausência); eixo x categórico, ordenado no tempo |
| **Descrição alternativa** | barras verticais, um discurso por barra em ordem cronológica; 1985 é a mais alta (19); 1992, 2003 e 2007 têm altura zero |
| **Padrão** | 1985 concentra 19 das 55 ocorrências do corpus; 3 dos 12 discursos não usam o termo |
| **Caso** | Lula 2003 e 2007 — dois discursos longos (3.881 e 3.833 palavras) com zero ocorrências, do mesmo presidente que em 2023 registra 7 |
| **Limite** | contagem absoluta não é comparável entre textos de tamanhos diferentes; ausência do lexema não é ausência do tema (Lula 2007 usa `livre` 3×) |
| **Hipótese** | o termo é acionado em conjunturas de disputa sobre o regime, não como vocabulário permanente do gênero de posse |"""),

md("""### Figura 2 — histograma e boxplot: extensão dos discursos

**Pergunta:** os discursos são comparáveis em tamanho? A resposta condiciona a leitura da Figura 1."""),
code("""q1, q3 = docs["palavras"].quantile(.25), docs["palavras"].quantile(.75)
iqr = q3 - q1
limite_inferior, limite_superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr

fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 3.6))
a1.hist(docs["palavras"], bins=range(0, 7000, 1000), color="#3b6ea5", edgecolor="white")
a1.set_title("Extensão dos discursos")
a1.set_xlabel("Palavras (tokens)"); a1.set_ylabel("Discursos")
a2.boxplot(docs["palavras"], vert=False, widths=.5)
a2.set_title("Boxplot (regra 1,5·IQR)")
a2.set_xlabel("Palavras (tokens)"); a2.set_yticks([])
plt.tight_layout(); plt.show()

print(f"Q1={q1:.0f}  Q3={q3:.0f}  IQR={iqr:.0f}  "
      f"limites=[{limite_inferior:.0f}, {limite_superior:.0f}]")
docs.loc[docs["palavras"].lt(limite_inferior) | docs["palavras"].gt(limite_superior),
         ["id_doc", "palavras"]]"""),
md("""| Item | Conteúdo |
|---|---|
| **Por que histograma e boxplot** | a pergunta é sobre a forma da distribuição de uma variável quantitativa; o boxplot acrescenta a regra explícita de 1,5·IQR para localizar casos a inspecionar |
| **Escala** | `palavras` é numérica de razão, discreta |
| **Tabela** | Q1 = 2.686, Q3 = 3.865, IQR = 1.180, limites [916; 5.635]; fora deles, Collor (5.917) e Itamar (614) |
| **Descrição alternativa** | histograma com maior barra na faixa 3.000–4.000 palavras e cauda dos dois lados; boxplot com dois pontos fora dos whiskers |
| **Padrão** | os discursos variam de 614 a 5.917 palavras, quase 10× |
| **Caso** | Itamar 1992 (614 palavras) — o zero da Figura 1 tem base textual mínima |
| **Limite** | os dois extremos são de natureza documental distinta (Itamar assume em contexto de impeachment) e não devem ser excluídos automaticamente |
| **Hipótese** | parte da variação da Figura 1 é efeito de extensão, não de escolha lexical — o que exige normalização |"""),

md("""### Figura 3 — série temporal: taxa por 1.000 palavras

**Pergunta:** controlada a extensão, como a presença do termo se distribui no tempo?"""),
code("""fig, ax = plt.subplots(figsize=(9.5, 4))
ax.plot(docs["ano"], docs["taxa_liberdade_mil"], marker="o", color="#3b6ea5")
for _, r in docs.iterrows():
    ax.annotate(r["curto"], (r["ano"], r["taxa_liberdade_mil"]),
                textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
ax.set_title('Taxa de "liberdade" por 1.000 palavras (1 discurso por ano de posse)')
ax.set_xlabel("Ano da posse"); ax.set_ylabel("Ocorrências por 1.000 palavras")
ax.set_ylim(-.3, 5.6)
plt.show()

docs[["ano", "curto", "palavras", "ocorrencias_liberdade", "taxa_liberdade_mil"]].round(3)"""),
md("""| Item | Conteúdo |
|---|---|
| **Por que série temporal** | a pergunta do projeto é sobre transformação ao longo do tempo, e a taxa corrige o viés de extensão diagnosticado na Figura 2 |
| **Escala** | taxa numérica de razão sobre eixo temporal discreto e irregular (anos de posse, não anos consecutivos) |
| **Tabela** | `taxa_liberdade_mil` por ano; denominador = `palavras` de cada discurso, um discurso por ponto |
| **Descrição alternativa** | linha com marcadores: pico em 1985 (4,92), zero em 1992, repique em 1995 (2,46), platô próximo de zero entre 1999 e 2007, subida a 2,65 em 2019 e 2,66 em 2023 |
| **Padrão** | forma em U: valores altos nas pontas (1985 e 2019–2023) e vale entre 1999 e 2007 |
| **Caso** | 2019 e 2023 quase empatam na taxa (2,650 e 2,659) com contagens distintas (3 e 7), porque Bolsonaro fala 1.132 palavras e Lula 2.633 |
| **Limite** | cada ponto é **um único discurso**, não uma média anual; a linha liga anos não contíguos e sugere continuidade que o corpus não sustenta |
| **Hipótese** | há dois picos de uso com sentidos possivelmente opostos — 1985 e 2019–2023 — e não uma tendência monotônica |"""),

md("""### Figura 4 — frequências textuais: coocorrentes por período

**Pergunta:** com que campo semântico o termo aparece associado em cada período?"""),
code("""coocorrencias["periodo"] = coocorrencias["ano"].map(
    lambda a: "1985-1995" if a <= 1995 else "1999-2023"
)
tabela = (coocorrencias.groupby(["periodo", "termo_coocorrente"])["frequencia"]
          .sum().reset_index().sort_values("frequencia", ascending=False))
denominadores = coocorrencias.groupby("periodo")["frequencia"].sum()
top = {p: tabela[tabela["periodo"] == p].head(8) for p in ["1985-1995", "1999-2023"]}

fig, eixos = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
for eixo, periodo in zip(eixos, top):
    d = top[periodo].iloc[::-1]
    eixo.barh(d["termo_coocorrente"], d["frequencia"], color="#3b6ea5")
    eixo.set_title(f"{periodo} (N={int(denominadores[periodo])} tokens de conteúdo)",
                   fontsize=10)
    eixo.set_xlabel("Frequência na janela ±5")
fig.suptitle('Termos de conteúdo mais frequentes no entorno de "liberdade"', fontsize=11)
plt.tight_layout(); plt.show()

pd.concat([top["1985-1995"], top["1999-2023"]])"""),
md("""| Item | Conteúdo |
|---|---|
| **Por que barras horizontais** | comparam termos nomeados preservando o valor exato, ao contrário da nuvem de palavras, e o rótulo longo cabe no eixo y |
| **Escala** | frequência absoluta (razão) por termo nominal |
| **Tabela** | oito termos mais frequentes por período; denominadores N = 171 (1985–1995) e N = 94 (1999–2023) tokens de conteúdo na janela ±5 |
| **Descrição alternativa** | dois painéis de barras horizontais; à esquerda encabeçam `justiça`, `desenvolvimento`, `política`; à direita, `individuais`, `direitos`, `plena`, `expressão`, `opinião`, `culto` |
| **Padrão** | o entorno migra de vocabulário socioeconômico e de regime para vocabulário de direitos individuais, culto, opinião e expressão |
| **Caso** | Dilma 2011 — `liberdades individuais`, `liberdade de culto e de religião`, `liberdade de imprensa e de opinião` em sequência; boa parte do painel direito vem desse discurso e de 2023 |
| **Limite** | frequências baixíssimas (máximo 6); a janela ±5 corta sintagmas, `plena` é adjetivo, e a partição em dois períodos é decisão minha, não corte da fonte |
| **Hipótese** | a ressignificação ocorre menos na frequência do que no complemento do termo — de liberdade como condição do regime para liberdade como lista de direitos enumerados |"""),

md("""### Retorno aos trechos

Nenhuma figura substitui a leitura. Amostra de sentenças-alvo:"""),
code("""amostra = trechos[trechos["id_doc"].isin(
    ["DISCURSO_1985_SARNEY", "DISCURSO_2011_DILMA", "DISCURSO_2023_LULA"]
)].groupby("id_doc").head(3)
for linha in amostra.itertuples():
    print(f"[{linha.trecho_id}] {linha.sentenca_alvo[:150]}")"""),
]

FECHO = md("""## U04-A04 — Atividade — visualização exploratória

Produza barras, histograma/boxplot, dispersão ou tempo e frequência textual. Para
cada figura, entregue tabela, descrição alternativa, escala, padrão, caso, limite
e hipótese. Explique também por que o gráfico escolhido responde à pergunta.

**Minha análise:** cada figura acima é seguida da sua própria tabela de análise —
justificativa do tipo de gráfico, escala, tabela, descrição alternativa, padrão, caso,
limite e hipótese. Síntese:

**Quatro figuras selecionadas para o Notebook 04** — Figuras 1 a 4, nesta ordem:
presença, extensão, tempo normalizado e campo semântico. Cada uma responde à pergunta
que a anterior deixa aberta, e nenhuma repete o denominador da outra.

**Limite comum a todas** — n = 12 discursos, 55 ocorrências ao todo. Nenhuma figura
sustenta teste, tendência ou comparação inferencial: isso pertence à Unidade 5.""")

saida = []
for celula in nb.cells:
    if celula.cell_type == "markdown" and "U04-A04" in celula.source:
        saida.extend(celulas)
        saida.append(FECHO)
        continue
    saida.append(celula)
nb.cells = saida
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, "unidade_04_03_visualizacao_exploratoria_RESPONDIDO.ipynb")
print("células:", len(nb.cells))
