import asyncio, pulp, re, sys
import pandas as pd
from geopy.distance import geodesic
from utils.busca_ceps import cep_to_coords
from datetime import datetime
from pathlib import Path


def _consultores_handler(df_consultores):
    print("_consultores_handler()")
    df = df_consultores.dropna()
    df["CEP"] = df["CEP"].str.replace("-", "")
    df = asyncio.run(cep_to_coords(df, "CEP"))

    return df[["Consultor", "lat", "lon"]]


def _calcula_distancias(df_escolas, df_consultores):
    print("_calcula_distancias()")
    pre_df = {"CO_ENTIDADE": df_escolas["CO_ENTIDADE"]}
    for _, consultor in df_consultores.iterrows():
        nome_co = consultor["Consultor"]
        lat_co = consultor["lat"]
        lon_co = consultor["lon"]

        dists = []
        for _, escola in df_escolas.iterrows():
            lat_es = escola["lat"]
            lon_es = escola["lon"]
            dists.append(round(geodesic((lat_es, lon_es), (lat_co, lon_co)).km))

        pre_df.update({nome_co: dists})

    print("fim _calcula_distancias()")
    return pd.DataFrame(pre_df)


def _get_final_df(df_afinidade, df_consultores):
    print("_get_final_df()")
    df_consultores = _consultores_handler(df_consultores)
    df_distancias = _calcula_distancias(df_afinidade, df_consultores)

    df_afinidade["motivacao"] = round(
        df_afinidade["afinidade"] * df_afinidade["valor_venda"]
    )
    df_afinidade = df_afinidade[["CO_ENTIDADE", "motivacao"]]

    return df_distancias.merge(df_afinidade, on="CO_ENTIDADE")


def _run_optimizer(df_final, cobertura, data_hora):
    """
    Roda o solver
    Retorna um df com as colunas "cod_escola", "consultor"
    """
    print("_run_optimizer()")
    nome_arquivo_log = str(Path(f"dados/resultados/log_{data_hora}.txt"))

    # --- MODELO ---
    modelo = pulp.LpProblem("Poliedro", pulp.LpMinimize)

    # --- DADOS ---
    df_final = df_final.set_index("CO_ENTIDADE")
    distancias = df_final.drop(columns="motivacao")
    motivacao = df_final["motivacao"]
    consultores = distancias.columns.to_list()
    escolas = df_final.index.tolist()
    mm = sum(motivacao) / len(consultores)

    # --- VARIÁVEL ---
    x = pulp.LpVariable.dicts(
        "x", [(i, j) for i in escolas for j in consultores], lowBound=0, cat="Binary"
    )

    # --- FUNÇÃO OBJETIVO ---
    modelo += pulp.lpSum(
        distancias.loc[i, j] * x[(i, j)] for i in escolas for j in consultores
    )

    # --- RESTRIÇÕES ---
    for i in escolas:  # Cada escola é atribuida a no maximo um consultor
        modelo += pulp.lpSum(x[(i, j)] for j in consultores) <= 1
    for j in consultores:
        modelo += (
            pulp.lpSum(x[(i, j)] * motivacao[i] for i in escolas) >= cobertura * mm
        )

    # --- SOLUÇÃO ---
    highs_bin = "highs.exe" if sys.platform.startswith("win") else "highs"
    solver_path = Path("solver/highsbox/highs_dist/bin") / highs_bin
    modelo.solve(
        pulp.HiGHS_CMD(
            path=str(solver_path),
            logPath=nome_arquivo_log,
            gapRel=0.02,
            options=["presolve=off"],
        )
    )

    # --- FORMATANDO SOLUCAO ---
    padrao = re.compile(r"x_\((\d+),_'([^']+)'\)")
    # padrao = re.compile(r"x_*\((\d+),_['\"]?([^'\")]+)['\"]?\)")

    consultores, escolas = [], []
    for v in modelo.variables():
        if v.value() != 0:
            m = padrao.match(v.name)
            escolas.append(m.group(1))
            consultores.append(m.group(2))

    df = pd.DataFrame({"cod_escola": escolas, "consultor": consultores})

    return df


def _result_handler(
    df_resultado: pd.DataFrame,
    df_training: pd.DataFrame,
    data_hora: str,
    usar_afinidade: bool,
    cobertura: float,
) -> pd.DataFrame:
    """
    Gera e salva o excel com o resultado nas seguintes colunas:
    "consultor", "cod_escola", "cep", "valor_venda"

    Retorna um df com as seguintes colunas:
    "consultor", "cod_escola", "valor_venda", "lat", "lon"
    """
    print("_result_handler()")

    df_training = df_training[["CO_ENTIDADE", "CO_CEP", "valor_venda", "lat", "lon"]]
    df_training["CO_ENTIDADE"] = df_training["CO_ENTIDADE"].astype(str).str.zfill(8)

    df_resultado = df_resultado.merge(
        df_training, left_on="cod_escola", right_on="CO_ENTIDADE"
    )

    df_excel = df_resultado[
        ["consultor", "cod_escola", "CO_CEP", "valor_venda", "lat", "lon"]
    ]
    df_excel = df_excel.rename(columns={"CO_CEP": "cep"})
    df_excel["cep"] = (
        df_excel["cep"]
        .astype(str)
        .str.zfill(8)
        .replace(r"(\d{5})(\d{3})", r"\1-\2", regex=True)
    )

    if usar_afinidade:
        sheet_name = f"{cobertura}_com_afinidade"
    else:
        sheet_name = f"{cobertura}_sem_afinidade"

    df_excel.to_excel(
        Path(f"dados/resultados/resultado_{data_hora}.xlsx"),
        sheet_name=sheet_name,
        index=False,
        freeze_panes=(1, 1),
    )

    # df_resultado[["consultor", "cod_escola", "valor_venda", "lat", "lon"]].to_csv(
    #     "dados/temporarios/df_resultado.csv", index=False
    # )  # ATENCAO

    return df_resultado[["consultor", "cod_escola", "valor_venda", "lat", "lon"]]


def get_results(df_afinidade, df_training, df_consultores, usar_afinidade, cobertura):
    print("get_results()")
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")

    df_final = _get_final_df(df_afinidade, df_consultores)
    df_resultado = _run_optimizer(df_final, cobertura, data_hora)

    return _result_handler(
        df_resultado, df_training, data_hora, usar_afinidade, cobertura
    )
