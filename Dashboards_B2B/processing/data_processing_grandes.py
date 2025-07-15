import pandas as pd
import numpy as np
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir,"..","data")

caminho_spg = os.path.join(data_dir,"semana_passada_grandes.csv")
caminho_pig = os.path.join(data_dir,"previsao_inicial_grandes.csv")
caminho_esg = os.path.join(data_dir,"esta_semana_grandes.csv")
caminho_phg = os.path.join(data_dir,"previsao_hoje_grandes.csv")

def processar_comparativo_grandes(semana_1_df, esta_semana_df):
    """
    Organiza os períodos em colunas separadas, alinha corretamente os horários entre 'Semana Passada' e 'Esta Semana',
    e aplica transformações adicionais, como renomear a linha final e truncar os horários.
    """
    # Renomear colunas para manter organização
    semana_1_df = semana_1_df.rename(
        columns={"Horario": "Hora", "Valor": "Valor_C", "Quantidade": "Acordos_C"}
    )
    esta_semana_df = esta_semana_df.rename(
        columns={"Horario": "Hora", "Valor": "Valor_H", "Quantidade": "Acordos_H"}
    )

    # Garantir que as colunas de horas estejam corretas, exceto para a linha 'Total'
    semana_1_df["Hora"] = semana_1_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))
    esta_semana_df["Hora"] = esta_semana_df["Hora"].apply(lambda x: x if x == "Total" else pd.to_datetime(x, errors="coerce").strftime('%H:00'))

    # Mesclar corretamente pelo horário
    df_final = pd.merge(semana_1_df, esta_semana_df, on="Hora", how="left")

    df_final["TKM_C"] = (df_final["Valor_C"]/df_final["Acordos_C"])
    df_final["TKM_H"] = (df_final["Valor_H"]/df_final["Acordos_H"])
    df_final["Valor_H"] = df_final["Valor_H"].fillna(0).astype(float)    
    df_final["TKM_H"] = df_final["TKM_H"].fillna(0).astype(float)
    df_final["Valor_C"] = df_final["Valor_C"].fillna(0).astype(float) 
    df_final["TKM_C"] = df_final["TKM_C"].fillna(0).astype(float)
    df_final["Acordos_H"] = df_final["Acordos_H"].fillna(0).astype(int)
    df_final["Acordos_C"] = df_final["Acordos_C"].fillna(0).astype(int)

    # Calcular a diferença: Se hoje ainda não tiver nenhum valor gerado, diferença fica em 0
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

    # Garantir que Delta_Valor tenha 2 casas decimais
    df_final["Δ_Valor"] = df_final["Δ_Valor"].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else x)

    colunas_numericas = ["Valor_C", "Acordos_C","TKM_C", "Valor_H", "Acordos_H","TKM_H", "Δ_Valor", "Δ_Acordos","Δ_TKM"]
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
        "Acordos_H": [df_filtrado["Acordos_H"].sum()],
        "Valor_H": [df_filtrado["Valor_H"].sum()],
        "TKM_H": [df_filtrado["Valor_H"].sum() / df_filtrado["Acordos_H"].sum()],
        "Δ_Acordos": [df_filtrado["Δ_Acordos"].sum()],
        "Δ_Valor": [df_filtrado["Δ_Valor"].sum()],
        "Δ_TKM": [(df_filtrado["Valor_H"].sum() / df_filtrado["Acordos_H"].sum()) - (df_filtrado["Valor_C"].sum() / df_filtrado["Acordos_C"].sum())]
    })

    # Mantém todos os dados originais e adiciona a linha Total no final
    df_final = pd.concat([df_final, total_row], ignore_index=True)

    return df_final

def processar_dados_grandes():
    # 🔹 Carregar os dados
    df_semana_passada = pd.read_csv(caminho_spg)  # Substitua pelo caminho correto
    df_esta_semana = pd.read_csv(caminho_esg)  # Substitua pelo caminho correto

    # 🔹 Remover linhas onde `codsuper` ou `super` são `NULL`
    df_semana_passada = df_semana_passada.dropna(subset=["cliente"])
    df_esta_semana = df_esta_semana.dropna(subset=["cliente"])

    # 🔹 Criar dicionários para armazenar os DataFrames separados por carteira
    dfs_semana_passada = {carteira: df_carteira.copy() for carteira, df_carteira in df_semana_passada.groupby("cliente")}
    dfs_esta_semana = {carteira: df_carteira.copy() for carteira, df_carteira in df_esta_semana.groupby("cliente")}

    # 🔹 Criar um dicionário para armazenar os DataFrames processados
    dfs_processados = {}

    # 🔹 Processar os dados para cada carteira
    for carteira in dfs_esta_semana.keys():
        if carteira in dfs_semana_passada:  # Verifica se o carteira existe nos dois conjuntos de dados
            df_semana_passada_carteira = dfs_semana_passada[carteira].drop(columns=["cliente"])  # 🔄 Remove as colunas
            df_esta_semana_carteira = dfs_esta_semana[carteira].drop(columns=["cliente"])  # 🔄 Remove as colunas
            
            df_final = processar_comparativo_grandes(df_semana_passada_carteira, df_esta_semana_carteira)
            
            # Adiciona o DataFrame processado ao dicionário
            dfs_processados[carteira] = df_final

    return dfs_processados

def processar_dados_grandes_previsao():
    """Lê os arquivos CSV, une os dados por carteira e calcula a evolução."""

    # 🔹 Carregar os dados
    df_previsao_inicial = pd.read_csv(caminho_pig)
    df_previsao_hoje = pd.read_csv(caminho_phg)

    # 🔹 Remover linhas onde `carteira` está `NULL`
    df_previsao_inicial = df_previsao_inicial.dropna(subset=["cliente"])
    df_previsao_hoje = df_previsao_hoje.dropna(subset=["cliente"])

    # 🔹 Criar dicionários para armazenar os DataFrames separados por carteira
    dfs_previsao_inicial = {carteira: df_carteira.copy() for carteira, df_carteira in df_previsao_inicial.groupby("cliente")}
    dfs_previsao_hoje = {carteira: df_carteira.copy() for carteira, df_carteira in df_previsao_hoje.groupby("cliente")}

    # 🔹 Criar um dicionário para armazenar os DataFrames processados
    dfs_processados = {}

    # 🔹 Processar os dados para cada carteira
    for carteira in dfs_previsao_hoje.keys():
        if carteira in dfs_previsao_inicial:  # Verifica se a carteira existe nos dois conjuntos de dados
            df_previsao_inicio_carteira = dfs_previsao_inicial[carteira].drop(columns=["cliente"])  # 🔄 Remove a coluna
            df_previsao_hoje_carteira = dfs_previsao_hoje[carteira].drop(columns=["cliente"])  # 🔄 Remove a coluna

            # 🔹 Realiza o merge dos dois DataFrames
            df_final = pd.merge(df_previsao_inicio_carteira, df_previsao_hoje_carteira, left_index=True, right_index=True)

            # 🔹 Calcular a evolução com base em previsao_inicio e previsao_hoje
            df_final["Evolucao"] = (df_final["Previsao_hoje"] - df_final["Previsao_inicio"]).astype(float).round(2)

            # 🔹 Salvar o DataFrame processado no dicionário
            dfs_processados[carteira] = df_final
    
            dfs_processados[carteira] = dfs_processados[carteira].rename(
                columns={"Previsao_inicio": "Previsão_Inicial", "Previsao_hoje": "Previsão_Atualizada","Evolucao":"Evolução"}
                        )

    return dfs_processados