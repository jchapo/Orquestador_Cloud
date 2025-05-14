#!/bin/bash

# Script para eliminar toda la topología, incluyendo VMs, VLANs y configuraciones de red
# Uso: ./cleanup_topology.sh [--keep-vlans]
# La opción --keep-vlans mantiene las VLANs y solo elimina las VMs

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

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
    
    # Obtener lista de VMs en ejecución
    vm_list=$(ssh ubuntu@$worker "sudo ps -ef | grep qemu | grep -v grep | grep -o 'vm[0-9]*' | sort | uniq")
    
    if [ -n "$vm_list" ]; then
        echo "VMs encontradas en $worker: $vm_list"
        
        # Eliminar cada VM
        for vm in $vm_list; do
            echo "Eliminando VM $vm en $worker..."
            
            # Obtener el PID de la VM
            pid=$(ssh ubuntu@$worker "sudo cat /var/run/vm_${vm}.pid 2>/dev/null || sudo ps -ef | grep qemu | grep $vm | grep -v grep | awk '{print \$2}'")
            
            if [ -n "$pid" ]; then
                # Matar el proceso QEMU
                ssh ubuntu@$worker "sudo kill -9 $pid"
                echo "Proceso QEMU con PID $pid terminado."
            fi
            
            # Eliminar el archivo PID
            ssh ubuntu@$worker "sudo rm -f /var/run/vm_${vm}.pid"
            
            # Eliminar la interfaz TAP
            ssh ubuntu@$worker "sudo ip link show tap_${vm} &>/dev/null && sudo ip link set dev tap_${vm} down && sudo ip link delete tap_${vm} && echo 'Interfaz tap_${vm} eliminada.'"
            
            # Eliminar la configuración del OVS
            ssh ubuntu@$worker "sudo ovs-vsctl --if-exists del-port br-int tap_${vm} && echo 'Puerto tap_${vm} eliminado del OVS.'"
            
            echo "VM $vm eliminada de $worker con éxito."
        done
    else
        echo "No se encontraron VMs en ejecución en $worker."
    fi
done

# Paso 2: Eliminar las reglas de flujo en el OFS
echo "Paso 2: Eliminando reglas de flujo en el OFS..."
ssh ubuntu@$OFS_NODE "sudo ovs-ofctl del-flows br-int && sudo ovs-ofctl add-flow br-int priority=0,actions=normal && echo 'Reglas de flujo en OFS restablecidas.'"

# Paso 3: Eliminar las reglas de flujo en los workers
echo "Paso 3: Eliminando reglas de flujo en los workers..."
for worker in "${WORKERS[@]}"; do
    ssh ubuntu@$worker "sudo ovs-ofctl del-flows br-int && sudo ovs-ofctl add-flow br-int priority=0,actions=normal && echo 'Reglas de flujo en $worker restablecidas.'"
done

# Paso 4: Eliminar las VLANs (a menos que se indique lo contrario)
if [ "$KEEP_VLANS" = false ]; then
    echo "Paso 4: Eliminando VLANs y configuración de red..."
    
    # Obtener lista de VLANs activas
    vlan_list=$(ip -br link show | grep "vlan[0-9]*" | awk '{print $1}')
    
    if [ -n "$vlan_list" ]; then
        echo "VLANs encontradas: $vlan_list"
        
        # Eliminar cada VLAN
        for vlan in $vlan_list; do
            echo "Eliminando VLAN $vlan..."
            
            # Obtener el ID de VLAN
            vlan_id=${vlan#vlan}
            
            # Eliminar namespace DHCP
            echo "Eliminando namespace DHCP para VLAN $vlan_id..."
            ip netns list | grep -q "dhcp_vlan$vlan_id" && ip netns delete "dhcp_vlan$vlan_id" && echo "Namespace dhcp_vlan$vlan_id eliminado."
            
            # Eliminar interfaces veth
            echo "Eliminando interfaces veth para VLAN $vlan_id..."
            ip link show "veth_ovs_$vlan_id" &>/dev/null && ip link set dev "veth_ovs_$vlan_id" down && ip link delete "veth_ovs_$vlan_id" && echo "Interfaz veth_ovs_$vlan_id eliminada."
            
            # Eliminar configuración de dnsmasq
            echo "Eliminando configuración de dnsmasq para VLAN $vlan_id..."
            rm -f "/etc/dnsmasq.d/vlan$vlan_id.conf"
            rm -f "/var/run/dnsmasq_vlan$vlan_id.pid"
            
            # Eliminar el puerto VLAN del OVS
            echo "Eliminando puerto VLAN del OVS..."
            ovs-vsctl --if-exists del-port br-int "$vlan" && echo "Puerto $vlan eliminado del OVS."
            
            # Eliminar la interfaz VLAN
            echo "Eliminando interfaz VLAN..."
            ip link show "$vlan" &>/dev/null && ip link set dev "$vlan" down && ip link delete "$vlan" && echo "Interfaz $vlan eliminada."
            
            echo "VLAN $vlan_id eliminada con éxito."
        done
    else
        echo "No se encontraron VLANs activas."
    fi
    
    # Limpiar reglas de iptables relacionadas con VLANs
    echo "Eliminando reglas de iptables relacionadas con VLANs..."
    sudo iptables -t nat -F POSTROUTING
    sudo iptables -F FORWARD
    echo "Reglas de iptables eliminadas."
else
    echo "Paso 4: Manteniendo VLANs según lo solicitado."
fi

echo "===== Limpieza de la topología completada ====="
exit 0
