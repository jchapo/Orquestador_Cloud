#!/bin/bash

# Script para inicializar el HeadNode
# Uso: ./initialize_headnode.sh <nombreOvS> <interfaz1> [<interfaz2> ...]

if [ $# -lt 2 ]; then
    echo "Uso: $0 <nombreOvS> <interfaz1> [<interfaz2> ...]"
    exit 1
fi

OVS_NAME=$1
shift

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

# Crear OvS si no existe
if ! ovs-vsctl show | grep "Bridge \"$OVS_NAME\"" > /dev/null; then
    echo -ne "Creando Open vSwitch $OVS_NAME...\r"
    ovs-vsctl add-br $OVS_NAME
    echo "	✅ OvS $OVS_NAME creado correctamente."
else
    echo "	✅ OvS $OVS_NAME ya existe."
fi

# Conectar las interfaces al OvS
for interface in "$@"; do
    if ip link show $interface > /dev/null 2>&1; then
        # Verificar si la interfaz ya está conectada al OvS
        if ! ovs-vsctl show | grep "Port \"$interface\"" > /dev/null; then
            echo -ne  "	Conectando interfaz $interface al OvS $OVS_NAME...\r"
            ovs-vsctl add-port $OVS_NAME $interface
            echo "	✅ Interfaz $interface conectada correctamente."
        else
            echo "	✅ Interfaz $interface ya está conectada al OvS."
        fi
    else
        echo "      ❌ Error: La interfaz $interface no existe."
    fi
done

# Activar IPv4 Forwarding
echo -ne "	Activando IPv4 Forwarding...\r"
echo 1 > /proc/sys/net/ipv4/ip_forward
# Hacer que el cambio sea permanente
if ! grep -q "net.ipv4.ip_forward = 1" /etc/sysctl.conf; then
    echo -ne "net.ipv4.ip_forward = 1\r" >> /etc/sysctl.conf
    sysctl -p
fi
echo "      ✅ IPv4 Forwarding activado."

# Cambiar default action del chain FORWARD de la tabla FILTER en iptables de ACCEPT a DROP
echo -ne  "      Cambiando política por defecto del chain FORWARD a DROP...\r"
iptables -P FORWARD DROP
echo "      ✅ Política FORWARD cambiada a DROP."

echo "      ⭐ Inicialización del HeadNode completada!"
