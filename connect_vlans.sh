#!/bin/bash

# Script para permitir la comunicación entre dos VLANs
# Versión mejorada con manejo de errores y redes predefinidas

if [ $# -ne 2 ]; then
    echo "Uso: $0 <vlan_id_1> <vlan_id_2>"
    echo "Ejemplo: $0 100 200"
    exit 1
fi

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

VLAN_ID_1=$1
VLAN_ID_2=$2

# Configuración de redes predefinidas para cada VLAN
declare -A PREDEFINED_NETWORKS=(
    [100]="192.168.10.0/24"
    [200]="192.168.20.0/24"
    [300]="192.168.30.0/24"
)

# Verificar que las interfaces VLAN existan
if ! sudo ip link show vlan$VLAN_ID_1 &> /dev/null; then
    echo "Error: La interfaz vlan$VLAN_ID_1 no existe."
    exit 1
fi

if ! sudo ip link show vlan$VLAN_ID_2 &> /dev/null; then
    echo "Error: La interfaz vlan$VLAN_ID_2 no existe."
    exit 1
fi

# Función para obtener la red de una VLAN
get_network() {
    local vlan_id=$1
    local network
    
    # Primero intentar obtener la red de la interfaz
    network=$(sudo ip -o -4 addr show vlan$vlan_id 2>/dev/null | awk '{print $4}')
    
    # Si no se encuentra, usar la red predefinida
    if [ -z "$network" ]; then
        network=${PREDEFINED_NETWORKS[$vlan_id]}
        if [ -z "$network" ]; then
            echo "Error: No se pudo determinar la red para VLAN $vlan_id y no hay configuración predefinida"
            return 1
        fi
        echo "Advertencia: Usando red predefinida para VLAN $vlan_id: $network"
    fi
    
    echo "$network"
    return 0
}

# Obtener las redes de las VLANs
NETWORK_1=$(get_network $VLAN_ID_1) || exit 1
NETWORK_2=$(get_network $VLAN_ID_2) || exit 1

# Verificar que ipcalc esté instalado para calcular la red correctamente
if ! command -v ipcalc &> /dev/null; then
    echo "Advertencia: ipcalc no está instalado, usando las redes directamente"
    NETWORK_1_FULL=$NETWORK_1
    NETWORK_2_FULL=$NETWORK_2
else
    NETWORK_1_FULL=$(ipcalc -n $NETWORK_1 | grep Network | awk '{print $2}')
    NETWORK_2_FULL=$(ipcalc -n $NETWORK_2 | grep Network | awk '{print $2}')
fi

echo "Habilitando comunicación entre VLAN $VLAN_ID_1 ($NETWORK_1_FULL) y VLAN $VLAN_ID_2 ($NETWORK_2_FULL)..."

# Añadir reglas para permitir el tráfico entre las VLANs en ambas direcciones
if ! sudo iptables -A FORWARD -i vlan$VLAN_ID_1 -o vlan$VLAN_ID_2 -j ACCEPT; then
    echo "Error: Falló al agregar regla de iptables para tráfico de $VLAN_ID_1 a $VLAN_ID_2"
    exit 1
fi

if ! sudo iptables -A FORWARD -i vlan$VLAN_ID_2 -o vlan$VLAN_ID_1 -j ACCEPT; then
    echo "Error: Falló al agregar regla de iptables para tráfico de $VLAN_ID_2 a $VLAN_ID_1"
    exit 1
fi

echo "Reglas de iptables añadidas correctamente."
echo "Las VLANs $VLAN_ID_1 y $VLAN_ID_2 ahora pueden comunicarse entre sí."

exit 0
