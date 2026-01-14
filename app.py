import warnings

warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from pathlib import Path

from time import sleep

from utils import (
    input_checker,
    build_training_df,
    get_afinidade_df,
    get_results,
    sh,
    show_result,
    get_prev_results_infos,
)


st.logo("imagens/logo_ita.png", size="large")
st.image("imagens/logo_poliedro.svg")
st.header("Projeto clusterização de escolas", divider="rainbow")


def selecionar_result(result_idx, texto):
    st.session_state["result_idx"] = result_idx
    st.session_state["texto"] = texto


# --- Body ---

tab1, tab2 = st.tabs(["Novo Planejamento", "Historico de Planejamentos"])
with tab1:
    st.subheader("Inputs")

    try:
        df_training = pd.read_csv(Path("dados/temporarios/df_training.csv"))
        df_consultores = pd.read_csv(Path("dados/temporarios/df_consultores.csv"))
        st.success("Inputs prontos!")
        inputs_ready = True
    except FileNotFoundError as e:
        inputs_ready = False

    re_button = st.button(
        "Carregar novos inputs",
        help="Clique aqui após fazer alteração nos inputs",
    )

    if not inputs_ready or re_button:
        inputs = []
        inputs.append(input_checker("escolas_atuais"))
        inputs.append(input_checker("local_consultores"))
        inputs.append(input_checker("ticket_medio"))
        inputs.append(input_checker("microdados_ed_basica"))
        inputs.append(input_checker("RESULTADOS"))

        inputs = [v for v in inputs if v is not None]
        if len(inputs) == 5:
            build_training_df(inputs)
            inputs[1].to_csv(Path("dados/temporarios/df_consultores.csv"), index=False)
            st.cache_data.clear()
            st.rerun()

    sh("Ajustes")

    usar_afinidade = st.toggle(
        "Usar Afinidade (beta)",
        help="Caso não use afinidade o sistema irá distribuir iguais valores de potencial de venda para cada consultor",
    )
    st.write("\n")
    col1, _ = st.columns(2)
    with col1:
        cobertura = st.slider(
            "Quanto das escolas distribuir",
            min_value=0.05,
            max_value=0.95,
            value=0.35,
            step=0.05,
        )

    st.write("\n")

    st.session_state["calcular"] = st.button(
        "Calcular", type="primary", disabled=not inputs_ready, width="stretch"
    )

    # st.session_state["calcular"] = True  # ATENCAO

    if st.session_state.get("calcular"):
        st.session_state["calcular"] = False
        with st.spinner("Calculando...", show_time=True):
            df_afinidade = get_afinidade_df(df_training, usar_afinidade)
            df_resultado = get_results(
                df_afinidade, df_training, df_consultores, usar_afinidade, cobertura
            )

            # df_resultado = pd.read_csv("dados/temporarios/df_resultado.csv")  # ATENCAO
            # sleep(5)  # ATENCAO

        show_result(-1)


with tab2:
    st.subheader("Resultados anteriores")

    prev_results_infos = get_prev_results_infos()

    for result_info in prev_results_infos:

        texto = f"📋 **Data**: {result_info[0]} {result_info[1]} **Cobertura:** {result_info[2]} **Afinidade:** {result_info[3]}"
        result_idx = result_info[4]

        st.button(
            texto,
            width="stretch",
            on_click=selecionar_result,
            args=(result_idx, texto),
        )

    result_idx = st.session_state.get("result_idx")
    if result_idx != None:
        show_result(result_idx, st.session_state.get("texto"))


# --- Rodapé ---
sh()
st.markdown(
    """
<div style="text-align: left; color: gray;">
    Desenvolvido para a disciplina PO-207 de Pós Graduação no ITA/Unifesp por:
    <ul style="margin: 0; padding-left: 18px;">
        <li>Gabriel Guidoni (ITA)</li>
        <li>Guilherme Ferracini (Unifesp)</li>
        <li>Gustavo Guardia (Unifesp)</li>
        <li>Jardel Ferreira (Unifesp)</li>
        <li>Gabriel Ribeiro (ITA)</li>
    </ul>
    Sob orientação do professor Luiz Leduino Salles Neto (Unifesp)
</div>
    """,
    unsafe_allow_html=True,
)
