import schedule
import time
import pandas as pd
import os
from datetime import datetime
from querys_grandes import buscar_esta_semana_grandes, buscar_semana_passada_grandes,buscar_previsao_grandes_inicio,buscar_previsao_grandes_hoje


base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir,"..","data")

caminho_spg = os.path.join(data_dir,"semana_passada_grandes.csv")
caminho_pig = os.path.join(data_dir,"previsao_inicial_grandes.csv")
caminho_esg = os.path.join(data_dir,"esta_semana_grandes.csv")
caminho_phg = os.path.join(data_dir,"previsao_hoje_grandes.csv")


def salvar_semana_passada():
    try:
        # Consulta os dados da semana passada
        df_semana_passada_grandes = buscar_semana_passada_grandes()
        df_previsao_inicial_grandes = buscar_previsao_grandes_inicio()

        # Salva os dados em um arquivo CSV
        df_semana_passada_grandes.to_csv(caminho_spg, index=False)
        print(f"Dados da semana passada salvos com sucesso em {caminho_spg}.")
        df_previsao_inicial_grandes.to_csv(caminho_pig, index=False)
        print(f"Dados da previsão inicial salvos com sucesso em {caminho_pig}.")
    except Exception as e:
        print(f"Erro ao salvar os dados da semana passada: {e}")

def salvar_esta_semana():
    try:
        # Verificar se o horário atual está entre 08h e 19h
        now = datetime.now()
        if now.hour >= 7 and now.hour <= 19:
            # Consulta os dados da semana atual
            df_esta_semana_grandes = buscar_esta_semana_grandes()
            df_previsao_hoje_grandes = buscar_previsao_grandes_hoje()

            # Salva os dados em um arquivo CSV
            df_esta_semana_grandes.to_csv(caminho_esg, index=False)
            print(f"Dados da semana atual salvos com sucesso em {caminho_esg}.")
            df_previsao_hoje_grandes.to_csv(caminho_phg, index=False)
            print(f"Dados da previsão hoje salvos com sucesso em {caminho_phg}.")


            # Atualizar o horário da última atualização
            with open("ultima_atualizacao_grandes.txt", "w") as f:
                f.write(now.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            print("Fora do horário de execução (08h às 19h).")
    except Exception as e:
        print(f"Erro ao salvar os dados da semana atual: {e}")

# Agendar o processamento às 08h para semana_passada
schedule.every().day.at("07:50").do(salvar_semana_passada)

# Agendar o processamento a cada 5 minutos para esta_semana
schedule.every(4).minutes.do(salvar_esta_semana)

# Loop para manter o agendamento ativo
if __name__ == "__main__":
    print("Agendamento iniciado. Aguardando execução...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica as tarefas pendentes a cada 60 segundos (1 minuto)