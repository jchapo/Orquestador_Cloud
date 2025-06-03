#!/bin/bash

# Script para eliminar una topología
# Uso: ./destroy_topology.sh <archivo_json>

# Verificar que se proporcione un archivo
if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_json>"
    echo "Ejemplo: $0 mi_topologia.json"
    exit 1
fi

JSON_FILE=$1

# Verificar que el archivo exista
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: El archivo $JSON_FILE no existe."
    exit 1
fi

echo "Eliminando topología definida en $JSON_FILE"

# Verificar que jq está instalado
if ! command -v jq &> /dev/null; then
    echo "Error: Se requiere jq para procesar el archivo JSON."
    echo "Por favor, instale jq con 'sudo apt-get install jq'"
    exit 1
fi

# Comprobar que jq está instalado
JQ_PATH=$(which jq)
if [ -z "$JQ_PATH" ]; then
    echo "Error: No se encontró jq. Por favor instale jq con 'sudo apt-get install jq'"
    exit 1
fi

# Obtener información del archivo JSON
TOPOLOGY_NAME=$(jq -r '.name' "$JSON_FILE" 2>/dev/null)
if [ -z "$TOPOLOGY_NAME" ] || [ "$TOPOLOGY_NAME" == "null" ]; then
    echo "Error: No se pudo leer el nombre de la topología del archivo."
    exit 1
fi

HEAD_NODE=$(jq -r '.nodes.head_node' "$JSON_FILE" 2>/dev/null)
OFS_NODE=$(jq -r '.nodes.ofs_node' "$JSON_FILE" 2>/dev/null)
WORKERS=$(jq -r '.nodes.workers | join(" ")' "$JSON_FILE" 2>/dev/null)

echo "Nombre de la topología: $TOPOLOGY_NAME"
echo "Nodo principal: $HEAD_NODE"
echo "Nodo OFS: $OFS_NODE"
echo "Workers: $WORKERS"

# Obtener listado de VMs
VM_COUNT=$(jq '.vms | length' "$JSON_FILE" 2>/dev/null)
if [[ ! "$VM_COUNT" =~ ^[0-9]+$ ]]; then
    echo "Error: No se pudo determinar el número de VMs."
    VM_COUNT=0
fi

echo "Número de VMs: $VM_COUNT"

# Eliminar cada VM
echo "Eliminando VMs..."
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE" 2>/dev/null)
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE" 2>/dev/null)
    
    if [ -z "$VM_NAME" ] || [ "$VM_NAME" == "null" ] || [ -z "$WORKER_IDX" ] || [ "$WORKER_IDX" == "null" ]; then
        echo "Error: No se pudo obtener información para la VM #$i"
        continue
    fi
    
    # Obtener la dirección IP del worker
    WORKER_ADDRESS=$(echo $WORKERS | cut -d' ' -f$WORKER_IDX 2>/dev/null)
    if [ -z "$WORKER_ADDRESS" ] || [ "$WORKER_ADDRESS" == "null" ]; then
        echo "Error: No se pudo determinar la dirección del worker para la VM $VM_NAME"
        continue
    fi
    
    echo "Eliminando VM $VM_NAME del worker $WORKER_ADDRESS..."
    
    # Verificar si la VM existe
    SSH_RESULT=$(ssh ubuntu@$WORKER_ADDRESS "sudo virsh dominfo $VM_NAME" 2>&1)
    if [[ $SSH_RESULT == *"No se ha podido abrir la máquina virtual"* || $SSH_RESULT == *"failed to get domain"* ]]; then
        echo "La VM $VM_NAME no existe en $WORKER_ADDRESS, omitiendo..."
        continue
    fi
    
    # Detener y eliminar la VM
    ssh ubuntu@$WORKER_ADDRESS "sudo virsh destroy $VM_NAME 2>/dev/null || true"
    ssh ubuntu@$WORKER_ADDRESS "sudo virsh undefine $VM_NAME --remove-all-storage 2>/dev/null || true"
    
    echo "VM $VM_NAME eliminada."
done

# Eliminar las redes creadas para la topología
echo "Eliminando redes..."

# Obtener todas las VLANs únicas utilizadas
VLAN_IDS=$(jq -r '.connections[].vlan_id' "$JSON_FILE" 2>/dev/null | sort -n | uniq)
for VLAN_ID in $VLAN_IDS; do
    if [ -n "$VLAN_ID" ] && [ "$VLAN_ID" != "null" ]; then
        echo "Eliminando red para VLAN $VLAN_ID..."
        sudo ovs-vsctl del-br br-vlan$VLAN_ID 2>/dev/null || true
        sudo ip link delete dev vlan$VLAN_ID 2>/dev/null || true
        echo "Red VLAN $VLAN_ID eliminada."
    fi
done

# Eliminar red de Internet (VLAN 10) si existe
echo "Eliminando red de Internet (VLAN 10)..."
sudo ovs-vsctl del-br br-vlan10 2>/dev/null || true
sudo ip link delete dev vlan10 2>/dev/null || true

# Limpiar reglas de flujo en el switch OFS
echo "Limpiando reglas de flujo en OFS..."
if [ -n "$OFS_NODE" ] && [ "$OFS_NODE" != "null" ]; then
    ssh ubuntu@$OFS_NODE "sudo ovs-ofctl del-flows br-int" 2>/dev/null || true
    echo "Reglas de flujo eliminadas."
fi

# Eliminar configuración de red en HeadNode
echo "Limpiando configuración de red en HeadNode..."
sudo ovs-vsctl del-br br-int 2>/dev/null || true

echo "Topología $TOPOLOGY_NAME eliminada con éxito."
exit 0