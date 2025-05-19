#!/bin/bash

# Script mejorado para crear una VM cloud con soporte cloud-init
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
CLOUD_INIT_DIR="$SCRIPT_DIR/cloud-init"

# Crear directorios necesarios
mkdir -p "$IMAGES_DIR"
mkdir -p "$CLOUD_INIT_DIR"

# Verificar si existe la imagen base
if ! ls "$BASE_IMAGE" &>/dev/null; then
    echo "ls: cannot access '$BASE_IMAGE': No such file or directory"
    if [ "$IMAGE_FILE" = "cirros.img" ]; then
        echo "La imagen cirros.img no existe. Descargando CirrOS..."
        wget -q -O "$BASE_IMAGE.tmp" "https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img"
        mv "$BASE_IMAGE.tmp" "$BASE_IMAGE"
    elif [ "$IMAGE_FILE" = "debian.img" ]; then
        echo "La imagen Debian no existe. Descargando..."
        wget -q -O "$IMAGES_DIR/debian.img.tmp" "https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-nocloud-amd64.qcow2"
        mv "$IMAGES_DIR/debian.img.tmp" "$IMAGES_DIR/debian.img"
        BASE_IMAGE="$IMAGES_DIR/debian.img"
    else
        echo "La imagen $IMAGE_FILE no existe. Descargando imagen Debian como fallback..."
        wget -q -O "$IMAGES_DIR/debian.img.tmp" "https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-nocloud-amd64.qcow2"
        mv "$IMAGES_DIR/debian.img.tmp" "$IMAGES_DIR/debian.img"
        BASE_IMAGE="$IMAGES_DIR/debian.img"
    fi
fi

# Verificar si cloud-localds está instalado
if ! command -v cloud-localds &> /dev/null; then
    echo "Instalando cloud-image-utils para soporte de cloud-init..."
    apt-get update && apt-get install -y cloud-image-utils
fi

# Crear imagen de VM si no existe
if [ ! -f "$VM_IMAGE" ]; then
    echo "Creando imagen de VM desde $BASE_IMAGE con tamaño ${DISK}G..."
    qemu-img create -f qcow2 -b "$BASE_IMAGE" "$VM_IMAGE" "${DISK}G"
    # Redimensionar el sistema de archivos dentro de la imagen (si es necesario)
    if command -v virt-customize &> /dev/null; then
        echo "Redimensionando el sistema de archivos en la imagen..."
        virt-customize -a "$VM_IMAGE" --run-command "growpart /dev/sda 1 && resize2fs /dev/sda1" || true
    else
        echo "ADVERTENCIA: virt-customize no está instalado. La imagen podría no usar todo el espacio asignado."
        echo "Puede instalar con: sudo apt-get install -y libguestfs-tools"
    fi
fi

# Crear archivos de cloud-init
CLOUD_INIT_ISO="$CLOUD_INIT_DIR/$VM_NAME-cidata.iso"

# Crear archivo meta-data
cat > "$CLOUD_INIT_DIR/meta-data" <<EOF
instance-id: $VM_NAME
local-hostname: $VM_NAME
EOF

# Crear archivo user-data con configuración básica para Debian
cat > "$CLOUD_INIT_DIR/user-data" <<EOF
#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: users, admin
    shell: /bin/bash
    lock_passwd: false
    passwd: "$(openssl passwd -1 -salt SaltSalt ubuntu)"

ssh_pwauth: true

package_upgrade: true
packages:
  - iperf
  - iperf3
  - htop
  - tcpdump

write_files:
  - path: /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
    content: |
      network: {config: disabled}

runcmd:
  - echo "La VM $VM_NAME (Debian) se ha iniciado correctamente" > /var/log/vm-init.log
EOF

# Crear disco ISO para cloud-init
cloud-localds "$CLOUD_INIT_ISO" "$CLOUD_INIT_DIR/user-data" "$CLOUD_INIT_DIR/meta-data"

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
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='$CLOUD_INIT_ISO'/>
      <target dev='hdb' bus='ide'/>
      <readonly/>
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

# Mensaje final
echo "VM $VM_NAME (Debian) creada correctamente con soporte cloud-init."
echo "Usuario: ubuntu, Contraseña: ubuntu"
echo "Usa add_interface.sh para añadir interfaces antes de iniciarla."
