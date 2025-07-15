import pandas as pd
import pyodbc
import openpyxl
import traceback
import re

# --- Função para limpar strings antes de exportar para Excel (sem alterações) ---
def clean_excel_string(text_val):
    """Remove caracteres de controle ilegais do XML de uma string."""
    if isinstance(text_val, str):
        # Expressão regular para encontrar caracteres ilegais no XML
        cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text_val)
        return cleaned_text
    return text_val

# --- Função importar_dados_excel (com remoção de múltiplos zeros à esquerda) ---
def importar_dados_excel(caminho_arquivo, sheet_name, coluna_cnpj, coluna_titulo, coluna_parcela):
    """
    Importa os dados e padroniza o CNPJ/CPF, removendo pontuação e TODOS os zeros
    à esquerda, para consulta no banco.
    """
    try:
        # 1. Ler as colunas-chave como texto (str) para garantir que os zeros sejam preservados na leitura inicial.
        colunas_como_texto = {
            coluna_cnpj: str,
            coluna_titulo: str,
            coluna_parcela: str
        }
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name, dtype=colunas_como_texto)

        print(f"Total de linhas lidas do Excel (antes da filtragem): {len(df)}")

        # 2. Verificar se todas as colunas necessárias existem.
        for col in ['status ', coluna_cnpj, coluna_titulo, coluna_parcela]:
            if col not in df.columns:
                print(f"Erro: A coluna '{col}' não foi encontrada na planilha '{sheet_name}'.")
                return None

        # 3. Filtrar pelo status de pagamento.
        df_PD = df[df["status "] == "pagamento direto"].copy()
        print(f"Total de linhas após a filtragem por 'PAGAMENTO DIRETO': {len(df_PD)}")

        if df_PD.empty:
            print("Nenhuma linha com 'PAGAMENTO DIRETO' encontrada.")
            return []

        # --- LÓGICA DE TRATAMENTO ATUALIZADA ---
#        def limpar_e_ajustar_cnpj_cpf(valor):
            """Remove pontuação e todos os zeros à esquerda, exceto para o valor '0'."""
            # Garante que o valor seja uma string e remove tudo que não for dígito.
#            limpo = re.sub(r'\D', '', str(valor))
#            if not limpo:
#                return ""

            # Se o número for '0', '00', etc., retorna um único '0'.
            # Usamos a conversão para int apenas para esta checagem.
#            if int(limpo) == 0:
#                return '0'

            # Remove todos os zeros do início da string. Ex: '000123' -> '123'
#            return limpo.lstrip('0')

        # 4. Aplica a nova função de limpeza.
#        df_PD['cnpj_ajustado'] = df_PD[coluna_cnpj].apply(limpar_e_ajustar_cnpj_cpf)

        # Mantém as outras colunas como estão (apenas tratando nulos).
        df_PD['titulo_bruto'] = df_PD[coluna_titulo].fillna('')
        df_PD['parcela_bruta'] = df_PD[coluna_parcela].fillna('')
        df_PD['cnpj_bruto'] = df_PD[coluna_cnpj].fillna('')

        # 5. Criar a lista de tuplas com os dados para consulta.
        mask_validos = df_PD['cnpj_bruto'] != ''
        dados_para_db = list(zip(
            df_PD.loc[mask_validos, 'cnpj_bruto'],
            df_PD.loc[mask_validos, 'titulo_bruto'],
            df_PD.loc[mask_validos, 'parcela_bruta']
        ))

        if not dados_para_db:
            print("Nenhum CPF/CNPJ válido encontrado após a limpeza.")
            return []

        # Salvar um CSV para conferência dos dados exatos que serão enviados ao banco.
        df_para_conferencia = pd.DataFrame(dados_para_db, columns=['CNPJ_ENVIADO', 'TITULO_ENVIADO', 'PARCELA_ENVIADA'])
        df_para_conferencia.to_csv("dados_enviados_para_consulta.csv", index=False, sep=';', encoding='utf-8')
        print(f"Dados exatos que serão consultados foram salvos em 'dados_enviados_para_consulta.csv'")

        return dados_para_db

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo Excel: {e}")
        traceback.print_exc()
        return None