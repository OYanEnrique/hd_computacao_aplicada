import nbformat as nbf

nb = nbf.read("/mnt/user-data/uploads/04_oficina_relatorio_exploratorio.ipynb", as_version=4)
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
c = nb.cells


def troca(i, antigo, novo):
    assert antigo in c[i].source, f"não encontrado na célula {i}: {antigo[:40]}"
    c[i].source = c[i].source.replace(antigo, novo, 1)


# ----------------------------------------------------------------- 1. escopo
troca(2, """| Elemento | Resposta |
|---|---|
| Pergunta exploratória | Escreva aqui. |
| Corpus e período | Escreva aqui. |
| Unidade de análise | Escreva aqui. |
| Variáveis e escalas | Escreva aqui. |
| Cobertura e ausências | Escreva aqui. |
| Erros conhecidos e casos extremos | Escreva aqui. |
| Adequação e principal limite | Escreva aqui. |""",
"""| Elemento | Resposta |
|---|---|
| **Pergunta exploratória** | Como a palavra *liberdade* é empregada e com que termos aparece associada nos discursos de posse presidencial brasileiros entre 1985 e 2023? |
| **Corpus e período** | 12 discursos de posse, 1985–2023 (Sarney, Collor, Itamar, FHC ×2, Lula ×3, Dilma ×2, Temer, Bolsonaro). 39.069 tokens. Fonte: repositório `estadao/discurso-de-posse-presidentes` (até 2003 derivado de *Palavra de Presidente*, de João Bosco Bezerra Bonfim; depois, acervo do Estadão e Biblioteca da Presidência); o discurso de 2023 foi fornecido pelo autor do projeto. |
| **Unidade de análise** | Duas, articuladas por `id_doc`: o **discurso** (`documentos_processaveis.csv`, 12 linhas) e o **trecho** com ocorrência de `liberdade(s)` (`discursos_trechos.csv`, 49 linhas) — sentença-alvo mais uma sentença à esquerda e uma à direita. |
| **Variáveis e escalas** | `presidente`, `tipo_discurso`, `termo_coocorrente` → categóricas nominais; `ano` → temporal (data); `palavras`, `ocorrencias_liberdade`, `frequencia` → numéricas de razão; `taxa_liberdade_mil` e `ttr` → razões derivadas; `id_doc` e `trecho_id` → identificadores, não medidas. |
| **Cobertura e ausências** | Cobertura completa dos mandatos iniciados entre 1985 e 2023. `partido` está integralmente nulo, com `razao_partido_ausente` (não verificado em fonte documental). Três discursos têm `ocorrencias_liberdade = 0`, com `razao_ausencia` preenchida — ausência observada, não dado faltante. Exclusões em `motivos_exclusao.csv`: Tancredo Neves (não tomou posse) e os 24 discursos anteriores a 1985 (fora do recorte). |
| **Erros conhecidos e casos extremos** | Só o arquivo de 2023 preserva quebras de parágrafo, o que forçou a segmentação por sentença em todo o corpus. Sarney (1985) e Temer (2016) são casos limítrofes: nenhum proferiu o texto na sessão solene de posse. Extremos de extensão pela regra de 1,5·IQR: Collor (5.917 palavras) e Itamar (614). |
| **Adequação e principal limite** | A base responde a *onde e com que companhia lexical o termo aparece*; não responde a *o que cada presidente quis dizer*. Com n = 12 e 55 ocorrências, nenhuma diferença entre períodos comporta teste ou generalização. |"""
)

setup = code("""import math
import re
from collections import Counter

import pandas as pd
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

TOKEN = re.compile(r"[a-záàâãéêíóôõúüçñ]+")
ALVO = {"liberdade", "liberdades"}
docs["tokens"] = [TOKEN.findall((open(f"dados/brutos/{a}", encoding="utf-8").read()).lower())
                  for a in docs["arquivo_bruto"]]

print("discursos:", len(docs), "| trechos:", len(trechos),
      "| tokens do corpus:", sum(docs["tokens"].map(len)))
docs[["ano", "curto", "palavras", "ocorrencias_liberdade",
      "taxa_liberdade_mil", "n_trechos"]]""")

# ------------------------------------------------------- 2. perfil quantitativo
quant = code("""# (a) frequência e proporção: discursos que mencionam o termo
docs["menciona"] = docs["ocorrencias_liberdade"].gt(0).map(
    {True: "menciona", False: "não menciona"})
frequencia = docs["menciona"].value_counts().rename("frequencia")
proporcao = docs["menciona"].value_counts(normalize=True).rename("proporcao").round(3)
display(pd.concat([frequencia, proporcao], axis=1))

# (b) centro e dispersão de `palavras` (ddof=1, quartis por interpolação linear)
x = docs["palavras"]
q1, q3 = x.quantile(.25), x.quantile(.75)
iqr = q3 - q1
limite_inferior, limite_superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
display(pd.Series({
    "n": x.count(), "media": round(x.mean(), 1), "mediana": x.median(),
    "desvio_padrao_ddof1": round(x.std(ddof=1), 1),
    "q1": q1, "q3": q3, "iqr": iqr,
    "limite_inferior": round(limite_inferior), "limite_superior": round(limite_superior),
}, name="palavras"))

# (c) registros sinalizados pela regra de 1,5 IQR — inspecionados, não removidos
display(docs.loc[x.lt(limite_inferior) | x.gt(limite_superior),
                 ["id_doc", "palavras", "ocorrencias_liberdade", "taxa_liberdade_mil"]])

# (d) contingência: período × intensidade de uso
docs["periodo"] = docs["ano"].map(
    lambda a: "1985-1995" if a <= 1995 else ("1999-2007" if a <= 2007 else "2011-2023"))
docs["classe_uso"] = docs["taxa_liberdade_mil"].map(
    lambda t: "sem menção" if t == 0 else ("até 1/mil" if t <= 1 else "acima de 1/mil"))
ordem = ["sem menção", "até 1/mil", "acima de 1/mil"]
display(pd.crosstab(docs["periodo"], docs["classe_uso"])[ordem])
display(pd.crosstab(docs["periodo"], docs["classe_uso"], normalize="index")[ordem].round(3))""")

troca(3, """| Resultado | Denominador ou convenção | Valor observado | Leitura e limite |
|---|---|---|---|
| frequência/proporção | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| centro e dispersão | `ddof`, quartis e variável | Escreva aqui. | Escreva aqui. |
| caso extremo | limites inferior e superior | Escreva aqui. | Escreva aqui. |
| contingência | total de cada linha | Escreva aqui. | Escreva aqui. |""",
"""| Resultado | Denominador ou convenção | Valor observado | Leitura e limite |
|---|---|---|---|
| frequência/proporção | n = 12 discursos | 9 mencionam o termo (0,75); 3 não mencionam (0,25) | a ausência é observada, não faltante; mas o lexema não esgota o tema — Lula 2007 usa `livre` 3× sem usar `liberdade` |
| centro e dispersão | `palavras`, `ddof=1`, quartis por interpolação linear | média 3.243,3; mediana 3.541,5; dp 1.431,8; Q1 2.685,5; Q3 3.865,3; IQR 1.179,8 | média abaixo da mediana indica assimetria à esquerda puxada por Itamar; a dispersão inviabiliza comparar contagens brutas entre discursos |
| caso extremo | limites [916; 5.635] | Collor 1990 (5.917) e Itamar 1992 (614) | os dois são documentalmente explicáveis, não erros de contagem; nenhum foi removido |
| contingência | total de cada linha (4, 3 e 5 discursos) | 1985–1995: 0,75 acima de 1/mil; 1999–2007: 0,67 sem menção; 2011–2023: 0,60 acima de 1/mil e 0 sem menção | distribuição em U; com 3 a 5 discursos por linha, uma única mudança de documento altera a proporção |"""
)

troca(3, "**Minha análise quantitativa:** Escreva aqui.",
"""**Minha análise quantitativa**

- **Procedimento:** contagem de `liberdade(s)` por regex `\\bliberdades?\\b` sobre os 12 discursos normalizados; medidas de centro e dispersão sobre `palavras` com `ddof=1`; regra de 1,5·IQR; contingência período × classe de uso, com proporções por linha.
- **Descrição:** 55 ocorrências em 39.069 tokens (1,41 por mil no corpus inteiro), muito desigualmente distribuídas: 19 estão em 1985. Três discursos têm zero. A extensão varia de 614 a 5.917 palavras. A contingência mostra uso alto nas pontas do período e concentração de ausências entre 1999 e 2007.
- **Interpretação:** nesta base, o termo se comporta como vocabulário de conjuntura — associado à transição de 1985 e ao período recente — e não como item estável do gênero de posse.
- **Limite:** n = 12; a forma em U pode ser efeito de composição do corpus (um discurso por posse) e da própria extensão dos textos; nada aqui é teste de diferença.
- **Próximo passo:** normalizar por extensão (Figura 3) e examinar o entorno do termo, já que a contagem não distingue sentidos."""
)

# ------------------------------------------------------------ 3. perfil textual
textual = code("""# (a) tokenização e frequências, com os dois denominadores declarados
STOPWORDS = {"a", "o", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "e", "é",
             "em", "no", "na", "nos", "nas", "que", "com", "por", "para", "se", "ao",
             "aos", "à", "às", "não", "sua", "seu", "mais", "como", "mas", "ou", "nossa",
             "nosso", "esta", "este", "isso", "sem", "ser", "foi", "já", "também"}
todos = [t for ts in docs["tokens"] for t in ts]
conteudo = [t for t in todos if t not in STOPWORDS]
ocorrencias_alvo = sum(1 for t in todos if t in ALVO)
display(pd.Series({
    "N_todos_tokens": len(todos), "N_tokens_conteudo": len(conteudo),
    "formas_distintas": len(set(todos)), "ocorrencias_liberdade": ocorrencias_alvo,
    "relativa_por_mil_todos": round(ocorrencias_alvo / len(todos) * 1000, 3),
    "relativa_por_mil_conteudo": round(ocorrencias_alvo / len(conteudo) * 1000, 3),
}, name="corpus"))

# (b) concordâncias: janela de 5 tokens, com identificador documental
def concordancias(janela=5):
    linhas = []
    for linha in docs.itertuples():
        for pos, token in enumerate(linha.tokens):
            if token in ALVO:
                ini, fim = max(0, pos - janela), min(len(linha.tokens), pos + janela + 1)
                linhas.append({"id_doc": linha.id_doc,
                               "contexto": " ".join(linha.tokens[ini:fim])})
    return pd.DataFrame(linhas)

kwic = concordancias()
display(kwic.groupby("id_doc").head(1).head(9))

# (c) bigramas e PMI, frequência mínima 2, restritos ao termo-alvo
bigramas, esquerda, direita = Counter(), Counter(), Counter()
for ts in docs["tokens"]:
    pares = list(zip(ts, ts[1:]))
    bigramas.update(pares); esquerda.update(a for a, _ in pares); direita.update(b for _, b in pares)
N_bigramas = sum(bigramas.values())
linhas_pmi = [(f"{a} {b}", f, math.log2(f * N_bigramas / (esquerda[a] * direita[b])))
              for (a, b), f in bigramas.items()
              if f >= 2 and (a in ALVO or b in ALVO)]
display(pd.DataFrame(sorted(linhas_pmi, key=lambda l: -l[2]),
                     columns=["bigrama", "frequencia", "pmi"]).round(2).head(6))

# (d) TTR bruta e padronizada em segmento comum
m = int(docs["tokens"].map(len).min())
docs["ttr_padronizada"] = docs["tokens"].map(lambda ts: len(set(ts[:m])) / m)
print("tamanho comum adotado (m):", m, "tokens")
display(docs[["ano", "curto", "palavras", "ttr", "ttr_padronizada"]].round(3))""")

troca(4, """| Etapa | Regra ou parâmetro | Resultado selecionado | Interpretação e limite |
|---|---|---|---|
| tokenização/normalização | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| frequências | denominador: Escreva aqui. | Escreva aqui. | Escreva aqui. |
| concordância | termo e janela: Escreva aqui. | Escreva aqui. | Escreva aqui. |
| colocação | frequência mínima: Escreva aqui. | Escreva aqui. | Escreva aqui. |
| diversidade | tamanho comum: Escreva aqui. | Escreva aqui. | Escreva aqui. |""",
"""| Etapa | Regra ou parâmetro | Resultado selecionado | Interpretação e limite |
|---|---|---|---|
| tokenização/normalização | minúsculas; `re.findall(r"[a-záàâãéêíóôõúüçñ]+")`; pontuação e números descartados; tokenização **por documento**, para não criar bigramas entre o fim de um discurso e o início do seguinte | 39.069 tokens, 6.360 formas distintas | a regra une `liberdade` e `Liberdade` e separa formas hifenizadas; `livre` e `livremente` ficam fora do alvo por decisão, não por acidente |
| frequências | N = 39.069 (todos os tokens); N_c após stopwords, para a tabela de conteúdo | 55 ocorrências de `liberdade(s)` = 1,408 por mil tokens | a taxa do corpus esconde a concentração em 1985; por isso a taxa por documento é calculada separadamente |
| concordância | termo `liberdade/liberdades`, janela ±5 tokens, `id_doc` preservado | 55 janelas; em 2023, `a liberdade que eles pregam é a de oprimir o vulnerável` | o retorno ao texto mostra o termo em disputa explícita, algo que nenhuma contagem registra; a janela corta orações longas |
| colocação | bigramas com o termo, frequência mínima 2, PMI em log₂ | `liberdades individuais` PMI 12,03 (f = 3); `liberdade econômica` 6,12 (f = 3); `liberdade política` 5,13 (f = 4) | PMI alto com f = 3 é frágil por construção: a medida favorece eventos raros; a leitura só se sustenta junto das concordâncias |
| diversidade | m = 621 tokens (menor documento, Itamar 1992); primeiros m tokens | TTR bruta 0,319–0,526; TTR padronizada 0,490–0,567 | a TTR bruta ordena os discursos quase pelo inverso do tamanho; padronizada, a variação quase desaparece — a diversidade aparente era efeito de extensão |"""
)

troca(4, "**Meu perfil textual:** Escreva aqui.",
"""**Meu perfil textual**

- **Procedimento:** tokenização por documento; frequências com denominador declarado; 55 concordâncias com janela ±5; bigramas com o termo-alvo e PMI (f ≥ 2); TTR bruta e padronizada em m = 621 tokens.
- **Descrição:** o termo aparece 1,41 vezes por mil tokens no corpus. Os bigramas de maior PMI são `liberdades individuais`, `liberdade econômica` e `liberdade política`. A TTR bruta vai de 0,319 (Dilma 2015) a 0,526 (Itamar 1992); padronizada, fica entre 0,490 e 0,567.
- **Interpretação:** o termo quase nunca aparece sozinho — vem qualificado por um adjetivo ou por um complemento (`de expressão`, `de culto`, `de empreender`). É nesse complemento, e não na frequência, que a variação entre períodos se manifesta.
- **Limite:** com f = 3 ou 4, PMI é instável; a lista de stopwords é minha e altera a tabela de conteúdo; a TTR padronizada usa os primeiros 621 tokens, que em discurso de posse são majoritariamente vocativos protocolares.
- **Próximo passo:** classificar manualmente os 49 trechos por tipo de liberdade invocada (civil, política, econômica, de expressão), com dupla codificação — a coocorrência automática sugere, mas não decide."""
)

# ----------------------------------------------------------- 4. visualizações
troca(5, """**Figura 1 e análise:** Escreva aqui.

**Figura 2 e análise:** Escreva aqui.

**Figura 3 e análise:** Escreva aqui.

**Figura 4 e análise:** Escreva aqui.""",
"""As quatro figuras estão nas células seguintes, cada uma acompanhada da sua tabela
equivalente e da análise correspondente. São as mesmas selecionadas no Notebook 03.""")

fig1 = code("""fig, ax = plt.subplots(figsize=(9.5, 4))
ax.bar(rotulos, docs["ocorrencias_liberdade"], color="#3b6ea5")
ax.set_title('Figura 1 — ocorrências de "liberdade/liberdades" por discurso (n = 12)')
ax.set_xlabel("Discurso de posse"); ax.set_ylabel("Ocorrências (contagem absoluta)")
ax.tick_params(axis="x", labelsize=8)
plt.show()

docs[["ano", "curto", "palavras", "ocorrencias_liberdade", "n_trechos", "razao_ausencia"]]""")

an1 = md("""**Figura 1 — análise**

| Item | Conteúdo |
|---|---|
| Pergunta e justificativa | Em quais discursos o termo aparece? Barras comparam unidades discretas e tornam a ausência visível como altura zero — uma linha a interpolaria. |
| Escalas e unidades | Eixo x categórico (discurso, ordem cronológica); eixo y numérico de razão, contagem absoluta. |
| Tabela equivalente | Acima: ano, presidente, palavras, ocorrências, trechos e `razao_ausencia`. |
| Descrição alternativa | Doze barras verticais em ordem cronológica; 1985 é a mais alta, com 19; 1992, 2003 e 2007 têm altura zero; as demais ficam entre 1 e 9. |
| Padrão e caso | 1985 concentra 19 das 55 ocorrências. Caso: Lula, zero em 2003 e 2007 e 7 em 2023 — o mesmo presidente, comportamento oposto. |
| Interpretação e limite | O uso do termo parece ligado à conjuntura, não ao locutor. Limite: contagem absoluta não é comparável entre textos de tamanhos diferentes, e a ausência do lexema não é ausência do tema. |""")

fig2 = code("""fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 3.6))
a1.hist(docs["palavras"], bins=range(0, 7000, 1000), color="#3b6ea5", edgecolor="white")
a1.set_title("Figura 2a — extensão dos discursos")
a1.set_xlabel("Palavras (tokens)"); a1.set_ylabel("Discursos")
a2.boxplot(docs["palavras"], vert=False, widths=.5)
a2.set_title("Figura 2b — boxplot (1,5·IQR)")
a2.set_xlabel("Palavras (tokens)"); a2.set_yticks([])
plt.tight_layout(); plt.show()

faixas = pd.cut(docs["palavras"], bins=range(0, 7000, 1000))
display(docs.groupby(faixas, observed=False).size().rename("discursos"))
docs.loc[docs["palavras"].lt(limite_inferior) | docs["palavras"].gt(limite_superior),
         ["id_doc", "palavras"]]""")

an2 = md("""**Figura 2 — análise**

| Item | Conteúdo |
|---|---|
| Pergunta e justificativa | Os discursos são comparáveis em tamanho? Histograma mostra a forma da distribuição; o boxplot acrescenta a regra explícita de 1,5·IQR para sinalizar casos. |
| Escalas e unidades | `palavras`, numérica de razão, discreta; intervalos de 1.000 tokens. |
| Tabela equivalente | Contagem por faixa e lista dos registros fora dos limites [916; 5.635]. |
| Descrição alternativa | Histograma com a maior barra na faixa de 3.000 a 4.000 palavras e caudas dos dois lados; boxplot horizontal com dois pontos fora dos whiskers. |
| Padrão e caso | Variação de quase 10×, de 614 a 5.917 palavras. Caso: Itamar 1992, com 614 palavras — o zero da Figura 1 tem base textual mínima. |
| Interpretação e limite | A heterogeneidade de extensão obriga a normalizar antes de comparar contagens. Limite: a regra de 1,5·IQR sinaliza, não demonstra erro; nenhum dos dois extremos foi excluído. |""")

fig3 = code("""fig, ax = plt.subplots(figsize=(9.5, 4))
ax.plot(docs["ano"], docs["taxa_liberdade_mil"], marker="o", color="#3b6ea5")
for _, r in docs.iterrows():
    ax.annotate(r["curto"], (r["ano"], r["taxa_liberdade_mil"]),
                textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
ax.set_title('Figura 3 — taxa de "liberdade" por 1.000 palavras (1 discurso por ano)')
ax.set_xlabel("Ano da posse"); ax.set_ylabel("Ocorrências por 1.000 palavras")
ax.set_ylim(-.3, 5.6)
plt.show()

docs[["ano", "curto", "palavras", "ocorrencias_liberdade", "taxa_liberdade_mil"]].round(3)""")

an3 = md("""**Figura 3 — análise**

| Item | Conteúdo |
|---|---|
| Pergunta e justificativa | Controlada a extensão, como o uso se distribui no tempo? A linha ordena cronologicamente e a taxa corrige o viés diagnosticado na Figura 2. |
| Escalas e unidades | Eixo x temporal, discreto e irregular (anos de posse); eixo y em ocorrências por 1.000 palavras. |
| Tabela equivalente | Acima: ano, presidente, palavras (denominador), ocorrências e taxa. Cada ponto é **um** discurso, não uma média anual. |
| Descrição alternativa | Linha com marcadores: 4,92 em 1985, queda a 0 em 1992, 2,46 em 1995, platô próximo de zero entre 1999 e 2007, subida a 2,65 em 2019 e 2,66 em 2023. |
| Padrão e caso | Forma em U. Caso: 2019 e 2023 quase empatam na taxa (2,650 e 2,659) com contagens bem diferentes (3 e 7), porque Bolsonaro fala 1.132 palavras e Lula 2.633. |
| Interpretação e limite | O uso reaparece nas duas pontas do período democrático. Limite: a linha liga anos não contíguos e sugere continuidade que 12 pontos não sustentam. |""")

fig4 = code("""coocorrencias["periodo"] = coocorrencias["ano"].map(
    lambda a: "1985-1995" if a <= 1995 else "1999-2023")
tabela_coo = (coocorrencias.groupby(["periodo", "termo_coocorrente"])["frequencia"]
              .sum().reset_index().sort_values("frequencia", ascending=False))
denominadores = coocorrencias.groupby("periodo")["frequencia"].sum()
top = {p: tabela_coo[tabela_coo["periodo"] == p].head(8) for p in ["1985-1995", "1999-2023"]}

fig, eixos = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
for eixo, periodo in zip(eixos, top):
    d = top[periodo].iloc[::-1]
    eixo.barh(d["termo_coocorrente"], d["frequencia"], color="#3b6ea5")
    eixo.set_title(f"{periodo} (N={int(denominadores[periodo])} tokens de conteúdo)", fontsize=10)
    eixo.set_xlabel("Frequência na janela ±5")
fig.suptitle('Figura 4 — termos de conteúdo no entorno de "liberdade"', fontsize=11)
plt.tight_layout(); plt.show()

pd.concat([top["1985-1995"], top["1999-2023"]])""")

an4 = md("""**Figura 4 — análise**

| Item | Conteúdo |
|---|---|
| Pergunta e justificativa | Com que campo semântico o termo aparece associado em cada período? Barras horizontais preservam o valor exato e acomodam rótulos longos, ao contrário da nuvem de palavras. |
| Escalas e unidades | Frequência absoluta por termo nominal, dentro da janela ±5 tokens, após remoção de stopwords. |
| Tabela equivalente | Oito termos por período, com os denominadores N = 171 (1985–1995) e N = 94 (1999–2023). |
| Descrição alternativa | Dois painéis de barras horizontais: à esquerda, `justiça` (6), `desenvolvimento` (5), `política` (5); à direita, `individuais` (5), `direitos` (4), `plena` (4), `expressão` (3), `opinião` (3), `culto` (3). |
| Padrão e caso | O entorno migra de vocabulário socioeconômico e de regime para vocabulário de direitos individuais enumerados. Caso: Dilma 2011 enumera `liberdades individuais`, `de culto e de religião`, `de imprensa e de opinião` em sequência, e sozinha responde por boa parte do painel direito. |
| Interpretação e limite | A ressignificação se manifesta no complemento do termo, não na frequência. Limite: frequências baixíssimas (máximo 6), janela que corta sintagmas e partição em dois períodos decidida por mim, não pela fonte. |""")

# ------------------------------------------------------------ 5. casos
casos = code("""for id_doc in ["DISCURSO_2023_LULA", "DISCURSO_1992_ITAMAR", "DISCURSO_1985_SARNEY"]:
    print(f"--- {id_doc} | palavras={int(docs.loc[docs.id_doc == id_doc, 'palavras'].iloc[0])} "
          f"| ocorrências={int(docs.loc[docs.id_doc == id_doc, 'ocorrencias_liberdade'].iloc[0])}")
    for r in trechos[trechos.id_doc == id_doc].head(3).itertuples():
        print(f"  [{r.trecho_id}] {r.sentenca_alvo[:140]}")""")

troca(6, """| Caso/ID | Por que foi escolhido? | Evidência documental ou trecho | O que muda na leitura do agregado? |
|---|---|---|---|
| Caso 1 | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| Caso 2 | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| Caso 3 | Escreva aqui. | Escreva aqui. | Escreva aqui. |""",
"""| Caso/ID | Por que foi escolhido? | Evidência documental ou trecho | O que muda na leitura do agregado? |
|---|---|---|---|
| **DISCURSO_2023_LULA** (caso inesperado) | Fecha a série e tem a maior taxa do período recente (2,66/mil, 7 ocorrências) | `A liberdade que eles pregam é a de oprimir o vulnerável, massacrar o oponente e impor a lei do mais forte` — e, logo antes, `a negação da política, na destruição do Estado em nome de supostas liberdades individuais` | O agregado trata toda ocorrência como uso do conceito; aqui o termo é **disputado**, usado para recusar o sentido atribuído ao adversário. Coocorrência alta com `individuais` não indica adesão a esse sentido — indica polêmica sobre ele. |
| **DISCURSO_1992_ITAMAR** (caso extremo) | Único discurso com zero ocorrências e simultaneamente o mais curto (614 palavras), fora do limite inferior de 1,5·IQR | Discurso inteiro de 614 palavras, proferido na posse após o impeachment de Collor | O zero na Figura 1 não é escolha lexical: é efeito de um pronunciamento mínimo. A ausência deveria ser lida como não-evidência, e não como evidência de recuo do conceito. |
| **DISCURSO_1985_SARNEY** (caso que sustenta o agregado) | Máximo absoluto e relativo do corpus (19 ocorrências, 4,92/mil) | `Respira-se liberdade.` · `A liberdade é um legado de Deus.` · `As leis dão ordem ao exercício da liberdade.` · `Nossos objetivos passam por cinco pontos fundamentais: Liberdade Desenvolvimento Opção social...` | Confirma o pico, mas qualifica-o: parte das ocorrências vem de uma **lista programática** e de formulações aforísticas, não de argumentação distribuída ao longo do texto. O pico é também um efeito de gênero retórico. |"""
)

# --------------------------------------------------------------- 6. hipóteses
troca(7, """| Hipótese provisória | Evidência exploratória | Explicação alternativa | Dados adicionais necessários | Método futuro |
|---|---|---|---|---|
| H1 | Escreva aqui. | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| H2, se necessária | Escreva aqui. | Escreva aqui. | Escreva aqui. | Escreva aqui. |
| H3, se necessária | Escreva aqui. | Escreva aqui. | Escreva aqui. | Escreva aqui. |""",
"""| Hipótese provisória | Evidência exploratória | Explicação alternativa | Dados adicionais necessários | Método futuro |
|---|---|---|---|---|
| **H1.** A diferença observada entre períodos pode estar associada ao **complemento** do termo, e não à sua frequência: de liberdade como condição do regime para liberdade como lista de direitos enumeráveis | Figura 4: `justiça`, `desenvolvimento`, `política` (1985–1995) contra `individuais`, `direitos`, `expressão`, `culto` (1999–2023); bigrama `liberdades individuais` com PMI 12,03 | Convenção do gênero: enumerar direitos pode ser praxe de posse pós-Constituição de 1988, independente de projeto político | Discursos de posse estaduais e mensagens anuais ao Congresso, para verificar se a enumeração é praxe institucional | Codificação manual dos trechos por tipo de liberdade, com dupla codificação e medida de concordância |
| **H2.** O uso do termo pode estar associado a **conjunturas de disputa sobre o regime**, e não ao presidente ou ao partido | Forma em U da Figura 3: picos em 1985 e 2019–2023, vale em 1999–2007; Lula registra 0, 0 e 7 em três posses | Efeito de extensão e de estilo do redator: discursos curtos e programáticos concentram mais o vocabulário | Séries de pronunciamentos ao longo de cada mandato, não apenas as posses | Comparação de taxas entre gêneros discursivos do mesmo governo |
| **H3.** Em 2023 o termo pode estar funcionando como **objeto de disputa** e não como valor afirmado | Trechos `a liberdade que eles pregam...` e `supostas liberdades individuais`, ambos com marcação de distanciamento | Recurso retórico pontual de um único discurso, sem continuidade | Discursos de 2023 em diante e pronunciamentos do campo adversário no mesmo período | Análise de polaridade e de marcadores de atribuição de voz nos trechos |"""
)

# --------------------------------------------- 7. limitações e reprodutibilidade
troca(8, "**Limitações do relatório:** Escreva aqui.",
"""**Limitações do relatório**

- **Sub-representação.** Só o chefe do Executivo federal, só no rito de posse. Oposição, Legislativo, movimentos sociais e governos estaduais estão fora. O gênero é conciliador por convenção e tende a suavizar disputas.
- **Escolhas que afetam o resultado.** A regex `\\bliberdades?\\b` exclui `livre`, `livremente` e `libertário`; a janela ±5 corta sintagmas longos; a lista de stopwords é minha; a partição 1985–1995 / 1999–2023 é analítica, não documental; e a segmentação por sentença substituiu a segmentação por parágrafo prevista no protocolo, porque só o arquivo de 2023 preserva parágrafos.
- **Construção institucional da base.** As transcrições são de terceiros (livro e acervo jornalístico), não do registro oficial primário; o texto de 2023 vem de origem diferente dos demais. Sarney (1985) e Temer (2016) entram como casos limítrofes, por não terem proferido o texto na sessão solene de posse.
- **Conclusões que não devem ser formuladas.** Que houve mudança ideológica demonstrada; que a diferença entre períodos é estatisticamente significativa; que a ausência do termo indica ausência do tema; que o discurso de posse representa o pensamento do governo ou da sociedade."""
)

troca(8, "**Instruções para reproduzir:** Escreva aqui.",
"""**Instruções para reproduzir**

1. **Entradas.** `dados/brutos/`: 12 arquivos `.txt` imutáveis, `metadados_discursos.csv` e `proveniencia_base_publica.json` (fonte, endereço, data de acesso 2026-09-17, recorte e ressalvas).
2. **Ambiente.** Python 3.12, `pandas` 3.0, `matplotlib` 3.10; bibliotecas padrão `pathlib`, `re`, `json`, `unicodedata`, `collections`.
3. **Ordem de execução.** `01_ingestao.py` → `02_base_processavel.py` → `03_figuras.py` → este notebook. Nenhuma etapa edita arquivos brutos.
4. **Parâmetros alteráveis.** alvo `\\bliberdades?\\b`; janela de coocorrência ±5; `STOPWORDS`; frequência mínima de PMI = 2; `bins` do histograma de 1.000 em 1.000; corte de período em 1995; `m` da TTR padronizada = menor documento (621).
5. **Tabelas que sustentam cada figura.** Fig. 1 e 3 → `documentos_processaveis.csv`; Fig. 2 → mesma tabela, coluna `palavras`; Fig. 4 → `coocorrencias.csv`.
6. **Caminho do agregado ao documento.** agregado → `id_doc` → `trecho_id` (com `posicao_sentenca` e `total_sentencas`) → `dados/brutos/<id_doc>.txt`. As regras aplicadas estão em `dados/intermediarios/log_transformacoes.csv`; as exclusões, em `dados/derivados/motivos_exclusao.csv`."""
)

# ------------------------------------------------------- 9. parecer / 10. rubrica
troca(10, "**Parecer recebido:** Escreva aqui.",
"**Parecer recebido:** pendente — a revisão por pares ainda não foi realizada.")
troca(10, "**Mudanças realizadas após a revisão:** Escreva aqui.",
"**Mudanças realizadas após a revisão:** pendente, aguardando o parecer.")

troca(11, """| Critério | 0 | 1 | 2 | Minha nota e evidência |
|---|---|---|---|---|
| escopo e qualidade | não definidos | parciais | pergunta, unidade, cobertura e limites coerentes | Escreva aqui. |
| correção quantitativa | cálculos inadequados | resultados sem convenções | medidas, denominadores e extremos verificados | Escreva aqui. |
| exploração textual | regras ausentes | resultados sem contexto | regras, métricas e concordâncias documentadas | Escreva aqui. |
| visualização e acessibilidade | gráficos inadequados | documentação parcial | quatro figuras com tabela e descrição | Escreva aqui. |
| retorno aos casos | ausente | casos apenas confirmatórios | três casos que qualificam agregados | Escreva aqui. |
| hipóteses e limites | conclusão indevida | limites genéricos | hipóteses alternativas e limites específicos | Escreva aqui. |
| reprodutibilidade | percurso desconhecido | instruções incompletas | entradas, parâmetros e ordem reconstruíveis | Escreva aqui. |""",
"""| Critério | 0 | 1 | 2 | Minha nota e evidência |
|---|---|---|---|---|
| escopo e qualidade | não definidos | parciais | pergunta, unidade, cobertura e limites coerentes | **2** — duas unidades declaradas, exclusões registradas em `motivos_exclusao.csv`, casos limítrofes identificados |
| correção quantitativa | cálculos inadequados | resultados sem convenções | medidas, denominadores e extremos verificados | **2** — `ddof=1`, quartis por interpolação linear, limites de 1,5·IQR explícitos, extremos inspecionados sem remoção |
| exploração textual | regras ausentes | resultados sem contexto | regras, métricas e concordâncias documentadas | **2** — tokenização por documento, dois denominadores, 55 concordâncias com `id_doc`, PMI com frequência mínima, TTR padronizada |
| visualização e acessibilidade | gráficos inadequados | documentação parcial | quatro figuras com tabela e descrição | **2** — quatro figuras, cada uma com tabela equivalente e descrição alternativa |
| retorno aos casos | ausente | casos apenas confirmatórios | três casos que qualificam agregados | **2** — 2023 contradiz a leitura da coocorrência, 1992 explica o zero, 1985 confirma mas qualifica o pico |
| hipóteses e limites | conclusão indevida | limites genéricos | hipóteses alternativas e limites específicos | **2** — três hipóteses provisórias, cada uma com explicação alternativa e dados necessários |
| reprodutibilidade | percurso desconhecido | instruções incompletas | entradas, parâmetros e ordem reconstruíveis | **1** — scripts, parâmetros e log estão registrados, mas as versões de pacotes não estão fixadas em arquivo de ambiente |"""
)

troca(11, """**Total:** Escreva aqui, de 14 pontos.""",
"""**Total:** 13 de 14 pontos. O ponto perdido é de reprodutibilidade: falta um
`requirements.txt` com versões fixadas.""")

# ---------------------------------------------------------- referências (anexo)
referencias = md("""## 11. Referências utilizadas

1. BONFIM, João Bosco Bezerra. *Palavra de Presidente: os discursos presidenciais de posse, de Deodoro a Lula*. Brasília: Senado Federal, 2007. — fonte primária das transcrições até 2003.
2. D'IGNAZIO, Catherine; KLEIN, Lauren F. *Data Feminism*. Cambridge: MIT Press, 2020. — fundamenta o tratamento de silêncios e a declaração de escopo.
3. KOSELLECK, Reinhart. *Futuro Passado: contribuição à semântica dos tempos históricos*. Rio de Janeiro: Contraponto/PUC-Rio, 2006. — fundamenta a leitura de "liberdade" como conceito em disputa, base da H3.
4. RAWSON, Katie; MUÑOZ, Trevor. Against Cleaning. In: *Debates in the Digital Humanities*, 2019. — fundamenta o log de transformações e a recusa de exclusões automáticas.
5. STEVENS, S. S. On the Theory of Scales of Measurement. *Science*, 1946. — base da classificação de variáveis da seção 1.
6. Repositório `estadao/discurso-de-posse-presidentes`. — origem das transcrições legíveis por máquina; proveniência em `dados/brutos/proveniencia_base_publica.json`.""")

# ------------------------------------------------------------ montagem final
def dividir(indice, marcador):
    """Separa uma célula em duas, no ponto em que o marcador aparece."""
    fonte = c[indice].source
    k = fonte.index(marcador)
    return md(fonte[:k].rstrip()), md(fonte[k:])

quant_topo, quant_base = dividir(3, "### Evidências mínimas")
textual_topo, textual_base = dividir(4, "### Evidências mínimas")
casos_topo, casos_base = dividir(6, "| Caso/ID |")

nb.cells = [c[0], c[1], c[2], setup,
            quant_topo, quant, quant_base,
            textual_topo, textual, textual_base,
            c[5], fig1, an1, fig2, an2, fig3, an3, fig4, an4,
            casos_topo, casos, casos_base,
            c[7], c[8], c[9], c[10], c[11], referencias]
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, "04_oficina_relatorio_exploratorio_RESPONDIDO.ipynb")
print("células:", len(nb.cells))
