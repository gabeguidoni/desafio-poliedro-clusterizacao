import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import plotly.graph_objects as go


DIVIDER = "rainbow"


def sh(text: str = ""):
    """
    subheader
    """
    st.subheader("", divider=DIVIDER)

    if text:
        st.subheader(text)


def input_checker(name) -> pd.DataFrame:
    """
    Recebe o path para o arquivo

    Confere se o input existe

    Imprime mensagem

    Retorna o input como um df
    """
    try:
        if name in ["microdados_ed_basica", "RESULTADOS"]:
            if name == "microdados_ed_basica":
                title = "Micro Dados da Educação Básica"
            else:
                title = "Resultados do ENEM"

            file_name = name + ".csv"
            input_path = Path(f"dados/inputs/{file_name}")
            arquivo = pd.read_csv(
                input_path, sep=";", encoding="latin1", low_memory=False
            )

        elif name == "escolas_atuais":
            title = "Escolas Atuais no Sistema de Ensino Poliedro"
            file_name = name + ".xlsx"
            input_path = Path(f"dados/inputs/{file_name}")

            dict_dfs = pd.read_excel(input_path, sheet_name=None)  # dict com os df
            arquivo = tuple(dict_dfs.values())  # tupla com os dfs

        elif name == "local_consultores":
            title = "Local dos Consultores"
            file_name = name + ".xlsx"
            input_path = Path(f"dados/inputs/{file_name}")
            arquivo = pd.read_excel(input_path)

        elif name == "ticket_medio":
            title = "Ticket Médio"
            file_name = name + ".json"
            input_path = Path(f"dados/inputs/{file_name}")
            arquivo = json.loads(input_path.read_text())

        st.success(title)
        return arquivo

    except FileNotFoundError as e:
        st.error(
            f"**{title}** não encontrado, o nome deve ser exatamente: **{file_name}** e deve estar localizado em: **{input_path}**\n\n{e}"
        )
        return None

    except Exception as e:
        st.error(f"Erro desconhecido: {e}")
        return None


def _draw_map(df_resultado):
    print("draw_map()")

    cores = [
        "#E41A1C",
        "#377EB8",
        "#4DAF4A",
        "#FF7F00",
        "#FFFF33",
        "#A65628",
        "#F781BF",
        "#999999",
    ]

    fig = go.Figure()

    consultores_unicos = df_resultado["consultor"].unique()

    for idx, cons in enumerate(consultores_unicos):
        dfc = df_resultado[df_resultado["consultor"] == cons]

        fig.add_trace(
            go.Scattermap(
                lat=dfc["lat"],
                lon=dfc["lon"],
                mode="markers",
                name=str(cons),  # aparece na legenda
                marker=dict(size=10, color=cores[idx % len(cores)]),  # cor distinta
                text=dfc["valor_venda"],  # aparece no hover
                hovertemplate="<b>%{text}</b><br>Consultor: " + str(cons),
            )
        )

    fig.update_layout(
        map=dict(
            style="open-street-map", center=dict(lat=-14.2350, lon=-51.9253), zoom=3
        ),
        legend=dict(x=0.02, y=0.98, xanchor="left", yanchor="top"),
        height=500,
        margin=dict(r=0, t=0, l=0, b=0),
    )

    st.plotly_chart(fig, width="stretch")


def _downl_button(result_idx: int = -1):
    pasta = Path("dados/resultados")
    arquivos = sorted(pasta.glob("resultado_*.xlsx"))
    file_path = arquivos[result_idx]

    with file_path.open("rb") as f:
        st.download_button(
            "Baixar resultado em Excel",
            data=f,
            file_name=file_path.name,
            on_click="ignore",
            type="primary",
            icon=":material/download:",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def show_result(result_idx: int, header="Resultado"):
    print("show_result()")
    sh(header)

    pasta = Path("dados/resultados")
    path = sorted(pasta.glob("resultado_*.xlsx"))[result_idx]

    df_resultado = pd.read_excel(path)

    _draw_map(df_resultado)
    _downl_button()


def get_prev_results_infos():
    """
    retorna uma lista de tuplas com data, hora, cobertura, afinidade, file_path
    """
    pasta = Path("dados/resultados")
    paths = sorted(pasta.glob("resultado_*.xlsx"))[-5:]  # apenas os 5 ultimos

    infos = []
    for result_idx, arquivo in enumerate(paths):
        data_hora = arquivo.stem.replace("resultado_", "")
        dt = datetime.strptime(data_hora, "%Y%m%d_%H%M%S")
        data = dt.strftime("%d/%m/%Y")
        hora = dt.strftime("%H:%M:%S")

        xls = pd.ExcelFile(arquivo)
        nome_aba = xls.sheet_names[0].split("_")
        cobertura = nome_aba[0]
        if nome_aba[1] == "sem":
            afinidade = "Não"
        else:
            afinidade = "Sim"

        infos.append((data, hora, cobertura, afinidade, result_idx))

    return infos
