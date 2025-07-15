import schedule
import threading
import time
import pandas as pd
import os

from datetime import datetime
from querys_unidades import buscar_semana_passada,buscar_esta_semana,buscar_previsao_inicio,buscar_previsao_hoje,buscar_acion_hoje,buscar_acion_semana_passada

def run_threaded(job_func):
    thread = threading.Thread(target=job_func)
    thread.start()


base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir,"..","data")

caminho_spu = os.path.join(data_dir,"semana_passada_unidades.csv")
caminho_piu = os.path.join(data_dir,"previsao_inicial_unidades.csv")
caminho_asu = os.path.join(data_dir,"acion_semana_passada_unidades.csv")
caminho_esu = os.path.join(data_dir,"esta_semana_unidades.csv")
caminho_phu = os.path.join(data_dir,"previsao_hoje_unidades.csv")
caminho_ahu = os.path.join(data_dir,"acion_esta_semana_unidades.csv")


def salvar_semana_passada():
    try:
        # Consulta os dados da semana passada
        df_semana_passada = buscar_semana_passada()
        df_previsao_inicial = buscar_previsao_inicio()

        # Salva os dados em um arquivo CSV
        df_semana_passada.to_csv(caminho_spu, index=False)
        print(f"Dados da semana passada salvos com sucesso em {caminho_spu}.")
        df_previsao_inicial.to_csv(caminho_piu, index=False)
        print(f"Dados da previsão inicial salvos com sucesso em {caminho_piu}.")

    except Exception as e:
        print(f"Erro ao salvar os dados da semana passada: {e}")

def salvar_esta_semana():
    try:
        # Verificar se o horário atual está entre 08h e 19h
        now = datetime.now()
        if now.hour >= 7 and now.hour <= 19:
            # Consulta os dados da semana atual
            df_esta_semana = buscar_esta_semana()
            df_previsao_hoje = buscar_previsao_hoje()

            # Salva os dados em um arquivo CSV
            df_esta_semana.to_csv(caminho_esu, index=False)
            print(f"Dados da semana atual salvos com sucesso em {caminho_esu}.")
            df_previsao_hoje.to_csv(caminho_phu, index=False)
            print(f"Dados da previsão hoje salvos com sucesso em {caminho_phu}.")

            # Atualizar o horário da última atualização
            with open("ultima_atualizacao_unidades.txt", "w") as f:
                f.write(now.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            print("Fora do horário de execução (07h às 19h).")
    except Exception as e:
        print(f"Erro ao salvar os dados da semana atual: {e}")

def salvar_acion_semana_passada():

    try:
        # Consulta os dados da semana atual
        df_acion_semana_passada = buscar_acion_semana_passada()

        # Salva os dados em um arquivo CSV
        df_acion_semana_passada.to_csv(caminho_asu, index=False)
        print(f"Dados de acionamento semana passada salvos com sucesso em {caminho_asu}.")
    except Exception as e:
        print(f"Erro ao salvar os dados de acionamento hoje: {e}")

def salvar_acion_esta_semana():

    try:
        # Verificar se o horário atual está entre 08h e 19h
        now = datetime.now()
        if now.hour >= 7 and now.hour <= 19:
            # Consulta os dados da semana atual
            df_acion_esta_semana = buscar_acion_hoje()

            # Salva os dados em um arquivo CSV
            df_acion_esta_semana.to_csv(caminho_ahu, index=False)
            print(f"Dados de acionamento hoje salvos com sucesso em {caminho_ahu}.")
        else:
            print("Fora do horário de execução (08h às 19h).")
    except Exception as e:
        print(f"Erro ao salvar os dados de acionamento hoje: {e}")

# Agendar o processamento às 08h para semana_passada
schedule.every().day.at("07:40").do(run_threaded, salvar_semana_passada)
schedule.every().day.at("07:45").do(run_threaded, salvar_acion_semana_passada)
schedule.every().day.at("07:30").do(run_threaded, salvar_acion_esta_semana)

# Agendar o processamento a cada 4 minutos para esta_semana
schedule.every(4).minutes.do(run_threaded,salvar_esta_semana)

# Agendar o processamento duas vezes a cada hora para acion_esta_semana
schedule.every().hour.at(":25").do(run_threaded, salvar_acion_esta_semana)
schedule.every().hour.at(":50").do(run_threaded, salvar_acion_esta_semana)


# Loop para manter o agendamento ativo
if __name__ == "__main__":
    print("Agendamento iniciado. Aguardando execução...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica as tarefas pendentes a cada 60 segundos (1 minuto)