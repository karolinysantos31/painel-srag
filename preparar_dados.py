"""Prepara a base do painel de SRAG a partir dos arquivos INFLUD do OpenDataSUS.

Os arquivos brutos têm uma linha por notificação, com dados de saúde de pessoas
(município, data de nascimento, hospital, número da notificação). Este script
não leva nada disso para o painel: ele conta casos por categoria e grava só
tabelas agregadas, sem município, sem data completa e sem identificadores.

Como usar
1. Baixe os arquivos INFLUDxx-dd-mm-aaaa.csv em
   https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
2. Coloque todos na pasta dados_brutos/
3. Rode:  python preparar_dados.py
"""
import json
import re
from pathlib import Path

import pandas as pd

PASTA_BRUTOS = Path("dados_brutos")
PASTA_SAIDA = Path(".")

# Colunas lidas. As que não existirem em algum ano (arquivos antigos têm
# menos campos) ficam vazias, sem quebrar o processamento.
COLUNAS = [
    "SEM_NOT", "SG_UF", "CS_SEXO", "NU_IDADE_N", "TP_IDADE", "CS_RACA",
    "CLASSI_FIN", "EVOLUCAO", "UTI", "SUPORT_VEN",
    "PCR_SARS2", "AN_SARS2", "POS_PCRFLU", "POS_AN_FLU", "PCR_VSR", "AN_VSR",
    "PCR_RINO", "PCR_ADENO", "PCR_PARA1", "PCR_PARA2", "PCR_PARA3", "PCR_PARA4",
    "PCR_METAP", "PCR_BOCA",
    "CARDIOPATI", "HEMATOLOGI", "SIND_DOWN", "HEPATICA", "ASMA", "DIABETES",
    "NEUROLOGIC", "PNEUMOPATI", "IMUNODEPRE", "RENAL", "OBESIDADE", "PUERPERA",
]

CLASSIFICACAO = {
    "1": "SRAG por influenza",
    "2": "SRAG por outro vírus respiratório",
    "3": "SRAG por outro agente etiológico",
    "4": "SRAG não especificada",
    "5": "SRAG por COVID-19",
}
DESFECHO = {
    "1": "Cura",
    "2": "Óbito por SRAG",
    "3": "Óbito por outras causas",
    "9": "Ignorado",
}
SEXO = {"M": "Masculino", "F": "Feminino", "I": "Ignorado"}
RACA = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena", "9": "Ignorado"}
UTI = {"1": "Sim", "2": "Não", "9": "Ignorado"}
SUPORTE = {"1": "Invasivo", "2": "Não invasivo", "3": "Não usou", "9": "Ignorado"}

FAIXAS = ["Menos de 1 ano", "1 a 4", "5 a 9", "10 a 19", "20 a 39", "40 a 59", "60 a 79", "80 ou mais"]

# Vírus detectados (resultado positivo em PCR ou teste de antígeno).
VIRUS = {
    "SARS-CoV-2": ["PCR_SARS2", "AN_SARS2"],
    "Influenza": ["POS_PCRFLU", "POS_AN_FLU"],
    "VSR": ["PCR_VSR", "AN_VSR"],
    "Rinovírus": ["PCR_RINO"],
    "Adenovírus": ["PCR_ADENO"],
    "Parainfluenza": ["PCR_PARA1", "PCR_PARA2", "PCR_PARA3", "PCR_PARA4"],
    "Metapneumovírus": ["PCR_METAP"],
    "Bocavírus": ["PCR_BOCA"],
}
COMORBIDADES = {
    "Cardiopatia": "CARDIOPATI", "Diabetes": "DIABETES", "Obesidade": "OBESIDADE",
    "Doença pneumológica crônica": "PNEUMOPATI", "Imunodepressão": "IMUNODEPRE",
    "Doença renal crônica": "RENAL", "Doença neurológica crônica": "NEUROLOGIC",
    "Asma": "ASMA", "Doença hematológica": "HEMATOLOGI", "Doença hepática": "HEPATICA",
    "Síndrome de Down": "SIND_DOWN", "Puérpera": "PUERPERA",
}


def sim(serie: pd.Series) -> pd.Series:
    """Campos de sim/não do sistema: 1 é sim."""
    return (serie == "1").astype("int32")


def ler_arquivo(caminho: Path, ano: int) -> pd.DataFrame:
    df = pd.read_csv(
        caminho, sep=";", dtype=str, encoding="utf-8",
        usecols=lambda c: c in COLUNAS,
    )
    for c in COLUNAS:
        if c not in df.columns:
            df[c] = pd.NA

    out = pd.DataFrame(index=df.index)
    out["ano"] = ano
    out["semana"] = pd.to_numeric(df["SEM_NOT"], errors="coerce").astype("Int16")
    out["uf"] = df["SG_UF"].fillna("Não informado")
    out["classificacao"] = df["CLASSI_FIN"].map(CLASSIFICACAO).fillna("Em investigação ou sem classificação")
    out["desfecho"] = df["EVOLUCAO"].map(DESFECHO).fillna("Sem desfecho registrado")
    out["sexo"] = df["CS_SEXO"].map(SEXO).fillna("Ignorado")
    out["raca"] = df["CS_RACA"].map(RACA).fillna("Ignorado")
    out["uti"] = df["UTI"].map(UTI).fillna("Sem informação")
    out["suporte"] = df["SUPORT_VEN"].map(SUPORTE).fillna("Sem informação")

    # Idade em anos completos. TP_IDADE: 1 dias, 2 meses, 3 anos.
    idade = pd.to_numeric(df["NU_IDADE_N"], errors="coerce")
    anos = idade.where(df["TP_IDADE"] == "3", 0)
    anos = anos.where(idade.notna())
    faixa = pd.cut(anos, bins=[-1, 0, 4, 9, 19, 39, 59, 79, 200], labels=FAIXAS)
    out["faixa"] = faixa.astype("object").fillna("Sem informação")

    for nome, cols in VIRUS.items():
        positivo = pd.Series(0, index=df.index, dtype="int32")
        for c in cols:
            positivo = positivo | sim(df[c])
        out["v_" + nome] = positivo
    for nome, col in COMORBIDADES.items():
        out["c_" + nome] = sim(df[col])
    return out


def contar(df: pd.DataFrame, dims: list[str], somas: list[str] | None = None) -> pd.DataFrame:
    agg = {"casos": ("ano", "size")}
    for s in somas or []:
        agg[s] = (s, "sum")
    tab = df.groupby(dims, observed=True, dropna=False).agg(**agg).reset_index()
    return tab


def main() -> None:
    PASTA_SAIDA.mkdir(exist_ok=True)
    arquivos = sorted(PASTA_BRUTOS.glob("INFLUD*.csv"))
    if not arquivos:
        raise SystemExit("Nenhum arquivo INFLUD*.csv encontrado em dados_brutos/")

    partes, extracoes = [], {}
    for arq in arquivos:
        m = re.match(r"INFLUD(\d{2})-(\d{2})-(\d{2})-(\d{4})", arq.name)
        ano = 2000 + int(m.group(1))
        extracoes[ano] = f"{m.group(2)}/{m.group(3)}/{m.group(4)}"
        print(f"Lendo {arq.name} ...", flush=True)
        partes.append(ler_arquivo(arq, ano))
    df = pd.concat(partes, ignore_index=True)
    print(f"{len(df):,} notificações no total".replace(",", "."))

    base = ["ano", "uf", "classificacao"]
    v = ["v_" + n for n in VIRUS]
    c = ["c_" + n for n in COMORBIDADES]

    tabelas = {
        "serie": contar(df, base + ["semana", "desfecho"]),
        "perfil": contar(df, base + ["sexo", "faixa", "desfecho"]),
        "raca": contar(df, base + ["raca", "desfecho"]),
        "cuidado": contar(df, base + ["uti", "suporte", "desfecho"]),
        "agentes": contar(df, base + ["desfecho"], v + c),
    }
    for nome, tab in tabelas.items():
        for col in tab.columns:
            if not pd.api.types.is_numeric_dtype(tab[col]):
                tab[col] = tab[col].astype("category")
        tab.to_parquet(PASTA_SAIDA / f"srag_{nome}.parquet", index=False)
        print(f"{nome}: {len(tab):,} linhas".replace(",", "."))

    # Total por arquivo, para conferência
    totais = df.groupby("ano").size().to_dict()
    meta = {"extracoes": extracoes, "linhas_por_ano": totais, "total": int(len(df))}
    (PASTA_SAIDA / "srag_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Pronto.")


if __name__ == "__main__":
    main()
