#!/bin/bash

# Caminho do script Python
SCRIPT="Home"

# Iniciar com nohup e guardar o PID
echo "Iniciando $SCRIPT com poetry + nohup..."
nohup poetry run streamlit run "$SCRIPT.py" > $SCRIPT.log 2>&1 &
echo $! > $SCRIPT.pid
echo "Processo iniciado com PID $(cat $SCRIPT.pid)"

