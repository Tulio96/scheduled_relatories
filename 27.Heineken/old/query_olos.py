import pandas as pd
import pyodbc
import openpyxl
from sqlalchemy import text
from database import get_engine # Assumindo que você tem este módulo configurado
from database_olos import get_engine_olos
import traceback
import re
from ler_excel import clean_excel_string

# --- Função executar_query (sem alterações) ---
def executar_query(dados_lista,caminho_arquivo,sheet_name): # Recebe a LISTA de tuplas (cnpj, titulo, parcela)
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
                    pro.CodProcesso                                     AS [CodProcesso],
                    cli.NomCliente                                      AS [Cliente],
                    dev.NomCliente                                      AS [Devedor],
                    CONVERT(NVARCHAR,cdev.CodDevedorCliente)            AS [Codigo ], 
                    COALESCE(prt.ValCapital,0)                          AS [ValRecebidoGlobal],
                    --pt.CodTitulo                                      AS [CodTitulo],
                    --pt.CodParcela                                     AS [CodParcela],
                    --CONCAT(cdev.CodDevedorCliente,pt.CodTitulo,pt.CodParcela)   AS [Chave_Unica],
                    COUNT(ph.DtaHistorico)                              AS [Acionamentos]
                FROM
                    Processo pro
                    LEFT JOIN Cliente cli ON cli.CodCliente = pro.CodCliente
                    LEFT JOIN ProcessoTitulo pt ON pt.CodProcesso = pro.CodProcesso
                    LEFT JOIN ProcessoHistorico ph ON ph.CodProcesso = pro.CodPRocesso
                    LEFT JOIN ProcessoRecebimentoTitulo prt ON prt.CodProcesso = pro.CodProcesso
                                                            AND prt.CodTitulo = pt.CodTitulo
                                                            AND prt.CodParcela = pt.CodParcela
                    LEFT JOIN Cliente dev ON dev.CodCliente = pro.CodDevedor
                    LEFT JOIN DevedorCliente cdev ON cdev.CodDevedor = pro.CodDevedor AND cdev.CodCliente = pro.CodCliente
                    INNER JOIN #TempDados tmp ON tmp.CNPJTemp = cdev.CodDevedorCliente
                WHERE
                    cli.CodGrupoEmpresa = '2081'
                GROUP BY
                    pro.CodProcesso,
                    cli.NomCliente,
                    dev.NomCliente,
                    CONVERT(NVARCHAR,cdev.CodDevedorCliente),
                    prt.ValCapital;
                    --CONCAT(cdev.CodDevedorCliente,pt.CodTitulo,pt.CodParcela);
                """)

                print("\nExecutando: Consulta SELECT principal com JOIN em CNPJ, Título e Parcela...")
                df_query = pd.read_sql(main_select_query, connection)

                df_heineken = pd.read_excel(caminho_arquivo, sheet_name=sheet_name, dtype=str)

                df_resultados = pd.merge(df_heineken,df_query, on="Codigo ",how="left")

                print(f"Consulta executada com sucesso. Total de {len(df_resultados)} registros encontrados.")

                # Limpar strings para evitar problemas no Excel
                for col in df_resultados.select_dtypes(include=['object']).columns:
                    df_resultados[col] = df_resultados[col].apply(clean_excel_string)

                # Salvar em Excel com ajuste de colunas
                with pd.ExcelWriter(caminho_salvamento, engine='openpyxl') as writer:
                    df_resultados.to_excel(writer, sheet_name='Dados', index=False)
                    worksheet = writer.sheets['Dados']
                    for col_idx, col_name in enumerate(df_resultados.columns, 1):
                        column_letter = openpyxl.utils.get_column_letter(col_idx)
                        try:
                            max_len = max(
                                df_resultados[col_name].astype(str).map(len).max(),
                                len(str(col_name))
                            ) + 2
                        except (ValueError, TypeError):
                             max_len = len(str(col_name)) + 2

                        adjusted_width = min(max_len, 50) # Limita a largura a 50
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                print(f"Relatório salvo com sucesso em '{caminho_salvamento}'")

    except Exception as e:
        print(f"Ocorreu um erro em executar_query: {e}")
        traceback.print_exc()
