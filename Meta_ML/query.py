import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
import datetime
from sqlalchemy import text
from database import get_engine

def query_metas():

    # Configurar conexão com banco de dados
    engine = get_engine()

    # Definir a query SQL
    query = """
WITH Cadastro_Operador AS
	(
	SELECT
			pro.CodProcesso						AS [CodProcesso],
			pt.CodTitulo						AS [CodTitulo],
		        pt.CodParcela						AS [CodParcela],
			pro.CodCliente						AS [CodCliente],
			pro.CodCobrador						AS [CodCobrador],
			et.CodResponsavel					AS [CodSuper],
			pro.CodPortador						AS [CodPortador],
			pt.ValTitulo						AS [ValCad],
			prt.DtaAuditado						AS [DtaPag],
			pt.DtaVencimento					AS [DtaVenc],
			COALESCE(prt.ValCapital,0)+COALESCE(prt.ValMulta,0)+COALESCE(prt.ValJuros,0)+COALESCE(prt.ValProtesto,0)+COALESCE(prt.ValProtestoAdicional,0)			AS [ValRepasse],
			COALESCE(prt.ValCapital,0)+COALESCE(prt.ValHonorarioDevedor,0)+COALESCE(prt.ValMulta,0)+COALESCE(prt.ValJuros,0)+COALESCE(prt.ValProtesto,0)+
			COALESCE(prt.ValDespesaBancaria,0)+COALESCE(prt.ValDespesaDiverso,0)+COALESCE(prt.ValDespesaHonorarioDevedor,0)+COALESCE(prt.ValComplementoTaxa,0)+
			COALESCE(prt.ValProtestoAdicional,0)			AS [ValPgto],
			
			COALESCE(prt.ValHonorarioDevedor,0)+COALESCE(prt.ValTaxaContrato,0)+COALESCE(prt.ValComplementoTaxa,0)+COALESCE(ValHonorarioCobrador,0)+COALESCE(prt.ValTaxaAdicional,0)	AS [ValReceita],
			COALESCE(prt.ValTaxaContrato,0)		AS [Taxa]
	FROM
			ProcessoTitulo pt
			LEFT JOIN Processo pro						ON pt.CodProcesso = pro.CodProcesso
			LEFT JOIN Cliente cob						ON cob.CodCliente = pro.CodCobrador
			LEFT JOIN EquipeTrabalho et					ON et.CodEquipeTrabalho = cob.CodEquipeTrabalho
			LEFT JOIN ProcessoRecebimentoTitulo prt		ON prt.CodProcesso = pt.CodProcesso AND prt.CodTitulo = pt.CodTitulo AND prt.CodParcela = pt.CodParcela
			LEFT JOIN ContaCorrenteMovimento ccm		ON ccm.CodMovimento = prt.CodMovimento
	WHERE
			1=1
			AND prt.DtaAuditado >= '2025-02-01 00:00:00'
			AND prt.DtaAuditado < '2025-07-01 00:00:00'
            AND pt.DtaCadastro < '2025-07-01 00:00:00'
			AND pro.CadJuridico = '0'
			AND et.CodResponsavel IN ('7123245','7803018','6012687','7945415','6506149','7982952','4891651','7856237','2523178','7161829','6012690')
	),
Dias_Uteis AS
	(
    SELECT 1 AS mes, 22 AS dias_uteis -- Janeiro: 23 dias úteis
    UNION ALL
    SELECT 2 AS mes, 20 AS dias_uteis -- Fevereiro: 19 dias úteis
    UNION ALL
    SELECT 3 AS mes, 20 AS dias_uteis -- Março: 21 dias úteis
    UNION ALL
    SELECT 4 AS mes, 20 AS dias_uteis -- Abril: 22 dias úteis
    UNION ALL
    SELECT 5 AS mes, 21 AS dias_uteis -- Maio: 22 dias úteis
    UNION ALL
    SELECT 6 AS mes, 20 AS dias_uteis -- Junho: 20 dias úteis
    UNION ALL
    SELECT 7 AS mes, 23 AS dias_uteis -- Julho: 22 dias úteis
    UNION ALL
    SELECT 8 AS mes, 21 AS dias_uteis -- Agosto: 22 dias úteis
    UNION ALL
    SELECT 9 AS mes, 22 AS dias_uteis -- Setembro: 21 dias úteis
    UNION ALL
    SELECT 10 AS mes, 23 AS dias_uteis -- Outubro: 23 dias úteis
    UNION ALL
    SELECT 11 AS mes, 19 AS dias_uteis -- Novembro: 21 dias úteis
    UNION ALL
    SELECT 12 AS mes, 20 AS dias_uteis -- Dezembro: 20 dias úteis
	),
Agrupamento AS
	(
	SELECT
		co.CodSuper					        AS [CodSuper],
		co.CodCobrador					        AS [CodCobrador],
		YEAR(co.DtaPag)		                                AS [YrPag],
		MONTH(co.DtaPag)		                        AS [MesPag],
		ra.DesRamoAtividade				        AS [Segmento],
		CASE 
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <  1	THEN 0--'1.Sem atraso'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 30	THEN 1--'2.Menor que 30'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 60	THEN 2--'3.Entre 31 e 60'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 90	THEN 3--'4.Entre 61 e 90'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 180	THEN 4--'5.Entre 91 e 180'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 360	THEN 5--'6.Entre 181 e 360'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 720	THEN 6--'7.Entre 361 e 720'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 1080	THEN 7--'8.Entre 721 e 1080'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 1800	THEN 8--'9.Entre 1081 e 1800'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) >  1800	THEN 9--'10.Acima que 1800'
				ELSE -1
		END									AS [FaixaAtraso],
		SUM(co.ValCad)						AS [ValorCadastrado],
		SUM(co.ValPgto)						AS [ValorPago],
		SUM(co.ValRepasse)					AS [ValorRepasse],
		SUM(co.ValReceita)					AS [ValorReceita],
		SUM(co.Taxa)						AS [ValorTaxa]
	FROM
		Cadastro_Operador co
		LEFT JOIN Cliente cli						ON cli.CodCliente = co.CodCliente
		LEFT JOIN RamoAtividade ra					ON ra.CodRamoAtividade = cli.CodRamoAtividade
	GROUP BY
		co.CodCobrador,
		co.CodSuper,
                YEAR(co.DtaPag),
		MONTH(DtaPag),
		ra.DesRamoAtividade,
		CASE
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <  1	THEN 0--'1.Sem atraso'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 30	THEN 1--'2.Menor que 30'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 60	THEN 2--'3.Entre 31 e 60'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 90	THEN 3--'4.Entre 61 e 90'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 180	THEN 4--'5.Entre 91 e 180'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 360	THEN 5--'6.Entre 181 e 360'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 720	THEN 6--'7.Entre 361 e 720'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 1080	THEN 7--'8.Entre 721 e 1080'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) <= 1800	THEN 8--'9.Entre 1081 e 1800'
				WHEN DATEDIFF(DAY,co.DtaVenc,co.DtaPag) >  1800	THEN 9--'10.Acima que 1800'
				ELSE -1
		END
	)
SELECT
		CAST(ag.YrPag AS INT)           AS [AnoPag],
		CAST(ag.MesPag AS INT)          AS [MesPag],
		COALESCE(super.NomCliente,'SEMNOME')									AS [Responsavel],
                COALESCE(CAST(ag.CodSuper AS INT),'000000')                     AS [CodSuper],
                ag.CodCobrador, 
		cob.NomCliente			AS [Negociador],
		ag.Segmento		        AS [Segmento],
		ag.FaixaAtraso			AS [FaixaAtraso],
		ag.ValorCadastrado		AS [ValCad],
		ag.ValorPago			AS [ValPago],
		ag.ValorTaxa			AS [ValTaxa],
		ag.ValorReceita			AS [ValReceita]
FROM
		Agrupamento ag
		LEFT JOIN Cliente super		ON super.CodCliente = ag.CodSuper
		LEFT JOIN Cliente cob		ON cob.CodCliente = ag.CodCobrador
UNION ALL
SELECT
		MAX(ag.YrPag),
                MAX(ag.MesPag)+1,
		COALESCE(super.NomCliente,'SEMNOME'),
                COALESCE(CAST(ag.CodSuper AS INT),'000000'),
                ag.CodCobrador, 
		cob.NomCliente,
		ag.Segmento,
		ag.FaixaAtraso,
		AVG(ag.ValorCadastrado),
		AVG(ag.ValorPago),
		AVG(ag.ValorTaxa),
		''
FROM
		Agrupamento ag
		LEFT JOIN Cliente super	ON super.CodCliente = ag.CodSuper
		LEFT JOIN Cliente cob		ON cob.CodCliente = ag.CodCobrador
WHERE ag.MesPag IN (6)
GROUP BY
		COALESCE(super.NomCliente,'SEMNOME'),
                COALESCE(CAST(ag.CodSuper AS INT),'000000'),
                ag.CodCobrador,
		cob.NomCliente,
		ag.Segmento,
		ag.FaixaAtraso

ORDER BY
		AnoPag,MesPag,CodSuper,CodCobrador,Segmento
    """

    # Executar a query e carregar os dados em um DataFrame
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

        # Definir o nome do arquivo CSV
        nome_arquivo = f"dados_receita_julho.csv"

        # Salvar o DataFrame como CSV
        df.to_csv(nome_arquivo, index=False, encoding="utf-8")

        print(f"Arquivo salvo com sucesso: {nome_arquivo}")
