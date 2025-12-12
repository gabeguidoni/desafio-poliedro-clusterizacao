import streamlit as st
import pandas as pd
from pathlib import Path

from utils.st_functions import sh, show_result, input_checker
from utils.inputs_handler import build_training_df
from utils.ml_scripts import get_afinidade_df
from utils.po_scripts import get_results


st.logo("imagens/logo_ita.png", size="large")
st.image("imagens/logo_poliedro.svg")
st.header("Projeto clusterização de escolas", divider="rainbow")


def selecionar_result(result):
    st.session_state["result"] = result


# --- Rodapé ---

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

    if not inputs_ready or st.button(
        "Carregar novos inputs",
        help="Clique aqui após fazer alteração nos inputs",
    ):
        inputs = []
        inputs.append(input_checker("escolas_atuais"))  # adicionar aba escolas ban
        inputs.append(input_checker("local_consultores"))
        inputs.append(input_checker("ticket_medio"))
        inputs.append(input_checker("microdados_ed_basica"))
        inputs.append(input_checker("RESULTADOS"))

        if all(x != "erro" for x in inputs):
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
            "Quanto das escolas distribuir/ignorar",
            min_value=0.05,
            max_value=0.95,
            value=0.85,
            step=0.05,
        )

    st.write("\n")

    st.session_state["calcular"] = st.button(
        "Calcular", type="primary", disabled=not inputs_ready, width="stretch"
    )

    # st.session_state["calcular"] = True  # ATENCAO

    if st.session_state.get("calcular"):
        st.session_state["calcular"] = False
        df_afinidade = get_afinidade_df(df_training, usar_afinidade)

        df_resultado = get_results(
            df_afinidade, df_training, df_consultores, usar_afinidade, cobertura
        )


with tab2:
    st.subheader("Resultados anteriores")
    texto = "📋 **Data**: 2XX/11/2025 10:27:32 **Consultores:** 25 **Escolas:** 32.123 **Afinidade:** Não **Batata:** 0,90"

    rels = range(20)
    for rel in rels[1:6]:
        st.button(
            texto.replace("XX", f"{rel}"),
            width="stretch",
            on_click=selecionar_result,
            args=(rel,),
        )

    # result = st.session_state.get("result")
    # if result:
    #     show_result(result)


# --- Rodapé ---
sh()
st.markdown(
    """
<div style="text-align: left; color: gray;">
    Desenvolvido para a disciplina PO-207 de Pós Graduação no ITA/Unifesp por:
    <ul style="margin: 0; padding-left: 18px;">
        <li>Gabriel Guidoni (ITA)</li>
        <li>Gustavo Guardia (Unifesp)</li>
        <li>Guilherme Ferracini (Unifesp)</li>
        <li>Jardel Ferreira (Unifesp)</li>
        <li>Gabriel Ribeiro (ITA)</li>
    </ul>
    Sob orientação do professor Luiz Leduino Salles Neto (Unifesp)
</div>
    """,
    unsafe_allow_html=True,
)
