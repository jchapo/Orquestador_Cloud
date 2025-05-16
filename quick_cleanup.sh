#!/bin/bash

# Script mejorado para eliminar todas las VMs, redes, interfaces y configuraciones
# Uso: ./quick_cleanup.sh [--force]

# Verificar si se ejecuta con --force para omitir la confirmación
if [[ "$1" == "--force" ]]; then
    FORCE=true
else
    FORCE=false
fi

echo "===== Script de limpieza completa ====="
echo "Este script eliminará:"
echo "- TODAS las VMs en todos los workers"
echo "- TODAS las interfaces TAP y conexiones OVS"
echo "- TODAS las redes VLAN y namespaces DHCP"
echo "- TODAS las reglas iptables y flujos OpenFlow"
echo ""
echo "¡ADVERTENCIA! Esta acción no se puede deshacer."

if [[ "$FORCE" != "true" ]]; then
    read -p "¿Está seguro de que desea continuar? (s/n): " CONFIRM
    if [[ $CONFIRM != "s" && $CONFIRM != "S" ]]; then
        echo "Operación cancelada."
        exit 0
    fi
fi

# Definir variables con valores predeterminados
OFS_NODE="10.0.10.5"
WORKERS=("10.0.10.2" "10.0.10.3" "10.0.10.4")
HEAD_INTERNET_IFACE="ens3"
OVS_BRIDGE="br-int"

echo "===== Iniciando limpieza completa ====="

# Paso 1: Eliminar todas las VMs y limpiar interfaces TAP en workers
echo "Paso 1: Eliminando todas las VMs e interfaces TAP..."

for WORKER in "${WORKERS[@]}"; do
    echo "Limpiando worker $WORKER..."
    
    TMP_SCRIPT=$(mktemp)
    
    cat > $TMP_SCRIPT << 'EOFWORKER'
#!/bin/bash
# Configurar variables
OVS_BRIDGE="br-int"
CLEAN_IMAGES=true

echo "==== Limpiando worker $(hostname) ===="

# Función para log de errores sin detener el script
log_error() {
    echo "ADVERTENCIA: $1" >&2
}

# Paso 1.1: Detener y eliminar todas las VMs
echo "Eliminando todas las VMs..."
VMS=$(virsh list --all --name | grep -v "^$")

if [ -z "$VMS" ]; then
    echo "No se encontraron VMs en este worker."
else
    echo "VMs encontradas: $VMS"
    
    # Eliminar cada VM
    for VM in $VMS; do
        echo "Procesando VM $VM..."
        # Primero obtener todas las interfaces de la VM para limpiarlas después
        IFACES=$(virsh domiflist "$VM" | grep -v "^$" | tail -n +3 | awk '{print $1}' | grep -v "^$")
        
        # Detener la VM
        virsh destroy "$VM" 2>/dev/null || log_error "No se pudo detener $VM"
        
        # Eliminar completamente la VM
        virsh undefine "$VM" --remove-all-storage 2>/dev/null || log_error "No se pudo eliminar $VM"
        
        echo "VM $VM eliminada."
        
        # Limpiar interfaces que estaban conectadas a esta VM
        if [ -n "$IFACES" ]; then
            for IFACE in $IFACES; do
                echo "Limpiando interfaz $IFACE..."
                # Verificar si la interfaz existe en OVS
                if ovs-vsctl list-ports "$OVS_BRIDGE" | grep -q "$IFACE"; then
                    ovs-vsctl del-port "$OVS_BRIDGE" "$IFACE" || log_error "No se pudo eliminar puerto OVS $IFACE"
                fi
                
                # Eliminar la interfaz TAP si existe
                if ip link show "$IFACE" &>/dev/null; then
                    ip link set "$IFACE" down 2>/dev/null || true
                    ip link delete "$IFACE" 2>/dev/null || log_error "No se pudo eliminar interfaz $IFACE"
                fi
            done
        fi
    done
fi

# Paso 1.2: Limpiar todas las interfaces TAP
echo "Eliminando todas las interfaces TAP..."
TAP_INTERFACES=$(ip link show | grep -E 'tap-|vnet' | cut -d: -f2 | tr -d ' ' | grep -v "^$")

if [ -n "$TAP_INTERFACES" ]; then
    for TAP in $TAP_INTERFACES; do
        echo "Limpiando interfaz TAP $TAP..."
        # Verificar si la interfaz está en OVS
        if ovs-vsctl list-ports "$OVS_BRIDGE" | grep -q "$TAP"; then
            ovs-vsctl del-port "$OVS_BRIDGE" "$TAP" || log_error "No se pudo eliminar puerto OVS $TAP"
        fi
        
        # Eliminar la interfaz
        ip link set "$TAP" down 2>/dev/null || true
        ip link delete "$TAP" 2>/dev/null || log_error "No se pudo eliminar interfaz $TAP"
    done
else
    echo "No se encontraron interfaces TAP."
fi

# Paso 1.3: Eliminar imágenes de VM
if [ "$CLEAN_IMAGES" = "true" ]; then
    # Ubicaciones comunes de imágenes
    IMAGE_DIRS=("/home/ubuntu/cloud-orchestrator/images" "/home/ubuntu/images" "/var/lib/libvirt/images")
    
    for DIR in "${IMAGE_DIRS[@]}"; do
        if [ -d "$DIR" ]; then
            echo "Eliminando imágenes de VMs en $DIR..."
            rm -f "$DIR"/*.qcow2 "$DIR"/vm*.img 2>/dev/null || log_error "No se pudieron eliminar todas las imágenes en $DIR"
        fi
    done
fi

# Paso 1.4: Limpiar otros puertos OVS que podrían quedar
echo "Verificando puertos adicionales en OVS..."
REMAINING_PORTS=$(ovs-vsctl list-ports "$OVS_BRIDGE" | grep -E 'tap-|vnet|vm' || true)
if [ -n "$REMAINING_PORTS" ]; then
    for PORT in $REMAINING_PORTS; do
        echo "Eliminando puerto OVS $PORT..."
        ovs-vsctl del-port "$OVS_BRIDGE" "$PORT" || log_error "No se pudo eliminar puerto $PORT"
    done
fi

echo "Limpieza de worker $(hostname) completada."
EOFWORKER

    chmod +x $TMP_SCRIPT
    scp $TMP_SCRIPT ubuntu@$WORKER:/tmp/full_cleanup.sh
    ssh ubuntu@$WORKER "sudo bash /tmp/full_cleanup.sh"
    rm $TMP_SCRIPT
    
    echo "Limpieza completada en worker $WORKER."
done

# Paso 2: Eliminar todos los namespaces DHCP, interfaces veth y configuraciones
echo "Paso 2: Eliminando namespaces DHCP, interfaces veth y configuraciones..."

DHCP_NAMESPACES=$(ip netns list | grep -E 'dhcp_vlan|ns-dhcp' | awk '{print $1}' || true)

if [ -n "$DHCP_NAMESPACES" ]; then
    for NS in $DHCP_NAMESPACES; do
        echo "Eliminando namespace $NS..."
        VLAN_ID=$(echo $NS | grep -oE '[0-9]+' || echo "unknown")
        sudo pkill -f "dnsmasq.*$NS" || true
        sudo pkill -f "dnsmasq.*vlan$VLAN_ID" || true
        sudo ip netns del $NS || true
        sudo rm -f "/etc/dnsmasq.d/vlan$VLAN_ID.conf" 2>/dev/null || true
        echo "Namespace $NS eliminado."
    done
else
    echo "No se encontraron namespaces DHCP."
fi

# Eliminar interfaces veth conectadas al OVS
echo "Eliminando interfaces veth..."
VETH_INTERFACES=$(ip link show | grep -E 'veth_ovs|veth_ns' | cut -d: -f2 | tr -d ' ' || true)

if [ -n "$VETH_INTERFACES" ]; then
    for VETH in $VETH_INTERFACES; do
        echo "Eliminando interfaz veth $VETH..."
        # Eliminar de OVS si está conectada
        if sudo ovs-vsctl list-ports "$OVS_BRIDGE" | grep -q "$VETH"; then
            sudo ovs-vsctl del-port "$OVS_BRIDGE" "$VETH" || true
        fi
        # Eliminar la interfaz
        sudo ip link delete "$VETH" 2>/dev/null || true
    done
else
    echo "No se encontraron interfaces veth."
fi

# Paso 3: Eliminar todas las interfaces VLAN
echo "Paso 3: Eliminando interfaces VLAN..."

VLAN_INTERFACES=$(ip link show | grep -E '@|vlan[0-9]+' | cut -d: -f2 | tr -d ' ' || true)
OVS_VLAN_PORTS=$(sudo ovs-vsctl list-ports "$OVS_BRIDGE" 2>/dev/null | grep -E 'vlan|veth' || true)

if [ -n "$VLAN_INTERFACES" ]; then
    for IFACE in $VLAN_INTERFACES; do
        echo "Eliminando interfaz $IFACE..."
        sudo ip link set "$IFACE" down 2>/dev/null || true
        sudo ip link delete "$IFACE" 2>/dev/null || true
        echo "Interfaz $IFACE eliminada."
    done
fi

if [ -n "$OVS_VLAN_PORTS" ]; then
    for PORT in $OVS_VLAN_PORTS; do
        echo "Eliminando puerto OVS $PORT..."
        sudo ovs-vsctl --if-exists del-port "$OVS_BRIDGE" "$PORT" || true
        echo "Puerto OVS $PORT eliminado."
    done
fi

# Paso 4: Eliminar reglas de iptables
echo "Paso 4: Eliminando reglas de iptables..."

# Limpiar reglas NAT
echo "Limpiando reglas NAT..."
sudo iptables -t nat -S | grep -E 'MASQUERADE|VLAN|vlan|192\.168\.' | while read -r line; do
    RULE=$(echo "$line" | sed 's/^-A//')
    TABLE_CHAIN=$(echo "$RULE" | awk '{print $1}')
    RULE_REST=$(echo "$RULE" | cut -d' ' -f2-)
    sudo iptables -t nat -D "$TABLE_CHAIN" $RULE_REST 2>/dev/null || true
done

# Limpiar reglas FORWARD
echo "Limpiando reglas FORWARD..."
sudo iptables -S FORWARD | grep -E 'VLAN|vlan|vm|tap|192\.168\.' | while read -r line; do
    RULE=$(echo "$line" | sed 's/^-A//')
    TABLE_CHAIN=$(echo "$RULE" | awk '{print $1}')
    RULE_REST=$(echo "$RULE" | cut -d' ' -f2-)
    sudo iptables -D "$TABLE_CHAIN" $RULE_REST 2>/dev/null || true
done

# Reiniciar políticas por defecto
sudo iptables -P FORWARD ACCEPT
sudo iptables -P INPUT ACCEPT
sudo iptables -P OUTPUT ACCEPT

# Paso 5: Limpiar reglas de flujo en OFS
echo "Paso 5: Limpiando reglas de flujo en OFS..."

TMP_FLOW_SCRIPT=$(mktemp)

cat > $TMP_FLOW_SCRIPT << 'EOFFLOW'
#!/bin/bash
echo "==== Limpiando reglas OpenFlow en $(hostname) ===="
OVS_BRIDGE="br-int"

# Eliminar todas las reglas de flujo
echo "Eliminando todas las reglas de flujo..."
ovs-ofctl del-flows "$OVS_BRIDGE"

# Añadir una regla por defecto para permitir el tráfico normal
echo "Añadiendo regla por defecto..."
ovs-ofctl add-flow "$OVS_BRIDGE" "priority=0,actions=normal"

# Mostrar reglas después de la limpieza
echo "Reglas de flujo después de la limpieza:"
ovs-ofctl dump-flows "$OVS_BRIDGE"

echo "Limpieza de reglas OpenFlow completada."
EOFFLOW

chmod +x $TMP_FLOW_SCRIPT
scp $TMP_FLOW_SCRIPT ubuntu@$OFS_NODE:/tmp/cleanup_flows.sh
ssh ubuntu@$OFS_NODE "sudo bash /tmp/cleanup_flows.sh"
rm $TMP_FLOW_SCRIPT

# Paso 6: Limpiar archivos temporales y directorios
echo "Paso 6: Limpiando archivos temporales y directorios..."

# Limpiar archivos temporales en el HeadNode
echo "Limpiando archivos temporales en HeadNode..."
sudo rm -f /tmp/create_vm.sh /tmp/add_interface.sh /tmp/cleanup_*.sh

# Limpiar en todos los workers
for WORKER in "${WORKERS[@]}"; do
    echo "Limpiando archivos temporales en $WORKER..."
    ssh ubuntu@$WORKER "sudo rm -f /tmp/create_vm.sh /tmp/add_interface.sh /tmp/cleanup_*.sh /tmp/flow_rules.sh /tmp/full_cleanup.sh"
done

# Verificar si hay procesos dnsmasq huérfanos y matarlos
echo "Verificando procesos dnsmasq huérfanos..."
ORPHANED_DNSMASQ=$(ps aux | grep dnsmasq | grep -v grep || true)
if [ -n "$ORPHANED_DNSMASQ" ]; then
    echo "Encontrados procesos dnsmasq:"
    echo "$ORPHANED_DNSMASQ"
    echo "Deteniendo procesos dnsmasq..."
    sudo pkill dnsmasq || true
fi

echo "===== Limpieza completa finalizada ====="
echo "Se han eliminado:"
echo "- Todas las VMs en los workers"
echo "- Todas las interfaces TAP y conexiones OVS"
echo "- Todos los namespaces DHCP e interfaces veth"
echo "- Todas las interfaces VLAN"
echo "- Todas las reglas de iptables relacionadas"
echo "- Todas las reglas de flujo OpenFlow personalizadas"
echo "- Archivos temporales y scripts"
echo ""
echo "El sistema ha sido restaurado a su estado inicial."