import requests
import json
import datetime
import os
from dotenv import load_dotenv # Importa a função para carregar o .env

# --- Configuração de Carregamento do .env ---
# Chama load_dotenv() para carregar as variáveis de ambiente do arquivo .env.
# Por padrão, ele procura por um arquivo .env no diretório atual ou nos diretórios pais.
load_dotenv()

# --- Configuração da URL do Webhook ---
# Tenta obter a URL da variável de ambiente.
# Se a variável de ambiente GOOGLE_CHAT_WEBHOOK_URL não estiver definida (nem no .env, nem no sistema),
# a variável GOOGLE_CHAT_WEBHOOK_URL neste script será uma string vazia ("").
# A função de envio verificará isso e imprimirá um erro.
GOOGLE_CHAT_WEBHOOK_URL = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL")

def enviar_mensagem_google_chat(mensagem: str, script_nome: str = None, status: str = None, caminho_arquivo: str = None):
    """
    Envia uma mensagem formatada para um webhook do Google Chat.

    Args:
        mensagem (str): A mensagem principal a ser enviada.
        script_nome (str, opcional): O nome do script que está enviando a mensagem.
        status (str, opcional): O status da execução ('SUCESSO', 'ERRO', 'FALHA', etc.).
        caminho_arquivo (str, opcional): O caminho de um arquivo relacionado à mensagem.
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário.
    """
    # Verifica se a URL do webhook foi carregada
    if not GOOGLE_CHAT_WEBHOOK_URL:
        print("Erro (notificador_chat): GOOGLE_CHAT_WEBHOOK_URL não configurada no ambiente ou no .env. Não é possível enviar mensagem para o Google Chat.")
        return False

    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }

    # Constrói a mensagem com base nos parâmetros fornecidos
    full_message_parts = []

    # Adiciona ícone e status
    if status:
        if status.upper() == 'SUCESSO':
            full_message_parts.append("✅ SUCESSO: ")
        elif status.upper() == 'ERRO' or status.upper() == 'FALHA':
            full_message_parts.append("❌ ERRO: ")
        elif status.upper() == 'AVISO':
            full_message_parts.append("⚠️ AVISO: ")
        else:
            full_message_parts.append(f"[{status.upper()}]: ")

    # Adiciona nome do script
    if script_nome:
        full_message_parts.append(f"Script '{script_nome}' - ") # Adicionado um traço para melhor legibilidade

    # Adiciona a mensagem principal
    full_message_parts.append(mensagem)

    # Adiciona caminho do arquivo, se fornecido
    if caminho_arquivo:
        full_message_parts.append(f" Caminho: `{caminho_arquivo}`") # Usando ` ` para formatar como código

    # Adiciona o timestamp da execução
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message_parts.append(f" (Executado em: {timestamp})")

    # Junta todas as partes da mensagem
    chat_message = {
        "text": "".join(full_message_parts)
    }

    try:
        response = requests.post(
            GOOGLE_CHAT_WEBHOOK_URL,
            headers=headers,
            data=json.dumps(chat_message)
        )
        response.raise_for_status() # Levanta um erro para códigos de status HTTP 4xx/5xx
        print(f"Mensagem de notificação enviada para o Google Chat.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Google Chat: {e}")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado na função enviar_mensagem_google_chat: {e}")
        return False

# --- Bloco de Teste ---
# Este código só será executado se você rodar notificador_chat.py diretamente.
# Não será executado quando o módulo for importado em outro script.
if __name__ == "__main__":
    print("--- Testando o módulo notificador_chat.py ---")

    # Para este teste funcionar, você DEVE ter um arquivo .env no mesmo diretório
    # com a linha: GOOGLE_CHAT_WEBHOOK_URL="SUA_URL_DO_WEBHOOK_DO_GOOGLE_CHAT_AQUI"
    # ou definir a variável de ambiente antes de executar este script.

    # Teste de sucesso
    enviar_mensagem_google_chat(
        "Teste de execução bem-sucedida.",
        script_nome="ScriptDeTeste1",
        status="Sucesso",
        caminho_arquivo="/home/user/logs/test_success.log"
    )

    # Teste de erro
    enviar_mensagem_google_chat(
        "Ocorreu um erro inesperado durante o processamento de dados.",
        script_nome="ScriptDeTeste2",
        status="Erro",
        caminho_arquivo="/data/raw/input_data.csv"
    )

    # Teste de aviso
    enviar_mensagem_google_chat(
        "Alguns registros foram pulados devido a inconsistências.",
        script_nome="ProcessamentoCSV",
        status="Aviso"
    )

    # Teste sem URL configurada (remova ou comente a linha do .env para testar este cenário)
    # print("\n--- Testando sem URL configurada ---")
    # os.environ.pop("GOOGLE_CHAT_WEBHOOK_URL", None) # Remove temporariamente a variável
    # GOOGLE_CHAT_WEBHOOK_URL = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL") # Força a re-leitura
    # enviar_mensagem_google_chat(
    #     "Esta mensagem não deve ser enviada, pois a URL não está configurada.",
    #     script_nome="ScriptSemWebhook",
    #     status="INFO"
    # )
    # os.environ["GOOGLE_CHAT_WEBHOOK_URL"] = "SUA_URL_DO_WEBHOOK_DO_GOOGLE_CHAT_AQUI" # Restaura para testes subsequentes