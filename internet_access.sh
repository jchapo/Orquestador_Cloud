#!/bin/bash

# Script para otorgar acceso a Internet a una VLAN
# Uso: ./internet_access.sh <vlan_id> <internet_interface>
# Ejemplo: ./internet_access.sh 100 eth0

if [ $# -ne 2 ]; then
    echo "Uso: $0 <vlan_id> <internet_interface>"
    echo "Ejemplo: $0 100 eth0"
    exit 1
fi

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

VLAN_ID=$1
INTERNET_IFACE=$2

# Verificar que la interfaz VLAN exista
if ! ip link show vlan$VLAN_ID &> /dev/null; then
    echo "Error: La interfaz vlan$VLAN_ID no existe."
    exit 1
fi

# Verificar que la interfaz de Internet exista
if ! ip link show $INTERNET_IFACE &> /dev/null; then
    echo "Error: La interfaz $INTERNET_IFACE no existe."
    exit 1
fi

# Obtener la red de la VLAN
#VLAN_NETWORK=$(ip addr show vlan$VLAN_ID | grep inet | awk '{print $2}')
#VLAN_NETWORK=$(ip addr show vlan$VLAN_ID | grep -w inet | awk '{print $2}' | cut -d'/' -f1)
# Reemplazar la verificación de red con:
#VLAN_NETWORK=$(ip -o -4 addr show vlan$VLAN_ID | awk '{print $4}' | cut -d'/' -f1)

#if [ -z "$VLAN_NETWORK" ]; then
    # Si no encuentra IP, usar la configurada en el script
    case $VLAN_ID in
        100) VLAN_NETWORK="192.168.10.0/24" ;;
        200) VLAN_NETWORK="192.168.20.0/24" ;;
        300) VLAN_NETWORK="192.168.30.0/24" ;;
        *) echo "Error: VLAN no configurada"; exit 1 ;;
    esac
    echo "Advertencia: Usando red predefinida para VLAN $VLAN_ID: $VLAN_NETWORK"
#fi
if [ -z "$VLAN_NETWORK" ]; then
    echo "Error: No se puede determinar la red de la VLAN."
    exit 1
fi

echo "Habilitando acceso a Internet para VLAN $VLAN_ID a través de $INTERNET_IFACE..."

# Activar NAT/PAT para la VLAN
iptables -t nat -A POSTROUTING -o $INTERNET_IFACE -s $VLAN_NETWORK -j MASQUERADE

# Permitir el tráfico de la VLAN hacia la interfaz de Internet
iptables -A FORWARD -i vlan$VLAN_ID -o $INTERNET_IFACE -j ACCEPT

# Permitir el tráfico establecido y relacionado desde Internet hacia la VLAN
iptables -A FORWARD -i $INTERNET_IFACE -o vlan$VLAN_ID -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "Reglas de iptables añadidas correctamente."
echo "La VLAN $VLAN_ID ahora tiene acceso a Internet a través de $INTERNET_IFACE."
