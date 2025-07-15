import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import os
import sys

from processing.data_processing_unidades import processar_dados_unidades, processar_dados_unidades_previsao
from processing.static_table_unidades import static_table_unidades, static_table_previsao_unidades  # Importando a função de tabela estilizada

# Inicializar session_state corretamente
def carregar_ultima_atualizacao():
    try:
        with open("ultima_atualizacao_unidades.txt", "r") as f:
            return f.read().strip()  # 🔄 Garante que o valor seja atualizado corretamente
    except FileNotFoundError:
        return "Nunca"

st.set_page_config(layout="wide")

with st.sidebar:
    st.image("logo.png")

background_color = "#474747"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {background_color}; /* Define a cor de fundo */
        background-attachment: fixed; /* Garante que a cor permaneça fixa ao rolar */
        background-size: cover; /* Importante se você tivesse uma imagem junto com a cor */
    }}
    </style>
    """,
    unsafe_allow_html=True
)

col1,col2,col3,col4 = st.columns(4)
# 🔄 Atualizar session_state ao carregar a página
if "ultima_atualizacao" not in st.session_state:
    st.session_state["ultima_atualizacao"] = carregar_ultima_atualizacao()

with col4:
    # Exibir última atualização
    st.markdown(f"📅 **Última atualização:** `{st.session_state['ultima_atualizacao']}`")

with col1:
    # Botão de atualização manual
    if st.button("🔄 Atualizar Dados"):
        st.session_state["ultima_atualizacao"] = carregar_ultima_atualizacao()  # 🔄 Atualiza o valor ao clicar no botão
        st.rerun()  # 🚀 Recarrega a página para refletir a mudança

# 🔹 Carregar os dados processados
dfs_processados = processar_dados_unidades()
dfs_previsao = processar_dados_unidades_previsao()

# 🔹 Verificar se há unidades disponíveis
if not dfs_processados:
    st.error("Nenhum dado processado foi encontrado. Verifique os arquivos de entrada.")
    st.stop()

# 🔹 Criar o dashboard no Streamlit
st.markdown("<h1 style='text-align: center;'>Acompanhamento Hora a Hora - B2B</h1>", unsafe_allow_html=True)

# 🔹 Inicializar `session_state` para armazenar a escolha do usuário
unidades = list(dfs_processados.keys())
if "unidade_selecionada" not in st.session_state:
    st.session_state["unidade_selecionada"] = unidades[0]  # 🔄 Define o primeiro unidade como padrão

col1, col2, col3, col4 = st.columns(4)

with col1:
    unidade_selecionada = st.selectbox(
        "Seleção de unidade/supervisor:",
        unidades,
        index=unidades.index(st.session_state["unidade_selecionada"]),
        key="unidade_radio"
        )

# 🔹 Atualizar `session_state` imediatamente ao mudar a opção
if unidade_selecionada != st.session_state["unidade_selecionada"]:
    st.session_state["unidade_selecionada"] = unidade_selecionada
    st.rerun()  # 🚀 Recarrega a página para refletir a mudança


# 🔹 Exibir os dados do unidade selecionada
if unidade_selecionada in dfs_processados:

    col1, col2 = st.columns(2)
    with col1:

        st.markdown(f"#### 📌 Previsão de Recebimento")
        static_table_previsao_unidades(dfs_previsao[unidade_selecionada][["Previsão_Inicial", "Previsão_Atualizada", "Evolução"]])

    st.markdown(f"### 📊 Dados Consolidados - {unidade_selecionada}")
    #st.markdown('###### [C - Dados do mesmo dia da semana passada ou 14 dias quando feriado] / [H - Dados do dia de H] / [Δ - Subtração dos valores de H e do dia em comparação]')

    # Exibe a tabela com todos os dados e a linha de total
    static_table_unidades(dfs_processados[unidade_selecionada][["Hora", "Acordos_C", "Valor_C", "TKM_C", "Acion_C", "Acordos_H", "Valor_H", "TKM_H", "Acion_H", "Δ_Acordos", "Δ_Valor", "Δ_TKM"]])
        
    # Adicionar gráfico de barras com Delta_Valor usando Plotly
    st.markdown(f"### 📊 Variação no Valor de Acordos por Horário - {unidade_selecionada}")

    # Criar o gráfico com Plotly, excluindo a linha 'Total'
    fig = px.bar(
            dfs_processados[unidade_selecionada][dfs_processados[unidade_selecionada]["Hora"] != "Total"],  # Excluir a linha 'Total' do gráfico
            x="Hora",
            y="Δ_Valor",
            color="Δ_Valor",
            color_continuous_scale=["red", "yellow", "green"],  # Gradiente de cores
            labels={"Δ_Valor": "Δ_Valor", "Hora": "Horário"},
        )

    # Ajustar layout do gráfico
    fig.update_layout(
            xaxis_title="Horário",
            yaxis_title="Δ_Valor",
            paper_bgcolor="#404040",
            plot_bgcolor="#474747",
        )

        # Calcula os extremos absolutos
    max_val = abs(dfs_processados[unidade_selecionada]["Δ_Valor"].max())
    min_val = abs(dfs_processados[unidade_selecionada]["Δ_Valor"].min())

        # Decide o deslocamento base dependendo de qual valor absoluto é maior
    if max_val >= min_val:
        deslocamento_base = 0.1 * max_val
    else:
        deslocamento_base = 0.1 * min_val

    # Adicionar os valores das barras acima de cada barra
    for i, row in dfs_processados[unidade_selecionada][dfs_processados[unidade_selecionada]["Hora"] != "Total"].iterrows():
        deslocamento = deslocamento_base if row["Δ_Valor"] > 0 else deslocamento_base - row["Δ_Valor"]
        fig.add_annotation(
            x=row["Hora"],
            y=row["Δ_Valor"] + deslocamento,  # Aplicando deslocamento vertical
            text=f"<b>R$ {row['Δ_Valor']:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),  # Formatar com separadores personalizados
            showarrow=False,
            font=dict(size=12, color="white"),
            align="center",
            )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)