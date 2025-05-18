#!/bin/bash
#comandos:

#chmod +x app.sh

# Uso: ./app.sh

VERDE='\033[0;32m'
AZUL='\033[0;34m'
ROJO='\033[0;31m'
NORMAL='\033[0m'

clear
echo -e "${AZUL}====================================================${NORMAL}"
echo -e "${AZUL}       INICIANDO PUCP CLOUD ORCHESTRATOR           ${NORMAL}"
echo -e "${AZUL}====================================================${NORMAL}"
echo ""
echo -e "${VERDE}Conectando al servidor...${NORMAL}"
echo ""

nc 10.20.12.252 3080

echo ""
echo -e "${ROJO}La sesión ha finalizado.${NORMAL}"
echo -e "${VERDE}Para volver a conectarse, ejecute este script nuevamente.${NORMAL}"
echo ""

read -p "Presione Enter para salir..."
