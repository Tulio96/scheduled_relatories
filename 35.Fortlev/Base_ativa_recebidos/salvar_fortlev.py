import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
from sqlalchemy import text
from notificador_chat import enviar_mensagem_google_chat

def salvar_script(nome_script, query_base, query_resumo, caminho_arquivo, engine):
    try:
        with engine.connect() as conn:
            df_base = pd.read_sql(text(query_base), conn)
            df_resumo = pd.read_sql(text(query_resumo), conn)

        # Salvar os DataFrames em abas diferentes no mesmo arquivo Excel
        with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
            df_base.to_excel(writer, sheet_name="Base Ativa", index=False)
            df_resumo.to_excel(writer, sheet_name="Recebidos", index=False)

        # Abrir o arquivo e aplicar formatação em cada aba
        wb = openpyxl.load_workbook(caminho_arquivo)
        abas_para_formatar = ["Base Ativa", "Recebidos"]
        MAX_WIDTH = 50

        for aba in abas_para_formatar:
            ws = wb[aba]
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = min(MAX_WIDTH, max(max_length, len(str(cell.value))))
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    except:
                        pass
                ws.column_dimensions[col_letter].width = max_length + 2  # margem extra

        # Salvar alterações
        wb.save(caminho_arquivo)
        print(f"Consultas executadas e arquivo salvo em: {caminho_arquivo}")

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


