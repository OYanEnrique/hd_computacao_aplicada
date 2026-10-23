"""Ingestão: copia os discursos da fonte aberta para dados/brutos/ e escreve metadados + proveniência.

Fonte: repositório estadao/discurso-de-posse-presidentes (transcrições dos discursos
de posse; até 2003 a partir do livro "Palavra de Presidente", de João Bosco Bezerra
Bonfim; posteriores transcritos do acervo do Estadão / Biblioteca da Presidência).
Nenhum texto é editado nesta etapa: os arquivos são cópias imutáveis.
"""
from pathlib import Path
import json
import shutil
import csv

FONTE = Path("/home/claude/estadao/output/txts-limpos")
BRUTOS = Path("dados/brutos")
BRUTOS.mkdir(parents=True, exist_ok=True)

# (arquivo_origem, id_doc, ano_posse, presidente, tipo_discurso, caso_limitrofe, observacao)
INCLUIDOS = [
    ("jose-sarney-1985.txt", "DISCURSO_1985_SARNEY", 1985, "José Sarney",
     "pronunciamento de posse", True,
     "O compilador registra como pronunciamento de posse um discurso proferido cerca de quatro meses após a assunção do cargo."),
    ("fernando-collor-1990.txt", "DISCURSO_1990_COLLOR", 1990, "Fernando Collor de Mello",
     "posse no Congresso Nacional", False, ""),
    ("itamar-franco-1992.txt", "DISCURSO_1992_ITAMAR", 1992, "Itamar Franco",
     "posse no Congresso Nacional", False, ""),
    ("fernando-henrique-cardoso-1-1994.txt", "DISCURSO_1995_FHC", 1995, "Fernando Henrique Cardoso",
     "posse no Congresso Nacional", False,
     "Arquivo de origem nomeado pelo ano da eleição (1994); a posse ocorreu em 01/01/1995."),
    ("fernando-henrique-cardoso-2-1999.txt", "DISCURSO_1999_FHC", 1999, "Fernando Henrique Cardoso",
     "posse no Congresso Nacional", False, ""),
    ("lula-1-2003.txt", "DISCURSO_2003_LULA", 2003, "Luiz Inácio Lula da Silva",
     "posse no Congresso Nacional", False, ""),
    ("lula-2-2007.txt", "DISCURSO_2007_LULA", 2007, "Luiz Inácio Lula da Silva",
     "posse no Congresso Nacional", False, ""),
    ("dilma-rousseff-1-2011.txt", "DISCURSO_2011_DILMA", 2011, "Dilma Rousseff",
     "posse no Congresso Nacional", False, ""),
    ("dilma-rousseff-2-2015.txt", "DISCURSO_2015_DILMA", 2015, "Dilma Rousseff",
     "posse no Congresso Nacional", False, ""),
    ("michel-temer-2016.txt", "DISCURSO_2016_TEMER", 2016, "Michel Temer",
     "primeiro pronunciamento no exercício da Presidência", True,
     "Não houve sessão solene de posse no Congresso; o compilador registra o primeiro pronunciamento como equivalente."),
    ("jair-bolsonaro-1-2019.txt", "DISCURSO_2019_BOLSONARO", 2019, "Jair Bolsonaro",
     "posse no Congresso Nacional", False, ""),
    ("DISCURSO_2023_LULA.txt", "DISCURSO_2023_LULA", 2023, "Luiz Inácio Lula da Silva",
     "posse no Congresso Nacional", False,
     "Transcrição fornecida pelo autor do projeto; único arquivo do corpus que preserva quebras de parágrafo."),
]

EXCLUIDOS = [
    ("DISCURSO_1985_TANCREDO", "tancredo-neves-1985.txt", "gênero discursivo não compatível",
     "Tancredo Neves não chegou a tomar posse; o texto foi lido por José Sarney aos ministros, fora da cerimônia de posse."),
    ("DISCURSOS_ANTERIORES_A_1985", "(24 arquivos)", "fora do período",
     "Discursos de posse de 1889 a 1979 presentes na fonte, excluídos pelo recorte temporal da Redemocratização."),
]

linhas_meta = []
UPLOADS = Path("/mnt/user-data/uploads")

for arquivo, id_doc, ano, presidente, tipo, limitrofe, obs in INCLUIDOS:
    origem = FONTE / arquivo
    if not origem.exists():
        origem = UPLOADS / arquivo
    texto = origem.read_text(encoding="utf-8")
    destino = BRUTOS / f"{id_doc}.txt"
    shutil.copyfile(origem, destino)
    linhas_meta.append({
        "id_doc": id_doc,
        "ano": ano,
        "presidente": presidente,
        "tipo_discurso": tipo,
        "caso_limitrofe": limitrofe,
        "nome_arquivo_origem": arquivo,
        "arquivo_bruto": destino.name,
        "observacao": obs,
    })

with open(BRUTOS / "metadados_discursos.csv", "w", encoding="utf-8", newline="") as f:
    escritor = csv.DictWriter(f, fieldnames=list(linhas_meta[0].keys()))
    escritor.writeheader()
    escritor.writerows(linhas_meta)

Path("dados/derivados").mkdir(parents=True, exist_ok=True)
with open("dados/derivados/motivos_exclusao.csv", "w", encoding="utf-8", newline="") as f:
    escritor = csv.writer(f)
    escritor.writerow(["id_doc", "arquivo", "tipo_descarte", "justificativa"])
    escritor.writerows(EXCLUIDOS)

proveniencia = {
    "fonte": "estadao/discurso-de-posse-presidentes (GitHub)",
    "endereco": "https://github.com/estadao/discurso-de-posse-presidentes",
    "licenca_repositorio": "ver LICENSE do repositório de origem",
    "fonte_primaria_ate_2003": "BONFIM, João Bosco Bezerra. Palavra de Presidente.",
    "fonte_primaria_apos_2003": "acervo do Estadão e Biblioteca da Presidência da República",
    "fonte_2023": "transcrição fornecida pelo autor do projeto (arquivo DISCURSO_2023_LULA.txt)",
    "data_de_acesso": "2026-09-17",
    "recorte": "discursos de posse presidencial, 1985-2023",
    "cobertura": "12 discursos, 1985-2023; o discurso de 2023 foi fornecido pelo autor do projeto, os demais vêm do repositório citado",
    "ressalva": "transcrições de terceiros, sem quebras de parágrafo preservadas; não substituem a consulta ao registro oficial",
    "natureza": "documentos públicos oficiais (pronunciamentos de chefes de Estado)",
}
(BRUTOS / "proveniencia_base_publica.json").write_text(
    json.dumps(proveniencia, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Discursos ingeridos:", len(linhas_meta))
print("Registros de exclusão:", len(EXCLUIDOS))
