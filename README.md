# SRAG no Brasil

> **Painel sem caráter oficial.** Feito com dados abertos do Ministério da Saúde (SIVEP-Gripe). Não é uma publicação oficial do órgão e não representa o seu posicionamento.

**Fonte dos dados:** https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026

## O que é

Painel interativo com as notificações de Síndrome Respiratória Aguda Grave (SRAG) de 2023 a 2026, com mais de 1,1 milhão de registros. Filtros por ano, UF de residência e classificação final.

## O que o painel mostra

- Indicadores: notificações, óbitos por SRAG, letalidade, passagem por UTI e proporção de casos com 60 anos ou mais
- Evolução por semana epidemiológica, com um ano sobre o outro
- Classificação final e vírus detectados em exame
- Mapa por UF de residência e ranking das 10 maiores
- Faixa etária, sexo, letalidade por faixa etária, raça ou cor e condições de risco
- UTI e suporte ventilatório

## Como os dados foram tratados

- **Fonte:** arquivos anuais INFLUD do Portal de Dados Abertos do SUS. Os de 2023 e 2024 foram extraídos em 23/03/2026 e os de 2025 e 2026 em 09/11/2026.
- **Só dados agregados.** Os arquivos originais têm uma linha por pessoa notificada, com município, data de nascimento, hospital e número da notificação. Nada disso vai para o painel. O script `preparar_dados.py` conta os casos por categoria e grava tabelas agregadas, sem município, sem data completa e sem identificadores.
- **Ano:** é o ano do arquivo publicado, que segue a semana epidemiológica. O painel usa a semana, não a data completa.
- **Letalidade:** óbitos por SRAG divididos pelos casos com desfecho registrado (cura, óbito por SRAG ou óbito por outras causas).
- **Vírus detectados:** resultado positivo em PCR ou teste de antígeno. Um caso pode ter mais de um vírus.
- **Conferência:** o total de cada tabela agregada bate com o total de linhas de cada arquivo original.

## Limitações

- O ano de 2026 vai até a semana epidemiológica 46.
- As semanas mais recentes sobem depois, porque notificações e desfechos são digitados com atraso. A letalidade dos anos recentes é afetada por casos ainda sem desfecho.
- Casos sem classificação final estão em investigação ou nunca foram encerrados no sistema.
- Muitos casos não têm exame registrado, então os vírus detectados não representam todos os casos de cada vírus.
- O mapa mostra volume absoluto por UF, sem ajuste pela população.
- A SRAG depende da notificação feita pelos hospitais. Mudanças de cobertura e de qualidade do registro ao longo dos anos afetam a comparação entre períodos.
- Os anos de 2019 a 2022 estão disponíveis na fonte, mas ainda não foram incluídos.

## Tecnologias

Python, Pandas, Plotly, Streamlit e PyArrow.

## Arquivos

| Arquivo | Função |
|---|---|
| `painel.py` | Código do painel |
| `preparar_dados.py` | Gera as tabelas agregadas a partir dos arquivos originais |
| `dados/` | Tabelas agregadas usadas pelo painel |
| `br_estados.geojson` | Contornos dos estados, usados no mapa |
| `requirements.txt` | Bibliotecas necessárias |

## Como rodar no computador

Requer Python 3.10 ou mais recente.

```
pip install -r requirements.txt
streamlit run painel.py
```

## Como refazer a base

1. Baixe os arquivos `INFLUDxx-dd-mm-aaaa.csv` da fonte e coloque na pasta `dados_brutos/`.
2. Rode `python preparar_dados.py`.

## Aviso

Painel independente, feito com dados abertos, sem caráter oficial. Os números refletem a base publicada e as regras de tratamento descritas acima.
