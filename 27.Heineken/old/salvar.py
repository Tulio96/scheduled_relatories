import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
from sqlalchemy import text
from notificador_chat import enviar_mensagem_google_chat

def salvar_script(nome_script, query, caminho_arquivo, engine):
    try:
        # Executar a query e carregar os dados em um DataFrame
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        # Salvar os dados no Excel
        df.to_excel(caminho_arquivo, index=False, engine="openpyxl")

        # Abrir o arquivo para ajustar a formatação
        wb = openpyxl.load_workbook(caminho_arquivo)
        ws = wb.active

        MAX_WIDTH = 50

        # Ajustar largura automaticamente e centralizar células
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter  # Obtém a letra da coluna
            for cell in col:
                try:
                    # Ajusta largura baseado no conteúdo
                    if cell.value:
                        max_length = min(MAX_WIDTH, max(max_length, len(str(cell.value))))
                    cell.alignment = Alignment(horizontal="center", vertical="center")  # Centraliza
                except:
                    pass
            ws.column_dimensions[col_letter].width = max_length + 2  # Ajusta a largura com margem

        # Salvar alterações
        wb.save(caminho_arquivo)

        print(f"Consulta executada e resultados salvos em: {caminho_arquivo}")

        status_execucao = "SUCESSO"
        mensagem_final = "Consulta executada e resultados salvos em"

    except Exception as e:
        # Se ocorrer algum erro
        status_execucao = "ERRO"
        mensagem_final = "{nome_script} - Erro ao executar e salvar o arquivo."
        detalhes_erro = str(e)
        print(f"{nome_script} - Ocorreu um erro: {detalhes_erro}")
        traceback.print_exc()

    finally:
        if status_execucao == "SUCESSO":
            mensagem = mensagem_final
        else:
            mensagem = f"{mensagem_final} (Detalhes: {detalhes_erro})"

    enviar_mensagem_google_chat(
        mensagem = mensagem_final,
        script_nome = nome_script,
        status=status_execucao,
        caminho_arquivo=caminho_arquivo
        )

    print(f"{nome_script} - Finalizado. Status: {status_execucao}.")

    if status_execucao == "ERRO":
            sys.exit(1)


