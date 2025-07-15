import sys
import os
import datetime

def enviar_baseativarecebidosfortlev():

    #Obtém a data de hoje
    data_hoje = datetime.datetime.today().strftime("%Y-%m-%d")
    data_hoje_texto = datetime.datetime.today().strftime("%d-%m-%Y")

    #Obtém o caminho "pai" do script_email.py
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))

    #Constrói o caminho para a pasta Envio_emails
    caminho_envio_emails = os.path.join(diretorio_atual, "..", "..", "Envio_emails")

    print(f"Caminho construído para Envio_emails: {caminho_envio_emails}")

    #Adiciona o caminho ao sys.path
    sys.path.append(caminho_envio_emails)

    from funcao_enviar_email import enviar_email_automatico

    email_destinatario = ["rosimery@fortlev.com.br","kamila.vs@fortlev.com.br","tratativas.gestao@fortlev.com.br"]
    email_cc = ["luan.capistrano@somosglobal.com.br","mis@somosglobal.com.br"]
    caminho_credenciais = "/home/global/MIS/B2B_Global/Relatorios_Agendados/Envio_emails/credenciais_email"
    assunto_email = fr"Base ativa e recebimentos - Fortlev - {data_hoje_texto}"
    corpo_email = f"""
<html>
<body>
<p>Bom dia,</p>
</p>
<p>Segue o relatório de base ativa e de recebimentos, atualizado na data {data_hoje_texto}.</p>
</p>
<p>Em caso de dúvidas, contate o CS de sua carteira ou entre em contato pelo e-mail: csglobal@somosglobal.com.br.</p>
</p>
<p>Atenciosamente,</p>
</p>
<p>Time Global</p>
</html>
    """

    caminho_anexo = fr"/mnt/Rede/MIS/B2B - Global/35 - Fortlev/Base_ativa_recebidos_Fortlev_{data_hoje}.xlsx"

    enviar_email_automatico(email_destinatario, email_cc, assunto_email, corpo_email, caminho_credenciais, caminho_anexo)