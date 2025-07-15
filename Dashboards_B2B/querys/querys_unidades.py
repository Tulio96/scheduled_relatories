import pandas as pd
from sqlalchemy import text
from database import get_engine
import streamlit as st

cod_responsavel_sede = ['6506149','7982952','4891651','7856237','2523178','7161829','6012690']
cod_responsavel_araquari = ['7123245','7803018','6012687','7945415']

sede_str = ','.join(f"'{cod}'" for cod in cod_responsavel_sede)
araquari_str = ','.join(f"'{cod}'" for cod in cod_responsavel_araquari)

todos_responsaveis = sede_str + ',' + araquari_str

def buscar_semana_passada():
    engine = get_engine()

    query = f""" 
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
			super.NomCliente AS super,
            --Seleciona a unidade de acordo com o supervisor
            CASE
            		WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
					WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
            END AS [unidade]
	FROM
			ProcessoProposta pp
			LEFT JOIN Processo pro					ON pro.CodProcesso = pp.CodProcesso
			LEFT JOIN Usuario usu					ON usu.Usuario = pp.UsuProposta
			LEFT JOIN Cliente cob					ON usu.CodColaborador = cob.CodCliente
			LEFT JOIN EquipeTrabalho eq				ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
			LEFT JOIN Cliente super					ON super.CodCliente = eq.CodResponsavel
			LEFT JOIN OrigemAcordo oa				ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
	WHERE	1=1
			AND DtaProposta >= @dt_pastweek_start
			AND DtaProposta <= @dt_pastweek_end
			--FILTRO TODOS SUPERVISORES
	        AND eq.CodResponsavel IN ({todos_responsaveis})
			AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
            AND TipPropostaAcordo = '1'
	),
Acordos_Valores AS
	(
	SELECT
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
            pp.unidade,
			pp.super,
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
			pp.super,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.unidade
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
Final_unidades AS
    (
	SELECT
		av.unidade,
		FORMAT(DiasW_1.Dia_W_1, 'HH:00')		AS [Horario],
		SUM(
				CASE 
						WHEN av.CodProcesso IS NULL THEN 0
						ELSE 1
				end
			)																	AS [Quantidade],
		COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 				        AS [Valor]

	FROM	DiasW_1
		LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_1.Dia_W_1 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_1.Dia_W_1)
	GROUP BY
		DiasW_1.Dia_W_1,
		av.unidade
    ),
Final_supers AS
    (
	SELECT
		av.super,
		FORMAT(DiasW_1.Dia_W_1, 'HH:00')		AS [Horario],
		SUM(
				CASE 
						WHEN av.CodProcesso IS NULL THEN 0
						ELSE 1
				end
			)																	AS [Quantidade],
		COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 				        AS [Valor]

	FROM	DiasW_1
		LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_1.Dia_W_1 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_1.Dia_W_1)
	GROUP BY
		DiasW_1.Dia_W_1,
		av.super
    )
SELECT * FROM Final_unidades

UNION ALL

SELECT 
		' Sede + Araquari',
        Horario,
        SUM(Quantidade),
        SUM(Valor)
FROM 
		Final_unidades
WHERE 		1=1
		AND Horario >= '08:00'
		AND Horario <= '18:59:59:99'
GROUP BY
		Horario

UNION ALL

SELECT * FROM Final_supers
"""

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#####################################################################################################################################

def buscar_esta_semana():
    engine = get_engine()

    query = f""" 
DECLARE @dt_thisweek_start  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),8,0,0,0);
DECLARE @dt_thisweek_end    AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),18,59,59,99);
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
WITH Acordos_Periodo AS
	(
	SELECT
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.UsuProposta,
			super.NomCliente AS super,
            --Seleciona a unidade de acordo com o supervisor
            CASE
            		WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
					WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
            END AS [unidade]
	FROM
			ProcessoProposta pp
			LEFT JOIN Processo pro					ON pro.CodProcesso = pp.CodProcesso
			LEFT JOIN Usuario usu					ON usu.Usuario = pp.UsuProposta
			LEFT JOIN Cliente cob					ON usu.CodColaborador = cob.CodCliente
			LEFT JOIN EquipeTrabalho eq				ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
			LEFT JOIN Cliente super					ON super.CodCliente = eq.CodResponsavel
			LEFT JOIN OrigemAcordo oa				ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
	WHERE	1=1
			AND DtaProposta >= @dt_thisweek_start
			AND DtaProposta <= @dt_thisweek_end
			--FILTRO TODOS SUPERVISORES
	        AND eq.CodResponsavel IN ({todos_responsaveis})
			AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
            AND SelPropostaAcordo = '1'
	),
Acordos_Valores AS
	(
	SELECT
			pp.CodProcesso,
			pp.CodProcessoProposta,
			pp.DtaProposta,
            pp.unidade,
			pp.super,
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
			pp.super,
			pp.CodProcessoProposta,
			pp.DtaProposta,
			pp.unidade
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
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
Final_unidades AS
    (
	SELECT
		av.unidade,
		FORMAT(DiasW_0.Dia_W_0, 'HH:00')		AS [Horario],
		SUM(
				CASE 
						WHEN av.CodProcesso IS NULL THEN 0
						ELSE 1
				end
			)																	AS [Quantidade],
		COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 				        AS [Valor]

	FROM	DiasW_0
		LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_0.Dia_W_0 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_0.Dia_W_0)
	GROUP BY
		DiasW_0.Dia_W_0,
		av.unidade
    ),
Final_supers AS
    (
	SELECT
		av.super,
		FORMAT(DiasW_0.Dia_W_0, 'HH:00')		AS [Horario],
		SUM(
				CASE 
						WHEN av.CodProcesso IS NULL THEN 0
						ELSE 1
				end
			)																	AS [Quantidade],
		COALESCE(SUM(CAST(av.Valor AS DECIMAL(18,2))),0) 				        AS [Valor]

	FROM	DiasW_0
		LEFT JOIN Acordos_Valores av ON CAST(av.DtaProposta AS DATE) = CAST(DiasW_0.Dia_W_0 AS DATE) AND DATEPART(HOUR,av.DtaProposta) = DATEPART(HOUR,DiasW_0.Dia_W_0)
	GROUP BY
		DiasW_0.Dia_W_0,
		av.super
    )
SELECT * FROM Final_unidades

UNION ALL

SELECT 
		' Sede + Araquari',
        Horario,
        SUM(Quantidade),
        SUM(Valor)
FROM 
		Final_unidades
WHERE 		1=1
		AND Horario >= '08:00'
		AND Horario <= '18:59:59:99'
GROUP BY
		Horario

UNION ALL

SELECT * FROM Final_supers

OPTION (RECOMPILE);

"""

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

######################################################################################################################################

def buscar_previsao_inicio():
    engine = get_engine()

    query = f"""
DECLARE @todayh  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),0,0,0,0);
DECLARE @today AS DATE = GETDATE();

WITH Previsao AS
	(
    SELECT
		super.Nomcliente AS super,
        CASE 
            	WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
				WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
        END AS [unidade],
        SUM(pppb.ValCapital + pppb.ValProtesto + pppb.ValJuros + pppb.ValMulta + pppb.ValHonorarioDevedor) AS [Previsao_inicio]
FROM 
		ProcessoProposta pp
		LEFT JOIN ProcessoPropostaParcelaBaixa pppb 	ON pp.CodProcesso = pppb.CodProcesso AND pp.CodProcessoProposta = pppb.CodProcessoProposta
		LEFT JOIN ProcessoPropostaParcela ppp 			ON ppp.CodProcesso = pppb.CodProcesso AND ppp.CodProcessoProposta = pppb.CodProcessoProposta AND ppp.CodParcela = pppb.CodParcelaProposta
        LEFT JOIN Processo pro							ON pp.CodProcesso = pro.CodProcesso
		LEFT JOIN Usuario usu							ON usu.Usuario = pp.UsuProposta
		LEFT JOIN Cliente cob							ON usu.CodColaborador = cob.CodCliente
		LEFT JOIN EquipeTrabalho eq						ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
		LEFT JOIN Cliente super							ON super.CodCliente = eq.CodResponsavel
		LEFT JOIN OrigemAcordo oa						ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
WHERE
		CAST(ppp.DtaVencimento AS DATE) = @today
        AND CAST (pp.Dtaproposta AS DATE) < @today
		AND pp.SelPropostaAcordo = '1'
	    AND eq.CodResponsavel IN ({todos_responsaveis})
		AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
        AND pro.CodProcessoSituacao IN ('5','21','39','48','100','102','149')
GROUP BY
		super.CodCliente,
        super.NomCliente
	)
    
SELECT unidade, SUM(Previsao_inicio) AS Previsao_inicio
FROM Previsao
GROUP BY unidade

UNION ALL

SELECT super, SUM(Previsao_inicio)
FROM Previsao
GROUP BY super

UNION ALL

SELECT
		' Sede + Araquari',
       	SUM(Previsao_inicio)
FROM Previsao

    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#######################################################################################################################################

def buscar_previsao_hoje():
    engine = get_engine()

    query = f"""
DECLARE @todayh  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),0,0,0,0);
DECLARE @today AS DATE = GETDATE();

WITH Previsao AS
	(
    SELECT
		super.Nomcliente AS super,
        CASE 
            	WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
				WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
        END AS [unidade],
        SUM(pppb.ValCapital + pppb.ValProtesto + pppb.ValJuros + pppb.ValMulta + pppb.ValHonorarioDevedor) AS [Previsao_hoje]
FROM 
		ProcessoProposta pp
		LEFT JOIN ProcessoPropostaParcelaBaixa pppb 	ON pp.CodProcesso = pppb.CodProcesso AND pp.CodProcessoProposta = pppb.CodProcessoProposta
		LEFT JOIN ProcessoPropostaParcela ppp 			ON ppp.CodProcesso = pppb.CodProcesso AND ppp.CodProcessoProposta = pppb.CodProcessoProposta AND ppp.CodParcela = pppb.CodParcelaProposta
        LEFT JOIN Processo pro							ON pp.CodProcesso = pro.CodProcesso
		LEFT JOIN Usuario usu							ON usu.Usuario = pp.UsuProposta
		LEFT JOIN Cliente cob							ON usu.CodColaborador = cob.CodCliente
		LEFT JOIN EquipeTrabalho eq						ON eq.CodEquipeTrabalho = cob.CodEquipeTrabalho
		LEFT JOIN Cliente super							ON super.CodCliente = eq.CodResponsavel
		LEFT JOIN OrigemAcordo oa						ON oa.CodOrigemAcordo = pp.CodOrigemAcordo
WHERE
		CAST(ppp.DtaVencimento AS DATE) = @today
		AND pp.SelPropostaAcordo = '1'
	    AND eq.CodResponsavel IN ({todos_responsaveis})
		AND oa.CodOrigemAcordo IN ('1','7','10','13','14','15','18','19','22','21')
        AND pro.CodProcessoSituacao IN ('5','21','39','48','100','102','149')
GROUP BY
		super.CodCliente,
        super.Nomcliente
	)
SELECT unidade, SUM(Previsao_hoje) AS Previsao_hoje
FROM Previsao
GROUP BY unidade

UNION ALL

SELECT super, SUM(Previsao_hoje)
FROM Previsao
GROUP BY super

UNION ALL

SELECT
		' Sede + Araquari',
       	SUM(Previsao_hoje)
FROM Previsao

--OPTION (RECOMPILE);
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#######################################################################################################################################

def buscar_acion_hoje():
    engine = get_engine()

    query = f"""
DECLARE @todayh  AS DATETIME = DATETIMEFROMPARTS(YEAR(GETDATE()),MONTH(GETDATE()),DAY(GETDATE()),0,0,0,0);
DECLARE @today AS DATE = GETDATE();

WITH Usuarios AS
    (
SELECT
	usu.Usuario,
        super.Nomcliente AS super,
        CASE 
        	WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
		WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
        END AS [unidade]
FROM
	Usuario usu
	LEFT JOIN Cliente usuc			ON usuc.CodCliente = usu.CodColaborador
	LEFT JOIN EquipeTrabalho et		ON et.CodEquipeTrabalho = usuc.CodEquipeTrabalho
        LEFT JOIN Cliente super 		ON super.CodCliente = et.CodResponsavel
WHERE
	1=1
	AND et.CodResponsavel IN ({todos_responsaveis})
    ),Super_uni AS(
SELECT
	super,
	unidade
FROM
	Usuarios
GROUP BY
	super,
	unidade
    )
,Acion_Hoje AS
    (
SELECT
	ph.UsuHistorico,
	ph.DtaHistorico
FROM
	ProcessoHistorico ph WITH (NOLOCK)
WHERE
	1=1
	AND CAST(ph.DtaHistorico AS DATE) = @today
    ),Acion_Exis AS(
SELECT
    usu.super AS super,
    usu.unidade AS unidade,
    COALESCE(FORMAT(ah.DtaHistorico, 'HH:00'),'00:00') AS Hora,
    COALESCE(COUNT(ah.DtaHistorico),0) AS Acionamento
FROM
    Usuarios usu
    INNER JOIN Acion_Hoje ah ON usu.Usuario = ah.UsuHistorico
GROUP BY
    FORMAT(ah.DtaHistorico, 'HH:00'),
    usu.unidade,
    usu.super
    )
SELECT
    su.super AS unidade,
    COALESCE(Hora,'08:00')     AS [Hora],
    SUM(COALESCE(Acionamento,0))    AS [Acionamento]
FROM
    Super_uni su
    LEFT JOIN Acion_Exis ah ON su.super = ah.super
GROUP BY
    COALESCE(Hora,'08:00'),
    su.super

UNION ALL

SELECT
    su.unidade,
    COALESCE(Hora,'08:00'),
    SUM(COALESCE(Acionamento,0))
FROM
    Super_uni su
    LEFT JOIN Acion_Exis ah ON su.super = ah.super
GROUP BY
    COALESCE(Hora,'08:00'),
    su.unidade

UNION ALL

SELECT
    ' Sede + Araquari',
    Hora,
    SUM(COALESCE(Acionamento,0))
FROM
    Acion_Exis ah
GROUP BY
    Hora

OPTION (RECOMPILE);
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df

#######################################################################################################################################

def buscar_acion_semana_passada():
    engine = get_engine()

    query = f"""
DECLARE @dt_pastweek AS DATETIME = 
CASE
		WHEN CONVERT(NVARCHAR,DATEADD(DAY,-7,GETDATE())) IN (SELECT DtaFeriado FROM Feriado)
		THEN DATEFROMPARTS(YEAR(DATEADD(DAY,-14,GETDATE())),MONTH(DATEADD(DAY,-14,GETDATE())),DAY(DATEADD(DAY,-14,GETDATE())))
		ELSE DATEFROMPARTS(YEAR(DATEADD(DAY,-7,GETDATE())),MONTH(DATEADD(DAY,-7,GETDATE())),DAY(DATEADD(DAY,-7,GETDATE())))
END;
WITH Usuarios AS
	(
SELECT 
		usu.Usuario,
        super.Nomcliente AS super,
        CASE 
            	WHEN super.CodCliente IN ({araquari_str}) THEN ' Araquari'
				WHEN super.CodCliente IN ({sede_str}) THEN ' Sede'
        END AS [unidade]
FROM
		Usuario usu
		LEFT JOIN Cliente usuc			ON usuc.CodCliente = usu.CodColaborador
		LEFT JOIN EquipeTrabalho et		ON et.CodEquipeTrabalho = usuc.CodEquipeTrabalho
        LEFT JOIN Cliente super 		ON super.CodCliente = et.CodResponsavel
WHERE
		1=1
		AND et.CodResponsavel IN ({todos_responsaveis})
	)
,Acion_Hoje AS
	(
SELECT
		ph.UsuHistorico,
		ph.DtaHistorico
FROM
		ProcessoHistorico ph
WHERE
		1=1
		AND CAST(ph.DtaHistorico AS DATE) = @dt_pastweek
	)
SELECT
		usu.super AS unidade,
		FORMAT(ah.DtaHistorico, 'HH:00') AS Hora,
		COUNT(ah.DtaHistorico) AS Acionamento
FROM
		Acion_Hoje ah
		INNER JOIN Usuarios usu ON usu.Usuario = ah.UsuHistorico
GROUP BY
		FORMAT(ah.DtaHistorico, 'HH:00'),
        usu.super

UNION ALL

SELECT
		usu.unidade,
		FORMAT(ah.DtaHistorico, 'HH:00'),
		COUNT(ah.DtaHistorico)
FROM
		Acion_Hoje ah
		INNER JOIN Usuarios usu ON usu.Usuario = ah.UsuHistorico
GROUP BY
		FORMAT(ah.DtaHistorico, 'HH:00'),
        usu.unidade
        
UNION ALL

SELECT
		' Sede + Araquari',
		FORMAT(ah.DtaHistorico, 'HH:00'),
		COUNT(ah.DtaHistorico)
FROM
		Acion_Hoje ah
		INNER JOIN Usuarios usu ON usu.Usuario = ah.UsuHistorico
GROUP BY
		FORMAT(ah.DtaHistorico, 'HH:00')

OPTION (RECOMPILE);
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df