#!/bin/bash

echo "Iniciando servidor netcat para Cloud Orchestrator en puerto 3080..."

# Verificar que el directorio exista
if [ ! -d "/opt/cloud-orchestrator" ]; then
    echo "Error: El directorio de la aplicación no existe!"
    exit 1
fi

# Cambiar al directorio de la aplicación
cd /opt/cloud-orchestrator

# Iniciar el servidor Python que gestiona las conexiones netcat
python3 cli_server.py
