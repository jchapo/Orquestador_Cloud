"""
Script para eliminar una topología

Este script se encarga de eliminar todas las máquinas virtuales y recursos
definidos en un archivo de topología JSON.
"""

#!/bin/bash

# Verificar argumentos
if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo_json>"
    exit 1
fi

JSON_FILE=$1
echo "Eliminando topología definida en $JSON_FILE"

# Verificar si jq está instalado
if ! command -v jq &> /dev/null; then
    echo "Error: Se requiere jq para procesar el archivo JSON."
    echo "Por favor, instale jq con 'sudo apt-get install jq'"
    exit 1
fi

# Leer las VMs del archivo JSON
VMS=$(jq -r '.vms[].name' $JSON_FILE 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "Error al leer el archivo JSON. Asegúrese de que es un archivo JSON válido."
    exit 1
fi

# Eliminar cada VM
for VM in $VMS; do
    echo "Eliminando VM $VM"
    
    # Parar la VM si está ejecutándose
    virsh destroy $VM 2>/dev/null || true
    
    # Eliminar la VM completamente
    virsh undefine $VM --remove-all-storage 2>/dev/null || true
done

echo "Topología eliminada con éxito."
echo "Nota: Este script solo elimina las VMs. Las configuraciones de red y otros recursos"
echo "pueden requerir limpieza manual adicional."

exit 0