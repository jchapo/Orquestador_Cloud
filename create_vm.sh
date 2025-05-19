#!/bin/bash

# Script para crear una VM sin interfaces de red iniciales
# Uso: ./create_vm.sh <vm_name> <vnc_port> <mac_address> <cpu> <ram> <disk> <image>

if [ $# -lt 7 ]; then
    echo "Uso: $0 <vm_name> <vnc_port> <mac_address> <cpu> <ram> <disk> <image>"
    exit 1
fi

VM_NAME=$1
VNC_PORT=$2
MAC_ADDRESS=$3
CPU=$4
RAM=$5           # RAM en MiB
DISK=$6          # Tamaño del disco en GB
IMAGE_FILE=$7

if [ "$VNC_PORT" -lt 5900 ]; then
    VNC_PORT=$((5900 + $VNC_PORT))
fi

# Obtener el directorio base desde donde se ejecuta el script
SCRIPT_DIR="/home/ubuntu/cloud-orchestrator"
IMAGES_DIR="$SCRIPT_DIR/images"
VM_IMAGE="$IMAGES_DIR/$VM_NAME.qcow2"
BASE_IMAGE="$IMAGES_DIR/$IMAGE_FILE"

#echo "Script ubicado en: $SCRIPT_DIR"
#echo "Usando BASE_IMAGE: $BASE_IMAGE"
#ls -l "$BASE_IMAGE"

mkdir -p "$IMAGES_DIR"

# Verificar si existe la imagen base
if ! ls "$BASE_IMAGE" &>/dev/null; then
    echo "ls: cannot access '$BASE_IMAGE': No such file or directory"
    if [ "$IMAGE_FILE" = "cirros.img" ]; then
        echo "La imagen cirros.img no existe. Descargando CirrOS..."
        mkdir -p "$IMAGES_DIR"
        wget -q -O "$BASE_IMAGE.tmp" "https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img"
        mv "$BASE_IMAGE.tmp" "$BASE_IMAGE"
    else
        echo "La imagen $IMAGE_FILE no existe. Descargando imagen base por defecto: ubuntu.img"
        mkdir -p "$IMAGES_DIR"
        wget -q -O "$IMAGES_DIR/ubuntu.img.tmp" "https://cloud-images.ubuntu.com/focal/20250514/focal-server-cloudimg-amd64.img"
        mv "$IMAGES_DIR/ubuntu.img.tmp" "$IMAGES_DIR/ubuntu.img"
        BASE_IMAGE="$IMAGES_DIR/ubuntu.img"
    fi
fi

# Crear imagen de VM si no existe
if [ ! -f "$VM_IMAGE" ]; then
    echo "Creando imagen de VM desde $BASE_IMAGE con tamaño ${DISK}G..."
    qemu-img create -f qcow2 -b "$BASE_IMAGE" "$VM_IMAGE" "${DISK}G"
fi

# Crear archivo XML para definir la VM SIN interfaces de red
XML_FILE="/tmp/$VM_NAME.xml"
cat > "$XML_FILE" <<EOF
<domain type='kvm'>
  <name>$VM_NAME</name>
  <memory unit='MiB'>$RAM</memory>
  <vcpu placement='static'>$CPU</vcpu>
  <os>
    <type arch='x86_64'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='$VM_IMAGE'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <graphics type='vnc' port='$VNC_PORT' listen='0.0.0.0'/>
    <video>
      <model type='cirrus'/>
    </video>
  </devices>
</domain>
EOF

# Definir la VM - sin iniciarla todavía
virsh define "$XML_FILE"

# Nota: No iniciamos la VM aquí, primero se añaden interfaces y luego se inicia
echo "VM $VM_NAME creada correctamente. Usa add_interface.sh para añadir interfaces antes de iniciarla."