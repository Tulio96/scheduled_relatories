import streamlit as st
import os
import sys

from processing.data_processing_grandes import processar_dados_grandes,processar_dados_grandes_previsao
from processing.static_table_grandes import static_table_grandes,static_table_previsao_grandes  # Importando a função de tabela estilizada

# Inicializar session_state corretamente
def carregar_ultima_atualizacao():
    try:
        with open("ultima_atualizacao_grandes.txt", "r") as f:
            return f.read().strip()  # 🔄 Garante que o valor seja atualizado corretamente
    except FileNotFoundError:
        return "Nunca"


# 🔄 Atualizar session_state ao carregar a página
if "ultima_atualizacao" not in st.session_state:
    st.session_state["ultima_atualizacao"] = carregar_ultima_atualizacao()

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

#st.link_button("HOME", "http://10.103.4.250/hora_hora/")

col1,col2,col3,col4 = st.columns(4)
with col4:
    # Exibir última atualização
    st.markdown(f"📅 **Última atualização:** `{st.session_state['ultima_atualizacao']}`")

with col1:
    # Botão de atualização manual
    if st.button("🔄 Atualizar Dados"):
        st.session_state["ultima_atualizacao"] = carregar_ultima_atualizacao()  # 🔄 Atualiza o valor ao clicar no botão
        st.rerun()  # 🚀 Recarrega a página para refletir a mudança
# 🔹 Carregar os dados processados

dfs_processados = processar_dados_grandes()
dfs_previsao = processar_dados_grandes_previsao()

# 🔹 Verificar se há grandes disponíveis
if not dfs_processados:
    st.error("Nenhum dado processado foi encontrado. Verifique os arquivos de entrada.")
    st.stop()

# 🔹 Criar o dashboard no Streamlit
st.markdown("<h1 style='text-align: center;'>Acompanhamento Hora a Hora - Grandes Carteiras</h1>", unsafe_allow_html=True)

# 🔹 Inicializar `session_state` para armazenar a escolha do usuário
grandes = list(dfs_processados.keys())
if "carteira_selecionada" not in st.session_state:
    st.session_state["carteira_selecionada"] = grandes[0]  # 🔄 Define o primeiro supervisor como padrão

col1, col2, col3, col4 = st.columns(4)

with col1:
    carteira_selecionada = st.selectbox(
        "Selecione a carteira:",
        grandes,
        index=grandes.index(st.session_state["carteira_selecionada"]),
        key="carteira_radio"
        )

# 🔹 Atualizar `session_state` imediatamente ao mudar a opção
if carteira_selecionada != st.session_state["carteira_selecionada"]:
    st.session_state["carteira_selecionada"] = carteira_selecionada
    st.rerun()  # 🚀 Recarrega a página para refletir a mudança

# 🔹 Exibir os dados do supervisor selecionado
if carteira_selecionada in dfs_processados:

    col1, col2 = st.columns(2)
    with col1:

        st.markdown(f"#### 📌 Previsão de Recebimento")
        static_table_previsao_grandes(dfs_previsao[carteira_selecionada][["Previsão_Inicial", "Previsão_Atualizada", "Evolução"]])

    st.markdown(f"### 📊 Dados Consolidados - {carteira_selecionada}")
  #  st.markdown('###### [Gerado - Dados do mesmo dia da semana passada ou 14 dias quando feriado] / [Hoje - Dados do dia de hoje] / [Diferença - Subtração dos valores de hoje e do dia em comparação]')
    static_table_grandes(dfs_processados[carteira_selecionada][["Hora", "Acordos_C", "Valor_C", "TKM_C", "Acordos_H", "Valor_H", "TKM_H", "Δ_Acordos", "Δ_Valor", "Δ_TKM"]])
