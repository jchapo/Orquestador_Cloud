#!/bin/bash

# Script para otorgar acceso a Internet a una VLAN
# Uso: ./internet_access.sh <vlan_id> <internet_interface>
# Ejemplo: ./internet_access.sh 100 eth0

if [ $# -ne 2 ]; then
    echo "Uso: $0 <vlan_id> <internet_interface>"
    echo "Ejemplo: $0 100 eth0"
    exit 1
fi

VLAN_ID=$1
INTERNET_IFACE=$2
VLAN_NAME="vlan$VLAN_ID"

# Verificar que la interfaz VLAN exista
if ! ip link show $VLAN_NAME &> /dev/null; then
    echo "Error: VLAN no configurada"
    exit 1
fi

# Verificar que la interfaz de Internet exista
if ! ip link show $INTERNET_IFACE &> /dev/null; then
    echo "Error: La interfaz $INTERNET_IFACE no existe."
    exit 1
fi

# Obtener la dirección IP y máscara de red de la VLAN
VLAN_CIDR=$(ip -o -4 addr show $VLAN_NAME | awk '{print $4}')
if [ -z "$VLAN_CIDR" ]; then
    echo "Error: No se puede determinar la dirección IP de $VLAN_NAME"
    exit 1
fi

# Extraer la dirección IP sin la máscara
VLAN_IP=$(echo $VLAN_CIDR | cut -d'/' -f1)
if [ -z "$VLAN_IP" ]; then
    echo "Error: No se puede determinar la dirección IP de $VLAN_NAME"
    exit 1
fi

# Construir la red completa (cambiando el último octeto a 0)
VLAN_NETWORK="${VLAN_IP%.*}.0/24"

echo "Habilitando acceso a Internet para VLAN $VLAN_ID ($VLAN_NETWORK) a través de $INTERNET_IFACE..."

# Activar NAT/PAT para la VLAN
sudo iptables -t nat -A POSTROUTING -o $INTERNET_IFACE -s $VLAN_NETWORK -j MASQUERADE

# Permitir el tráfico de la VLAN hacia la interfaz de Internet
sudo iptables -A FORWARD -i $VLAN_NAME -o $INTERNET_IFACE -j ACCEPT

# Permitir el tráfico establecido y relacionado desde Internet hacia la VLAN
sudo iptables -A FORWARD -i $INTERNET_IFACE -o $VLAN_NAME -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "Reglas de iptables añadidas correctamente."
echo "La VLAN $VLAN_ID ahora tiene acceso a Internet a través de $INTERNET_IFACE."

exit 0