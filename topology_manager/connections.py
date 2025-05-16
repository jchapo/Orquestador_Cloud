"""
Módulo para la gestión de conexiones entre VMs

Este módulo contiene funciones para agregar, eliminar y modificar conexiones
entre máquinas virtuales en una topología.
"""

from .utils import print_connections

def list_connections(topology):
    """Muestra una lista numerada de las conexiones existentes"""
    if not topology.connections:
        print("No hay conexiones definidas.")
        return
    
    print("\nConexiones existentes:")
    print("-" * 40)
    print(f"{'#':<4} {'Origen':<15} {'Destino':<15}")
    print("-" * 40)
    
    for i, conn in enumerate(topology.connections):
        print(f"{i+1:<4} {conn['from']:<15} {conn['to']:<15}")
    
    print("-" * 40)

def add_connection(topology, from_vm=None, to_vm=None, bidirectional=True, vlan_id=None):
    """
    Agrega una nueva conexión entre VMs existentes
    
    Args:
        topology: Objeto de topología
        from_vm: Nombre de la VM de origen (opcional)
        to_vm: Nombre de la VM de destino (opcional)
        bidirectional: Si True, agrega también la conexión inversa
        vlan_id: ID de VLAN para esta conexión (opcional)
        
    Returns:
        True si la conexión se agregó con éxito, False en caso contrario
    """
    # Mostrar lista de VMs disponibles
    if not from_vm or not to_vm:
        print("\nVMs disponibles:")
        for i, vm in enumerate(topology.vms):
            print(f"{i+1}. {vm['name']} (Worker: {vm['worker']}, VLAN: {vm['vlan']})")
    
    try:
        # Obtener VM de origen
        if not from_vm:
            from_idx = int(input("\nSeleccione la VM de origen (número): ")) - 1
            if from_idx < 0 or from_idx >= len(topology.vms):
                print("Índice fuera de rango.")
                return False
            from_vm = topology.vms[from_idx]['name']
        
        # Obtener VM de destino
        if not to_vm:
            to_idx = int(input("Seleccione la VM de destino (número): ")) - 1
            if to_idx < 0 or to_idx >= len(topology.vms):
                print("Índice fuera de rango.")
                return False
            to_vm = topology.vms[to_idx]['name']
        
        # Verificar que las VMs existan
        from_vm_exists = False
        to_vm_exists = False
        for vm in topology.vms:
            if vm['name'] == from_vm:
                from_vm_exists = True
            if vm['name'] == to_vm:
                to_vm_exists = True
        
        if not from_vm_exists:
            print(f"Error: La VM de origen '{from_vm}' no existe.")
            return False
        
        if not to_vm_exists:
            print(f"Error: La VM de destino '{to_vm}' no existe.")
            return False
        
        # Verificar que la conexión no exista ya
        for conn in topology.connections:
            if conn['from'] == from_vm and conn['to'] == to_vm:
                print(f"La conexión {from_vm} -> {to_vm} ya existe.")
                return False
        
        # Si no se proporcionó un ID de VLAN, generarlo automáticamente
        if vlan_id is None:
            # Encontrar el próximo ID de VLAN disponible
            used_vlans = [conn.get('vlan_id') for conn in topology.connections if 'vlan_id' in conn]
            vlan_id = 100  # VLAN inicial
            while vlan_id in used_vlans and vlan_id <= 4094:  # 4094 es el máximo ID de VLAN
                vlan_id += 1
            
            if vlan_id > 4094:
                print("Error: Se ha alcanzado el límite de VLANs disponibles.")
                return False
        else:
            # Verificar que el ID de VLAN proporcionado sea válido
            try:
                vlan_id = int(vlan_id)
                if vlan_id < 1 or vlan_id > 4094:
                    print("Error: El ID de VLAN debe estar entre 1 y 4094.")
                    return False
            except ValueError:
                print("Error: El ID de VLAN debe ser un número entero.")
                return False
        
        # Agregar la conexión
        topology.add_connection({
            "from": from_vm,
            "to": to_vm,
            "vlan_id": vlan_id
        })
        
        print(f"Conexión {from_vm} -> {to_vm} (VLAN {vlan_id}) agregada con éxito.")
        
        # Agregar la conexión inversa si se especificó
        if bidirectional:
            # Verificar que la conexión inversa no exista ya
            for conn in topology.connections:
                if conn['from'] == to_vm and conn['to'] == from_vm:
                    print(f"La conexión inversa {to_vm} -> {from_vm} ya existe.")
                    return True
            
            # Agregar la conexión inversa con la misma VLAN
            topology.add_connection({
                "from": to_vm,
                "to": from_vm,
                "vlan_id": vlan_id  # Usar la misma VLAN para la conexión bidireccional
            })
            
            print(f"Conexión inversa {to_vm} -> {from_vm} (VLAN {vlan_id}) agregada con éxito.")
        
        return True
    
    except ValueError:
        print("Entrada inválida. Se espera un número entero.")
        return False

def remove_connection(topology, connection_idx=None):
    """
    Elimina una conexión existente entre VMs
    
    Args:
        topology: Objeto de topología
        connection_idx: Índice de la conexión a eliminar (opcional)
        
    Returns:
        True si la conexión se eliminó con éxito, False en caso contrario
    """
    # Mostrar conexiones existentes
    if not topology.connections:
        print("No hay conexiones para eliminar.")
        return False
    
    # Listar conexiones disponibles
    list_connections(topology)
    
    try:
        # Obtener índice de la conexión a eliminar
        if connection_idx is None:
            conn_idx = int(input("\nSeleccione la conexión a eliminar (número): ")) - 1
        else:
            conn_idx = connection_idx - 1
        
        if conn_idx < 0 or conn_idx >= len(topology.connections):
            print("Índice fuera de rango.")
            return False
        
        # Obtener la conexión a eliminar
        conn_to_remove = topology.connections[conn_idx]
        from_vm = conn_to_remove['from']
        to_vm = conn_to_remove['to']
        
        # Eliminar la conexión
        topology.connections.pop(conn_idx)
        
        print(f"Conexión {from_vm} -> {to_vm} eliminada con éxito.")
        
        # Buscar la conexión inversa
        inverse_idx = None
        for i, conn in enumerate(topology.connections):
            if conn['from'] == to_vm and conn['to'] == from_vm:
                inverse_idx = i
                break
        
        # Preguntar si se quiere eliminar también la conexión inversa
        if inverse_idx is not None:
            remove_inverse = input("¿Desea eliminar también la conexión inversa? (s/n): ").lower()
            if remove_inverse in ['s', 'si', 'sí', 'y', 'yes']:
                topology.connections.pop(inverse_idx)
                print(f"Conexión inversa {to_vm} -> {from_vm} eliminada con éxito.")
        
        return True
    
    except ValueError:
        print("Entrada inválida. Se espera un número entero.")
        return False

def manage_connections(topology):
    """
    Menú para gestionar las conexiones entre VMs
    
    Args:
        topology: Objeto de topología
    """
    while True:
        print("\nGestión de Conexiones")
        print("---------------------")
        print("1. Listar conexiones existentes")
        print("2. Agregar una conexión")
        print("3. Eliminar una conexión")
        print("4. Volver al menú anterior")
        
        try:
            option = int(input("\nSeleccione una opción (1-4): "))
            
            if option == 1:
                list_connections(topology)
            
            elif option == 2:
                add_connection(topology)
            
            elif option == 3:
                remove_connection(topology)
            
            elif option == 4:
                break
            
            else:
                print("Opción inválida.")
        
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")
