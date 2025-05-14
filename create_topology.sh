#!/bin/bash

# Script para crear la topología completa según la Fig.3
# Este script debe ejecutarse desde el HeadNode

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

echo "===== Creando topología completa de orquestación ====="

# Configuración de nodos
HEAD_NODE="localhost"
WORKER1="10.0.10.2"
WORKER2="10.0.10.3"
WORKER3="10.0.10.4"
OFS_NODE="10.0.10.5"

# Configuración de interfaces
HEAD_INTERNET_IFACE="ens3"  # Interfaz de Internet en HeadNode
HEAD_OFS_IFACE="ens4"       # Interfaz que conecta HeadNode con OFS
WORKER_OFS_IFACE="ens4"     # Interfaz que conecta Workers con OFS

# Configuración de VLANs
VLAN_IDS=("100" "200" "300")
VLAN_NETWORKS=("192.168.10.0/24" "192.168.20.0/24" "192.168.30.0/24")
VLAN_DHCP_RANGES=("192.168.10.10,192.168.10.200" "192.168.20.10,192.168.20.200" "192.168.30.10,192.168.30.200")

# Paso 1: Inicializar el HeadNode
echo "Paso 1: Inicializando HeadNode..."
./initialize_headnode.sh br-int $HEAD_OFS_IFACE
echo "HeadNode inicializado."

# Paso 2: Inicializar el nodo OFS
echo "Paso 2: Inicializando nodo OFS..."
#Asumimos que el nodo OFS tiene SSH configurado
ssh ubuntu@$OFS_NODE "sudo bash -s" < initialize_worker.sh br-int ens5 ens6 ens7 ens8
echo "Nodo OFS inicializado."

# Paso 3: Inicializar los Workers
echo "Paso 3: Inicializando Workers..."
for worker in $WORKER1 $WORKER2 $WORKER3; do
    echo "Inicializando $worker..."

    # Opción 1: Forzar el uso de llaves SSH
    # ssh -o IdentityFile=~/.ssh/id_rsa -o BatchMode=yes ubuntu@$worker "bash -s" < initialize_worker.sh br-int $WORKER_OFS_IFACE
    
    # Si la opción 1 no funciona, prueba esto (comenta la anterior y descomenta esta):
    # ssh -i ~/.ssh/id_rsa ubuntu@$worker "bash -s" < initialize_worker.sh br-int $WORKER_OFS_IFACE
    # ssh ubuntu@$worker "bash -s" < initialize_worker.sh br-int $WORKER_OFS_IFACE 
    ssh ubuntu@$worker "sudo bash -s" < initialize_worker.sh br-int $WORKER_OFS_IFACE
    echo "$worker inicializado."
done

# Paso 4: Crear las redes VLAN en el HeadNode
echo "Paso 4: Creando redes VLAN..."
for i in "${!VLAN_IDS[@]}"; do
    VLAN_ID=${VLAN_IDS[$i]}
    VLAN_NETWORK=${VLAN_NETWORKS[$i]}
    VLAN_DHCP_RANGE=${VLAN_DHCP_RANGES[$i]}
    
    echo "Creando red VLAN $VLAN_ID con red $VLAN_NETWORK..."
    ./create_network.sh vlan$VLAN_ID $VLAN_ID $VLAN_NETWORK $VLAN_DHCP_RANGE
    echo "Red VLAN $VLAN_ID creada."
    sleep 2
    # Configurar acceso a Internet para la VLAN
    echo "Configurando acceso a Internet para VLAN $VLAN_ID..."
    ./internet_access.sh $VLAN_ID $HEAD_INTERNET_IFACE
    echo "Acceso a Internet configurado para VLAN $VLAN_ID."
done

# Paso 5: Permitir comunicación entre las VLANs (opcional)
echo "Paso 5: Configurando comunicación entre VLANs..."
sudo ./connect_vlans.sh 100 200
#sudo ./connect_vlans.sh 200 300
echo "Comunicación entre VLANs configurada."

# Paso 6: Crear VMs en los Workers
echo "Paso 6: Creando VMs en los Workers..."

PUCP_CODE="20:12:54:24"

# Crear VMs en Worker1
echo "Creando VMs en $WORKER1..."
ssh ubuntu@$WORKER1 "sudo bash -s" < create_vm.sh vm1-w1-v1 br-int 100 1 "${PUCP_CODE}:ee:01"
ssh ubuntu@$WORKER1 "sudo bash -s" < create_vm.sh vm2-w1-v2 br-int 200 2 "${PUCP_CODE}:ee:02"
ssh ubuntu@$WORKER1 "sudo bash -s" < create_vm.sh vm3-w1-v3 br-int 300 3 "${PUCP_CODE}:ee:03"

# Crear VMs en Worker2
echo "Creando VMs en $WORKER2..."
ssh ubuntu@$WORKER2 "sudo bash -s" < create_vm.sh vm1-w2-v1 br-int 100 1 "${PUCP_CODE}:ee:04"
ssh ubuntu@$WORKER2 "sudo bash -s" < create_vm.sh vm2-w2-v2 br-int 200 2 "${PUCP_CODE}:ee:05"
ssh ubuntu@$WORKER2 "sudo bash -s" < create_vm.sh vm3-w2-v3 br-int 300 3 "${PUCP_CODE}:ee:06"

# Crear VMs en Worker3
echo "Creando VMs en $WORKER3..."
ssh ubuntu@$WORKER3 "sudo bash -s" < create_vm.sh vm1-w3-v1 br-int 100 1 "${PUCP_CODE}:ee:07"
ssh ubuntu@$WORKER3 "sudo bash -s" < create_vm.sh vm2-w3-v2 br-int 200 2 "${PUCP_CODE}:ee:08"
ssh ubuntu@$WORKER3 "sudo bash -s" < create_vm.sh vm3-w3-v3 br-int 300 3 "${PUCP_CODE}:ee:09"

echo "===== Topología completa creada con éxito ====="
#echo "Se han creado:"
#echo "- 3 redes VLAN (100, 200, 300)"
#echo "- 6 VMs distribuidas en 3 Workers"
#echo "- Servicio DHCP para cada VLAN en el HeadNode"
#echo "- Acceso a Internet para todas las VLANs"
#echo "- Comunicación entre VLANs 100-200 y 200-300"
#echo ""
#echo "Puedes acceder a las VMs a través de VNC en los siguientes puertos:"
#echo "- Worker1: 5901 (VM en VLAN 100), 5902 (VM en VLAN 200)"
#echo "- Worker2: 5901 (VM en VLAN 100), 5902 (VM en VLAN 300)"
#echo "- Worker3: 5901 (VM en VLAN 200), 5902 (VM en VLAN 300)"
#echo ""
#echo "Nota: Las VMs utilizan la imagen CirrOS y se ejecutan en modo snapshot,"
#echo "lo que significa que los cambios no se guardarán al reiniciar la VM."
