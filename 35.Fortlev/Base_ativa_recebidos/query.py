import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
import datetime
from sqlalchemy import text
from database import get_engine
from salvar_fortlev import salvar_script

def query_baseativarecebidosfortlev():

    # Data atual para nome do arquivo
    data_hoje = datetime.datetime.today().strftime("%Y-%m-%d")

    # Definir o caminho do arquivo
    caminho_arquivo=fr"/mnt/Rede/MIS/B2B - Global/35 - Fortlev/Base_ativa_recebidos_Fortlev_{data_hoje}.xlsx"

    # Definir o nome do script
    nome_script = fr"Base ativa e recebimentos Fortlev"

    engine = get_engine()

    # === 1ª Consulta: Base Devolução ===
    query_base = """
with 
ultimoacordo as 
(select * from ProcessoProposta where SelPropostaAcordo = 1),
pgto as 
(select
    Processo.CodProcesso,
    ProcessoTitulo.CodTitulo,
    ProcessoTitulo.CodParcela,
    Sum(ProcessoRecebimentoTitulo.ValCapital) as ValCap,
    Sum(ProcessoRecebimentoTitulo.ValHonorarioDevedor) as ValHD,
    Sum(ProcessoRecebimentoTitulo.Valtaxacontrato) as ValTaxa,
    Sum(ProcessoRecebimentoTitulo.ValComplementoTaxa) as ValComplemento
from
    Processo
    INNER JOIN Processotitulo ON Processo.codprocesso = Processotitulo.CodProcesso
    INNER JOIN ProcessoRecebimentoTitulo ON (
        Processotitulo.codprocesso = ProcessoRecebimentoTitulo.codprocesso
        and ProcessoTitulo.CodTitulo = ProcessoRecebimentoTitulo.CodTitulo
        and ProcessoTitulo.CodParcela = ProcessoRecebimentoTitulo.CodParcela
    )
    INNER JOIN ProcessoRecebimento ON (
        ProcessoRecebimentoTitulo.CodProcesso = Processorecebimento.codprocesso
        and ProcessoRecebimentoTitulo.CodMovimento = Processorecebimento.CodMovimento
    )
    LEFT JOIN ContaCorrenteMovimento ON Processorecebimento.CodMovimento = ContaCorrenteMovimento.CodMovimento
Group By
    Processo.CodProcesso,
    ProcessoTitulo.CodTitulo,
    ProcessoTitulo.CodParcela)


select
    cli.NomCliente2                 empresa,
    dvc.CodDevedorCliente           cliente,
    prt.CodTitulo                   titulo,
    prt.DtaCadastro                 data_cadastro,
    prt.DtaVencimento               data_vencimento,
    DATEDIFF(DAY, prt.DtaVencimento, GETDATE()) AS dias_vencidos,
    case when pgto.ValCap is not null then prt.ValTitulo - pgto.ValCap else prt.ValTitulo end  saldo_restante,
    prs.DesProcessoSituacao         status_processo,
    CAST(GETDATE() AS DATE)         AS ativo_em,
    dev.Uf                          uf,
    ''                              status_contrato,
    CASE WHEN prs.DesProcessoSituacao = 'ACORDO' THEN CAST(ppt.DtaProposta AS DATE) ELSE null END   data_acordo
from ProcessoTitulo prt
    LEFT JOIN Processo pro on pro.CodProcesso = prt.CodProcesso
    LEFT JOIN Cliente cli on cli.CodCliente = pro.CodCliente
    LEFT JOIN Cliente dev on dev.CodCliente = pro.CodDevedor
    LEFT JOIN DevedorCliente dvc on dvc.CodCliente = pro.CodCliente and dvc.CodDevedor = pro.CodDevedor
    LEFT JOIN pgto ON pro.CodProcesso = PGTO.CodProcesso
    and prt.CodTitulo = PGTO.CodTitulo
    and prt.CodParcela = PGTO.CodParcela
    LEFT JOIN ProcessoSituacao prs on prs.CodProcessoSituacao = pro.CodProcessoSituacao
    LEFT JOIN ultimoacordo ppt on ppt.CodProcesso = prt.CodProcesso
where 1=1
    and cli.CodGrupoEmpresa = 557
    and prt.DtaEncerrado is null

OPTION (RECOMPILE);
    """

    # === 2ª Consulta: Resumo por UF (exemplo) ===
    query_resumo = """
    select DISTINCT

	dvc.CodDevedorCliente                              cod_cliente,
	dev.NomCliente                                     devedor,
	prt.CodTitulo                                      titulo_recebido,
	prt.CodParcela                                     parcela_titulo,
	ptt.DtaVencimento                                  vencimento_titulo,
	prt.ValCapital                                     saldo_repasse,
	cmm.DtaMovimento                                   data_pg,
	ptt.DtaCadastro                                    data_cadastro,
	DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento)  atraso,
	    CASE 
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 1 AND 30 THEN '01-30'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 31 AND 60 THEN '31-60'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 61 AND 90 THEN '61-90'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 91 AND 120 THEN '91-120'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 121 AND 180 THEN '121-180'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 181 AND 360 THEN '181-360'
        WHEN DATEDIFF(DAY, ptt.DtaVencimento, cmm.DtaMovimento) BETWEEN 361 AND 720 THEN '361-720'
        ELSE 'Acima 720'
    END AS                                             aging,
	dev.Uf                                             uf,
    
	CASE 
    	WHEN mtp.DesMovimentoTipo = 'PAGAMENTO DIRETO AO CREDOR' THEN 'PAGAMENTO DIRETO AO CREDOR' 
        ELSE 'PAGAMENTO GLOBAL' 
    END  tipo
        
from ProcessoRecebimentoTitulo prt
	LEFT JOIN ProcessoRecebimento prr on prr.CodProcesso = prt.CodProcesso and prr.CodMovimento = prt.CodMovimento
	LEFT JOIN Processo pro on pro.CodProcesso = prt.CodProcesso
	LEFT JOIN Cliente cli on cli.CodCliente = pro.CodCliente
	LEFT JOIN Cliente dev on dev.CodCliente = pro.CodDevedor
	LEFT JOIN DevedorCliente dvc on dvc.CodCliente = pro.CodCliente and dvc.CodDevedor = pro.CodDevedor
	LEFT JOIN ProcessoTitulo ptt on ptt.CodProcesso = prt.CodProcesso and ptt.CodParcela = prt.CodParcela and ptt.CodTitulo = prt.CodTitulo
	LEFT JOIN ContaCorrenteMovimento cmm on cmm.CodMovimento = prr.CodMovimento
	LEFT JOIN MovimentoTipo mtp on mtp.CodMovimentoTipo = cmm.CodMovimentoTipo
    
WHERE 1=1
	AND cli.CodGrupoEmpresa = 557
	AND cmm.DtaMovimento >= '2025-01-01' AND CAST(cmm.DtaMovimento AS DATE) < CAST(GETDATE() AS DATE)

OPTION (RECOMPILE);
    """

    salvar_script(
        caminho_arquivo=caminho_arquivo,
        nome_script=nome_script,
        query_base=query_base,
        query_resumo=query_resumo,
        engine=engine
    )