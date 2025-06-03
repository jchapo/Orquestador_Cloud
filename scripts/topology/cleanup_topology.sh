#!/bin/bash

# Script para eliminar toda la topología, incluyendo VMs, VLANs y configuraciones de red
# Uso: ./cleanup_topology.sh [--keep-vlans]
# La opción --keep-vlans mantiene las VLANs y solo elimina las VMs

# Definir los nodos
OFS_NODE="10.0.10.5"
WORKERS=("10.0.10.2" "10.0.10.3" "10.0.10.4")
KEEP_VLANS=false

# Procesar opciones
for arg in "$@"; do
    case $arg in
        --keep-vlans)
            KEEP_VLANS=true
            shift
            ;;
    esac
done

echo "===== Iniciando limpieza de la topología ====="

# Paso 1: Eliminar las VMs en todos los workers
echo "Paso 1: Eliminando máquinas virtuales..."

for worker in "${WORKERS[@]}"; do
    echo "Buscando VMs en $worker..."
    
    vm_list=$(ssh ubuntu@$worker "sudo ps -ef | grep qemu | grep -v grep | grep -o 'vm[0-9]*' | sort | uniq")
    
    if [ -n "$vm_list" ]; then
        echo "VMs encontradas en $worker: $vm_list"
        
        for vm in $vm_list; do
            echo "Eliminando VM $vm en $worker..."
            
            pid=$(ssh ubuntu@$worker "sudo cat /var/run/vm_${vm}.pid 2>/dev/null || sudo ps -ef | grep qemu | grep $vm | grep -v grep | awk '{print \$2}'")
            
            if [ -n "$pid" ]; then
                ssh ubuntu@$worker "sudo kill -9 $pid"
                echo "Proceso QEMU con PID $pid terminado."
            fi
            
            ssh ubuntu@$worker "sudo rm -f /var/run/vm_${vm}.pid"
            ssh ubuntu@$worker "sudo ip link show tap_${vm} &>/dev/null && sudo ip link set dev tap_${vm} down && sudo ip link delete tap_${vm} && echo 'Interfaz tap_${vm} eliminada.'"
            ssh ubuntu@$worker "sudo ovs-vsctl --if-exists del-port br-int tap_${vm} && echo 'Puerto tap_${vm} eliminado del OVS.'"
            
            echo "VM $vm eliminada de $worker con éxito."
        done
    else
        echo "No se encontraron VMs en ejecución en $worker."
    fi
done

# Paso 2: Eliminar reglas de flujo en el OFS
echo "Paso 2: Eliminando reglas de flujo en el OFS..."
ssh ubuntu@$OFS_NODE "sudo ovs-ofctl del-flows br-int && sudo ovs-ofctl add-flow br-int priority=0,actions=normal && echo 'Reglas de flujo en OFS restablecidas.'"

# Paso 3: Eliminar reglas de flujo en los workers
echo "Paso 3: Eliminando reglas de flujo en los workers..."
for worker in "${WORKERS[@]}"; do
    ssh ubuntu@$worker "sudo ovs-ofctl del-flows br-int && sudo ovs-ofctl add-flow br-int priority=0,actions=normal && echo 'Reglas de flujo en $worker restablecidas.'"
done

# Paso 4: Eliminar VLANs (a menos que se indique lo contrario)
if [ "$KEEP_VLANS" = false ]; then
    echo "Paso 4: Eliminando VLANs y configuración de red..."
    
    vlan_list=$(sudo ip -br link show | grep "vlan[0-9]*" | awk '{print $1}')
    
    if [ -n "$vlan_list" ]; then
        echo "VLANs encontradas: $vlan_list"
        
        for vlan in $vlan_list; do
            echo "Eliminando VLAN $vlan..."
            vlan_id=${vlan#vlan}
            
            echo "Eliminando namespace DHCP para VLAN $vlan_id..."
            sudo ip netns list | grep -q "dhcp_vlan$vlan_id" && sudo ip netns delete "dhcp_vlan$vlan_id" && echo "Namespace dhcp_vlan$vlan_id eliminado."
            
            echo "Eliminando interfaces veth para VLAN $vlan_id..."
            sudo ip link show "veth_ovs_$vlan_id" &>/dev/null && sudo ip link set dev "veth_ovs_$vlan_id" down && sudo ip link delete "veth_ovs_$vlan_id" && echo "Interfaz veth_ovs_$vlan_id eliminada."
            
            echo "Eliminando configuración de dnsmasq para VLAN $vlan_id..."
            sudo rm -f "/etc/dnsmasq.d/vlan$vlan_id.conf"
            sudo rm -f "/var/run/dnsmasq_vlan$vlan_id.pid"
            
            echo "Eliminando puerto VLAN del OVS..."
            sudo ovs-vsctl --if-exists del-port br-int "$vlan" && echo "Puerto $vlan eliminado del OVS."
            
            echo "Eliminando interfaz VLAN..."
            sudo ip link show "$vlan" &>/dev/null && sudo ip link set dev "$vlan" down && sudo ip link delete "$vlan" && echo "Interfaz $vlan eliminada."
            
            echo "VLAN $vlan_id eliminada con éxito."
        done
    else
        echo "No se encontraron VLANs activas."
    fi
    
    echo "Eliminando reglas de iptables relacionadas con VLANs..."
    sudo iptables -t nat -F POSTROUTING
    sudo iptables -F FORWARD
    echo "Reglas de iptables eliminadas."
else
    echo "Paso 4: Manteniendo VLANs según lo solicitado."
fi

echo "===== Limpieza de la topología completada ====="
exit 0
