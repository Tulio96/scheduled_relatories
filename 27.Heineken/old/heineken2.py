import pandas as pd
import pyodbc
import openpyxl # Importado para manipulação do ExcelWriter e ajuste de colunas
from sqlalchemy import text
from database import get_engine
import traceback
import re

# --- Função para limpar strings antes de exportar para Excel (sem alterações) ---
def clean_excel_string(text_val):
    if isinstance(text_val, str):
        cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text_val)
        return cleaned_text
    return text_val

# --- Função importar_cnpjs (sem alterações) ---
def importar_cnpjs(caminho_arquivo, sheet_name, coluna_cnpj, coluna_titulo):
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name)
        print(f"Total de linhas lidas do Excel (antes da filtragem): {len(df)}")

        if 'Status Pagamento' not in df.columns:
            print(f"Erro: A coluna 'Status Pagamento' não foi encontrada no Excel na planilha '{sheet_name}'. Verifique o nome da coluna.")
            return None

        df_PD = df[df["Status Pagamento"] == "PAGAMENTO DIRETO"]

        print(f"Total de linhas após a filtragem por 'PAGAMENTO DIRETO': {len(df_PD)}")

        if coluna_cnpj not in df.columns:
            print(f"Erro: A coluna de CNPJ '{coluna_cnpj}' não foi encontrada na planilha do Excel.")
            return None

        cnpjs_brutos = df_PD[coluna_cnpj].astype(str).fillna('')

        titulos = df_PD[coluna_titulo].astype(str).fillna('')

        cnpjs_limpos = cnpjs_brutos.apply(lambda x: ''.join(filter(str.isdigit, x)))

        cnpjs_validos_list = [cnpj for cnpj in cnpjs_limpos if cnpj]

        if not cnpjs_validos_list:
            print("Nenhum CPF/CNPJ válido encontrado após a filtragem e limpeza.")
            return []

        df_cnpjs_csv = pd.DataFrame(cnpjs_validos_list, columns=[coluna_cnpj])

        df_cnpjs_csv.to_csv("cnpjs.csv", index=False, sep=';', encoding='utf-8')

        print(f"CNPJs filtrados e limpos do Excel salvos em 'cnpjs.csv'")
        return cnpjs_validos_list

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None

    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo Excel: {e}")
        traceback.print_exc()
        return None

# --- Função executar_query (com ajustes para largura das colunas) ---
def executar_query(cnpjs_lista): # Recebe a LISTA de CNPJs
    caminho_salvamento = fr"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Avaliacao_PD.xlsx"
    engine = get_engine() 

    try:
        with engine.connect() as connection:
            with connection.begin():
                drop_table_sql = text("""
                IF OBJECT_ID('tempdb..#TempCNPJ') IS NOT NULL
                BEGIN
                    DROP TABLE #TempCNPJ;
                END
                """)
                print("Executando: Descarte da tabela temporária (se existir)...")
                connection.execute(drop_table_sql)

                create_table_sql = text("""
                CREATE TABLE #TempCNPJ
                (
                    CNPJTemp NVARCHAR(255) COLLATE Latin1_General_CI_AI PRIMARY KEY
                );
                """)
                print("Executando: Criação da tabela temporária...")
                connection.execute(create_table_sql)

                insert_data_sql = text("INSERT INTO #TempCNPJ (CNPJTemp) VALUES (:cnpj_val);")
                params_to_insert = [{"cnpj_val": cnpj} for cnpj in cnpjs_lista]
                
                print(f"Executando: Inserção de {len(params_to_insert)} CNPJs na tabela temporária...")
                connection.execute(insert_data_sql, params_to_insert)
            
            main_select_query = text("""
            SELECT
                    pro.CodProcesso                                 AS [CodProcesso],
                    dev.NomCliente                                  AS [Devedor],
                    dev.NumCpfCnpj                                  AS [CPF],
                    ph.DesHistorico                                 AS [UltimoAcionamento],
                    ps.DesProcessoSituacao                          AS [Situacao]
            FROM
                    Processo pro
                    LEFT JOIN Cliente cli ON cli.CodCliente = pro.CodCliente
                    LEFT JOIN ProcessoTitulo pt ON pt.CodProcesso = pro.CodProcesso
                    LEFT JOIN ProcessoHistorico ph ON ph.CodProcesso = pro.CodProcesso
                    LEFT JOIN ProcessoSituacao ps ON ps.CodProcessoSituacao = pro.CodProcessoSituacao
                    LEFT JOIN Cliente dev ON dev.CodCliente = pro.CodDevedor
                    INNER JOIN #TempCNPJ ON #TempCNPJ.CNPJTemp = dev.NumCpfCnpj
            GROUP BY
                    pro.CodProcesso,
                    dev.NomCliente,
                    dev.NumCpfCnpj,
                    ph.DesHistorico,
                    ps.DesProcessoSituacao;
            """)

            print("\nExecutando: Consulta SELECT principal com JOIN na tabela temporária...")
            
            df_resultados = pd.read_sql(main_select_query, connection) # Leitura dos dados
            
            print(f"Consulta executada com sucesso. Total de {len(df_resultados)} registros encontrados.")
            
            # Limpar strings antes de salvar no Excel
            string_columns = df_resultados.select_dtypes(include=['object']).columns
            for col in string_columns:
                df_resultados[col] = df_resultados[col].apply(clean_excel_string)

            # --- NOVO BLOCO: SALVAR EXCEL COM LARGURA DE COLUNA AJUSTADA E MÁXIMO DE 50 ---
            # Crie um objeto ExcelWriter
            with pd.ExcelWriter(caminho_salvamento, engine='openpyxl') as writer:
                # Salve o DataFrame na planilha (pode ser 'Dados' ou 'Sheet1' ou qualquer nome)
                df_resultados.to_excel(writer, sheet_name='Dados', index=False)
                
                # Acesse o objeto da planilha do openpyxl
                worksheet = writer.sheets['Dados']

                # Itere sobre as colunas para ajustar a largura
                for col_idx, col_name in enumerate(df_resultados.columns):
                    # Calcula a largura máxima do conteúdo da coluna (incluindo o cabeçalho)
                    # Certifica-se de que todos os valores são tratados como string para len()
                    max_len_content = 0
                    if not df_resultados[col_name].empty:
                        # Pega o comprimento máximo de todos os valores na coluna
                        max_len_content = df_resultados[col_name].astype(str).apply(len).max()

                    # Considera o comprimento do cabeçalho da coluna também
                    max_len_header = len(str(col_name))

                    # Pega o maior entre o conteúdo e o cabeçalho
                    ideal_width = max(max_len_content, max_len_header)
                    
                    # Adicione um pequeno padding (espaço extra, ex: 2 caracteres)
                    adjusted_width = ideal_width + 2

                    # Aplica a restrição de largura máxima de 50
                    final_width = min(adjusted_width, 50) 
                    
                    # Obtenha a letra da coluna (A, B, C, ...)
                    col_letter = openpyxl.utils.get_column_letter(col_idx + 1)
                    
                    # Defina a largura da coluna na planilha
                    worksheet.column_dimensions[col_letter].width = final_width
            
            print(f"Relatório salvo com sucesso em '{caminho_salvamento}' com largura de colunas ajustada (máx 50).")

    except Exception as e:
        print(f"Ocorreu um erro em executar_query: {e}")
        traceback.print_exc() # Imprime o stack trace completo do erro

# --- Bloco principal (if __name__ == "__main__":) permanece o mesmo ---
if __name__ == "__main__":
    CAMINHO_ARQUIVO = fr"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Base_Heineken_PD.xlsx"
    NOME_PLANILHA = fr"Base total"
    COLUNA_CNPJ = fr"CNPJ/CPF - Devedor"
    COLUNA_TITULO = fr"TITULO"

    print("Iniciando o processo de consulta de devedores...")

    cnpjs_recebidos_do_excel = importar_cnpjs(
              CAMINHO_ARQUIVO,
              NOME_PLANILHA,
              COLUNA_CNPJ,
              COLUNA_TITULO
    )

    if cnpjs_recebidos_do_excel is not None:
        if cnpjs_recebidos_do_excel:
            cnpjs_unicos = list(set(cnpjs_recebidos_do_excel))
            print(f"Número de CNPJs únicos após remoção de duplicatas: {len(cnpjs_unicos)}")
            executar_query(cnpjs_unicos)
        else:
            print("A lista de CNPJs do Excel está vazia após a filtragem. Nenhuma consulta será executada no banco de dados.")
    else:
        print("A importação de CNPJs do Excel falhou. Verifique as mensagens de erro acima.")