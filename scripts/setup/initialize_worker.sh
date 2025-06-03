#!/bin/bash

# Script para inicializar un Worker
# Uso: ./initialize_worker.sh <nombreOvS> <interfaz1> [<interfaz2> ...]

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
    echo "Creando Open vSwitch $OVS_NAME..."
    ovs-vsctl add-br $OVS_NAME
    echo "OvS $OVS_NAME creado correctamente."
else
    echo "OvS $OVS_NAME ya existe."
fi

# Conectar las interfaces al OvS
for interface in "$@"; do
    if ip link show $interface > /dev/null 2>&1; then
        # Verificar si la interfaz ya está conectada al OvS
        if ! ovs-vsctl show | grep "Port \"$interface\"" > /dev/null; then
            echo "Conectando interfaz $interface al OvS $OVS_NAME..."
            ovs-vsctl add-port $OVS_NAME $interface
            echo "Interfaz $interface conectada correctamente."
        else
            echo "Interfaz $interface ya está conectada al OvS."
        fi
    else
        echo "Error: La interfaz $interface no existe."
    fi
done

echo "Inicialización del Worker completada!"
