#!/bin/bash
#
# Script mejorado para crear una VM cloud con soporte cloud-init
# Uso: ./create_vm.sh <vm_name> <vnc_port> <mac_address> <cpu> <ram> <disk> [image]

# ──────────────────────────────────────────────────────────
# 1) Validación de argumentos básicos (6 obligatorios)
# ──────────────────────────────────────────────────────────
if [ $# -lt 6 ]; then
    echo "Uso: $0 <vm_name> <vnc_port> <mac_address> <cpu> <ram> <disk> [image]"
    exit 1
fi

VM_NAME=$1
VNC_PORT=$2
MAC_ADDRESS=$3
CPU=$4
RAM=$5           # RAM en MiB
DISK=$6          # Tamaño del disco en GB

# ──────────────────────────────────────────────────────────
# 2) Imagen: si no viene argumento ➜ cirros.img
# ──────────────────────────────────────────────────────────
DEFAULT_IMAGE="cirros.img"
IMAGE_FILE=${7:-$DEFAULT_IMAGE}

# VNC <5900 → ajustar
if [ "$VNC_PORT" -lt 5900 ]; then
    VNC_PORT=$((5900 + VNC_PORT))
fi

# ───── Rutas base ─────
SCRIPT_DIR="/home/ubuntu/cloud-orchestrator"
IMAGES_DIR="$SCRIPT_DIR/images"
CLOUD_INIT_DIR="$SCRIPT_DIR/cloud-init"

VM_IMAGE="$IMAGES_DIR/$VM_NAME.qcow2"
BASE_IMAGE="$IMAGES_DIR/$IMAGE_FILE"

mkdir -p "$IMAGES_DIR" "$CLOUD_INIT_DIR"

# ──────────────────────────────────────────────────────────
# 3) Asegurar que la imagen base exista (o descargar CirrOS)
# ──────────────────────────────────────────────────────────
if [ ! -f "$BASE_IMAGE" ]; then
    echo "La imagen '$IMAGE_FILE' no se encontró en $IMAGES_DIR."

    # Siempre caemos a CirrOS como fallback
    IMAGE_FILE="$DEFAULT_IMAGE"
    BASE_IMAGE="$IMAGES_DIR/$DEFAULT_IMAGE"

    if [ ! -f "$BASE_IMAGE" ]; then
        echo "Descargando CirrOS 0.5.1 (qcow2) como imagen base por defecto..."
        wget -q -O "$BASE_IMAGE.tmp" \
             "https://download.cirros-cloud.net/0.5.1/cirros-0.5.1-x86_64-disk.img"
        mv "$BASE_IMAGE.tmp" "$BASE_IMAGE"
        echo "Descarga completada: $BASE_IMAGE"
    fi
fi

# ──────────────────────────────────────────────────────────
# 4) Verificar utilidades necesarias
# ──────────────────────────────────────────────────────────
if ! command -v cloud-localds &>/dev/null; then
    echo "Instalando cloud-image-utils..."
    sudo apt-get update && sudo apt-get install -y cloud-image-utils
fi

# ──────────────────────────────────────────────────────────
# 5) Clonar/redimensionar imagen si aún no existe la del VM
# ──────────────────────────────────────────────────────────
if [ ! -f "$VM_IMAGE" ]; then
    echo "Creando copia de '$BASE_IMAGE' en '$VM_IMAGE'..."
    cp "$BASE_IMAGE" "$VM_IMAGE"

    echo "Redimensionando imagen a ${DISK}G..."
    qemu-img resize "$VM_IMAGE" "${DISK}G"
fi

# ──────────────────────────────────────────────────────────
# 6) Generar seed ISO de cloud-init
# ──────────────────────────────────────────────────────────
CLOUD_INIT_ISO="$CLOUD_INIT_DIR/${VM_NAME}-cidata.iso"

cat > "$CLOUD_INIT_DIR/meta-data" <<EOF
instance-id: $VM_NAME
local-hostname: $VM_NAME
EOF

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
packages: [iperf, iperf3, htop, tcpdump]
runcmd:
  - echo "La VM $VM_NAME se ha iniciado correctamente" > /var/log/vm-init.log
EOF

cloud-localds "$CLOUD_INIT_ISO" "$CLOUD_INIT_DIR/user-data" "$CLOUD_INIT_DIR/meta-data"

# ──────────────────────────────────────────────────────────
# 7) Definición XML (sin NICs) e importación en libvirt
# ──────────────────────────────────────────────────────────
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
  <features><acpi/><apic/><pae/></features>
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
    <serial type='pty'><target port='0'/></serial>
    <console type='pty'><target type='serial' port='0'/></console>
    <graphics type='vnc' port='$VNC_PORT' listen='0.0.0.0'/>
    <video><model type='cirrus'/></video>
  </devices>
</domain>
EOF

virsh define "$XML_FILE"

echo "✅ VM '$VM_NAME' creada. Imagen base: '$IMAGE_FILE'"
echo "   Usuario: ubuntu  |  Contraseña: ubuntu"
echo "   Añade interfaces con add_interface.sh antes de arrancarla."