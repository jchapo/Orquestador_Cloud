#!/bin/bash

# Script para crear una VM
# Uso: ./create_vm.sh <nombre_vm> <nombre_ovs> <vlan_id> <puerto_vnc> [<mac_address>]
# Ejemplo: ./create_vm.sh vm1 br-int 100 1 aa:bb:cc:dd:ee:ff

if [ $# -lt 4 ]; then
    echo "Uso: $0 <nombre_vm> <nombre_ovs> <vlan_id> <puerto_vnc> [<mac_address>]"
    echo "Ejemplo: $0 vm1 br-int 100 1 aa:bb:cc:dd:ee:ff"
    exit 1
fi

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

VM_NAME=$1
OVS_NAME=$2
VLAN_ID=$3
VNC_PORT=$4

# MAC Address opcional (si no se proporciona, se genera uno)
if [ $# -ge 5 ]; then
    MAC_ADDRESS=$5
else
    # Generar un MAC address aleatorio
    MAC_ADDRESS=$(printf '52:54:00:%02x:%02x:%02x\n' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)))
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

# Crear interfaz TAP para la VM
TAP_INTERFACE="tap_${VM_NAME}"
#SHORT_VM_NAME=$(echo $VM_NAME | cut -c1-10)
#TAP_INTERFACE="tap_${SHORT_VM_NAME}"

if ! ip link show $TAP_INTERFACE &> /dev/null; then
    echo "Creando interfaz TAP para la VM..."
    ip tuntap add mode tap name  $TAP_INTERFACE
    ip link set dev $TAP_INTERFACE up
    echo "Interfaz TAP creada: $TAP_INTERFACE"
else
    echo "La interfaz TAP ya existe: $TAP_INTERFACE"
fi

# Conectar la interfaz TAP al OvS con la VLAN correspondiente
if ! ovs-vsctl show | grep "Port \"$TAP_INTERFACE\"" > /dev/null; then
    echo "Conectando interfaz TAP al OvS con VLAN $VLAN_ID..."
    ovs-vsctl add-port $OVS_NAME $TAP_INTERFACE
    ovs-vsctl set port $TAP_INTERFACE tag=$VLAN_ID
    echo "Interfaz TAP conectada al OvS con VLAN $VLAN_ID"
else
    echo "La interfaz TAP ya está conectada al OvS."
    # Actualizar la VLAN si es necesario
    ovs-vsctl set port $TAP_INTERFACE tag=$VLAN_ID
fi

# Crear directorio para los logs
LOG_DIR="/var/log/vms"
mkdir -p $LOG_DIR

# Iniciar la VM con QEMU/KVM
echo "Iniciando la VM $VM_NAME..."
VM_PID_FILE="/var/run/vm_${VM_NAME}.pid"

# Construir comando para iniciar la VM según los parámetros proporcionados
QEMU_CMD="qemu-system-x86_64 \
    -enable-kvm \
    -vnc 0.0.0.0:$VNC_PORT \
    -netdev tap,id=$TAP_INTERFACE,ifname=$TAP_INTERFACE,script=no,downscript=no \
    -device e1000,netdev=$TAP_INTERFACE,mac=$MAC_ADDRESS \
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

echo "Creación de VM completada!"
