#!/bin/bash

# Script para añadir interfaces VLAN a una VM existente
# Uso: ./add_interface.sh <vm_name> <bridge> <vlan_id> [mac_address]

# Verificar argumentos
if [ $# -lt 3 ]; then
    echo "Uso: $0 <vm_name> <bridge> <vlan_id> [mac_address]"
    echo "Ejemplo: $0 vm1 br-int 100 52:54:00:01:01:01"
    exit 1
fi

VM_NAME=$1
BRIDGE=$2
VLAN_ID=$3
MAC_ADDRESS=$4

# Si no se proporciona una MAC, generar una
if [ -z "$MAC_ADDRESS" ]; then
    # Generar MAC basada en el nombre de la VM y VLAN
    PREFIX="52:54:00"
    SUFFIX=$(echo -n "${VM_NAME}${VLAN_ID}" | md5sum | cut -c1-6 | sed 's/\(..\)/\1:/g' | sed 's/:$//')
    MAC_ADDRESS="${PREFIX}:${SUFFIX}"
fi

# Verificar que la VM existe
if ! virsh dominfo "$VM_NAME" &>/dev/null; then
    echo "Error: La VM '$VM_NAME' no existe."
    exit 1
fi

# Crear un nombre único para la interfaz TAP
TAP_NAME="tap-${VM_NAME}-vlan${VLAN_ID}"

# Crear la interfaz TAP
echo "Creando interfaz TAP: $TAP_NAME..."
ip tuntap add mode tap name "$TAP_NAME"
ip link set dev "$TAP_NAME" up

# Conectar la interfaz TAP al Open vSwitch con la VLAN asignada
echo "Conectando $TAP_NAME al OvS $BRIDGE con VLAN $VLAN_ID..."
ovs-vsctl add-port "$BRIDGE" "$TAP_NAME" tag="$VLAN_ID"

# Crear un XML temporal para la nueva interfaz
INTERFACE_XML=$(mktemp)

cat > $INTERFACE_XML << EOF
<interface type='bridge'>
    <mac address='$MAC_ADDRESS'/>
    <source bridge='$BRIDGE'/>
    <virtualport type='openvswitch'/>
    <target dev='$TAP_NAME'/>
    <model type='virtio'/>
    <vlan>
        <tag id='$VLAN_ID'/>
    </vlan>
</interface>
EOF

# Verificar si la interfaz ya existe (buscando la MAC)
if virsh dumpxml "$VM_NAME" | grep -q "$MAC_ADDRESS"; then
    echo "Advertencia: Ya existe una interfaz con MAC $MAC_ADDRESS en la VM $VM_NAME."
    rm $INTERFACE_XML
    exit 0
fi

# Verificar si la VM está en ejecución
VM_STATE=$(virsh domstate "$VM_NAME" 2>/dev/null)
if [ "$VM_STATE" = "running" ]; then
    # Si la VM está en ejecución, añadir la interfaz en caliente y de forma persistente
    virsh attach-device "$VM_NAME" $INTERFACE_XML --persistent --live
    echo "Interfaz añadida con éxito a $VM_NAME para VLAN $VLAN_ID con MAC $MAC_ADDRESS (en caliente)"
else
    # Si la VM no está en ejecución, añadir la interfaz solo de forma persistente
    virsh attach-device "$VM_NAME" $INTERFACE_XML --persistent
    echo "Interfaz añadida de forma persistente a $VM_NAME para VLAN $VLAN_ID con MAC $MAC_ADDRESS"
    echo "NOTA: Los cambios surtirán efecto cuando la VM se inicie."
fi

# Limpiar archivos temporales
rm $INTERFACE_XML

echo "Interfaz para VLAN $VLAN_ID añadida a $VM_NAME con MAC $MAC_ADDRESS y TAP $TAP_NAME"