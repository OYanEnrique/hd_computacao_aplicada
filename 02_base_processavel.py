"""Estrutura, limpa, segmenta e integra a base processável.

Produz:
  dados/intermediarios/catalogo_normalizado.csv
  dados/intermediarios/log_transformacoes.csv
  dados/derivados/documentos_processaveis.csv   (unidade: um discurso)
  dados/derivados/discursos_trechos.csv         (unidade: um trecho com "liberdade")
  dados/derivados/coocorrencias.csv             (unidade: termo-coocorrente por discurso)
"""
from pathlib import Path
import json
import re
import unicodedata
from collections import Counter

import pandas as pd

BRUTOS = Path("dados/brutos")
INTER = Path("dados/intermediarios")
DERIV = Path("dados/derivados")
INTER.mkdir(parents=True, exist_ok=True)
DERIV.mkdir(parents=True, exist_ok=True)

ALVO = re.compile(r"\bliberdades?\b", re.IGNORECASE)
TOKEN = re.compile(r"[a-záàâãéêíóôõúüçñ]+")
STOPWORDS = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "e", "é", "em", "no", "na", "nos", "nas", "que", "com", "por", "para", "se", "ao",
    "aos", "à", "às", "não", "sua", "seu", "suas", "seus", "mais", "como", "mas", "ou",
    "nossa", "nosso", "nossas", "nossos", "esta", "este", "isso", "sem", "ser", "foi",
    "já", "também", "todos", "todas", "sobre", "pela", "pelo", "pelos", "pelas", "me",
    "nós", "eu", "ele", "ela", "lhe", "há", "das", "aquele", "quem", "onde", "quando",
    "muito", "muita", "muitos", "muitas", "seja", "são", "tem", "ter", "entre", "ainda",
    "dessa", "desse", "deste", "desta", "nesta", "neste", "pelos", "num", "numa", "só",
    "vamos", "vai", "fazer", "depois", "antes", "sempre", "cada", "outro", "outra", "toda",
    "todo", "aqui", "hoje", "porque", "assim", "seus", "essa", "esse", "nem", "até", "mesmo",
}

# ---------------------------------------------------------------- 1. leitura e limpeza
metadados = pd.read_csv(BRUTOS / "metadados_discursos.csv", dtype={"ano": "Int64"})

def normalizar(texto: str) -> str:
    """Normaliza codificação e espaços. Não remove pontuação nem altera palavras."""
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t\u00a0]+", " ", texto)
    return texto.strip()

registros = []
for linha in metadados.itertuples():
    bruto = (BRUTOS / linha.arquivo_bruto).read_text(encoding="utf-8", errors="strict")
    limpo = normalizar(bruto)
    assert len(limpo) > 0, f"texto vazio em {linha.id_doc}"
    registros.append({
        "id_doc": linha.id_doc,
        "texto_bruto_caracteres": len(bruto),
        "texto_conteudo": limpo,
    })

catalogo = metadados.merge(pd.DataFrame(registros), on="id_doc", how="left",
                           validate="one_to_one", indicator=True)
assert (catalogo["_merge"] == "both").all()
catalogo = catalogo.drop(columns="_merge")

# ------------------------------------------------------------------- 2. medidas por documento
catalogo["tokens"] = catalogo["texto_conteudo"].map(lambda t: TOKEN.findall(t.lower()))
catalogo["palavras"] = catalogo["tokens"].map(len)
catalogo["formas"] = catalogo["tokens"].map(lambda ts: len(set(ts)))
catalogo["ttr"] = catalogo["formas"] / catalogo["palavras"]
catalogo["ocorrencias_liberdade"] = catalogo["texto_conteudo"].map(
    lambda t: len(ALVO.findall(t))
)
catalogo["taxa_liberdade_mil"] = (
    catalogo["ocorrencias_liberdade"] / catalogo["palavras"] * 1000
)
catalogo["razao_ausencia"] = catalogo["ocorrencias_liberdade"].map(
    lambda n: "pronunciamento sem menção ao termo" if n == 0 else pd.NA
)
catalogo["partido"] = pd.NA
catalogo["razao_partido_ausente"] = "não verificado em fonte documental nesta versão"

catalogo.drop(columns=["tokens", "texto_conteudo"]).to_csv(
    INTER / "catalogo_normalizado.csv", index=False
)

# --------------------------------------------------------------------- 3. segmentação
# A fonte não preserva quebras de parágrafo: o texto chega como bloco corrido.
# Regra adotada: segmentar em sentenças e definir o trecho como a sentença-alvo
# acrescida de uma sentença à esquerda e uma à direita (contexto imediato).
FIM_SENTENCA = re.compile(r"(?<=[.!?;])\s+")

linhas_trechos = []
for linha in catalogo.itertuples():
    sentencas = [s.strip() for s in FIM_SENTENCA.split(linha.texto_conteudo) if s.strip()]
    for i, sentenca in enumerate(sentencas):
        if not ALVO.search(sentenca):
            continue
        inicio, fim = max(0, i - 1), min(len(sentencas), i + 2)
        linhas_trechos.append({
            "trecho_id": f"{linha.id_doc}_SENT_{i + 1:03d}",
            "id_doc": linha.id_doc,
            "ano": linha.ano,
            "presidente": linha.presidente,
            "posicao_sentenca": i + 1,
            "total_sentencas": len(sentencas),
            "posicao_relativa": round((i + 1) / len(sentencas), 3),
            "ocorrencias_no_trecho": len(ALVO.findall(sentenca)),
            "sentenca_alvo": sentenca,
            "texto_trecho": " ".join(sentencas[inicio:fim]),
        })

trechos = pd.DataFrame(linhas_trechos)

# ------------------------------------------------------- 4. coocorrências (janela ±5 tokens)
JANELA = 5
linhas_coocorrencia = []
for linha in catalogo.itertuples():
    tokens = linha.tokens
    contador = Counter()
    for pos, token in enumerate(tokens):
        if not ALVO.fullmatch(token):
            continue
        ini, fim = max(0, pos - JANELA), min(len(tokens), pos + JANELA + 1)
        for vizinho in tokens[ini:pos] + tokens[pos + 1:fim]:
            if vizinho in STOPWORDS or len(vizinho) < 3 or ALVO.fullmatch(vizinho):
                continue
            contador[vizinho] += 1
    for termo, frequencia in contador.items():
        linhas_coocorrencia.append({
            "id_doc": linha.id_doc,
            "ano": linha.ano,
            "presidente": linha.presidente,
            "termo_coocorrente": termo,
            "frequencia": frequencia,
        })

coocorrencias = pd.DataFrame(linhas_coocorrencia)

# ----------------------------------------------------------------------- 5. integração
documentos = catalogo.drop(columns=["tokens"])
contagem_trechos = trechos.groupby("id_doc").size().rename("n_trechos")
documentos = documentos.merge(contagem_trechos, on="id_doc", how="left",
                              validate="one_to_one", indicator=True)
documentos["n_trechos"] = documentos["n_trechos"].fillna(0).astype(int)
documentos = documentos.drop(columns="_merge")

# ---------------------------------------------------------------------------- 6. testes
assert documentos["id_doc"].is_unique, "id_doc duplicado"
assert trechos["trecho_id"].is_unique, "trecho_id duplicado"
assert set(trechos["id_doc"]).issubset(set(documentos["id_doc"])), "trecho órfão"
assert set(coocorrencias["id_doc"]).issubset(set(documentos["id_doc"])), "coocorrência órfã"
assert documentos["id_doc"].nunique() == 12, "número de discursos alterado"
assert documentos[["id_doc", "ano", "presidente"]].notna().all().all(), "metadado nulo"

documentos.to_csv(DERIV / "documentos_processaveis.csv", index=False)
trechos.to_csv(DERIV / "discursos_trechos.csv", index=False)
coocorrencias.to_csv(DERIV / "coocorrencias.csv", index=False)

# ------------------------------------------------------------------------------- 7. log
log = pd.DataFrame([
    {"campo": "texto_conteudo", "problema": "codificação e espaçamento irregulares",
     "regra": "NFC + colapso de espaços; sem remoção de pontuação",
     "justificativa": "tornar a segmentação estável", "afetados": len(documentos),
     "teste": "len(texto) > 0 e leitura UTF-8 estrita", "reversivel": "sim (bruto imutável)",
     "perda": "hifenização e formatação de origem", "responsavel": "Yan Enrique"},
    {"campo": "trecho_id", "problema": "fonte sem quebras de parágrafo",
     "regra": "segmentação por sentença; trecho = sentença-alvo ± 1 sentença",
     "justificativa": "a unidade de parágrafo prevista no protocolo não é recuperável na fonte",
     "afetados": len(trechos), "teste": "trecho_id único; id_doc preservado",
     "reversivel": "sim (posicao_sentenca permite recompor)",
     "perda": "fronteiras de parágrafo do original", "responsavel": "Yan Enrique"},
    {"campo": "trecho_id (2023)", "problema": "DISCURSO_2023_LULA preserva parágrafos; os demais não",
     "regra": "mesma segmentação por sentença aplicada a todos os documentos",
     "justificativa": "manter a unidade comparável entre os 12 discursos",
     "afetados": 7, "teste": "posicao_sentenca e total_sentencas registrados",
     "reversivel": "sim (bruto com parágrafos preservado)",
     "perda": "a estrutura de parágrafo disponível apenas em 2023 não é aproveitada",
     "responsavel": "Yan Enrique"},
    {"campo": "id_doc", "problema": "nomes de arquivo heterogêneos na fonte",
     "regra": "DISCURSO_ANO_PRESIDENTE; ano = ano da posse",
     "justificativa": "chave primária estável", "afetados": len(documentos),
     "teste": "is_unique", "reversivel": "sim (nome_arquivo_origem preservado)",
     "perda": "denominação do custodiante", "responsavel": "Yan Enrique"},
    {"campo": "partido", "problema": "afiliação partidária não verificada em fonte documental",
     "regra": "campo mantido nulo com razao_partido_ausente",
     "justificativa": "não atribuir valor sem evidência", "afetados": len(documentos),
     "teste": "coluna integralmente nula", "reversivel": "sim",
     "perda": "agregação por legenda indisponível", "responsavel": "Yan Enrique"},
    {"campo": "coocorrencias", "problema": "palavras funcionais dominam o entorno",
     "regra": "janela ±5 tokens, remoção de stopwords e tokens < 3 caracteres",
     "justificativa": "isolar o campo semântico do termo", "afetados": len(coocorrencias),
     "teste": "id_doc rastreável até o documento", "reversivel": "sim (texto_trecho preservado)",
     "perda": "coesão sintática do entorno", "responsavel": "Yan Enrique"},
])
log.to_csv(INTER / "log_transformacoes.csv", index=False)

print(documentos[["id_doc", "ano", "presidente", "palavras", "ocorrencias_liberdade",
                  "taxa_liberdade_mil", "n_trechos", "ttr"]].to_string(index=False))
print("\ntrechos:", len(trechos), "| coocorrências (linhas):", len(coocorrencias))
