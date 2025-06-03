#!/bin/bash

# Script para crear una topología completamente personalizada basada en un archivo JSON
# Versión actualizada para soportar VLANs por conexión
# Uso: ./create_flexible_topology.sh <archivo_json>

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_json>"
    echo "Ejemplo: $0 mi_topologia.json"
    exit 1
fi

JSON_FILE=$1

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

# Verificar que el JSON es válido
if ! jq . "$JSON_FILE" > /dev/null 2>&1; then
    echo "Error: El archivo JSON no es válido."
    exit 1
fi

# Obtener el directorio actual (donde se ejecuta el script)
CURRENT_DIR=$(pwd)

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
ssh ubuntu@$OFS_NODE "sudo bash -s" < ./initialize_worker.sh br-int ens5 ens6 ens7 ens8
echo "Nodo OFS inicializado."

# Paso 3: Inicializar los Workers
echo "Paso 3: Inicializando Workers..."
for worker in $WORKERS; do
    echo "Inicializando $worker..."
    ssh ubuntu@$worker "sudo bash -s" < ./initialize_worker.sh br-int $WORKER_OFS_IFACE
    echo "$worker inicializado."
done

# Paso 4: Recopilar todas las VLANs únicas de las conexiones
echo "Paso 4: Identificando VLANs únicas en las conexiones..."

# Extraer todos los IDs de VLAN de las conexiones
VLAN_IDS=$(jq -r '.connections[].vlan_id' "$JSON_FILE" | sort -n | uniq)

# Crear un array con las VLANs únicas
readarray -t UNIQUE_VLANS <<< "$VLAN_IDS"

echo "VLANs únicas encontradas: ${UNIQUE_VLANS[*]}"

# Paso 5: Crear solo la red VLAN 10 si el acceso a Internet está habilitado
echo "Paso 5: Creando red de Internet (solo VLAN 10)..."

if [ "$ENABLE_INTERNET" = "true" ]; then
    VLAN_ID=10
    VLAN_NETWORK="192.168.10.0/24"
    VLAN_DHCP_RANGE="192.168.10.10,192.168.10.200"
    
    echo "Creando red VLAN 10 con red $VLAN_NETWORK..."
    ./create_network.sh vlan$VLAN_ID $VLAN_ID $VLAN_NETWORK $VLAN_DHCP_RANGE

    echo "Configurando acceso a Internet para VLAN 10..."
    sudo ./internet_access.sh $VLAN_ID $HEAD_INTERNET_IFACE
    echo "Acceso a Internet configurado para VLAN 10."
else
    echo "El acceso a Internet está deshabilitado. No se crea red para VLAN 10."
fi

# Ahora crear redes para cada VLAN única identificada
for VLAN_ID in "${UNIQUE_VLANS[@]}"; do
    if [ -n "$VLAN_ID" ] && [ "$VLAN_ID" != "null" ]; then
        # Generar una red única para esta VLAN
        # Usar el tercer octeto de la dirección IP basado en VLAN_ID para evitar colisiones
        VLAN_NETWORK="192.168.${VLAN_ID}.0/24"
        VLAN_DHCP_RANGE="192.168.${VLAN_ID}.10,192.168.${VLAN_ID}.200"
        
        echo "Creando red para VLAN $VLAN_ID con red $VLAN_NETWORK..."
        ./create_network.sh vlan$VLAN_ID $VLAN_ID $VLAN_NETWORK $VLAN_DHCP_RANGE
        echo "Red para VLAN $VLAN_ID creada con éxito."
    fi
done

# Paso 6: Permitir comunicación entre las VLANs (si está habilitado)
if [ "$ENABLE_VLAN_COMM" = "true" ]; then
    echo "Paso 6: Configurando comunicación entre VLANs..."
    
    # Permitir comunicación entre todas las combinaciones de VLANs
    for ((i=0; i<${#UNIQUE_VLANS[@]}; i++)); do
        for ((j=i+1; j<${#UNIQUE_VLANS[@]}; j++)); do
            if [ -n "${UNIQUE_VLANS[$i]}" ] && [ -n "${UNIQUE_VLANS[$j]}" ] && [ "${UNIQUE_VLANS[$i]}" != "null" ] && [ "${UNIQUE_VLANS[$j]}" != "null" ]; then
                sudo ./connect_vlans.sh ${UNIQUE_VLANS[$i]} ${UNIQUE_VLANS[$j]}
                echo "Comunicación entre VLANs ${UNIQUE_VLANS[$i]} y ${UNIQUE_VLANS[$j]} configurada."
            fi
        done
    done
else
    echo "Paso 6: Comunicación entre VLANs deshabilitada."
fi

# Paso 7: Crear las VMs en los Workers

# Leer lista de VMs con acceso a Internet
VM_INTERNET_ACCESS=($(jq -r '.vm_internet_access[]' "$JSON_FILE" 2>/dev/null))

# Inicializar las estructuras de datos para las VMs
declare -A VM_VLANS
declare -A VM_MAC_ADDRESSES
declare -A VM_VNC_PORTS
declare -A VM_WORKER_INFO

# Validar VM_COUNT
VM_COUNT=$(jq '.vms | length' "$JSON_FILE")
if [[ ! "$VM_COUNT" =~ ^[0-9]+$ ]] || [ "$VM_COUNT" -eq 0 ]; then
    echo "Error: No se encontraron VMs en el archivo JSON o VM_COUNT es inválido: $VM_COUNT"
    exit 1
fi

echo "Número de VMs: $VM_COUNT"

# Inicializar VM_VLANS para cada VM y almacenar MACs y VNC Ports
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    VM_MAC_ADDRESSES[$VM_NAME]=$(jq -r ".vms[$i].mac" "$JSON_FILE")
    VM_VLANS[$VM_NAME]=""
    
    # Guardar el VNC port y la info del worker
    VNC_PORT=$(jq -r ".vms[$i].vnc_port" "$JSON_FILE")
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE")
    
    # Ajustar VNC_PORT para que esté dentro del rango válido (5900-65535)
    if [ "$VNC_PORT" -lt 5900 ]; then
        VNC_PORT_REAL=$((5900 + VNC_PORT))
    else
        VNC_PORT_REAL=$VNC_PORT
    fi
    
    VM_VNC_PORTS[$VM_NAME]=$VNC_PORT_REAL
    
    # Worker real (convertir índice a dirección)
    WORKER_ADDRESS=$(echo $WORKERS | cut -d' ' -f$WORKER_IDX)
    VM_WORKER_INFO[$VM_NAME]="$WORKER_IDX:$WORKER_ADDRESS"
done

# Recopilar las VLANs para cada VM desde las conexiones
CONNECTION_COUNT=$(jq '.connections | length' "$JSON_FILE")
for ((i=0; i<$CONNECTION_COUNT; i++)); do
    FROM_VM=$(jq -r ".connections[$i].from" "$JSON_FILE")
    TO_VM=$(jq -r ".connections[$i].to" "$JSON_FILE")
    CONN_VLAN=$(jq -r ".connections[$i].vlan_id" "$JSON_FILE")
    
    # Añadir la VLAN a ambas VMs de la conexión
    VM_VLANS[$FROM_VM]="${VM_VLANS[$FROM_VM]} $CONN_VLAN"
    VM_VLANS[$TO_VM]="${VM_VLANS[$TO_VM]} $CONN_VLAN"
done

# Limpiar las listas de VLANs (eliminar duplicados y espacios extras)
for VM_NAME in "${!VM_VLANS[@]}"; do
    # Convertir lista con espacios a lista única ordenada
    CLEAN_VLANS=$(echo "${VM_VLANS[$VM_NAME]}" | tr ' ' '\n' | sort -n | uniq | grep -v '^$' | tr '\n' ' ')
    VM_VLANS[$VM_NAME]="$CLEAN_VLANS"
    echo "VM $VM_NAME está conectada a las VLANs: ${VM_VLANS[$VM_NAME]}"
done

echo "Paso 7: Creando VMs en los Workers..."

# Crear las VMs en los workers correspondientes
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE")
    VNC_PORT=$(jq -r ".vms[$i].vnc_port" "$JSON_FILE")
    
    # Ajustar VNC_PORT para que esté dentro del rango válido (5900-65535)
    if [ "$VNC_PORT" -lt 5900 ]; then
        VNC_PORT_REAL=$((5900 + VNC_PORT))
    else
        VNC_PORT_REAL=$VNC_PORT
    fi
    
    MAC_ADDRESS=${VM_MAC_ADDRESSES[$VM_NAME]}
    
    # Datos del flavor
    CPU=$(jq -r ".vms[$i].flavor.cpu" "$JSON_FILE")
    RAM=$(jq -r ".vms[$i].flavor.ram" "$JSON_FILE")
    DISK=$(jq -r ".vms[$i].flavor.disk" "$JSON_FILE")
    IMAGE=$(jq -r ".vms[$i].flavor.image // \"ubuntu.img\"" "$JSON_FILE")  # Default a ubuntu.img si no está definido

    # Worker real (convertir índice a dirección)
    WORKER_ADDRESS=$(echo $WORKERS | cut -d' ' -f$WORKER_IDX)

    # Copiar scripts
    scp ./create_vm.sh ubuntu@$WORKER_ADDRESS:/tmp/
    scp ./add_interface.sh ubuntu@$WORKER_ADDRESS:/tmp/

    echo "Creando $VM_NAME en $WORKER_ADDRESS con CPU=$CPU, RAM=$RAM, DISK=$DISK, IMG=$IMAGE..."

    # Crear VM sin interfaces
    ssh ubuntu@$WORKER_ADDRESS "sudo bash /tmp/create_vm.sh \"$VM_NAME\" \"$VNC_PORT_REAL\" \"$MAC_ADDRESS\" \"$CPU\" \"$RAM\" \"$DISK\" \"$IMAGE\""

    # Interfaz para Internet (VLAN 10) si es necesario
    if printf '%s\n' "${VM_INTERNET_ACCESS[@]}" | grep -q -x "$VM_NAME"; then
        echo "Añadiendo interfaz para acceso a Internet (VLAN 10) a $VM_NAME..."
        ssh ubuntu@$WORKER_ADDRESS "sudo bash /tmp/add_interface.sh \"$VM_NAME\" br-int 10"
    fi

    # Añadir interfaces para todas las VLANs de la VM
    FIRST_VLAN=1
    for VLAN in ${VM_VLANS[$VM_NAME]}; do
        if [ -n "$VLAN" ] && [ "$VLAN" != "null" ]; then
            echo "Añadiendo interfaz para VLAN $VLAN a $VM_NAME..."
            
            # Para la primera VLAN usar la MAC principal, para las demás generar automáticamente
            if [ $FIRST_VLAN -eq 1 ]; then
                ssh ubuntu@$WORKER_ADDRESS "sudo bash /tmp/add_interface.sh \"$VM_NAME\" br-int \"$VLAN\" \"$MAC_ADDRESS\""
                FIRST_VLAN=0
            else
                ssh ubuntu@$WORKER_ADDRESS "sudo bash /tmp/add_interface.sh \"$VM_NAME\" br-int \"$VLAN\""
            fi
        fi
    done

    # Una vez añadidas todas las interfaces, iniciar la VM
    echo "Iniciando VM $VM_NAME..."
    ssh ubuntu@$WORKER_ADDRESS "sudo virsh start \"$VM_NAME\""

    echo "$VM_NAME creada con éxito."
done

# Paso 8: Configurar reglas de flujo en OFS basadas en las conexiones definidas
echo "Paso 8: Configurando reglas de flujo en OFS basadas en conexiones..."

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
    CONN_VLAN=$(jq -r ".connections[$i].vlan_id" "$JSON_FILE")
    
    FROM_MAC=${VM_MAC_ADDRESSES[$FROM_VM]}
    TO_MAC=${VM_MAC_ADDRESSES[$TO_VM]}
    
    echo "# Conexión de $FROM_VM a $TO_VM (VLAN $CONN_VLAN)" >> $TMP_FLOW_SCRIPT
    
    # Verificar que las MACs son válidas antes de usarlas
    if [[ "$FROM_MAC" =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]] && 
       [[ "$TO_MAC" =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]]; then
        # Reglas de flujo para permitir comunicación en la VLAN específica
        echo "ovs-ofctl add-flow br-int \"table=0,priority=500,dl_vlan=$CONN_VLAN,dl_src=$FROM_MAC,dl_dst=$TO_MAC,actions=normal\"" >> $TMP_FLOW_SCRIPT
    else
        echo "# ADVERTENCIA: Dirección MAC inválida para $FROM_VM o $TO_VM - Regla omitida" >> $TMP_FLOW_SCRIPT
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
            if [ -n "${VM_MAC_ADDRESSES[$vm]}" ]; then
                VM_MAC=${VM_MAC_ADDRESSES[$vm]}
                
                if [[ "$VM_MAC" =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]]; then
                    for VM_VLAN in ${VM_VLANS[$vm]}; do
                        echo "# Permitir acceso a Internet para $vm en VLAN $VM_VLAN" >> $TMP_FLOW_SCRIPT
                        echo "ovs-ofctl add-flow br-int \"table=0,priority=300,dl_vlan=$VM_VLAN,dl_src=$VM_MAC,actions=normal\"" >> $TMP_FLOW_SCRIPT
                    done
                else
                    echo "# ADVERTENCIA: Dirección MAC inválida para $vm - Regla de Internet omitida" >> $TMP_FLOW_SCRIPT
                fi
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
echo "- ${#UNIQUE_VLANS[@]} redes VLAN únicas"
for VLAN_ID in "${UNIQUE_VLANS[@]}"; do
    if [ -n "$VLAN_ID" ] && [ "$VLAN_ID" != "null" ]; then
        echo "  - VLAN $VLAN_ID"
    fi
done

WORKER_COUNT=$(echo "$WORKERS" | wc -w)
echo "- $VM_COUNT VMs distribuidas en $WORKER_COUNT Workers"
for ((i=0; i<$VM_COUNT; i++)); do
    VM_NAME=$(jq -r ".vms[$i].name" "$JSON_FILE")
    WORKER_IDX=$(jq -r ".vms[$i].worker" "$JSON_FILE")
    WORKER_ADDRESS=$(echo $WORKERS | cut -d' ' -f$WORKER_IDX)
    VNC_PORT=$(jq -r ".vms[$i].vnc_port" "$JSON_FILE")
    if [ "$VNC_PORT" -lt 5900 ]; then
        VNC_PORT_REAL=$((5900 + VNC_PORT))
    else
        VNC_PORT_REAL=$VNC_PORT
    fi
    
    CPU=$(jq -r ".vms[$i].flavor.cpu" "$JSON_FILE")
    RAM=$(jq -r ".vms[$i].flavor.ram" "$JSON_FILE")
    DISK=$(jq -r ".vms[$i].flavor.disk" "$JSON_FILE")
    
    INTERNET_ACCESS=""
    if printf '%s\n' "${VM_INTERNET_ACCESS[@]}" | grep -q -x "$VM_NAME"; then
        INTERNET_ACCESS=" (Con acceso a Internet)"
    fi
    
    echo "  - $VM_NAME en Worker $WORKER_IDX ($WORKER_ADDRESS) - VNC: $VNC_PORT_REAL - CPU: $CPU, RAM: ${RAM}MB, Disk: ${DISK}GB - VLANs: ${VM_VLANS[$VM_NAME]}$INTERNET_ACCESS"
done

echo "- $CONNECTION_COUNT conexiones configuradas entre VMs"
for ((i=0; i<$CONNECTION_COUNT; i++)); do
    FROM_VM=$(jq -r ".connections[$i].from" "$JSON_FILE")
    TO_VM=$(jq -r ".connections[$i].to" "$JSON_FILE")
    VLAN_ID=$(jq -r ".connections[$i].vlan_id" "$JSON_FILE")
    echo "  - $FROM_VM -> $TO_VM (VLAN $VLAN_ID)"
done

if [ "$ENABLE_INTERNET" = "true" ] && [ ${#VM_INTERNET_ACCESS[@]} -gt 0 ]; then
    echo "- VMs con acceso a Internet: ${VM_INTERNET_ACCESS[*]}"
fi

echo ""
echo "Para conectarte a una VM mediante VNC:"
echo "1. Establece un túnel SSH al worker: ssh -L <puerto_local>:<worker_ip>:<puerto_vnc> ubuntu@<worker_ip>"
echo "2. Conecta tu cliente VNC a localhost:<puerto_local>"
echo ""
echo "La topología está lista para su uso."