import pandas as pd
from typing import Literal
import streamlit as st
import plotly.express as px


def static_table_grandes(
    df: pd.DataFrame,
    text_align: Literal["left", "center", "right"] = "center",
    line_color: str = "rgba(1, 1, 1, 1000)",
) -> None:
    common_props = [
        ("text-align", text_align),
        ("border", f"1px solid {line_color}"),
        ("padding", "0.25rem 0.375rem"),
        ("vertical-align", "middle"),
        ("line-height", "1.5rem"),
    ]

    # Estilo condicional baseado nos valores
    def estilo_delta(valor):
        if valor > 0:
            return "color: #53c449; font-weight: bold;"
        elif valor < 0:
            return "color: #ff6437; font-weight: bold;"
        else:
            return "color: white;"

    # Colunas com bordas verticais
    col_borders = [
        {
            "selector": f"td.col{df.columns.get_loc('Hora')}",
            "props": [("border-right", "3px solid black"), ("border-left", "3px solid black")]
        },
        {
            "selector": f"th.col{df.columns.get_loc('Hora')}",
            "props": [("border-right", "3px solid black"), ("border-left", "3px solid black")]
        },
        {
            "selector": f"td.col{df.columns.get_loc('TKM_C')}",
            "props": [("border-right", "3px solid black")]
	},
        {
            "selector": f"th.col{df.columns.get_loc('TKM_C')}",
            "props": [("border-right", "3px solid black")]
        },

        #{
            #"selector": f"td.col{df.columns.get_loc('Acion_H')}",
            #"props": [("border-right", "2px solid black")]
        #},
        #{
            #"selector": f"th.col{df.columns.get_loc('Acion_H')}",
            #"props": [("border-right", "2px solid black")]
        #},

        {
            "selector": f"td.col{df.columns.get_loc('Δ_Acordos')}",
            "props": [("border-left", "3px solid black")]
        },
        {
            "selector": f"th.col{df.columns.get_loc('Δ_Acordos')}",
            "props": [("border-left", "3px solid black")]
        },

        {
            "selector": f"td.col{df.columns.get_loc('Δ_TKM')}",
            "props": [("border-right", "3px solid black")]
        },
        {
            "selector": f"th.col{df.columns.get_loc('Δ_TKM')}",
            "props": [("border-right", "3px solid black")]
        },
        {
            "selector": "thead th",
            "props": [("border-top", "3px solid black"), ("border-bottom", "3px solid black")]
        }
    ]

    # Bordas horizontal superior e inferior
    linha_primeira = df.index[0]
    linha_penultima = df.index[-2]
    linha_ultima = df.index[-1]
    colunas_com_borda = ["Hora", "Valor_C", "TKM_C", "Acordos_C", #"Acion_C",
			 "Acordos_H", "Valor_H", "TKM_H", #"Acion_H", 
			 "Δ_Acordos", "Δ_Valor","Δ_TKM"]

    borda_topo_rodape = []
    for col in colunas_com_borda:
        col_idx = df.columns.get_loc(col)
        borda_topo_rodape.extend([
            {
                "selector": f"tr:nth-child({linha_primeira + 1}) td.col{col_idx}",  # +1 porque nth-child inclui o header
                "props": [("border-top", "3px solid black")]
            },
            {
                "selector": f"tr:nth-child({linha_ultima + 1}) td.col{col_idx}",
                "props": [("border-bottom", "3px solid black")]
            },
            {
                "selector": f"tr:nth-child({linha_penultima + 1}) td.col{col_idx}",
                "props": [("border-bottom", "3px solid black")]
            }
        ])

    styled_df = (
        df.style.hide(axis="index")
        .map(estilo_delta, subset=["Δ_Valor", "Δ_Acordos", "Δ_TKM"])
        .format({
            "Valor_C": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Valor_H": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "TKM_C": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "TKM_H": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Δ_Valor": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Δ_TKM": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        })
        .set_table_styles(
            [
                {"selector": "th", "props": common_props + [("font-weight", "bold"), ("background-color", "#262730")]},
                {"selector": "td", "props": common_props},
            ] + col_borders + borda_topo_rodape
        )
    )

    st.markdown(
        styled_df.to_html(table_attributes='id="minha-tabela" style="width: 100%;"'),
        unsafe_allow_html=True,
    )


# Função para exibir tabela estilizada da previsão
def static_table_previsao_grandes(
    df: pd.DataFrame,
    text_align: Literal["left", "center", "right"] = "center",
    line_color: str = "rgba(1, 1, 1, 1000)",
) -> None:
    common_props = [
        ("text-align", text_align),
        ("border", f"1px solid {line_color}"),
        ("padding", "0.25rem 0.375rem"),
        ("vertical-align", "middle"),
        ("line-height", "1.5rem"),
    ]

    # Função para estilizar células com base nos valores
    def estilo_evolucao(valor):
        if valor > 0:
            return "color: #53c449; font-weight: bold;"  # Verde para valores positivos
        elif valor < 0:
            return "color: #ff6437; font-weight: bold;"  # Vermelho para valores negativos
        else:
            return "color: white;"  # Preto para zero ou valores neutros

    col_borders = [
        {
            "selector": f"td.col{df.columns.get_loc('Previsão_Inicial')}",
            "props": [("border-right", "3px solid black"), ("border-left", "3px solid black"), 
                      ("border-top", "3px solid black"), ("border-bottom", "3px solid black")]
        },
                {
            "selector": f"td.col{df.columns.get_loc('Previsão_Atualizada')}",
            "props": [("border-right", "3px solid black"), ("border-left", "3px solid black"), 
                      ("border-top", "3px solid black"), ("border-bottom", "3px solid black")]
        },
                {
            "selector": f"td.col{df.columns.get_loc('Evolução')}",
            "props": [("border-right", "3px solid black"), ("border-left", "3px solid black"), 
                      ("border-top", "3px solid black"), ("border-bottom", "3px solid black")]
        },
        {
            "selector": "thead th",
            "props": [("border-top", "3px solid black"), ("border-bottom", "3px solid black"),
                      ("border-left", "3px solid black"), ("border-right", "3px solid black")]
        }
    ]

    st.markdown(
        df.style.hide(axis="index")  # Esconde a coluna de índice
        .map(estilo_evolucao, subset=["Evolução"])  # Aplica estilo à coluna Evolução
        .format(
            {
                "Previsão_Inicial": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Previsão_Atualizada": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Evolução": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            }
        )  # Formata colunas como moeda com separadores personalizados
        .set_table_styles(
            [
                {  # Header
                    "selector": "th",
                    "props": common_props + [("font-weight", "bold"), ("background-color", "#262730")],
                },
                {  # Data
                    "selector": "td",
                    "props": common_props,
                },
            ] + col_borders
        )
        .to_html(table_attributes='id="tabela-previsao" style="width: 100%;"'),
        unsafe_allow_html=True,
    )
