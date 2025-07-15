import pandas as pd
from sqlalchemy import text
from database import get_engine
import streamlit as st

#@st.cache_data(ttl=300)  # Atualiza os dados a cada 5 minutos
def buscar_esta_semana_grandes():
    engine = get_engine()

    query = """ 
DECLARE @dt_thisweek_start  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),8,0,0,0);
DECLARE @dt_thisweek_end    AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),18,59,59,99);
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
WITH Carteiras AS
    (
    SELECT
	    CodCliente,
	    CodGrupoEmpresa,
            CASE
		WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
		WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
		WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
		WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
		WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
		WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END				AS Cliente
    FROM
	    Cliente cli
    WHERE (cli.CodGrupoEmpresa IN ('1496','1942','821','1392','2081') OR cli.CodCliente = '5157718')
    ),
Acordos_Periodo AS
    (
    SELECT
	    pp.CodProcesso,
	    pp.CodProcessoProposta,
	    pp.DtaProposta,
	    pp.UsuProposta,
	    CASE
		WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
		WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
		WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
		WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
		WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
		WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END				AS cliente
    FROM
	    ProcessoProposta pp
	    LEFT JOIN Processo pro					ON pro.CodProcesso = pp.CodProcesso
	    LEFT JOIN Usuario usu					ON usu.Usuario = pp.UsuProposta
            LEFT JOIN Cliente cli					ON cli.CodCliente = pro.CodCliente
	    LEFT JOIN Cliente cob					ON usu.CodColaborador = cob.CodCliente
	    LEFT JOIN EquipeTrabalho eq				ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
	    LEFT JOIN Cliente super					ON super.CodCliente = eq.CodResponsavel
	    LEFT JOIN OrigemAcordo oa				ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
    WHERE	1=1
	    AND DtaProposta >= @dt_thisweek_start
	    AND DtaProposta <= @dt_thisweek_end
            AND eq.CodResponsavel IN ('7123245','7803018','6012687','7945415','6506149','7982952','4891651','7856237','2523178','7161829','6012690')
            AND (cli.CodGrupoEmpresa IN ('1496','1942','821','1392','2081') OR cli.CodCliente = '5157718')
	    AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
            --AND pro.CodCobrador NOT IN ('6506149','7982952','4891651','7856237','2523178','7161829','6012690')
            AND SelPropostaAcordo = '1'
    ),
Acordos_Valores AS
    (
    SELECT
	    pp.CodProcesso,
	    pp.CodProcessoProposta,
	    pp.DtaProposta,
	    pp.cliente,
            SUM(ppt.ValCapital + ppt.ValJuros + ppt.ValMulta + ppt.ValProtesto + ppt.ValHonorarioDevedor) AS [Valor]
	--	SUM(CAST(ppt.ValTitulo AS DECIMAL(18,2)) + CAST(ppt.ValJuros AS DECIMAL(18,2)) + CAST(ppt.ValMulta AS DECIMAL(18,2))
	--	  + CAST(ppt.ValHonorarioDevedor AS DECIMAL(18,2)) + CAST(ppt.ValProtesto AS DECIMAL(18,2))) AS [Valor]
    FROM
	    Acordos_Periodo pp
	    LEFT JOIN ProcessoPropostaParcelaBaixa ppt	ON ppt.CodProcesso = pp.CodProcesso AND ppt.CodProcessoProposta = pp.CodProcessoProposta
    WHERE 	
	    1=1
    GROUP BY
	    pp.CodProcesso,
	    pp.CodProcessoProposta,
	    pp.DtaProposta,
	    pp.cliente
    ),
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
DiasW_0 AS
    (
    SELECT CAST(@dt_thisweek_start AS DATETIME) AS [Dia_W_0]
    UNION ALL
    SELECT DATEADD(HOUR, 1, [Dia_W_0])
    FROM DiasW_0
    WHERE [Dia_W_0] < @dt_thisweek_end
    ),
HORAS_GRANDES AS
    (
    SELECT
	cli.Cliente,
	Dia_W_0
    FROM
	Carteiras cli
	LEFT JOIN DiasW_0 ON 1=1
    GROUP BY
	cli.Cliente,
	Dia_W_0
    ),
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
Final AS
    (
    SELECT
        DiasW_0.Cliente   AS [cliente],
	FORMAT(DiasW_0.Dia_W_0, 'HH:00')		AS [Horario],
	SUM(
		CASE 
			WHEN av.CodProcesso IS NULL THEN 0
			ELSE 1
		end
	    )																	AS [Quantidade],
	COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 										AS [Valor]

    FROM
	HORAS_GRANDES DiasW_0
	LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_0.Dia_W_0 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_0.Dia_W_0)
	AND DiasW_0.Cliente = av.cliente
    GROUP BY
	DiasW_0.Dia_W_0,
	DiasW_0.cliente
    )
SELECT * FROM Final

 """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#########################################################################################################################################
#########################################################################################################################################

def buscar_previsao_grandes_hoje():
    engine = get_engine()

    query = f"""
DECLARE @todayh  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),0,0,0,0);
DECLARE @today AS DATE = GETDATE();

WITH Previsao AS
	(
    SELECT      
        CASE
				WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
				WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
				WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
				WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
				WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
				WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END				AS cliente,
        SUM(pppb.ValCapital + pppb.ValProtesto + pppb.ValJuros + pppb.ValMulta + pppb.ValHonorarioDevedor) AS [Previsao_hoje]
FROM 
		ProcessoProposta pp
		LEFT JOIN ProcessoPropostaParcelaBaixa pppb 	ON pp.CodProcesso = pppb.CodProcesso AND pp.CodProcessoProposta = pppb.CodProcessoProposta
		LEFT JOIN ProcessoPropostaParcela ppp 			ON ppp.CodProcesso = pppb.CodProcesso AND ppp.CodProcessoProposta = pppb.CodProcessoProposta AND ppp.CodParcela = pppb.CodParcelaProposta
        LEFT JOIN Processo pro							ON pp.CodProcesso = pro.CodProcesso
        LEFT JOIN Cliente cli							ON cli.CodCliente = pro.CodCliente
		LEFT JOIN Usuario usu							ON usu.Usuario = pp.UsuProposta
		LEFT JOIN Cliente cob							ON usu.CodColaborador = cob.CodCliente
		LEFT JOIN EquipeTrabalho eq						ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
		LEFT JOIN Cliente super							ON super.CodCliente = eq.CodResponsavel
		LEFT JOIN OrigemAcordo oa						ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
WHERE
		CAST(ppp.DtaVencimento AS DATE) = @today
		AND pp.SelPropostaAcordo = '1'
	    AND eq.CodResponsavel IN ('7123245','7803018','6012687','7945415','6506149','7982952','4891651','7856237','2523178','7161829','6012690')
        AND (cli.CodGrupoEmpresa IN ('1496','1942','821','1392','2081') OR cli.CodCliente = '5157718')
		AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
        AND pro.CodProcessoSituacao IN ('5','21','39','48','100','102','149')
GROUP BY
		CASE
				WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
				WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
				WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
				WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
				WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
				WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END
	)
SELECT cliente, SUM(Previsao_hoje) AS Previsao_hoje
FROM Previsao
GROUP BY cliente

    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#########################################################################################################################################
#########################################################################################################################################

def buscar_previsao_grandes_inicio():
    engine = get_engine()

    query = f"""
DECLARE @todayh  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),0,0,0,0);
DECLARE @today AS DATE = GETDATE();

WITH Previsao AS
	(
    SELECT      
        CASE
				WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
				WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
				WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
				WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
				WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
				WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END				AS cliente,
        SUM(pppb.ValCapital + pppb.ValProtesto + pppb.ValJuros + pppb.ValMulta + pppb.ValHonorarioDevedor) AS [Previsao_inicio]
FROM 
		ProcessoProposta pp
		LEFT JOIN ProcessoPropostaParcelaBaixa pppb 	ON pp.CodProcesso = pppb.CodProcesso AND pp.CodProcessoProposta = pppb.CodProcessoProposta
		LEFT JOIN ProcessoPropostaParcela ppp 			ON ppp.CodProcesso = pppb.CodProcesso AND ppp.CodProcessoProposta = pppb.CodProcessoProposta AND ppp.CodParcela = pppb.CodParcelaProposta
        LEFT JOIN Processo pro							ON pp.CodProcesso = pro.CodProcesso
        LEFT JOIN Cliente cli							ON cli.CodCliente = pro.CodCliente
		LEFT JOIN Usuario usu							ON usu.Usuario = pp.UsuProposta
		LEFT JOIN Cliente cob							ON usu.CodColaborador = cob.CodCliente
		LEFT JOIN EquipeTrabalho eq						ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
		LEFT JOIN Cliente super							ON super.CodCliente = eq.CodResponsavel
		LEFT JOIN OrigemAcordo oa						ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
WHERE
		CAST(ppp.DtaVencimento AS DATE) = @today
        AND CAST (pp.Dtaproposta AS DATE) < @todayh
		AND pp.SelPropostaAcordo = '1'
	    AND eq.CodResponsavel IN ('7123245','7803018','6012687','7945415','6506149','7982952','4891651','7856237','2523178','7161829','6012690')
        AND (cli.CodGrupoEmpresa IN ('1496','1942','821','1392','2081') OR cli.CodCliente = '5157718')
		AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
        AND pro.CodProcessoSituacao IN ('5','21','39','48','100','102','149')
GROUP BY
		CASE
				WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
				WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
				WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
				WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
				WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
				WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
		END
	)
SELECT cliente, SUM(Previsao_inicio) AS Previsao_inicio
FROM Previsao
GROUP BY cliente

    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#########################################################################################################################################
#########################################################################################################################################

def buscar_semana_passada_grandes():
    engine = get_engine()

    query = """ 
DECLARE @dt_pastweek_start  AS DATETIME = 
CASE
		WHEN CONVERT(NVARCHAR,DATEADD(DAY,-7,GETDATE())) IN (SELECT DtaFeriado FROM Feriado)
		THEN DATETIMEFROMPARTS(YEAR(DATEADD(DAY,-14,GETDATE())),MONTH(DATEADD(DAY,-14,GETDATE())),DAY(DATEADD(DAY,-14,GETDATE())),8,0,0,0)
		ELSE DATETIMEFROMPARTS(YEAR(DATEADD(DAY,-7,GETDATE())),MONTH(DATEADD(DAY,-7,GETDATE())),DAY(DATEADD(DAY,-7,GETDATE())),8,0,0,0)
END;
DECLARE @dt_pastweek_end  AS DATETIME = 
CASE
		WHEN CONVERT(NVARCHAR,DATEADD(DAY,-7,GETDATE())) IN (SELECT DtaFeriado FROM Feriado)
		THEN DATETIMEFROMPARTS(YEAR(DATEADD(DAY,-14,GETDATE())),MONTH(DATEADD(DAY,-14,GETDATE())),DAY(DATEADD(DAY,-14,GETDATE())),18,59,59,99)
		ELSE DATETIMEFROMPARTS(YEAR(DATEADD(DAY,-7,GETDATE())),MONTH(DATEADD(DAY,-7,GETDATE())),DAY(DATEADD(DAY,-7,GETDATE())),18,59,59,99)
END;
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
WITH Acordos_Periodo AS
	(
	SELECT
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.UsuProposta,
			CASE
				WHEN cli.CodGrupoEmpresa = '1392' THEN 'DELLYS'
				WHEN cli.CodGrupoEmpresa = '1496' THEN 'BAT/SOUZA CRUZ'
				WHEN cli.CodCliente = '5157718' THEN 'FEMSA'
				WHEN cli.CodGrupoEmpresa = '1942' THEN 'PEPSICO'
				WHEN cli.CodGrupoEmpresa = '821' THEN 'PMB'
				WHEN cli.CodGrupoEmpresa = '2081' THEN 'HEINEKEN'
				END				AS cliente
	FROM
			ProcessoProposta pp
			LEFT JOIN Processo pro					ON pro.CodProcesso = pp.CodProcesso
			LEFT JOIN Usuario usu					ON usu.Usuario = pp.UsuProposta
            LEFT JOIN Cliente cli					ON cli.CodCliente = pro.CodCliente
			LEFT JOIN Cliente cob					ON usu.CodColaborador = cob.CodCliente
			LEFT JOIN EquipeTrabalho eq				ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
			LEFT JOIN Cliente super					ON super.CodCliente = eq.CodResponsavel
			LEFT JOIN OrigemAcordo oa				ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
	WHERE	1=1
			AND DtaProposta >= @dt_pastweek_start
			AND DtaProposta <= @dt_pastweek_end
	        AND eq.CodResponsavel IN ('7123245','7803018','6012687','7945415','6506149','7982952','4891651','7856237','2523178','7161829','6012690')
            AND (cli.CodGrupoEmpresa IN ('1496','1942','821','1392','2081') OR cli.CodCliente = '5157718')
			AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
            --AND pro.CodCobrador NOT IN ('6506149','7982952','4891651','7856237','2523178','7161829','6012690')
            AND SelPropostaAcordo = '1'
	),
Acordos_Valores AS
	(
	SELECT
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.cliente,
            SUM(ppt.ValCapital + ppt.ValJuros + ppt.ValMulta + ppt.ValProtesto + ppt.ValHonorarioDevedor) AS [Valor]
		--	SUM(CAST(ppt.ValTitulo AS DECIMAL(18,2)) + CAST(ppt.ValJuros AS DECIMAL(18,2)) + CAST(ppt.ValMulta AS DECIMAL(18,2))
		--	  + CAST(ppt.ValHonorarioDevedor AS DECIMAL(18,2)) + CAST(ppt.ValProtesto AS DECIMAL(18,2))) AS [Valor]
	FROM
			Acordos_Periodo pp
			LEFT JOIN ProcessoPropostaParcelaBaixa ppt	ON ppt.CodProcesso = pp.CodProcesso AND ppt.CodProcessoProposta = pp.CodProcessoProposta
	WHERE 	
			1=1
	GROUP BY
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.cliente
	),
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
DiasW_1 AS
	(
	SELECT CAST(@dt_pastweek_start AS DATETIME) AS [Dia_W_1]
    UNION ALL
    SELECT DATEADD(HOUR, 1, [Dia_W_1])
    FROM DiasW_1
    WHERE [Dia_W_1] < @dt_pastweek_end
	),
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
Final AS
    (
	SELECT
        av.cliente,
		FORMAT(DiasW_1.Dia_W_1, 'HH:00')		AS [Horario],
		SUM(
				CASE 
						WHEN av.CodProcesso IS NULL THEN 0
						ELSE 1
				end
			)																	AS [Quantidade],
		COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 										AS [Valor]


	FROM	DiasW_1
		LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_1.Dia_W_1 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_1.Dia_W_1)
	GROUP BY
		DiasW_1.Dia_W_1,
		av.cliente
    )
SELECT * FROM Final

UNION ALL

SELECT
		cliente,
		'Total',
		SUM(Quantidade),
		SUM(Valor)
FROM
		Final
GROUP BY
		cliente
ORDER BY 
		cliente,
		Horario
"""

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#########################################################################################################################################
#########################################################################################################################################