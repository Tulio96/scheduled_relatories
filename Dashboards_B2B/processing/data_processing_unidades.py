import pandas as pd
import numpy as np
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir,"..","data")

caminho_spu = os.path.join(data_dir,"semana_passada_unidades.csv")
caminho_piu = os.path.join(data_dir,"previsao_inicial_unidades.csv")
caminho_asu = os.path.join(data_dir,"acion_semana_passada_unidades.csv")
caminho_esu = os.path.join(data_dir,"esta_semana_unidades.csv")
caminho_phu = os.path.join(data_dir,"previsao_hoje_unidades.csv")
caminho_ahu = os.path.join(data_dir,"acion_esta_semana_unidades.csv")

def processar_comparativo_unidades(semana_1_df, esta_semana_df,acion_semana_1_df,acion_esta_semana_df):
    """
    Organiza os períodos em colunas separadas, alinha corretamente os horários entre 'Semana Passada' e 'Esta Semana',
    e aplica transformações adicionais, como renomear a linha final e truncar os horários.
    """

    semana_1_df = semana_1_df.rename(columns={"Horario": "Hora"})
    esta_semana_df = esta_semana_df.rename(columns={"Horario": "Hora"})

    # Garantir que as colunas de horas estejam corretas, exceto para a linha 'Total'
    semana_1_df["Hora"] = semana_1_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))
    esta_semana_df["Hora"] = esta_semana_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))
    acion_semana_1_df["Hora"] = acion_semana_1_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))
    acion_esta_semana_df["Hora"] = acion_esta_semana_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))

    acion_semana_1_df = acion_semana_1_df.rename(columns={"Acionamento":"Acion_C"})
    acion_esta_semana_df = acion_esta_semana_df.rename(columns={"Acionamento":"Acion_H"})
    # Renomear colunas para manter organização
    semana_1_df = semana_1_df.rename(
        columns={"Valor": "Valor_C", "Quantidade": "Acordos_C"}
    )
    esta_semana_df = esta_semana_df.rename(
        columns={"Valor": "Valor_H", "Quantidade": "Acordos_H"}
    )

    # Mesclar corretamente pelo horário
    df_final = pd.merge(semana_1_df,esta_semana_df, on="Hora", how="left")
    df_final = pd.merge(df_final, acion_semana_1_df, on="Hora", how="left")
    df_final = pd.merge(df_final,acion_esta_semana_df, on="Hora", how="left")

    df_final["TKM_C"] = np.where(
	    df_final["Acordos_C"] == 0,
	    0.00,
	    (df_final["Valor_C"]/df_final["Acordos_C"])
    )
    df_final["TKM_H"] = np.where(
	    df_final["Acordos_H"] ==0,
	    0.00,
	    (df_final["Valor_H"]/df_final["Acordos_H"])
    )
    df_final["Valor_H"] = df_final["Valor_H"].fillna(0).astype(float)    
    df_final["TKM_H"] = df_final["TKM_H"].fillna(0).astype(float)
    df_final["Valor_C"] = df_final["Valor_C"].fillna(0).astype(float)
    df_final["TKM_C"] = df_final["TKM_C"].fillna(0).astype(float)
    df_final["Acordos_H"] = df_final["Acordos_H"].fillna(0).astype(int)
    df_final["Acordos_C"] = df_final["Acordos_C"].fillna(0).astype(int)
    df_final["Acion_H"] = df_final["Acion_H"].fillna(0).astype(int)
    df_final["Acion_C"] = df_final["Acion_C"].fillna(0).astype(int)

    # Calcular a Δ: Se H ainda não tiver nenhum valor C, Δ fica em 0
    df_final["Δ_Valor"] = np.where(
        df_final["Valor_H"] == 0,
        0.00,
        (df_final["Valor_H"] - df_final["Valor_C"]).astype(float).round(2)
    )
    df_final["Δ_Valor"] = df_final["Δ_Valor"].fillna(0).astype(float)

    df_final["Δ_Acordos"] = np.where(
        df_final["Acordos_H"] == 0,
        0,
        (df_final["Acordos_H"] - df_final["Acordos_C"])
    )
    df_final["Δ_Acordos"] = df_final["Δ_Acordos"].fillna(0).astype(int)

    df_final["Δ_TKM"] = np.where(
        df_final["TKM_H"] == 0,
        0.00,
        (df_final["TKM_H"] - df_final["TKM_C"])
    )
    df_final["Δ_TKM"] = df_final["Δ_TKM"].fillna(0).astype(float)

    # Truncar os horários entre 08h e 18h, mantendo a linha 'Total'
    df_final = df_final[(df_final["Hora"].between("08:00", "18:00", inclusive="both"))]

    # Ordenar corretamente os horários
    df_final = df_final.sort_values(by="Hora", key=lambda col: col.map(lambda x: "23:59" if x == "Total" else x))

    # Garantir que Δ_Valor tenha 2 casas decimais
    df_final["Δ_Valor"] = df_final["Δ_Valor"].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else x)

    colunas_numericas = ["Valor_C", "Acordos_C","TKM_C","Acion_C", "Valor_H", "Acordos_H","TKM_H", "Acion_H", "Δ_Valor", "Δ_Acordos","Δ_TKM"]
    for coluna in colunas_numericas:
        if coluna in df_final.columns:
            df_final[coluna] = pd.to_numeric(df_final[coluna], errors="coerce")

    # Obtém a hora atual
    hora_atual = datetime.now().strftime("%H:%M")

    # Converte a coluna "Hora" para formato de hora e filtra os valores
    df_filtrado = df_final[df_final["Hora"] <= hora_atual].copy()

    # Calcula os totais das colunas a partir do df_filtrado
    total_row = pd.DataFrame({
        "Hora": ["Total"],
        "Acordos_C": [df_filtrado["Acordos_C"].sum()],
        "Valor_C": [df_filtrado["Valor_C"].sum()],
        "TKM_C": [df_filtrado["Valor_C"].sum() / df_filtrado["Acordos_C"].sum()],
        "Acion_C": [df_filtrado["Acion_C"].sum()],
        "Acordos_H": [df_filtrado["Acordos_H"].sum()],
        "Valor_H": [df_filtrado["Valor_H"].sum()],
        "TKM_H": [df_filtrado["Valor_H"].sum() / df_filtrado["Acordos_H"].sum()],
        "Acion_H": [df_filtrado["Acion_H"].sum()],
        "Δ_Acordos": [df_filtrado["Δ_Acordos"].sum()],
        "Δ_Valor": [df_filtrado["Δ_Valor"].sum()],
        "Δ_TKM": [(df_filtrado["Valor_H"].sum() / df_filtrado["Acordos_H"].sum()) - (df_filtrado["Valor_C"].sum() / df_filtrado["Acordos_C"].sum())]
    })

    # Mantém todos os dados originais e adiciona a linha Total no final
    df_final = pd.concat([df_final, total_row], ignore_index=True)

    return df_final

def processar_dados_unidades():
    # 🔹 Carregar os dados
    df_semana_passada = pd.read_csv(caminho_spu)  # Substitua pelo caminho correto
    df_acion_esta_semana = pd.read_csv(caminho_ahu)
    df_esta_semana = pd.read_csv(caminho_esu)  # Substitua pelo caminho correto
    df_acion_semana_passada = pd.read_csv(caminho_asu)

    # 🔹 Remover linhas onde `codunidade` ou `unidade` são `NULL`
    df_semana_passada = df_semana_passada.dropna(subset=["unidade"])
    df_acion_semana_passada = df_acion_semana_passada.dropna(subset=["unidade"])
    df_esta_semana = df_esta_semana.dropna(subset=["unidade"])
    df_acion_esta_semana = df_acion_esta_semana.dropna(subset=["unidade"])

    # 🔹 Criar dicionários para armazenar os DataFrames separados por unidade
    dfs_semana_passada = {unidade: df_unidade.copy() for unidade, df_unidade in df_semana_passada.groupby("unidade")}
    dfs_acion_semana_passada = {unidade: df_unidade.copy() for unidade, df_unidade in df_acion_semana_passada.groupby("unidade")}
    dfs_esta_semana = {unidade: df_unidade.copy() for unidade, df_unidade in df_esta_semana.groupby("unidade")}
    dfs_acion_esta_semana = {unidade: df_unidade.copy() for unidade, df_unidade in df_acion_esta_semana.groupby("unidade")}

    # 🔹 Criar um dicionário para armazenar os DataFrames processados
    dfs_processados = {}

    # 🔹 Processar os dados para cada unidade
    for unidade in dfs_esta_semana.keys():
        if unidade in dfs_semana_passada:  # Verifica se o unidade existe nos dois conjuntos de dados
            df_semana_passada_unidade = dfs_semana_passada[unidade].drop(columns=["unidade"])  # 🔄 Remove as colunas
            df_acion_semana_passada = dfs_acion_semana_passada[unidade].drop(columns=["unidade"])
            df_esta_semana_unidade = dfs_esta_semana[unidade].drop(columns=["unidade"])  # 🔄 Remove as colunas
            df_acion_esta_semana = dfs_acion_esta_semana[unidade].drop(columns=["unidade"])

            df_final = processar_comparativo_unidades(df_semana_passada_unidade, df_esta_semana_unidade, df_acion_semana_passada, df_acion_esta_semana)
            
            # Adiciona o DataFrame processado ao dicionário
            dfs_processados[unidade] = df_final

    return dfs_processados

def processar_dados_unidades_previsao():
    """Lê os arquivos CSV, une os dados por unidade e calcula a evolução."""

    # 🔹 Carregar os dados
    df_previsao_inicial = pd.read_csv(caminho_piu)
    df_previsao_hoje = pd.read_csv(caminho_phu)

    # 🔹 Remover linhas onde `unidade` está `NULL`
    df_previsao_inicial = df_previsao_inicial.dropna(subset=["unidade"])
    df_previsao_hoje = df_previsao_hoje.dropna(subset=["unidade"])

    # 🔹 Criar dicionários para armazenar os DataFrames separados por unidade
    dfs_previsao_inicial = {unidade: df_unidade.copy() for unidade, df_unidade in df_previsao_inicial.groupby("unidade")}
    dfs_previsao_hoje = {unidade: df_unidade.copy() for unidade, df_unidade in df_previsao_hoje.groupby("unidade")}

    # 🔹 Criar um dicionário para armazenar os DataFrames processados
    dfs_processados = {}

    # 🔹 Processar os dados para cada unidade
    for unidade in dfs_previsao_hoje.keys():
        if unidade in dfs_previsao_inicial:  # Verifica se a unidade existe nos dois conjuntos de dados

            df_previsao_inicio_unidade = dfs_previsao_inicial[unidade]
            df_previsao_hoje_unidade = dfs_previsao_hoje[unidade]

            # 🔹 Realiza o merge dos dois DataFrames
            df_final = pd.merge(df_previsao_inicio_unidade, df_previsao_hoje_unidade, on="unidade")

            df_previsao_inicio_unidade = dfs_previsao_inicial[unidade].drop(columns=["unidade"])  # 🔄 Remove a coluna
            df_previsao_hoje_unidade = dfs_previsao_hoje[unidade].drop(columns=["unidade"])  # 🔄 Remove a coluna

            # 🔹 Calcular a evolução com base em previsao_inicio e previsao_hoje
            df_final["Evolucao"] = (df_final["Previsao_hoje"] - df_final["Previsao_inicio"]).astype(float).round(2)

            # 🔹 Salvar o DataFrame processado no dicionário
            dfs_processados[unidade] = df_final
    
            dfs_processados[unidade] = dfs_processados[unidade].rename(
                columns={"Previsao_inicio": "Previsão_Inicial", "Previsao_hoje": "Previsão_Atualizada","Evolucao":"Evolução"}
                        )

    return dfs_processados