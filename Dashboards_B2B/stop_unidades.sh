#!/bin/bash

SCRIPT="scheduler_unidades"

if [ -f $SCRIPT.pid ]; then
    PID=$(cat $SCRIPT.pid)
    echo "Parando processo com PID $PID..."
    kill $PID
    rm $SCRIPT.pid
    echo "Processo finalizado."
else
    echo "Arquivo $SCRIPT.pid não encontrado. Processo não iniciado via start.sh?"
fi

