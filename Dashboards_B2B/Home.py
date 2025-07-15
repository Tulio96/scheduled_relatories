import streamlit as st

# Configurações básicas da página
st.set_page_config(
    page_title="Home",
    layout="wide", # Pode ser "centered" ou "wide"
    initial_sidebar_state="expanded", # Pode ser "auto", "expanded", ou "collapsed"
)

with st.sidebar:
# Título principal do aplicativo
    st.image("logo.png", width=300)

st.title("Acompanhamento de Acordos B2B - Hora a Hora")

# Introdução ou descrição
st.markdown("""
Esta é a página inicial dos dashboards.
Utilize o menu à esquerda para navegar entre as visualizações.

**Funcionalidades:**
* **Dashboard Unidades e Supervisores:** Dados de acordos gerados por hora, visão Supervisor e unidades Sede e Araquari.
* **Dashboard Grandes Carteiras:** Dados de acordos gerados por hora, visão maiores carteiras B2B.
""")

# Algumas informações adicionais (opcional)
st.subheader("Informações Adicionais")
st.write("Consultas agendadas para gerar atualizações a cada 04 minutos") # Adapte a data conforme necessário


footer_html = """
<style>
.footer {
    position: fixed; /* Fixa o elemento na tela */
    left: 0;
    bottom: 0; /* Posiciona na parte inferior */
    width: 100%; /* Ocupa toda a largura */
    background-color: #262730; /* Cor de fundo */
    color: #f1f1f1; /* Cor do texto */
    text-align: center;
    padding: 8px;
    font-size: 14px;
    border-top: 1px solid #e1e1e1;
    z-index: 9999; /* Garante que ele fique acima de outros elementos */
}
</style>
<div class="footer">
    mis@somosglobal.com.br | © 2025
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# Exemplo de como você pode incluir uma imagem (opcional)
# Certifique-se de que a imagem esteja no mesmo diretório do app_principal.py

# Você pode adicionar mais elementos como gráficos pequenos, KPIs resumidos, etc.
# st.metric(label="Total de Unidades Monitoradas", value="15")
# st.metric(label="Média de Desempenho", value="85%", delta="2%")