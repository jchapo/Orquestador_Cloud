#!/bin/bash

# Script para crear una topología completamente personalizada basada en un archivo JSON
# Uso: ./create_flexible_topology.sh <archivo_json>

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_json>"
    echo "Ejemplo: $0 mi_topologia.json"
    exit 1
fi

JSON_FILE=$1

# Verificar si se está ejecutando como root
#if [[ $EUID -ne 0 ]]; then
#   echo "Este script debe ejecutarse como root" 
#   exit 1
#fi

# Verificar que el archivo JSON existe
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: El archivo de configuración $JSON_FILE no existe."
    exit 1
fi

# Verificar que jq está instalado
if ! command -v jq &> /dev/null; then
    echo "El comando jq no está instalado. Instalando..."
    apt-get update && apt-get install -y jq
fi

echo "Contenido del JSON:"
cat "$JSON_FILE"


# Leer configuración del JSON
TOPOLOGY_NAME=$(jq -r '.name' "$JSON_FILE")
HEAD_NODE=$(jq -r '.nodes.head_node' "$JSON_FILE")
OFS_NODE=$(jq -r '.nodes.ofs_node' "$JSON_FILE")
WORKERS=$(jq -r '.nodes.workers | join(" ")' "$JSON_FILE")
HEAD_INTERNET_IFACE=$(jq -r '.interfaces.head_internet' "$JSON_FILE")
HEAD_OFS_IFACE=$(jq -r '.interfaces.head_ofs' "$JSON_FILE")
WORKER_OFS_IFACE=$(jq -r '.interfaces.worker_ofs' "$JSON_FILE")
ENABLE_INTERNET=$(jq -r '.settings.enable_internet' "$JSON_FILE")
ENABLE_VLAN_COMM=$(jq -r '.settings.enable_vlan_communication' "$JSON_FILE")

echo "===== Creando topología personalizada: $TOPOLOGY_NAME ====="

# Paso 1: Inicializar el HeadNode
echo "Paso 1: Inicializando HeadNode..."
sudo ./initialize_headnode.sh br-int $HEAD_OFS_IFACE
echo "HeadNode inicializado."

# Paso 2: Inicializar el nodo OFS
echo "Paso 2: Inicializando nodo OFS..."
ssh ubuntu@$OFS_NODE "sudo bash -s" < initialize_worker.sh br-int ens5 ens6 ens7 ens8
echo "Nodo OFS inicializado."

# Paso 3: Inicializar los Workers
echo "Paso 3: Inicializando Workers..."
for worker in $WORKERS; do
    echo "Inicializando $worker..."
    ssh ubuntu@$worker "sudo bash -s" < initialize_worker.sh br-int $WORKER_OFS_IFACE
    echo "$worker inicializado."
done

# Paso 4: Crear las redes VLAN en el HeadNode
echo "Paso 4: Creando redes VLAN..."
VLAN_COUNT=$(jq '.vlans | length' "$JSON_FILE")

for ((i=0; i<$VLAN_COUNT; i++)); do
    VLAN_ID=$(jq -r ".vlans[$i].id" "$JSON_FILE")
    VLAN_NETWORK=$(jq -r ".vlans[$i].network" "$JSON_FILE")
    VLAN_DHCP_RANGE=$(jq -r ".vlans[$i].dhcp_range" "$JSON_FILE")
    
    echo "Creando red VLAN $VLAN_ID con red $VLAN_NETWORK..."
    ./create_network.sh vlan$VLAN_ID $VLAN_ID $VLAN_NETWORK $VLAN_DHCP_RANGE
    echo "Red VLAN $VLAN_ID creada."
    
    # Configurar acceso a Internet para la VLAN si está habilitado
    if [ "$ENABLE_INTERNET" = "true" ]; then
        echo "Configurando acceso a Internet para VLAN $VLAN_ID..."
        sudo ./internet_access.sh $VLAN_ID $HEAD_INTERNET_IFACE
        echo "Acceso a Internet configurado para VLAN $VLAN_ID."
    fi
done

# Paso 5: Permitir comunicación entre las VLANs (si está habilitado)
if [ "$ENABLE_VLAN_COMM" = "true" ]; then
    echo "Paso 5: Configurando comunicación entre VLANs..."
    
    # Obtener la lista de IDs de VLAN
    VLAN_IDS=($(jq -r '.vlans[].id' "$JSON_FILE"))
    
    # Permitir comunicación entre todas las combinaciones de VLANs
    for ((i=0; i<${#VLAN_IDS[@]}; i++)); do
        for ((j=i+1; j<${#VLAN_IDS[@]}; j++)); do
            sudo ./connect_vlans.sh ${VLAN_IDS[$i]} ${VLAN_IDS[$j]}
            echo "Comunicación entre VLANs ${VLAN_IDS[$i]} y ${VLAN_IDS[$j]} configurada."
        done
    done
else
    echo "Paso 5: Comunicación entre VLANs deshabilitada."
fi

# Paso 6: Crear VMs en los Workers
echo "Paso 6: Creando VMs en los Workers..."

# Crear un mapa de nombres de VM a índices
VM_COUNT=$(jq '.vms | length' "$JSON_FILE")
declare -A VM_INDICES
declare -A VM_MAC_ADDRESSES
declare -A VM_VLANS
declare -A VM_WORKERS

for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    VM_INDICES[$VM_NAME]=$((i+1))
    VM_MAC_ADDRESSES[$VM_NAME]=$(jq -r ".vms[$i].mac" "$JSON_FILE")
    VM_VLANS[$VM_NAME]=$(jq -r ".vms[$i].vlan" "$JSON_FILE")
    VM_WORKERS[$VM_NAME]=$(jq -r ".vms[$i].worker" "$JSON_FILE")
done

# Crear las VMs en los workers correspondientes
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE")
    VLAN_ID=$(jq -r ".vms[$i].vlan" "$JSON_FILE")
    VNC_PORT=$(jq -r ".vms[$i].vnc_port" "$JSON_FILE")
    MAC_ADDRESS=$(jq -r ".vms[$i].mac" "$JSON_FILE")
    
    # Obtener el worker real
    WORKER_ADDRESS=$(echo $WORKERS | cut -d' ' -f$WORKER_IDX)
    
    echo "Creando $VM_NAME en $WORKER_ADDRESS (VLAN: $VLAN_ID, MAC: $MAC_ADDRESS)..."
    ssh ubuntu@$WORKER_ADDRESS "sudo bash -s" < create_vm.sh $VM_NAME br-int $VLAN_ID $VNC_PORT "$MAC_ADDRESS"
    echo "$VM_NAME creada con éxito."
done

# Paso 7: Configurar reglas de flujo en OFS basadas en las conexiones definidas
echo "Paso 7: Configurando reglas de flujo en OFS basadas en conexiones..."

# Crear un script temporal con las reglas de flujo
TMP_FLOW_SCRIPT=$(mktemp)

cat > $TMP_FLOW_SCRIPT << 'EOF'
#!/bin/bash
# Limpiar reglas existentes
ovs-ofctl del-flows br-int

# Permitir tráfico DHCP (alta prioridad)
ovs-ofctl add-flow br-int "priority=1000,udp,tp_dst=67,actions=normal"
ovs-ofctl add-flow br-int "priority=1000,udp,tp_dst=68,actions=normal"

# Permitir ARP (media-alta prioridad pero solo broadcasts)
ovs-ofctl add-flow br-int "priority=900,dl_dst=ff:ff:ff:ff:ff:ff,arp,actions=normal"

# Reglas específicas para las conexiones
EOF

# Configurar reglas de flujo para cada conexión definida
CONNECTION_COUNT=$(jq '.connections | length' "$JSON_FILE")

for ((i=0; i<$CONNECTION_COUNT; i++)); do
    FROM_VM=$(jq -r ".connections[$i].from" "$JSON_FILE")
    TO_VM=$(jq -r ".connections[$i].to" "$JSON_FILE")
    
    FROM_MAC=${VM_MAC_ADDRESSES[$FROM_VM]}
    TO_MAC=${VM_MAC_ADDRESSES[$TO_VM]}
    FROM_VLAN=${VM_VLANS[$FROM_VM]}
    TO_VLAN=${VM_VLANS[$TO_VM]}
    
    echo "# Conexión de $FROM_VM a $TO_VM" >> $TMP_FLOW_SCRIPT
    
    # Si están en la misma VLAN, es una regla simple
    if [ "$FROM_VLAN" = "$TO_VLAN" ]; then
        echo "ovs-ofctl add-flow br-int \"table=0,priority=500,dl_vlan=$FROM_VLAN,dl_src=$FROM_MAC,dl_dst=$TO_MAC,actions=output:normal\"" >> $TMP_FLOW_SCRIPT
    else
        # Si están en diferentes VLANs, necesitamos cambiar la VLAN
        echo "ovs-ofctl add-flow br-int \"table=0,priority=600,dl_vlan=$FROM_VLAN,dl_src=$FROM_MAC,dl_dst=$TO_MAC,actions=mod_vlan_vid:$TO_VLAN,output:normal\"" >> $TMP_FLOW_SCRIPT
    fi
done

# Configurar acceso a Internet para VMs específicas (solo si el acceso a Internet está habilitado)
if [ "$ENABLE_INTERNET" = "true" ]; then
    echo "# Configuración de acceso a Internet para VMs específicas" >> $TMP_FLOW_SCRIPT
    
    # Obtener la lista de VMs con acceso a Internet
    VM_INTERNET_ACCESS=($(jq -r '.vm_internet_access[]' "$JSON_FILE" 2>/dev/null))
    
    if [ ${#VM_INTERNET_ACCESS[@]} -gt 0 ]; then
        echo "# VMs con acceso a Internet: ${VM_INTERNET_ACCESS[*]}" >> $TMP_FLOW_SCRIPT
        
        # Para cada VM con acceso a Internet, crear reglas para permitir el tráfico hacia la interfaz de Internet
        for vm in "${VM_INTERNET_ACCESS[@]}"; do
            if [ -n "${VM_MAC_ADDRESSES[$vm]}" ] && [ -n "${VM_VLANS[$vm]}" ]; then
                VM_MAC=${VM_MAC_ADDRESSES[$vm]}
                VM_VLAN=${VM_VLANS[$vm]}
                
                echo "# Permitir acceso a Internet para $vm" >> $TMP_FLOW_SCRIPT
                echo "ovs-ofctl add-flow br-int \"table=0,priority=300,dl_vlan=$VM_VLAN,dl_src=$VM_MAC,actions=normal\"" >> $TMP_FLOW_SCRIPT
            fi
        done
    fi
fi

# Regla por defecto para descartar el resto del tráfico no explícitamente permitido
echo "# Descartar el resto del tráfico" >> $TMP_FLOW_SCRIPT
echo "ovs-ofctl add-flow br-int \"priority=1,actions=drop\"" >> $TMP_FLOW_SCRIPT

# Mostrar las reglas que se van a aplicar
echo "# Reglas de flujo configuradas:" >> $TMP_FLOW_SCRIPT
echo "ovs-ofctl dump-flows br-int" >> $TMP_FLOW_SCRIPT

# Ejecutar el script de configuración de flujos en el nodo OFS
chmod +x $TMP_FLOW_SCRIPT
scp $TMP_FLOW_SCRIPT ubuntu@$OFS_NODE:/tmp/flow_rules.sh
ssh ubuntu@$OFS_NODE "sudo bash /tmp/flow_rules.sh"

# Limpiar archivos temporales
rm $TMP_FLOW_SCRIPT

echo "===== Topología personalizada creada con éxito ====="
echo "Nombre de la topología: $TOPOLOGY_NAME"
echo "Se han creado:"
echo "- $VLAN_COUNT redes VLAN"
for ((i=0; i<$VLAN_COUNT; i++)); do
    VLAN_ID=$(jq -r ".vlans[$i].id" "$JSON_FILE")
    echo "  - VLAN $VLAN_ID"
done

echo "- $VM_COUNT VMs distribuidas en ${#WORKERS[@]} Workers"
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE")
    VLAN_ID=$(jq -r ".vms[$i].vlan" "$JSON_FILE")
    echo "  - $VM_NAME en Worker $WORKER_IDX (VLAN $VLAN_ID)"
done

echo "- $CONNECTION_COUNT conexiones configuradas entre VMs"
for ((i=0; i<$CONNECTION_COUNT; i++)); do
    FROM_VM=$(jq -r ".connections[$i].from" "$JSON_FILE")
    TO_VM=$(jq -r ".connections[$i].to" "$JSON_FILE")
    echo "  - $FROM_VM -> $TO_VM"
done

if [ "$ENABLE_INTERNET" = "true" ] && [ ${#VM_INTERNET_ACCESS[@]} -gt 0 ]; then
    echo "- VMs con acceso a Internet: ${VM_INTERNET_ACCESS[*]}"
fi

echo "La topología está lista para su uso."