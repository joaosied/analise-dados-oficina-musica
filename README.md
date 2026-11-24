Grupo: Cesar, Eduardo, Gabriel Turra e João

# Análise de dados abertos - Oficina de Música de Curitiba

Trabalho do 2º bimestre de Análise de Dados Governamentais Abertos (UniBrasil).

A base é uma planilha com os cursos da 43ª Oficina de Música de Curitiba (114 linhas e 14 colunas). O projeto tem duas partes: um script que trata a planilha (`etl.py`) e um dashboard que mostra gráficos em cima dos dados tratados (`dashboard.py`). O relatório técnico completo está em `relatorio/`.

## O que tem no repositório

```
etl.py                       tratamento da planilha (Etapa 2)
dashboard.py                 dashboard em Streamlit (Etapa 3)
requirements.txt             bibliotecas necessárias
log_etl.txt                  o que o etl.py imprimiu na última execução
dados/
  base_oficina_musica.xlsx   planilha original
  dados_tratados.csv         resultado do etl.py
imagens/                     prints do dashboard usados no relatório
relatorio/
  relatorio_tecnico.pdf      relatório técnico final (Etapa 4)
  relatorio_tecnico.docx     mesmo relatório, editável
```

## Como reproduzir

Precisa de Python 3.10 ou mais novo. Pra ver a versão: `python3 --version`. Se for mais velho que isso, instala o Python novo em python.org/downloads.

Os comandos abaixo são de Mac/Linux. No Windows troca `python3` por `python` e `source venv/bin/activate` por `venv\Scripts\activate`.

1. Baixa o repositório e entra na pasta:

```
git clone https://github.com/joaosied/analise-dados-oficina-musica.git
cd analise-dados-oficina-musica
```

Se preferir, dá pra baixar o ZIP pelo botão Code do GitHub e abrir a pasta no terminal.

2. Cria o ambiente virtual e ativa:

```
python3 -m venv venv
source venv/bin/activate
```

Vai aparecer `(venv)` no começo da linha do terminal.

3. Instala as bibliotecas:

```
pip install -r requirements.txt
```

4. Roda o tratamento (opcional, o CSV já vem pronto):

```
python etl.py
```

Ele mostra cada etapa no terminal, salva o `log_etl.txt` e recria o `dados/dados_tratados.csv`. Rodando de novo o resultado é o mesmo.

5. Abre o dashboard:

```
streamlit run dashboard.py
```

Abre sozinho no navegador. Se não abrir, entra em http://localhost:8501.

Pra parar é Ctrl + C no terminal. Da próxima vez, entra na pasta e roda só `source venv/bin/activate` antes do `streamlit run`.

Testado com Python 3.13, pandas 3.0, openpyxl 3.1, plotly 7.1 e streamlit 1.67.

## Problemas que já apareceram

- `Could not open requirements file`: o terminal não está dentro da pasta do projeto. Usa o `cd` e confere com `ls` se aparece o `requirements.txt`.
- `FileNotFoundError` ao rodar o `etl.py`: a planilha tem que estar em `dados/` com o nome `base_oficina_musica.xlsx`.
- Erro de versão do Python na instalação: o Python está velho, instala um mais novo.
- Dashboard dando erro de arquivo: roda o `python etl.py` antes pra gerar o CSV.

## O que o etl.py faz

1. Lê a planilha e tira a linha de traços que vem logo abaixo do cabeçalho.
2. Tira espaços sobrando, renomeia as colunas e limpa um resto de código HTML (`&BULL,`) que veio nas ementas.
3. Ajusta os tipos: números, datas e colunas de sim/não.
4. Confere duplicados (linhas, IDs e títulos). Não tinha nenhum.
5. Trata os nulos: `valor` vazio vira 0 (só 3 cursos são pagos) e `data_publicacao` vazia continua vazia, só marcada em uma coluna.
6. Filtra só os cursos publicados e tira 10 atividades que não são de música (IDs 1794 a 1803, como plantio de árvores e visita guiada). Sobram 104 cursos.
7. Separa o título em nome do curso e responsável, cria a modalidade (workshop, palestra, prática etc.) e outras colunas que o dashboard usa.

## Hipóteses do dashboard

| Hipótese | Resultado |
|---|---|
| H1: a maioria dos cursos é gratuita | Confirmada: 101 de 104 (97%) |
| H2: práticas, workshops, palestras e colônias de férias não têm seleção por vídeo | Confirmada: 0 de 29 cursos com seleção |
| H3: cursos com seleção têm ementa mais longa | Confirmada: mediana de 3497 caracteres contra 913 |
| H4: 20% dos núcleos concentram mais da metade dos cursos | Não confirmada: os 5 maiores núcleos têm 40% dos cursos |
| H5: a maior parte dos cursos foi cadastrada em um único mês | Confirmada: 92 de 104 (88%) em setembro de 2025 |

Cada gráfico do dashboard mostra embaixo se a hipótese foi confirmada ou não, com os números dos dados filtrados. A base só tem o código do núcleo e do tipo do curso, não tem o nome de cada um.
