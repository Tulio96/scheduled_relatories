import pandas as pd
import pyodbc
import openpyxl
from sqlalchemy import text
from database import get_engine
from database_olos import get_engine_olos
import traceback
import re
from ler_excel import clean_excel_string
import numpy as np # Importar numpy para pd.isna

# --- Função executar_query (sem alterações) ---
def executar_querys(dados_lista,caminho_arquivo,sheet_name): # Recebe a LISTA de tuplas (cnpj, titulo, parcela)
    """
    Executa a consulta no banco de dados usando uma tabela temporária
    com CNPJ, Título e Parcela para o JOIN.
    """
    caminho_salvamento = r"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Avaliacao_PD.xlsx"
    engine = get_engine()

    try:
        with engine.connect() as connection:
            with connection.begin(): # Inicia uma transação
                # 1. Descartar tabela temporária se existir
                drop_table_sql = text("IF OBJECT_ID('tempdb..#TempDados') IS NOT NULL DROP TABLE #TempDados;")
                print("Executando: Descarte da tabela temporária (se existir)...")
                connection.execute(drop_table_sql)

                # 2. Criar a nova tabela temporária com CNPJ, Título e Parcela
                create_table_sql = text("""
                CREATE TABLE #TempDados (
                    CNPJTemp NVARCHAR(255) COLLATE Latin1_General_CI_AI,
                    TituloTemp NVARCHAR(255) COLLATE Latin1_General_CI_AI,
                    ParcelaTemp NVARCHAR(255) COLLATE Latin1_General_CI_AI,
                    PRIMARY KEY (CNPJTemp, TituloTemp, ParcelaTemp) -- Chave primária composta
                );
                """)
                print("Executando: Criação da tabela temporária com CNPJ, Título e Parcela...")
                connection.execute(create_table_sql)

                # 3. Inserir os dados (CNPJ, Título e Parcela)
                insert_data_sql = text("INSERT INTO #TempDados (CNPJTemp, TituloTemp, ParcelaTemp) VALUES (:cnpj_val, :titulo_val, :parcela_val);")
                params_to_insert = [{"cnpj_val": cnpj, "titulo_val": titulo, "parcela_val": parcela} for cnpj, titulo, parcela in dados_lista]

                if not params_to_insert:
                    print("Não há dados para inserir na tabela temporária. Abortando.")
                    return

                print(f"Executando: Inserção de {len(params_to_insert)} registros na tabela temporária...")
                connection.execute(insert_data_sql, params_to_insert)

                # 4. Executar a consulta principal com JOIN nas três colunas
                main_select_query = text("""
                SELECT
                    pro.CodProcesso                                 AS [CodProcesso],
                    pt.CodTitulo                                    AS [TITULO ],
                    pt.CodParcela                                   AS [Parcela ],
                    DATEDIFF(DAY,pt.DtaVencimento,pt.DtaCadastro)   AS [DiasAtraso],
                    dev.NumCpfCnpj                                  AS [CNPJ/CPF - Devedor],
                    COUNT(ph.DtaHistorico)                          AS [Acionamentos],
                    ps.DesProcessoSituacao                          AS [Situacao]
                FROM
                    Processo pro
                    LEFT JOIN Cliente dev ON dev.CodCliente = pro.CodDevedor
                    LEFT JOIN ProcessoTitulo pt ON pt.CodProcesso = pro.CodProcesso
                    LEFT JOIN ProcessoSituacao ps ON ps.CodProcessoSituacao = pro.CodProcessoSituacao
                    LEFT JOIN ProcessoHistorico ph ON ph.CodProcesso = pro.CodProcesso
                    INNER JOIN #TempDados tmp ON dev.NumCpfCnpj = tmp.CNPJTemp AND tmp.TituloTemp = pt.CodTitulo AND tmp.ParcelaTemp = pt.CodParcela
                GROUP BY
                    pro.CodProcesso,
                    pt.CodTitulo,
                    pt.CodParcela,
                    dev.NumCpfCnpj,
                    DATEDIFF(DAY,pt.DtaVencimento,pt.DtaCadastro),
                    ps.DesProcessoSituacao;
                """)

                print("\nExecutando: Consulta SELECT principal com JOIN em CNPJ, Título e Parcela...")

                df_query = pd.read_sql(main_select_query, connection)

                # --- Correção de limpeza de nomes de coluna e tipo antes do primeiro merge ---
                df_heineken = pd.read_excel(caminho_arquivo, sheet_name=sheet_name, dtype=str)
                df_heineken.columns = df_heineken.columns.str.strip()
                df_query.columns = df_query.columns.str.strip()

                df_resultados = pd.merge(df_heineken, df_query, on=["Codigo", "TITULO", "Parcela"], how="left")

                with pd.ExcelWriter(caminho_salvamento, engine='openpyxl') as writer:
                    df_resultados.to_excel(writer, sheet_name='Dados', index=False)

                print(f"Consulta executada com sucesso. Total de {len(df_resultados)} registros encontrados.")

    except Exception as e:
        print(f"Ocorreu um erro na primeira etapa da executar_query: {e}")
        traceback.print_exc()
        return # Adicionar um return aqui para parar se a primeira etapa falhar

    engine = get_engine_olos()

    print(f"Conectando ao banco da olos")

    try:
        with engine.connect() as connection:
            with connection.begin(): # Inicia uma transação
                # 1. Descartar tabela temporária se existir
                drop_table_sql = text("IF OBJECT_ID('tempdb..#TempDados') IS NOT NULL DROP TABLE #TempDados;")
                print("Executando: Descarte da tabela temporária (se existir)...")
                connection.execute(drop_table_sql)

                # 2. Criar a nova tabela temporária com Processo...
                create_table_sql = text("""
                CREATE TABLE #TempDados (
                    ProcessoTemp NVARCHAR(255) COLLATE SQL_Latin1_General_CP1_CI_AI,
                    PRIMARY KEY (ProcessoTemp)
                );
                """)
                print("Executando: Criação da tabela temporária com Processo...")
                connection.execute(create_table_sql)

                # --- NOVO TRECHO CRÍTICO DE CORREÇÃO PARA O CODPROCESSAMENTO OLOS ---
                # Função para formatar CodProcesso como string sem .0
                def format_id_for_db(value):
                    if pd.isna(value): # Verifica se é NaN, None ou pd.NA
                        return None # Retorna None para que o banco receba NULL
                    try:
                        # Tenta converter para float primeiro (para 123.0)
                        val_float = float(value)
                        # Se for um número inteiro (ex: 123.0), converte para int e depois para string
                        if val_float == int(val_float):
                            return str(int(val_float))
                        # Caso contrário (se tiver casas decimais significativas), mantém a string do float
                        return str(val_float)
                    except (ValueError, TypeError):
                        # Se não for numérico (já é string ou outro tipo), apenas converte para string
                        return str(value)

                # Aplica a formatação na coluna CodProcesso
                # Primeiro, ensure CodProcesso is object type if it's mixed numeric/string
                df_resultados["CodProcesso"] = df_resultados["CodProcesso"].astype(object)
                dados_devedor_limpos = df_resultados["CodProcesso"].apply(format_id_for_db)

                # Verifique se há Nones antes de criar o set e filtrar, para debugging
                # print("\nValores de dados_devedor_limpos antes de set/filtrar (amostra):")
                # print(dados_devedor_limpos.head(10).tolist())
                # print(f"Contagem de Nones em dados_devedor_limpos: {dados_devedor_limpos.isna().sum()}")

                dados_devedor_limpos.to_csv("dados.csv",index=False)

                # Converte para lista de valores únicos e filtra None,
                # pois PRIMARY KEY não pode ser NULL no SQL Server
                dados_query = [p for p in list(set(dados_devedor_limpos.tolist())) if p is not None]

                # --- FIM DO NOVO TRECHO ---

                # 3. Inserir os dados (apenas ProcessoTemp)
                insert_data_sql = text("INSERT INTO #TempDados (ProcessoTemp) VALUES (:processo_val);")
                params_to_insert = [{"processo_val": processo} for processo in dados_query]

                if not params_to_insert:
                    print("Não há dados para inserir na tabela temporária. Abortando.")
                    return

                print(f"Executando: Inserção de {len(params_to_insert)} registros na tabela temporária...")
                connection.execute(insert_data_sql, params_to_insert)

                # 4. Executar a consulta principal com JOIN
                main_select_query_olos = text("""
SELECT
    COUNT(CallId)                                   AS [Tentativas],
    temp.ProcessoTemp                               AS [CodProcesso]
FROM
    CallData cd
    INNER JOIN #TempDados temp ON temp.ProcessoTemp = cd.CustomerId
GROUP BY
    ProcessoTemp
                """)

                print("\nExecutando: Consulta SELECT principal com JOIN no banco OLOS...")
                df_olos = pd.read_sql(main_select_query_olos, connection)

                # --- Padronizar CodProcesso em AMBOS os DataFrames ANTES do merge final ---
                # Isso é crucial para que o merge encontre correspondências.
                # Aplicamos a mesma lógica de limpeza usada para a inserção no banco OLOS.
                df_resultados["CodProcesso"] = df_resultados["CodProcesso"].apply(format_id_for_db)
                df_olos["CodProcesso"] = df_olos["CodProcesso"].apply(format_id_for_db)

                # Realiza o merge final
                df_final = pd.merge(df_resultados, df_olos, on="CodProcesso", how="left")

                print(f"Consulta executada com sucesso. Total de {len(df_final)} registros encontrados no DF final.")

                # Limpar strings para evitar problemas no Excel e garantir a formatação final
                for col in df_final.select_dtypes(include=['object']).columns:
                    df_final[col] = df_final[col].apply(clean_excel_string)

                # Salvar em Excel com ajuste de colunas
                with pd.ExcelWriter(caminho_salvamento, engine='openpyxl') as writer:
                    df_final.to_excel(writer, sheet_name='Dados', index=False)
                    worksheet = writer.sheets['Dados']
                    for col_idx, col_name in enumerate(df_final.columns, 1):
                        column_letter = openpyxl.utils.get_column_letter(col_idx)
                        try:
                            # Esta parte tenta pegar o comprimento máximo para ajuste de coluna
                            # Se for numérico e tiver .0, ainda aparecerá no Excel, mas a limpeza
                            # para o merge e inserção já foi feita. A visualização no Excel
                            # pode ser controlada com formatação no próprio Excel se necessário.
                            max_len = max(
                                df_final[col_name].astype(str).map(len).max(),
                                len(str(col_name))
                            ) + 2
                        except (ValueError, TypeError):
                            max_len = len(str(col_name)) + 2

                        adjusted_width = min(max_len, 50) # Limita a largura a 50
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                print(f"Relatório salvo com sucesso em '{caminho_salvamento}'")

    except Exception as e:
        print(f"Ocorreu um erro na segunda etapa da executar_query: {e}")
        traceback.print_exc()