import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

def enviar_email_automatico(destinatario, cc, assunto, corpo_email, caminho_credenciais, caminho_anexo=None):
    """
    Envia um e-mail automático usando as credenciais fornecidas em um arquivo.

    Argumentos da função:
        destinatario (str): O endereço de e-mail do destinatário.
        assunto (str): O assunto do e-mail.
        corpo_email (str): O corpo do e-mail.
        caminho_credenciais (str): O caminho para o arquivo contendo as credenciais (e-mail e senha do app).
        caminho_anexo (str, optional): O caminho completo para o arquivo que será anexado. Padrão para None (sem anexo).
        cc (list or str, optional): Um e-mail ou lista de e-mails para colocar em cópia.
    """
    try:
        with open(caminho_credenciais, 'r') as f:
            remetente = f.readline().strip()
            senha_app = f.readline().strip()
    except FileNotFoundError:
        print(f"Erro: Arquivo de credenciais '{caminho_credenciais}' não encontrado.")
        print("Certifique-se de que o arquivo existe e contém seu e-mail e senha do app.")
        return
    except Exception as e:
        print(f"Erro ao ler as credenciais: {e}")
        return

    # Configurações do servidor SMTP para Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587 # Porta padrão para STARTTLS

    nome_exibicao = "Relatórios MIS"

    msg = MIMEMultipart()
    msg['From'] = f"{nome_exibicao}"

    if isinstance(destinatario,str):
        destinatario = [destinatario]
    if isinstance(cc, str):
        cc = [cc]

    msg['To'] = ", ".join(destinatario)

    if cc:
        msg['Cc'] = ", ".join(cc)

    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_email, 'html'))

    # --- Lógica para anexar arquivo ---
    if caminho_anexo:
        try:
            with open(caminho_anexo, 'rb') as anexo: # 'rb' para ler em modo binário
                part = MIMEBase('application', 'octet-stream') # Tipo genérico de byte stream
                part.set_payload(anexo.read())
            encoders.encode_base64(part) # Codifica o anexo em base64

            # Adiciona o cabeçalho Content-Disposition para definir o nome do arquivo
            import os
            nome_arquivo = os.path.basename(caminho_anexo)
            part.add_header('Content-Disposition', f'attachment; filename= {nome_arquivo}')

            msg.attach(part) # Anexa a parte do arquivo à mensagem
            print(f"Anexo '{nome_arquivo}' adicionado.")
        except FileNotFoundError:
            print(f"Aviso: Arquivo de anexo '{caminho_anexo}' não encontrado. O e-mail será enviado sem anexo.")
        except Exception as e:
            print(f"Erro ao anexar arquivo '{caminho_anexo}': {e}")
    # --- Fim da lógica para anexar arquivo ---

    todos_destinatarios = destinatario + (cc if cc else [])

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Habilita a segurança TLS
            server.login(remetente, senha_app)
            server.send_message(msg, remetente, todos_destinatarios)
        print(f"E-mail enviado com sucesso para {', '.join(destinatario)} (CC: {', '.join(cc) if cc else 'Nenhum'})\n")
    except smtplib.SMTPAuthenticationError:
        print("Erro de autenticação: Verifique se o e-mail e a senha do app estão corretos.\n")
        print("Lembre-se que é necessário usar uma 'senha de app' gerada nas configurações da sua conta Google.\n")
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o e-mail: {e}")

