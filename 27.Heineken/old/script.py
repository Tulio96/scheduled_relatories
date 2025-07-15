from querys_heineken import executar_querys
from ler_excel import importar_dados_excel

# --- Bloco principal (sem alterações) ---
if __name__ == "__main__":
    CAMINHO_ARQUIVO = r"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Exc.xlsx"
    NOME_PLANILHA = r"Base"
    COLUNA = r"Codigo "
#    COLUNA = "CNPJ/CPF - Devedor"
    COLUNA_TITULO = r"TITULO "
    COLUNA_PARCELA = r"Parcela "

    print("Iniciando o processo de consulta de devedores...")

    # Chama a função de importação com os três nomes de coluna
    dados_do_excel = importar_dados_excel(
        CAMINHO_ARQUIVO,
        NOME_PLANILHA,
        COLUNA,
        COLUNA_TITULO,
        COLUNA_PARCELA
    )

    if dados_do_excel is not None:
        if dados_do_excel:
            # Remove duplicatas baseadas na combinação (CNPJ, Título, Parcela)
            dados_unicos = list(set(dados_do_excel))
            print(f"Número de combinações (CNPJ, Título, Parcela) únicas: {len(dados_unicos)}")
            executar_querys(dados_unicos,CAMINHO_ARQUIVO,NOME_PLANILHA)
        else:
            print("A lista de dados do Excel está vazia após a filtragem. Nenhuma consulta será executada.")
    else:
        print("A importação de dados do Excel falhou. Verifique as mensagens de erro acima.")

