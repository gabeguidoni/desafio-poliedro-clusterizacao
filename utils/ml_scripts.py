import pandas as pd
import numpy as np


def _get_afinidade(df_training):
    """
    Retornará o df com a coluna com a afinidade de cada escola
    """
    print("_get_afinidade()")
    return np.random.normal(0.9, 0.01, size=len(df_training))


def get_afinidade_df(df_training, use_ml: bool):
    """
    Remove as escolas com ban
    Retorna um df com as colunas CO_ENTIDADE, valor_venda, afinidade, lat, lon
    """
    print("get_afinidade_df()")
    df_afinidade = df_training[df_training["cliente"] != -1]

    if use_ml:
        df_afinidade["afinidade"] = _get_afinidade(df_afinidade)
    else:
        df_afinidade["afinidade"] = 1

    df_afinidade = df_afinidade[df_afinidade["cliente"] == 0]

    df_afinidade = df_afinidade[
        ["CO_ENTIDADE", "valor_venda", "afinidade", "lat", "lon"]
    ]

    return df_afinidade
