#!/bin/bash

# Caminho do script Python
SCRIPT="scheduler_unidades"

# Iniciar com nohup e guardar o PID
echo "Iniciando $SCRIPT com poetry + nohup..."
nohup poetry run python "querys/$SCRIPT.py" > $SCRIPT.log 2>&1 &
echo $! > $SCRIPT.pid
echo "Processo iniciado com PID $(cat $SCRIPT.pid)"

