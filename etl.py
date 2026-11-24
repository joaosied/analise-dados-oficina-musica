"""Etapa 2 - Pipeline de tratamento (ETL)

Base: cursos da 43a Oficina de Musica de Curitiba (planilha .xlsx)
Entrada: dados/base_oficina_musica.xlsx
Saidas: dados/dados_tratados.csv e log_etl.txt

Para rodar (dentro da pasta do projeto): python etl.py
"""
from pathlib import Path

import pandas as pd

ARQ_ENTRADA = "dados/base_oficina_musica.xlsx"
ARQ_SAIDA = "dados/dados_tratados.csv"
ARQ_LOG = "log_etl.txt"

# Atividades de sustentabilidade que nao sao de musica (IDs 1794 a 1803)
ids_fora_do_tema = range(1794, 1804)

# Nomes originais da planilha -> nomes padronizados (minusculo com underline)
colunas = {
    "CUR_IDF": "id_curso",
    "CUR_TITULO": "titulo_original",
    "OFI_IDF": "ofi_codigo",
    "NUC_IDF": "nucleo_codigo",
    "CUR_TIPO": "tipo_codigo",
    "ESP_IDF": "esp_codigo",
    "CUR_EMENTA": "ementa",
    "CUR_REQUISITOS": "requisitos",
    "CUR_VALOR": "valor",
    "CUR_SELECAO": "tem_selecao",
    "CUR_PUBLICADO": "publicado",
    "CUR_DATA_CADASTRO": "data_cadastro",
    "CUR_DATA_PUBLICACAO": "data_publicacao",
    "CUR_OBRIG_VIDEO": "exige_video",
}

linhas_log = []


def log(texto=""):
    """Mostra o texto no terminal e guarda para salvar no log_etl.txt."""
    print(texto)
    linhas_log.append(str(texto))


def modalidade(titulo):
    """Define a modalidade do curso pela primeira palavra do titulo."""
    t = titulo.lower()
    for palavra in ["workshop", "palestra", "prática", "regência", "estágio", "colônia de férias", "oficina"]:
        if t.startswith(palavra):
            return palavra.capitalize()
    return "Curso"


# 1. Leitura
# Le tudo como texto; a tipagem correta e feita mais abaixo
log("1. LEITURA")
df = pd.read_excel(ARQ_ENTRADA, dtype=str)
log(f"Linhas lidas: {len(df)}")

# A segunda linha da planilha e so uma linha de tracos, nao e um curso
df = df[~df["CUR_IDF"].str.startswith("---")]
log(f"Linhas sem a linha de tracos: {len(df)}")

# 2. Limpeza de texto
log("\n2. LIMPEZA DE TEXTO")
# Tira espacos do comeco/fim e espacos duplicados de todas as colunas
df = df.apply(lambda c: c.str.strip().str.replace(r"\s+", " ", regex=True))
df = df.rename(columns=colunas)
# Sobra de codigo HTML que veio nas ementas
df["ementa"] = df["ementa"].str.replace("&BULL,", "-", regex=False)
log("Espacos extras removidos, colunas renomeadas e '&BULL,' trocado por '-' nas ementas")

# 3. Tipagem
log("\n3. TIPAGEM")
for c in ["id_curso", "ofi_codigo", "nucleo_codigo", "tipo_codigo", "esp_codigo"]:
    df[c] = df[c].astype(int)
# O valor ".00" vira 0.0
df["valor"] = pd.to_numeric(df["valor"])
for c in ["tem_selecao", "publicado", "exige_video"]:
    df[c] = df[c].astype(int).astype(bool)
df["data_cadastro"] = pd.to_datetime(df["data_cadastro"])
df["data_publicacao"] = pd.to_datetime(df["data_publicacao"])
log("Tipos das colunas:")
log(df.dtypes.to_string())

# 4. Duplicados
log("\n4. DUPLICADOS")
log(f"Linhas duplicadas: {df.duplicated().sum()}")
log(f"IDs repetidos: {df.duplicated(subset='id_curso').sum()}")
log(f"Titulos repetidos: {df['titulo_original'].str.upper().duplicated().sum()}")
df = df.drop_duplicates(subset="id_curso")

# 5. Valores nulos
log("\n5. VALORES NULOS")
nulos = df.isna().sum()
log("Nulos antes do tratamento:")
log(nulos[nulos > 0].to_string())

# Valor nulo = curso sem preco cadastrado. So 3 cursos tem valor maior que zero,
# entao o nulo vira 0 (gratuito) e a coluna valor_informado guarda quais eram nulos
df["valor_informado"] = df["valor"].notna()
df["valor"] = df["valor"].fillna(0)

# Nao da para saber a data de publicacao real, entao ela continua nula
# e a coluna sem_data_publicacao marca esses cursos
df["sem_data_publicacao"] = df["data_publicacao"].isna()
log(f"valor: {(~df['valor_informado']).sum()} nulos preenchidos com 0 (gratuito)")
log(f"data_publicacao: {df['sem_data_publicacao'].sum()} nulos mantidos e marcados")

# 6. Filtros
log("\n6. FILTROS")
log(f"Linhas antes dos filtros: {len(df)}")
# Fica so o que esta publicado
df = df[df["publicado"]]
log(f"Depois de filtrar publicados: {len(df)}")

# Tira as atividades que nao sao de musica
log("Removidos por nao serem de musica:")
for _, linha in df[df["id_curso"].isin(ids_fora_do_tema)].iterrows():
    log(f"  {linha['id_curso']} - {linha['titulo_original']}")
df = df[~df["id_curso"].isin(ids_fora_do_tema)]
log(f"Linhas depois dos filtros: {len(df)}")

# 7. Normalizacao estrutural
log("\n7. NORMALIZACAO ESTRUTURAL")
# Titulo no formato "Nome do curso | Responsavel": separa em duas colunas
partes = df["titulo_original"].str.split(" | ", n=1, expand=True, regex=False)
df["nome_curso"] = partes[0]
# O responsavel pode ser ministrante, grupo ou local (ex: colonia de ferias)
df["responsavel"] = partes[1].fillna("Não informado")
df["modalidade"] = df["titulo_original"].apply(modalidade)
df["tamanho_ementa"] = df["ementa"].str.len()
df["mes_cadastro"] = df["data_cadastro"].dt.strftime("%Y-%m")
# Dias entre o cadastro e a publicacao do curso
df["dias_ate_publicar"] = (df["data_publicacao"].dt.normalize() - df["data_cadastro"].dt.normalize()).dt.days

# Colunas que nao ajudam: ofi_codigo e publicado tem um valor unico
# e requisitos e um texto padrao do regulamento
for c in ["ofi_codigo", "publicado", "requisitos"]:
    log(f"Coluna removida: {c} (valores unicos: {df[c].nunique()})")
df = df.drop(columns=["ofi_codigo", "publicado", "requisitos"])

df = df[[
    "id_curso", "nome_curso", "responsavel", "modalidade", "tipo_codigo",
    "nucleo_codigo", "esp_codigo", "valor", "valor_informado", "tem_selecao",
    "exige_video", "data_cadastro", "data_publicacao", "sem_data_publicacao",
    "mes_cadastro", "dias_ate_publicar", "tamanho_ementa", "titulo_original", "ementa",
]]
df = df.sort_values("id_curso").reset_index(drop=True)
log("Cursos por modalidade:")
log(df["modalidade"].value_counts().to_string())

# 8. Resultado final
log("\n8. RESULTADO FINAL")
log(f"Linhas: {len(df)} | Colunas: {df.shape[1]}")
nulos = df.isna().sum()
# So devem sobrar nulos nas datas de publicacao
log("Nulos que sobraram:")
log(nulos[nulos > 0].to_string())

df.to_csv(ARQ_SAIDA, index=False, encoding="utf-8-sig")
log(f"\nArquivo salvo em {ARQ_SAIDA}")
Path(ARQ_LOG).write_text("\n".join(linhas_log), encoding="utf-8")
