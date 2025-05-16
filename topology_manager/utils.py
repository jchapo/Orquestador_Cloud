"""
Funciones de utilidad para la gestión de topologías

Este módulo contiene funciones de utilidad como generación de direcciones MAC,
formateo de pantalla, etc.
"""

import os
import random

def clear_screen():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_mac(worker_id, vm_num):
    """Genera una dirección MAC única"""
    mac_prefix = "52:54:00"
    return f"{mac_prefix}:{worker_id:02x}:{vm_num:02x}:{random.randint(0, 255):02x}"

def print_header(title):
    """Imprime un encabezado formateado"""
    clear_screen()
    print("="*80)
    print(f"{title:^80}")
    print("="*80)
    print()

def print_vms(topology):
    """Imprime la lista de VMs disponibles"""
    if not topology.vms:
        print("No hay VMs definidas.")
        return
    
    print("\nVMs disponibles:")
    print("-" * 60)
    print(f"{'Nombre':<10} {'Worker':<10} {'VNC Port':<10} {'MAC':<20}")
    print("-" * 60)
    
    for vm in topology.vms:
        print(f"{vm['name']:<10} {vm['worker']:<10} {vm['vnc_port']:<10} {vm['mac']:<20}")
    
    print("-" * 60)

def print_connections(topology):
    """Imprime las conexiones entre VMs"""
    if not topology.connections:
        print("No hay conexiones definidas.")
        return
    
    print("\\nConexiones:")
    print("-" * 40)
    print(f"{'#':<4} {'Origen':<15} {'Destino':<15} {'VLAN':<6}")
    print("-" * 40)
    
    for i, conn in enumerate(topology.connections):
        vlan_id = conn.get('vlan_id', 'N/A')
        print(f"{i+1:<4} {conn['from']:<15} {conn['to']:<15} {vlan_id:<6}")
    
    print("-" * 40)

def get_user_input(prompt, default=None, validator=None):
    """
    Solicita entrada al usuario con validación opcional
    
    Args:
        prompt: Mensaje a mostrar al usuario
        default: Valor por defecto si el usuario no ingresa nada
        validator: Función que valida la entrada del usuario
        
    Returns:
        La entrada del usuario o el valor por defecto
    """
    while True:
        if default is not None:
            result = input(f"{prompt} [default: {default}]: ") or default
        else:
            result = input(f"{prompt}: ")
        
        if validator is None:
            return result
        
        try:
            return validator(result)
        except Exception as e:
            print(f"Error: {e}")
            continue

def validate_int(value):
    """Valida que el valor sea un entero"""
    try:
        return int(value)
    except ValueError:
        raise ValueError("Se espera un número entero")

def validate_range(value, min_val, max_val):
    """Valida que el valor esté en el rango especificado"""
    val = validate_int(value)
    if val < min_val or val > max_val:
        raise ValueError(f"El valor debe estar entre {min_val} y {max_val}")
    return val

def validate_vm_name(value):
    """Valida que el nombre de la VM tenga el formato correcto"""
    if not value.startswith("vm"):
        raise ValueError("El nombre de la VM debe comenzar con 'vm'")
    try:
        int(value[2:])
    except ValueError:
        raise ValueError("El nombre de la VM debe ser 'vm' seguido de un número")
    return value

def parse_vm_list(input_string, available_vms=None):
    """
    Analiza una cadena de entrada que contiene una lista de VMs
    
    Args:
        input_string: Cadena con índices o nombres de VMs separados por comas
        available_vms: Lista de nombres de VMs disponibles (opcional)
        
    Returns:
        Lista de nombres de VMs
    """
    if not input_string:
        return []
    
    result = []
    
    # Comprobar si es "todos"
    if input_string.lower() == "todos" and available_vms:
        return available_vms
    
    # Intentar interpretar como índices
    try:
        indices = [int(idx.strip()) - 1 for idx in input_string.split(',') if idx.strip()]
        if available_vms:
            result = [available_vms[idx] for idx in indices if 0 <= idx < len(available_vms)]
        else:
            result = [f"vm{idx+1}" for idx in indices]
    except ValueError:
        # Interpretar como nombres de VM
        result = [vm.strip() for vm in input_string.split(',') if vm.strip()]
        
        # Validar formato de nombres
        for vm in result[:]:
            try:
                validate_vm_name(vm)
            except ValueError:
                result.remove(vm)
    
    return result

def confirm_action(message="¿Está seguro?"):
    """
    Solicita confirmación al usuario
    
    Args:
        message: Mensaje a mostrar
        
    Returns:
        True si el usuario confirma, False en caso contrario
    """
    response = input(f"{message} (s/n): ").lower()
    return response in ['s', 'si', 'sí', 'y', 'yes']

def find_vm_by_name(topology, vm_name):
    """
    Busca una VM por su nombre en la topología
    
    Args:
        topology: Objeto de topología
        vm_name: Nombre de la VM a buscar
        
    Returns:
        Diccionario con la información de la VM o None si no se encuentra
    """
    for vm in topology.vms:
        if vm["name"] == vm_name:
            return vm
    return None

def format_connection_summary(topology):
    """
    Genera un resumen de las conexiones agrupadas por VM
    
    Args:
        topology: Objeto de topología
        
    Returns:
        Cadena con el resumen de conexiones
    """
    if not topology.connections:
        return "No hay conexiones definidas."
    
    # Agrupar conexiones por VM de origen
    connections_by_vm = {}
    for conn in topology.connections:
        from_vm = conn["from"]
        to_vm = conn["to"]
        
        if from_vm not in connections_by_vm:
            connections_by_vm[from_vm] = []
        
        connections_by_vm[from_vm].append(to_vm)
    
    # Generar resumen
    summary = []
    for vm, connections in sorted(connections_by_vm.items()):
        summary.append(f"{vm} -> {', '.join(sorted(connections))}")
    
    return "\n".join(summary)

def generate_topology_summary(topology):
    """
    Genera un resumen de la topología
    
    Args:
        topology: Objeto de topología
        
    Returns:
        Cadena con el resumen de la topología
    """
    vm_count = len(topology.vms)
    connection_count = len(topology.connections)
    vlan_count = len(topology.vlans)
    
    # Contar VMs por VLAN
    vms_by_vlan = {}
    for vm in topology.vms:
        vlan = vm["vlan"]
        if vlan not in vms_by_vlan:
            vms_by_vlan[vlan] = 0
        vms_by_vlan[vlan] += 1
    
    # Contar VMs por worker
    vms_by_worker = {}
    for vm in topology.vms:
        worker = vm["worker"]
        if worker not in vms_by_worker:
            vms_by_worker[worker] = 0
        vms_by_worker[worker] += 1
    
    # Generar resumen
    summary = [
        f"Nombre: {topology.name}",
        f"Total de VMs: {vm_count}",
        f"Total de conexiones: {connection_count}",
        f"Total de VLANs: {vlan_count}",
        "\nVMs por VLAN:"
    ]
    
    for vlan, count in sorted(vms_by_vlan.items()):
        summary.append(f"  VLAN {vlan}: {count} VMs")
    
    summary.append("\nVMs por Worker:")
    for worker, count in sorted(vms_by_worker.items()):
        summary.append(f"  Worker {worker}: {count} VMs")
    
    # Añadir información de acceso a Internet
    if topology.vm_internet_access:
        summary.append("\nVMs con acceso a Internet:")
        for vm in sorted(topology.vm_internet_access):
            summary.append(f"  {vm}")
    else:
        summary.append("\nNinguna VM tiene acceso a Internet configurado.")
    
    return "\n".join(summary)

def validate_vlan_id(value, min_val=100, max_val=200):
    """
    Valida que el ID de VLAN esté en el rango especificado
    
    Args:
        value: Valor a validar
        min_val: Valor mínimo permitido (por defecto 100)
        max_val: Valor máximo permitido (por defecto 200)
        
    Returns:
        El ID de VLAN validado
    """
    # Si está vacío, usar el valor predeterminado
    if not value:
        return min_val
    
    # Validar que sea un entero en el rango
    val = validate_int(value)
    if val < min_val or val > max_val:
        raise ValueError(f"El ID de VLAN debe estar entre {min_val} y {max_val}")
    return val
