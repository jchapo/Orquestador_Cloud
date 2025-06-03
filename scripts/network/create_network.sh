#!/bin/bash
cidr2netmask() {
    local bits=$1
    local mask=""
    for ((i = 0; i < 4; i++)); do
        if ((bits >= 8)); then
            mask+="255."
            bits=$((bits - 8))
        elif ((bits > 0)); then
            mask+=$((256 - (1 << (8 - bits)))).
            bits=0
        else
            mask+="0."
        fi
    done
    echo "${mask%?}"
}


# Script para crear una red interna del orquestador
# Uso: ./create_network.sh <nombre_red> <vlan_id> <cidr> <rango_dhcp>
# Ejemplo: ./create_network.sh vlan100 100 192.168.100.0/24 192.168.100.10,192.168.100.200

if [ $# -ne 4 ]; then
    echo "Uso: $0 <nombre_red> <vlan_id> <cidr> <rango_dhcp>"
    echo "Ejemplo: $0 vlan100 100 192.168.100.0/24 192.168.100.10,192.168.100.200"
    exit 1
fi

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

NOMBRE_RED=$1
VLAN_ID=$2
CIDR=$3
RANGO_DHCP=$4

# Extraer información de la red desde el CIDR
IP_PREFIX=$(echo $CIDR | cut -d'/' -f1)
PREFIX_LENGTH=$(echo $CIDR | cut -d'/' -f2)

#IP_NETWORK=$(ipcalc -n $CIDR | grep Network | awk '{print $2}')
IFS=/ read IP_PREFIX PREFIX_LENGTH <<< "$CIDR"
IFS=. read -r i1 i2 i3 i4 <<< "$IP_PREFIX"
ip_int=$(( (i1 << 24) + (i2 << 16) + (i3 << 8) + i4 ))
mask=$(( 0xFFFFFFFF << (32 - PREFIX_LENGTH) & 0xFFFFFFFF ))
network_int=$(( ip_int & mask ))
n1=$(( (network_int >> 24) & 0xFF ))
n2=$(( (network_int >> 16) & 0xFF ))
n3=$(( (network_int >> 8) & 0xFF ))
n4=$(( network_int & 0xFF ))
IP_NETWORK="$CIDR"

GATEWAY_IP=$(echo $IP_PREFIX | sed 's/\.[0-9]*$/.1/')
DHCP_IP=$(echo $IP_PREFIX | sed 's/\.[0-9]*$/.2/')

echo "Creando red: $NOMBRE_RED"
echo "VLAN ID: $VLAN_ID"
echo "Red: $IP_NETWORK"
echo "Gateway IP: $GATEWAY_IP"
echo "DHCP IP: $DHCP_IP"
echo "Rango DHCP: $RANGO_DHCP"

# Crear la interfaz VLAN en el OvS
echo "Creando interfaz VLAN $VLAN_ID en br-int..."
# Verificar si la interfaz ya existe
if ! sudo ip link show vlan$VLAN_ID &> /dev/null; then
    # Crear la interfaz interna para el OvS
    sudo ovs-vsctl add-port br-int vlan$VLAN_ID -- set interface vlan$VLAN_ID type=internal
    # Configurar VLAN tag en el puerto
    sudo ovs-vsctl set port vlan$VLAN_ID tag=$VLAN_ID
    # Activar la interfaz
    sudo ip link set dev vlan$VLAN_ID up
    # Asignar IP a la interfaz (gateway)
    sudo ip addr add $GATEWAY_IP/$PREFIX_LENGTH dev vlan$VLAN_ID
    echo "Interfaz vlan$VLAN_ID creada y configurada con IP $GATEWAY_IP/$PREFIX_LENGTH"
else
    echo "La interfaz vlan$VLAN_ID ya existe."
fi

# Crear Network Namespace para el DHCP
echo "Creando Network Namespace para el DHCP..."
# Verificar si el namespace ya existe
if ! sudo ip netns list | grep -q "dhcp_vlan$VLAN_ID"; then
    # Crear el namespace
    sudo ip netns add dhcp_vlan$VLAN_ID
    echo "Network Namespace dhcp_vlan$VLAN_ID creado."
    
    # Crear par de interfaces veth para conectar el namespace con el OvS
    sudo ip link add veth_dhcp_$VLAN_ID type veth peer name veth_ovs_$VLAN_ID
    
    # Configurar la interfaz en el namespace
    sudo ip link set veth_dhcp_$VLAN_ID netns dhcp_vlan$VLAN_ID
    sudo ip netns exec dhcp_vlan$VLAN_ID ip link set dev veth_dhcp_$VLAN_ID up
    sudo ip netns exec dhcp_vlan$VLAN_ID ip addr add $DHCP_IP/$PREFIX_LENGTH dev veth_dhcp_$VLAN_ID
    
    # Configurar ruta por defecto en el namespace
    sudo ip netns exec dhcp_vlan$VLAN_ID ip route add default via $GATEWAY_IP
    
    # Conectar la otra interfaz al OvS con la VLAN correspondiente
    sudo ovs-vsctl add-port br-int veth_ovs_$VLAN_ID
    sudo ovs-vsctl set port veth_ovs_$VLAN_ID tag=$VLAN_ID
    sudo ip link set dev veth_ovs_$VLAN_ID up
    
    echo "Interfaces veth configuradas y conectadas."
else
    echo "El namespace dhcp_vlan$VLAN_ID ya existe."
fi

# Instalar dnsmasq si no está instalado
if ! command -v dnsmasq &> /dev/null; then
    echo "Instalando dnsmasq..."
    sudo apt-get update && apt-get install -y dnsmasq
fi

# Crear archivo de configuración para dnsmasq
DHCP_START=$(echo $RANGO_DHCP | cut -d',' -f1)
DHCP_END=$(echo $RANGO_DHCP | cut -d',' -f2)

# Crear directorio de configuración si no existe
sudo mkdir -p /etc/dnsmasq.d

# Crear el archivo de configuración para esta VLAN
# Calculate the netmask first
NETMASK=$(cidr2netmask $PREFIX_LENGTH)

sudo tee /etc/dnsmasq.d/vlan$VLAN_ID.conf > /dev/null << EOF
# Configuración DHCP para VLAN $VLAN_ID
interface=veth_dhcp_$VLAN_ID

dhcp-range=$DHCP_START,$DHCP_END,$NETMASK,12h
dhcp-option=option:router,$GATEWAY_IP
dhcp-option=option:dns-server,8.8.8.8,8.8.4.4
EOF

# Iniciar el servicio DHCP en el namespace
#echo "Iniciando servicio DHCP para VLAN $VLAN_ID..."
#ip netns exec dhcp_vlan$VLAN_ID dnsmasq \
#    --conf-file=/etc/dnsmasq.d/vlan$VLAN_ID.conf \
#    --pid-file=/var/run/dnsmasq_vlan$VLAN_ID.pid #\
#    --no-resolv

sudo ip netns exec dhcp_vlan$VLAN_ID dnsmasq \
    --conf-file=/etc/dnsmasq.d/vlan$VLAN_ID.conf \
    --pid-file=/var/run/dnsmasq_vlan$VLAN_ID.pid \
    --leasefile-ro \
    --no-hosts \
    --no-resolv \
    --bind-interfaces \
    --except-interface=lo




echo "Servicio DHCP para VLAN $VLAN_ID iniciado correctamente."
echo "Red $NOMBRE_RED (VLAN $VLAN_ID) creada y configurada con éxito!"
