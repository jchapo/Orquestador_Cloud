#!/bin/bash

# Nombre de la imagen y contenedor
IMAGE_NAME="orchestrator-web"
CONTAINER_NAME="orchestrator-launcher"
PORT_MAPPING="3080:3080"

# Colores para salida legible
VERDE='\033[0;32m'
ROJO='\033[0;31m'
NORMAL='\033[0m'

echo -e "${VERDE}🛑 Deteniendo y eliminando contenedor anterior...${NORMAL}"
podman stop $CONTAINER_NAME 2>/dev/null
podman rm $CONTAINER_NAME 2>/dev/null

echo -e "${VERDE}🔄 Reconstruyendo imagen: $IMAGE_NAME...${NORMAL}"
podman build -t $IMAGE_NAME .

echo -e "${VERDE}🚀 Iniciando contenedor actualizado: $CONTAINER_NAME...${NORMAL}"
podman run -d --name $CONTAINER_NAME -p $PORT_MAPPING $IMAGE_NAME

echo -e "${VERDE}✅ Contenedor actualizado y corriendo en puerto 3080.${NORMAL}"
