import pandas as pd
import numpy as np
from pathlib import Path
import json, asyncio
from utils.busca_ceps import cep_to_coords


def _remove_colunas(df):

    cols_interesse = json.loads(
        Path("dados/banco_dados/colunas_relevantes_md_edb.json").read_text()
    )
    df = df[cols_interesse]

    return df


def _soma_colunas(df: pd.DataFrame, colunas: list[str], novo_nome: str, drop=True):
    """
    df: DataFrame
    colunas: lista com nomes de colunas a serem somadas
    novo_nome: nome da nova coluna criada
    """
    df[novo_nome] = df[colunas].sum(axis=1).astype(int)
    if drop:
        df = df.drop(columns=colunas)

    return df


def _combina_colunas(df):

    infraestrutura = [
        "IN_ESGOTO_REDE_PUBLICA",
        "IN_ENERGIA_REDE_PUBLICA",
        "IN_LIXO_SERVICO_COLETA",
    ]
    df = _soma_colunas(df, infraestrutura, "infraestrutura")

    estrutura_pobre = ["IN_TERREIRAO", "IN_ACESSIBILIDADE_INEXISTENTE"]
    df = _soma_colunas(df, estrutura_pobre, "estrutura_pobre")

    estrutura_basica = [
        "IN_ALMOXARIFADO",
        "IN_BIBLIOTECA",
        "IN_LABORATORIO_INFORMATICA",
        "IN_PATIO_DESCOBERTO",
        "IN_QUADRA_ESPORTES_DESCOBERTA",
    ]
    df = _soma_colunas(df, estrutura_basica, "estrutura_basica")

    estrutura_padrao = [
        "IN_AUDITORIO",
        "IN_BIBLIOTECA_SALA_LEITURA",
        "IN_LABORATORIO_CIENCIAS",
        "IN_PATIO_COBERTO",
    ]
    df = _soma_colunas(df, estrutura_padrao, "estrutura_padrao")

    estrutura_premium = [
        "IN_AREA_PLANTIO",
        "IN_BANHEIRO_CHUVEIRO",
        "IN_PISCINA",
        "IN_SALA_ATELIE_ARTES",
        "IN_SALA_MUSICA_CORAL",
        "IN_SALA_ESTUDIO_DANCA",
        "IN_SALA_ESTUDIO_GRAVACAO",
        "IN_SALA_REPOUSO_ALUNO",
        "IN_ACESSIBILIDADE_ELEVADOR",
        "IN_MATERIAL_PED_MUSICAL",
    ]
    df = _soma_colunas(df, estrutura_premium, "estrutura_premium")

    ativos_basico = ["QT_EQUIP_TV", "QT_EQUIP_MULTIMIDIA", "QT_DESKTOP_ALUNO"]
    df = _soma_colunas(df, ativos_basico, "qt_ativos_basico")

    ativos_premium = [
        "QT_EQUIP_LOUSA_DIGITAL",
        "QT_COMP_PORTATIL_ALUNO",
        "QT_TABLET_ALUNO",
    ]
    df = _soma_colunas(df, ativos_premium, "qt_ativos_premium")

    pessoal_basico = [
        "QT_PROF_ADMINISTRATIVOS",
        "QT_PROF_SERVICOS_GERAIS",
        "QT_PROF_BIBLIOTECARIO",
        "QT_PROF_ALIMENTACAO",
        "QT_PROF_SECRETARIO",
    ]
    df = _soma_colunas(df, pessoal_basico, "pessoal_basico")

    pessoal_padrao = [
        "QT_PROF_SAUDE",
        "QT_PROF_COORDENADOR",
        "QT_PROF_PEDAGOGIA",
        "QT_PROF_MONITORES",
        "QT_PROF_GESTAO",
        "QT_PROF_ASSIST_SOCIAL",
    ]
    df = _soma_colunas(df, pessoal_padrao, "pessoal_padrao")

    pessoal_premium = [
        "QT_PROF_FONAUDIOLOGO",
        "QT_PROF_NUTRICIONISTA",
        "QT_PROF_PSICOLOGO",
        "QT_PROF_SEGURANCA",
        "QT_PROF_AGRICOLA",
    ]
    df = _soma_colunas(df, pessoal_premium, "pessoal_premium")

    alunos = ["QT_MAT_INF", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED"]
    df = _soma_colunas(df, alunos, "qt_alunos", drop=False)

    professores = ["QT_DOC_INF", "QT_DOC_FUND_AI", "QT_DOC_FUND_AF", "QT_DOC_MED"]
    df = _soma_colunas(df, professores, "qt_professores")

    # Arrumando os valores de tipo de ocupacao
    df["tipo_ocupacao"] = (
        df["TP_OCUPACAO_PREDIO_ESCOLAR"].fillna(2).replace({1: 3, 2: 1, 3: 2})
    )  # 1 alugado, 2 cedido, 3 proprio

    df = df.drop(columns=["TP_OCUPACAO_PREDIO_ESCOLAR"])

    return df


def _filtra_linhas(df):

    df = df[df["TP_DEPENDENCIA"] == 4]  # Mantem escolas particulares, reduz para 52_568
    df = df[
        (df["TP_CATEGORIA_ESCOLA_PRIVADA"] != 3)
    ]  # Remove escolas particulares confessionais, reduz para 52_101
    df = df[
        (df["TP_SITUACAO_FUNCIONAMENTO"] == 1)
    ]  # Mantem escolas em atividade, reduz para 42_751
    df = df[
        df["IN_MEDIACAO_PRESENCIAL"] == 1
    ]  # Remove escolas que nao tem aula presencial, reduz para 42_470

    df = df.drop(
        columns=[
            "TP_DEPENDENCIA",
            "TP_CATEGORIA_ESCOLA_PRIVADA",
            "TP_SITUACAO_FUNCIONAMENTO",
            "IN_MEDIACAO_PRESENCIAL",
        ]
    )

    df = df[
        df["qt_alunos"] > 20
    ]  # Remove escolas com menos de 20 alunos, reduz para 37_178

    return df


def _limita_outliers(serie, x, achatar=False):
    """
    serie: pandas Series numérica
    x: percentil (0–100)
    achatar: se True, substitui valores maiores pelo teto
    """

    limite = serie.quantile(x / 100)
    mediana = serie.median()

    # substitui os valores acima do percentil pela mediana
    tratada = serie.copy()
    if achatar:
        tratada[tratada > limite] = round(limite)
    else:
        tratada[tratada > limite] = round(mediana)

    return tratada


def _trata_outliers(df):

    df["QT_SALAS_UTILIZADAS"] = _limita_outliers(df["QT_SALAS_UTILIZADAS"], 98)
    df["IN_EXAME_SELECAO"] = df["IN_EXAME_SELECAO"].replace(
        {9: 0}
    )  # provavelmente esse 9 era um 0 feio
    df["QT_MAT_INF"] = _limita_outliers(df["QT_MAT_INF"], 99)
    df["QT_MAT_FUND_AI"] = _limita_outliers(df["QT_MAT_FUND_AI"], 99, True)
    df["QT_MAT_FUND_AF"] = _limita_outliers(df["QT_MAT_FUND_AF"], 99, True)
    df["QT_MAT_MED"] = _limita_outliers(df["QT_MAT_MED"], 99, True)

    # sem outlier: infraestrutura, estrutura_pobre, estrutura_basica, estrutura_padrao, estrutura_premium

    df["qt_ativos_basico"] = _limita_outliers(df["qt_ativos_basico"], 99, True)
    df["qt_ativos_premium"] = _limita_outliers(df["qt_ativos_premium"], 98, True)
    df["pessoal_basico"] = _limita_outliers(df["pessoal_basico"], 99, True)
    df["pessoal_padrao"] = _limita_outliers(df["pessoal_padrao"], 96, True)
    df["pessoal_premium"] = _limita_outliers(df["pessoal_premium"], 99.3, True)
    df["qt_alunos"] = _limita_outliers(df["qt_alunos"], 97, True)
    df["qt_professores"] = _limita_outliers(df["qt_professores"], 99, True)

    df["alunos_p_professor"] = df["qt_alunos"] / df["qt_professores"]
    df["alunos_p_professor"] = _limita_outliers(df["alunos_p_professor"], 99, True)

    df["alunos_p_sala"] = df["qt_alunos"] / df["QT_SALAS_UTILIZADAS"]
    df["alunos_p_sala"] = _limita_outliers(df["alunos_p_sala"], 98, True)

    return df


def _add_enem(df_training, df_enem):
    # Remover linhas que nao tenham codigo escola
    df_enem = df_enem.dropna(subset="CO_ESCOLA")  # 1.5M linhas

    # Remove quem faltou qualquer dia
    cols = ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"]
    df_enem = df_enem[df_enem[cols].eq(1).all(axis=1)]  # 1.19M linhas

    # Remove escolas com menos de 5 provas
    df_enem = df_enem.groupby("CO_ESCOLA").filter(lambda g: len(g) >= 5)  # 1.18M linhas

    df_enem = df_enem[
        [
            "CO_ESCOLA",
            "NU_NOTA_CN",
            "NU_NOTA_CH",
            "NU_NOTA_LC",
            "NU_NOTA_MT",
            "NU_NOTA_REDACAO",
        ]
    ]

    # Agrupando alunos por escolas
    df_enem = df_enem.groupby("CO_ESCOLA", as_index=False).agg("mean")  # 26_302 escolas
    df_enem["nota_objetiva"] = df_enem[
        ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT"]
    ].mean(axis=1)
    df_enem["nota_enem"] = df_enem["nota_objetiva"] + df_enem["NU_NOTA_REDACAO"]
    df_enem["cod_escola"] = df_enem["CO_ESCOLA"].astype(int)  # estava com .0 no final
    df_enem = df_enem[["cod_escola", "nota_enem"]]

    # Junta os dois df
    df = df_training.merge(
        df_enem, how="left", left_on="CO_ENTIDADE", right_on="cod_escola"
    )

    df = df.drop(columns=["cod_escola"])

    return df


def _add_val_venda(df_training, ticket_medio):

    df_training["valor_venda"] = (
        df_training["QT_MAT_INF"] * ticket_medio["ei"]
        + df_training["QT_MAT_FUND_AI"] * ticket_medio["efai"]
        + df_training["QT_MAT_FUND_AF"] * ticket_medio["efaf"]
        + df_training["QT_MAT_MED"] * ticket_medio["em"]
    )

    return df_training


def _add_clientes(df_training, df_clientes):
    """
    Adiciona a coluna "cliente" que discrimina se já é cliente (1)
    TODO: adicionar se é para remover essa escola (-1)
    TODO: preencher com 0 os None
    """
    df_clientes["cliente"] = 1

    df_clientes = df_clientes.melt(
        id_vars="cliente",
        value_vars=["Código INEP 1", "Código INEP 2", "Código INEP 3"],
        value_name="co_inep",
    )

    df_clientes = (
        df_clientes.dropna(subset="co_inep").drop(columns="variable").drop_duplicates()
    )

    df_clientes["co_inep"] = df_clientes["co_inep"].astype(int)

    df_training = df_training.merge(
        df_clientes, how="left", left_on="CO_ENTIDADE", right_on="co_inep"
    )

    return df_training.drop(columns="co_inep")


def build_training_df(inputs):
    """
    Recebe uma lista com os seguintes inputs na ordem:
    escolas_atuais, local_consultores, ticket_medio, microdados_ed_basica, RESULTADOS
    """
    nome_arquivo_temporario = Path("dados/temporarios/df_training.csv")

    df_training = _remove_colunas(inputs[3])  # df_md_ed_basica
    df_training = _combina_colunas(df_training)
    df_training = _filtra_linhas(df_training)
    df_training = _trata_outliers(df_training)

    df_training = _add_enem(df_training, inputs[4])  # df_enem
    df_training = _add_val_venda(df_training, inputs[2])  # ticket_medio
    df_training = asyncio.run(cep_to_coords(df_training, "CO_CEP", True))
    df_training = _add_clientes(df_training, inputs[0])  # escolas_atuais

    df_training.to_csv(nome_arquivo_temporario, index=False)

    # return df_training
