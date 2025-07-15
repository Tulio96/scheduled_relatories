from enviar_email import enviar_email_automatico
import datetime

data_hoje = datetime.datetime.today().strftime("%Y-%m-%d")

email_destinatario = "tulio.oliveira@somosglobal.com.br"
email_cc = ["daniel.gelich@somosglobal.com.br","henrique.oliveira@somosglobal.com.br"]
caminho_credenciais = "credenciais_email"
assunto_email = "Teste de Envio de Email - Com Cópias"
corpo_email = """
Olá,

Este é um teste de envio de email automático, com anexo e CC.

Atenciosamente,
"""
caminho_anexo = fr"/mnt/Rede/MIS/B2B - Global/35 - Fortlev/Base_ativa_recebidos_{data_hoje}.xlsx"


enviar_email_automatico(email_destinatario, email_cc, assunto_email, corpo_email, caminho_credenciais, caminho_anexo)