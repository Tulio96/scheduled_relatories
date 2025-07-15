import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
import datetime
from sqlalchemy import text
from database import get_engine
from salvar import salvar_script

def query_baseativaogochi():
    # Obter data atual para nome do arquivo
    data_hoje = datetime.datetime.today().strftime("%Y-%m-%d")

    # Definir caminho e nome do arquivo
    caminho_arquivo = fr"/mnt/Rede/MIS/B2B - Global/02 - Ogochi/Base_Ativa_Ogochi_{data_hoje}.xlsx"

    # Definir o nome do script
    nome_script = fr"Base Ativa Ogochi"

    # Configurar conexão com banco de dados
    engine = get_engine()

    # Definir a query SQL
    query = """
WITH Processos_Filtrados AS
    (
    SELECT
	    Processo.CodProcesso,
	    Processo.CodCliente,
	    Processo.CodDevedor,
	    Processo.CodProcessoSituacao
    FROM
	    Processo
	    LEFT JOIN Cliente ON Cliente.CodCliente = Processo.CodCliente
    WHERE 1=1
	    AND Cliente.CodGrupoEmpresa = '272'
	    AND Processo.DtaEncerrado IS NULL
	    AND Processo.CadJuridico = '0'
    ),
pgto AS
    (
    SELECT
	Processo.CodProcesso,
	ProcessoTitulo.CodTitulo,
	ProcessoTitulo.CodParcela,
	ProcessoRecebimentoTitulo.DtaAuditado 				 	AS DtaAuditado,
	SUM(ProcessoRecebimentoTitulo.ValCapital)				AS ValCap,
	SUM(ProcessoRecebimentoTitulo.ValHonorarioDevedor)  	AS ValHD,
	SUM(ProcessoRecebimentoTitulo.Valtaxacontrato)			AS ValTaxa,
	SUM(ProcessoRecebimentoTitulo.ValComplementoTaxa)		AS ValComplemento,
	SUM(ProcessoRecebimentoTitulo.ValProtesto)				AS ValProtesto,
	SUM(ProcessoRecebimentoTitulo.ValMulta)					AS ValMulta,
	SUM(ProcessoRecebimentoTitulo.ValDesconto)				AS ValDesconto,
	SUM(ProcessoRecebimentoTitulo.ValJuros)					AS ValJuros
    FROM
	Processos_Filtrados Processo
	INNER JOIN Processotitulo			 ON Processo.codprocesso = Processotitulo.CodProcesso
	INNER JOIN ProcessoRecebimentoTitulo ON (
		    Processotitulo.codprocesso = ProcessoRecebimentoTitulo.codprocesso
	    and ProcessoTitulo.CodTitulo = ProcessoRecebimentoTitulo.CodTitulo
	    and ProcessoTitulo.CodParcela = ProcessoRecebimentoTitulo.CodParcela
		)
	INNER JOIN ProcessoRecebimento		 ON (
		    ProcessoRecebimentoTitulo.CodProcesso = Processorecebimento.codprocesso
	    and ProcessoRecebimentoTitulo.CodMovimento = Processorecebimento.CodMovimento
		)
	LEFT JOIN ContaCorrenteMovimento	 ON Processorecebimento.CodMovimento = ContaCorrenteMovimento.CodMovimento
    GROUP BY
		Processo.CodProcesso,
		ProcessoTitulo.CodTitulo,
		ProcessoTitulo.CodParcela
		,ProcessoRecebimentoTitulo.DtaAuditado
    )

--------QUERRY BASE ATIVA--------
SELECT
        cli.NumCpfCnpj							AS [CNPJ Cliente],
        cli.NomCliente							AS [Cliente],
        cli.NomCliente2							AS [Nome Fantasia],
        pro.CodProcesso							AS [CodProcesso],
        cdev.NumCpfCnpj							AS [CNPJ/CPF Devedor],
        cdev.NomCliente							AS [NomDevedor],
        city.NomCidade							AS [Cidade],
        city.CodEstado							AS [Estado],
        ps.DesProcessoSituacao					AS [Situação],
        pt.CodTitulo							AS [Título],
        pt.CodParcela							AS [Parcela],
        FORMAT(pt.DtaCadastro, 'dd/MM/yyyy')	AS [Dt. Cadastro],
        FORMAT(pt.DtaVencimento,'dd/MM/yyyy')	AS [Dt. Vencimento],
        ROUND(pt.ValTitulo,2)					AS [Vl. Título],
        ROUND(pt.ValProtesto,2)					AS [Vl. Protesto],
        CASE 
		WHEN SUM(pgto.ValCap) IS NULL THEN 0
		ELSE SUM(Pgto.Valcap)
        END										AS [Vl. Pagamento],
        CASE
		WHEN SUM(pgto.ValCap) IS NULL THEN SUM(pt.ValTitulo)
		ELSE SUM(pt.ValTitulo) - SUM(pgto.ValCap)
        END										AS [Vl. Saldo],
        devc.CodDevedorCliente					AS [Cód. Devedor/Cliente],
	DATEDIFF(DAY,MIN(pt.DtaVencimento),GETDATE())	
						AS [Dias em Atraso]
FROM
    Processos_Filtrados pro
    INNER JOIN Cliente cli						 ON cli.CodCliente = pro.CodCliente
    INNER JOIN Cliente cdev						 ON pro.CodDevedor = cdev.CodCliente
    LEFT JOIN DevedorCliente devc				 ON devc.CodDevedor = pro.CodDevedor AND devc.CodCliente = pro.CodCliente
    LEFT JOIN ProcessoTitulo pt					 ON pt.CodProcesso = pro.Codprocesso
    LEFT JOIN ProcessoSituacao ps				 ON ps.CodProcessoSituacao = pro.CodProcessoSituacao
    LEFT JOIN TituloMotivoDevolucao tmd			 ON tmd.CodMotivoDevolucao = pt.CodMotivoDevolucao
    LEFT JOIN Cidade city						 ON city.CodCidade = cdev.CodCidade
    LEFT JOIN pgto								 ON pro.CodProcesso = pgto.CodProcesso AND pt.CodTitulo = pgto.CodTitulo AND pgto.CodParcela = pt.CodParcela
WHERE
    1=1
    AND pt.TipEncerrado IS NULL
GROUP BY
	pt.DtaCadastro,
	pro.CodProcesso,
	pt.CodTitulo,
	cdev.NomCliente,
	cli.NomCliente2,
	cli.CodGrupoEmpresa,
	pt.ValTitulo,
	pt.DtaEncerrado,
	ps.DesProcessoSituacao,
	pt.DtaVencimento,
	pt.CodParcela,
	cdev.NumCpfCnpj,
	cli.NumCpfCnpj,
	cli.NomCliente,
	devc.CodDevedorCliente,
	city.CodCidade,
	city.NomCidade,
	city.CodEstado,
	pt.ValTitulo,
	pt.ValProtesto

OPTION (RECOMPILE);
    """

    salvar_script(
        caminho_arquivo=caminho_arquivo,
        nome_script=nome_script,
        query=query,
        engine=engine
    )

