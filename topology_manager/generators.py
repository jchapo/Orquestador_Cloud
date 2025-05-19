"""
Generadores de topologías

Este módulo contiene las implementaciones para generar diferentes tipos
de topologías de red (anillo, estrella, lineal, personalizada).
"""

from .utils import generate_mac
from .models import VM, Connection
from .flavor_manager import select_flavor, get_flavor_data

class TopologyGenerator:
    """Clase para generar diferentes tipos de topologías"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def create_ring_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """
        Crea una topología en anillo con el número especificado de VMs
        Retorna una lista de los nombres de las VMs creadas
        """
        if start_vm_id is None:
            start_vm_id = self.manager.topology.get_next_vm_id()
        
        # Crear las VMs
        new_vms = []
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
            
            # Seleccionar flavor para esta VM si no se proporcionó uno por defecto
            vm_flavor = default_flavor
            if not vm_flavor:
                print(f"\nSeleccionar flavor para {vm_name}:")
                vm_flavor = select_flavor()

            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vnc_port": vnc_port,
                "mac": mac,
                "flavor": get_flavor_data(vm_flavor)
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones del anillo con VLANs únicas
        vlan_id_base = 100  # VLAN inicial
        connections_made = set()  # Registro de conexiones (para evitar duplicados)
        
        for i in range(num_vms):
            current_vm = new_vms[i]
            next_vm = new_vms[(i + 1) % num_vms]
            
            # Definir un identificador único para esta conexión (ordenado para bidireccionalidad)
            conn_pair = tuple(sorted([current_vm, next_vm]))
            
            # Si esta conexión ya se ha creado, omitirla
            if conn_pair in connections_made:
                continue
            
            # Asignar una VLAN única para esta conexión
            vlan_id = vlan_id_base + len(connections_made)
            
            # Conexión en ambas direcciones con la misma VLAN
            self.manager.topology.add_connection({
                "from": current_vm,
                "to": next_vm,
                "vlan_id": vlan_id
            })
            
            self.manager.topology.add_connection({
                "from": next_vm,
                "to": current_vm,
                "vlan_id": vlan_id
            })
            
            connections_made.add(conn_pair)
        
        return new_vms
    
    def create_star_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """
        Crea una topología en estrella con el número especificado de VMs
        
        Args:
            num_vms: Número de VMs a crear
            start_vm_id: ID inicial para las VMs (opcional)
            default_flavor: Flavor para asignar a todas las VMs (opcional)
            
        Returns:
            Lista de los nombres de las VMs creadas
        """
        if num_vms < 2:
            print("Una topología en estrella requiere al menos 2 VMs (centro + 1 extremo)")
            return []
        
        if start_vm_id is None:
            start_vm_id = self.manager.topology.get_next_vm_id()
        
        # Crear las VMs
        new_vms = []
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
         
            # Seleccionar flavor para esta VM si no se proporcionó uno por defecto
            vm_flavor = default_flavor
            if not vm_flavor:
                print(f"\nSeleccionar flavor para {vm_name}:")
                vm_flavor = select_flavor()
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vnc_port": vnc_port,
                "mac": mac,
                "flavor": get_flavor_data(vm_flavor)
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones de la estrella con VLANs únicas
        center_vm = new_vms[0]  # El primer nodo es el centro
        vlan_id_base = 100  # VLAN inicial
        
        # Conexiones desde el centro a cada extremo
        for i in range(1, num_vms):
            edge_vm = new_vms[i]
            vlan_id = vlan_id_base + (i - 1)
            
            # Conexión bidireccional entre el centro y el extremo
            self.manager.topology.add_connection({
                "from": center_vm,
                "to": edge_vm,
                "vlan_id": vlan_id
            })
            
            self.manager.topology.add_connection({
                "from": edge_vm,
                "to": center_vm,
                "vlan_id": vlan_id
            })
        
        return new_vms
    
    def create_linear_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """
        Crea una topología lineal con el número especificado de VMs
        
        Args:
            num_vms: Número de VMs a crear
            start_vm_id: ID inicial para las VMs (opcional)
            default_flavor: Flavor para asignar a todas las VMs (opcional)
            
        Returns:
            Lista de los nombres de las VMs creadas
        """
        if start_vm_id is None:
            start_vm_id = self.manager.topology.get_next_vm_id()
        
        # Crear las VMs
        new_vms = []
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
                    
            # Seleccionar flavor para esta VM si no se proporcionó uno por defecto
            vm_flavor = default_flavor
            if not vm_flavor:
                print(f"\nSeleccionar flavor para {vm_name}:")
                vm_flavor = select_flavor()
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vnc_port": vnc_port,
                "mac": mac,
                "flavor": get_flavor_data(vm_flavor)
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones lineales con VLANs únicas
        vlan_id_base = 100  # VLAN inicial
        
        for i in range(num_vms - 1):
            vlan_id = vlan_id_base + i
            
            # Conexión bidireccional con el siguiente nodo
            self.manager.topology.add_connection({
                "from": new_vms[i],
                "to": new_vms[i+1],
                "vlan_id": vlan_id
            })
            
            self.manager.topology.add_connection({
                "from": new_vms[i+1],
                "to": new_vms[i],
                "vlan_id": vlan_id
            })
        
        return new_vms

    def create_custom_topology(self, num_vms, default_flavor=None):
        """
        Crea una topología personalizada con conexiones definidas por el usuario
        Retorna una lista de los nombres de las VMs creadas
        """
        from .utils import get_user_input        
        
        start_vm_id = self.manager.topology.get_next_vm_id()

        new_vms = []
        
        # Crear las VMs
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
                    
            # Seleccionar flavor para esta VM si no se proporcionó uno por defecto
            vm_flavor = default_flavor
            if not vm_flavor:
                print(f"\nSeleccionar flavor para {vm_name}:")
                vm_flavor = select_flavor()
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vnc_port": vnc_port,
                "mac": mac,
                "flavor": get_flavor_data(vm_flavor)
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
            
            print(f"VM {vm_name} creada con éxito en Worker {worker_id}, VNC Port {vnc_port}.")
        
        # Solicitar conexiones para cada VM
        for vm in new_vms:
            print(f"\nDefinir conexiones para {vm}:")
            
            # Mostrar VMs disponibles para conectar
            print("\nVMs disponibles para conectar:")
            available_vms = [v["name"] for v in self.manager.topology.vms if v["name"] != vm]
            for i, available_vm in enumerate(available_vms):
                print(f"{i+1}. {available_vm}")
            
            # Solicitar conexiones
            connections_input = input("\nIngrese los números de las VMs a conectar (separados por coma) o 'todos' para conectar con todas: ")
            
            # Mapeo para evitar crear conexiones duplicadas
            connection_pairs = set()
            
            if connections_input.lower() == 'todos':
                # Conectar con todas las VMs
                for available_vm in available_vms:
                    # Verificar si esta conexión ya existe (en cualquier dirección)
                    conn_pair = tuple(sorted([vm, available_vm]))
                    if conn_pair in connection_pairs:
                        continue
                    
                    # Encontrar el próximo ID de VLAN disponible
                    used_vlans = [conn.get('vlan_id') for conn in self.manager.topology.connections if 'vlan_id' in conn]
                    vlan_id = 100  # VLAN inicial
                    while vlan_id in used_vlans and vlan_id <= 4094:
                        vlan_id += 1
                    
                    if vlan_id > 4094:
                        print("Error: Se ha alcanzado el límite de VLANs disponibles.")
                        break
                    
                    # Crear conexión bidireccional con VLAN asignada
                    self.manager.topology.add_connection({
                        "from": vm,
                        "to": available_vm,
                        "vlan_id": vlan_id
                    })
                    
                    self.manager.topology.add_connection({
                        "from": available_vm,
                        "to": vm,
                        "vlan_id": vlan_id
                    })
                    
                    print(f"Conexión establecida: {vm} <-> {available_vm} (VLAN {vlan_id})")
                    
                    # Registrar esta conexión como procesada
                    connection_pairs.add(conn_pair)
            else:
                # Conectar con las VMs seleccionadas
                try:
                    selected_indices = [int(idx.strip()) - 1 for idx in connections_input.split(',') if idx.strip()]
                    for idx in selected_indices:
                        if 0 <= idx < len(available_vms):
                            target_vm = available_vms[idx]
                            
                            # Verificar si esta conexión ya existe (en cualquier dirección)
                            conn_pair = tuple(sorted([vm, target_vm]))
                            if conn_pair in connection_pairs:
                                continue
                            
                            # Encontrar el próximo ID de VLAN disponible
                            used_vlans = [conn.get('vlan_id') for conn in self.manager.topology.connections if 'vlan_id' in conn]
                            vlan_id = 100  # VLAN inicial
                            while vlan_id in used_vlans and vlan_id <= 4094:
                                vlan_id += 1
                            
                            if vlan_id > 4094:
                                print("Error: Se ha alcanzado el límite de VLANs disponibles.")
                                break
                            
                            # Crear conexión bidireccional con VLAN asignada
                            self.manager.topology.add_connection({
                                "from": vm,
                                "to": target_vm,
                                "vlan_id": vlan_id
                            })
                            
                            self.manager.topology.add_connection({
                                "from": target_vm,
                                "to": vm,
                                "vlan_id": vlan_id
                            })
                            
                            print(f"Conexión establecida: {vm} <-> {target_vm} (VLAN {vlan_id})")
                            
                            # Registrar esta conexión como procesada
                            connection_pairs.add(conn_pair)
                        else:
                            print(f"Índice fuera de rango: {idx+1}")
                except ValueError:
                    print("Entrada inválida. Se esperaban números separados por comas.")
        
        return new_vms
    
    def add_vm_to_topology(self, default_flavor=None):
        """Agrega VMs individuales a la topología existente"""
        from .ui import print_vms
        from .utils import validate_vlan_id
        
        if not self.manager.topology.vms:
            print("No hay topología existente. Cree una nueva topología primero.")
            return
        
        print_vms(self.manager.topology)
        
        try:
            num_vms = int(input("\n¿Cuántas VMs desea agregar? "))
            if num_vms <= 0:
                print("Debe agregar al menos una VM.")
                return
            
            
            # Obtener el próximo ID disponible
            start_vm_id = self.manager.topology.get_next_vm_id()
            
            # Mostrar los nombres que tendrán las nuevas VMs
            print("\nLas nuevas VMs tendrán los siguientes nombres:")
            for i in range(num_vms):
                print(f"vm{start_vm_id + i}")
            
            # Determinar el último worker y vnc_port utilizados para continuar la secuencia
            last_vm_id = start_vm_id - 1
            last_worker = 3  # Por defecto, para que el siguiente sea 1 ((3 % 3) + 1 = 1)
            last_vnc_port = 5  # Por defecto, para que el siguiente sea 1 ((5 % 5) + 1 = 1)
            
            # Si hay VMs existentes, obtener el último worker y vnc_port
            if self.manager.topology.vms:
                # Intentar encontrar la VM con el mayor ID
                for vm in self.manager.topology.vms:
                    if vm["name"].startswith("vm"):
                        try:
                            vm_id = int(vm["name"][2:])
                            if vm_id == last_vm_id:
                                last_worker = vm["worker"]
                                last_vnc_port = vm["vnc_port"]
                        except ValueError:
                            continue
            
            # Crear las VMs usando round-robin
            new_vms = []
            for i in range(num_vms):
                vm_id = start_vm_id + i
                vm_name = f"vm{vm_id}"
                
                # Usar round-robin para worker y vnc_port, continuando la secuencia desde la última VM
                worker_id = ((last_worker + i) % 3) + 1
                vnc_port = ((last_vnc_port + i) % 5) + 1
                
                mac = generate_mac(worker_id, vm_id)
                    
                # Seleccionar flavor para esta VM si no se proporcionó uno por defecto
                vm_flavor = default_flavor
                if not vm_flavor:
                    print(f"\nSeleccionar flavor para {vm_name}:")
                    vm_flavor = select_flavor()
                
                # Añadir la VM a la topología
                vm = {
                    "name": vm_name,
                    "worker": worker_id,
                    "vnc_port": vnc_port,
                    "mac": mac,
                    "flavor": get_flavor_data(vm_flavor)
                }
                
                self.manager.topology.add_vm(vm)
                new_vms.append(vm_name)
                
                print(f"VM {vm_name} creada con éxito en Worker {worker_id}, VNC Port {vnc_port}.")
            
            # Solicitar conexiones para cada VM
            print_vms(self.manager.topology)
        
            for vm in new_vms:
                print(f"\nDefinir conexiones para {vm}:")
                
                # Mostrar VMs disponibles para conectar (excluyendo la VM actual)
                print("\nVMs disponibles para conectar:")
                available_vms = [v["name"] for v in self.manager.topology.vms if v["name"] != vm]
                for i, available_vm in enumerate(available_vms):
                    print(f"{i+1}. {available_vm}")
                
                # Solicitar conexiones
                connections_input = input("\nIngrese los números de las VMs a conectar (separados por coma): ")
                
                # Conectar con las VMs seleccionadas
                try:
                    selected_indices = [int(idx.strip()) - 1 for idx in connections_input.split(',') if idx.strip()]
                    for idx in selected_indices:
                        if 0 <= idx < len(available_vms):
                            target_vm = available_vms[idx]
                            
                            # Encontrar el próximo ID de VLAN disponible
                            used_vlans = [conn.get('vlan_id') for conn in self.manager.topology.connections if 'vlan_id' in conn]
                            vlan_id = 100  # VLAN inicial
                            while vlan_id in used_vlans and vlan_id <= 4094:
                                vlan_id += 1
                            
                            if vlan_id > 4094:
                                print("Error: Se ha alcanzado el límite de VLANs disponibles.")
                                break
                            
                            # Crear conexión bidireccional con VLAN asignada
                            self.manager.topology.add_connection({
                                "from": vm,
                                "to": target_vm,
                                "vlan_id": vlan_id
                            })
                            
                            self.manager.topology.add_connection({
                                "from": target_vm,
                                "to": vm,
                                "vlan_id": vlan_id
                            })
                            
                            print(f"Conexión establecida: {vm} <-> {target_vm} (VLAN {vlan_id})")
                        else:
                            print(f"Índice fuera de rango: {idx+1}")
                except ValueError:
                    print("Entrada inválida. Se esperaban números separados por comas.")
            
            print(f"\n{num_vms} VMs agregadas con éxito a la topología.")
            
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")

    def add_predefined_topology(self, default_flavor=None):
        """Agrega una topología predefinida a la existente usando round-robin para worker y vnc_port"""
        from .ui import print_vms, print_header
        from .utils import validate_vlan_id
        
        if not self.manager.topology.vms:
            print("No hay topología existente. Cree una nueva topología primero.")
            return
        
        print_header("Agregar topología predefinida a la existente")
        print_vms(self.manager.topology)
        
        print("\nSeleccione el tipo de topología a agregar:")
        print("1. Anillo")
        print("2. Estrella")
        print("3. Lineal")
        
        try:
            topology_type = int(input("\nIngrese su elección (1-3): "))
            if topology_type < 1 or topology_type > 3:
                print("Opción inválida.")
                return
            
            num_vms = int(input("\n¿Cuántas VMs tendrá la nueva topología? "))
            if num_vms <= 0:
                print("Debe agregar al menos una VM.")
                return
            
            # Obtener el próximo ID disponible
            start_vm_id = self.manager.topology.get_next_vm_id()
            
            # Mostrar los nombres que tendrán las nuevas VMs
            print("\nLas nuevas VMs tendrán los siguientes nombres:")
            for i in range(num_vms):
                print(f"vm{start_vm_id + i}")
            
            # Crear la topología seleccionada
            new_vms = []
            if topology_type == 1:
                # Anillo
                new_vms = self.create_ring_topology(num_vms, start_vm_id, default_flavor)
                topology_name = "anillo"
            elif topology_type == 2:
                # Estrella
                new_vms = self.create_star_topology(num_vms, start_vm_id, default_flavor)
                topology_name = "estrella"
            elif topology_type == 3:
                # Lineal
                new_vms = self.create_linear_topology(num_vms, start_vm_id, default_flavor)
                topology_name = "lineal"
            
            print(f"\nTopología de {topology_name} con {num_vms} VMs agregada con éxito.")
            
            # Conectar la nueva topología con la existente
            print("\nAhora debe conectar la nueva topología con la existente.")
            print("Seleccione VM(s) de la nueva topología para conectar con VM(s) de la topología existente:")
            
            print("\nVMs de la nueva topología:")
            for i, vm in enumerate(new_vms):
                print(f"{i+1}. {vm}")
            
            new_vm_indices = input("\nIngrese los números de las VMs de la nueva topología (separados por coma): ")
            try:
                selected_new_indices = [int(idx.strip()) - 1 for idx in new_vm_indices.split(',') if idx.strip()]
                selected_new_vms = [new_vms[idx] for idx in selected_new_indices if 0 <= idx < len(new_vms)]
                
                # Mostrar VMs existentes (excluyendo las nuevas)
                existing_vms = [v["name"] for v in self.manager.topology.vms if v["name"] not in new_vms]
                print("\nVMs de la topología existente:")
                for i, vm in enumerate(existing_vms):
                    print(f"{i+1}. {vm}")
                
                existing_vm_indices = input("\nIngrese los números de las VMs existentes a conectar (separados por coma): ")
                selected_existing_indices = [int(idx.strip()) - 1 for idx in existing_vm_indices.split(',') if idx.strip()]
                selected_existing_vms = [existing_vms[idx] for idx in selected_existing_indices if 0 <= idx < len(existing_vms)]
                
                # Crear conexiones entre las VMs seleccionadas
                for new_vm in selected_new_vms:
                    for existing_vm in selected_existing_vms:
                        # Encontrar el próximo ID de VLAN disponible
                        used_vlans = [conn.get('vlan_id') for conn in self.manager.topology.connections if 'vlan_id' in conn]
                        vlan_id = 100  # VLAN inicial
                        while vlan_id in used_vlans and vlan_id <= 4094:
                            vlan_id += 1
                        
                        if vlan_id > 4094:
                            print("Error: Se ha alcanzado el límite de VLANs disponibles.")
                            break
                        
                        # Crear conexión bidireccional con VLAN asignada
                        self.manager.topology.add_connection({
                            "from": new_vm,
                            "to": existing_vm,
                            "vlan_id": vlan_id
                        })
                        
                        self.manager.topology.add_connection({
                            "from": existing_vm,
                            "to": new_vm,
                            "vlan_id": vlan_id
                        })
                        
                        print(f"Conexión establecida: {new_vm} <-> {existing_vm} (VLAN {vlan_id})")
                
            except (ValueError, IndexError):
                print("Entrada inválida o índice fuera de rango.")
            
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")

    def _ensure_vlan_exists(self, vlan_id):
        """
        Asegura que la VLAN especificada exista en la topología.
        Si no existe, la crea con la configuración apropiada.
        
        Args:
            vlan_id: ID de la VLAN a verificar/crear
        """
        # Verificar si la VLAN ya existe
        for vlan in self.manager.topology.vlans:
            if vlan["id"] == vlan_id:
                return
        
        # La VLAN no existe, crearla con el formato solicitado
        new_vlan = {
            "id": vlan_id,
            "network": f"192.168.{vlan_id}.0/24",
            "dhcp_range": f"192.168.{vlan_id}.10,192.168.{vlan_id}.200"
        }
        
        self.manager.topology.vlans.append(new_vlan)
        print(f"Creada nueva VLAN {vlan_id} con red 192.168.{vlan_id}.0/24")