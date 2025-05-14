#!/bin/bash

# Script para crear una VM con múltiples interfaces
# Uso: ./create_multi_interface_vm.sh <nombre_vm> <nombre_ovs> <vlan_ids> <puerto_vnc> <base_mac> <num_interfaces>
# Ejemplo: ./create_multi_interface_vm.sh vm1 br-int "500,501" 1 52:54:00:01:01:01 2

if [ $# -lt 6 ]; then
    echo "Uso: $0 <nombre_vm> <nombre_ovs> <vlan_ids> <puerto_vnc> <base_mac> <num_interfaces>"
    echo "Ejemplo: $0 vm1 br-int \"500,501\" 1 52:54:00:01:01:01 2"
    exit 1
fi

# Verificar si se está ejecutando como root
if [[ $EUID -ne 0 ]]; then
   echo "Este script debe ejecutarse como root" 
   exit 1
fi

VM_NAME=$1
OVS_NAME=$2
VLAN_IDS=$3   # Lista de VLANs separadas por comas
VNC_PORT=$4
MAC_BASE=$5
NUM_INTERFACES=$6

# Convertir VLAN_IDS a array
IFS=',' read -r -a VLAN_ARRAY <<< "$VLAN_IDS"

# Verificar que el número de VLANs sea igual al número de interfaces
if [ ${#VLAN_ARRAY[@]} -ne $NUM_INTERFACES ]; then
    echo "Error: El número de VLANs (${#VLAN_ARRAY[@]}) no coincide con el número de interfaces ($NUM_INTERFACES)"
    exit 1
fi

# Directorio para las imágenes
IMG_DIR="/var/lib/images"
mkdir -p $IMG_DIR

# Nombre de la imagen CirrOS
IMG_NAME="cirros-0.5.1-x86_64-disk.img"
IMG_PATH="$IMG_DIR/$IMG_NAME"

# Verificar si la imagen existe, si no, descargarla
if [ ! -f "$IMG_PATH" ]; then
    echo "La imagen $IMG_NAME no existe. Descargando..."
    # URL de la imagen CirrOS
    IMG_URL="https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img"
    
    # Verificar si curl está instalado
    if ! command -v curl &> /dev/null; then
        echo "curl no está instalado. Instalando..."
        apt-get update && apt-get install -y curl
    fi
    
    # Descargar la imagen
    curl -L $IMG_URL -o $IMG_PATH
    
    if [ $? -ne 0 ]; then
        echo "Error al descargar la imagen. Verifique la conexión a Internet."
        exit 1
    fi
    
    echo "Imagen descargada correctamente: $IMG_PATH"
else
    echo "Usando imagen existente: $IMG_PATH"
fi

# Crear interfaces TAP para la VM
TAP_INTERFACES=""
NETDEV_OPTIONS=""
DEVICE_OPTIONS=""

for ((i=0; i<$NUM_INTERFACES; i++)); do
    # Generar un nombre único para la interfaz TAP
    TAP_INTERFACE="tap_${VM_NAME}_${i}"
    
    # Generar una dirección MAC única basada en la MAC base
    if [ $i -eq 0 ]; then
        # Para la primera interfaz, usar la MAC base
        MAC_ADDRESS=$MAC_BASE
    else
        # Para las siguientes interfaces, modificar el último byte de la MAC base
        MAC_ADDRESS=$(echo $MAC_BASE | sed "s/:[^:]*$/:$(printf "%02x" $i)/")
    fi
    
    # Crear la interfaz TAP
    if ! ip link show $TAP_INTERFACE &> /dev/null; then
        echo "Creando interfaz TAP para la VM: $TAP_INTERFACE"
        ip tuntap add mode tap name $TAP_INTERFACE
        ip link set dev $TAP_INTERFACE up
        echo "Interfaz TAP creada: $TAP_INTERFACE"
    else
        echo "La interfaz TAP ya existe: $TAP_INTERFACE"
    fi
    
    # Conectar la interfaz TAP al OvS con la VLAN correspondiente
    VLAN_ID=${VLAN_ARRAY[$i]}
    if ! ovs-vsctl show | grep "Port \"$TAP_INTERFACE\"" > /dev/null; then
        echo "Conectando interfaz TAP al OvS con VLAN $VLAN_ID..."
        ovs-vsctl add-port $OVS_NAME $TAP_INTERFACE
        ovs-vsctl set port $TAP_INTERFACE tag=$VLAN_ID
        echo "Interfaz TAP conectada al OvS con VLAN $VLAN_ID"
    else
        echo "La interfaz TAP ya está conectada al OvS. Actualizando VLAN..."
        ovs-vsctl set port $TAP_INTERFACE tag=$VLAN_ID
    fi
    
    # Añadir opciones para QEMU
    TAP_INTERFACES="$TAP_INTERFACES $TAP_INTERFACE"
    NETDEV_OPTIONS="$NETDEV_OPTIONS -netdev tap,id=$TAP_INTERFACE,ifname=$TAP_INTERFACE,script=no,downscript=no"
    DEVICE_OPTIONS="$DEVICE_OPTIONS -device e1000,netdev=$TAP_INTERFACE,mac=$MAC_ADDRESS"
done

# Crear directorio para los logs
LOG_DIR="/var/log/vms"
mkdir -p $LOG_DIR

# Iniciar la VM con QEMU/KVM
echo "Iniciando la VM $VM_NAME con $NUM_INTERFACES interfaces..."
VM_PID_FILE="/var/run/vm_${VM_NAME}.pid"

# Construir comando para iniciar la VM
QEMU_CMD="qemu-system-x86_64 \
    -enable-kvm \
    -vnc 0.0.0.0:$VNC_PORT \
    $NETDEV_OPTIONS \
    $DEVICE_OPTIONS \
    -daemonize \
    -snapshot \
    -pidfile $VM_PID_FILE \
    $IMG_PATH"

# Ejecutar el comando
echo "Ejecutando: $QEMU_CMD"
eval $QEMU_CMD

# Verificar si la VM se inició correctamente
if [ -f "$VM_PID_FILE" ]; then
    VM_PID=$(cat $VM_PID_FILE)
    echo "VM $VM_NAME iniciada correctamente con PID $VM_PID"
    echo "Acceso VNC disponible en el puerto 590$VNC_PORT"
else
    echo "Error al iniciar la VM $VM_NAME"
    exit 1
fi

echo "Creación de VM con múltiples interfaces completada!"
