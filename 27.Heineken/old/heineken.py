import pandas as pd
import pyodbc
import openpyxl
from sqlalchemy import text
from database import get_engine
from salvar import salvar_script

def importar_cnpjs(caminho_arquivo, sheet_name, coluna_cnpj):
    
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name)

        df_PD = df[df["Status Pagamento"] == "PAGAMENTO DIRETO"]

        if coluna_cnpj not in df.columns:
            print(f"Erro: A coluna '{coluna_cnpj}' não foi encontrada")
            return None
        cnpjs = df_PD[coluna_cnpj].astype(str).fillna('')

        cnpjs_limpos = cnpjs.apply(lambda x: ''.join(filter(str.isdigit,x)))

        string_cnpjs = ','.join(f"('{cod}')" for cod in cnpjs_limpos)

        df_cnpjs = pd.DataFrame(cnpjs_limpos,columns=[coluna_cnpj])

        df_cnpjs.to_csv("cnpjs.csv", index=False, sep=';', encoding='utf-8')


        return string_cnpjs

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo Excel: {e}")

def executar_query(string_cnpjs):

    caminho_salvamento = fr"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Avaliacao_PD.xlsx"

    nome_script = fr"pd_heineken"

    engine = get_engine()

    query = """

IF OBJECT_ID('tempdb..#TempCNPJ') IS NOT NULL
BEGIN
    DROP TABLE #TempCNPJ;
END

CREATE TABLE #TempCNPJ
(
CNPJTemp NVARCHAR(255) COLLATE Latin1_General_CI_AI PRIMARY KEY
);

INSERT INTO #TempCNPJ (CNPJTemp) VALUES {string_cnpjs};


SELECT
	pro.CodProcesso				AS [CodProcesso],
	dev.NomCliente				AS [Devedor],
	dev.NumCpfCnpj				AS [CPF],
	ph.DesHistorico				AS [UltimoAcionamento],
	ps.DesProcessoSituacao			AS [Situacao]
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
	ps.DesProcessoSituacao
"""

    salvar_script(
        caminho_arquivo=caminho_salvamento,
        nome_script=nome_script,
        query=query,
        engine=engine
    )

if __name__ == "__main__":

    CAMINHO_ARQUIVO = fr"/mnt/Rede/MIS/B2B - Global/27 - Heineken/Base_Heineken_PD.xlsx"
    NOME_PLANILHA = fr"Base total"
    COLUNA = fr"CNPJ/CPF - Devedor"

    string_cnpjs = importar_cnpjs(
          CAMINHO_ARQUIVO,
          NOME_PLANILHA,
          COLUNA
    )

    executar_query(string_cnpjs)

