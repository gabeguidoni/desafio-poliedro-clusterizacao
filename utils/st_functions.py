import streamlit as st
import pandas as pd
from pathlib import Path
import json

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
            arquivo = pd.read_csv(input_path, sep=";", encoding="latin1")

        elif name in ["escolas_atuais", "local_consultores"]:
            if name == "escolas_atuais":
                title = "Escolas Atuais no Sistema de Ensino Poliedro"
            else:
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
        return "erro"

    except Exception as e:
        st.error(f"Erro desconhecido: {e}")
        return "erro"


def show_result(rel, df=False):
    sh("Resultados")
    # TODO usar st.write_stream() para imprimir uma previa do resultado
    st.write(
        f"Rel {rel} -> imprimir previa, em seguida plotar mapa, e entao disponibilizar botao para download"
    )
