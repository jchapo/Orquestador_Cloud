"""
Generadores de topologías

Este módulo contiene las implementaciones para generar diferentes tipos
de topologías de red (anillo, estrella, lineal, personalizada).
"""

from .utils import generate_mac
from .models import VM, Connection

class TopologyGenerator:
    """Clase para generar diferentes tipos de topologías"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def create_ring_topology(self, num_vms, vlan_id=100, start_vm_id=None):
        """
        Crea una topología en anillo con el número especificado de VMs
        Retorna una lista de los nombres de las VMs creadas
        """
        if start_vm_id is None:
            start_vm_id = self.manager.topology.get_next_vm_id()

        # Asegurarse de que la VLAN exista en la topología
        self._ensure_vlan_exists(vlan_id)
        
        # Crear las VMs
        new_vms = []
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vlan": vlan_id,
                "vnc_port": vnc_port,
                "mac": mac
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones del anillo
        for i in range(num_vms):
            vm = new_vms[i]
            prev_vm = new_vms[(i-1) % num_vms]
            next_vm = new_vms[(i+1) % num_vms]
            
            # Conexión con el nodo anterior
            self.manager.topology.add_connection({
                "from": vm,
                "to": prev_vm
            })
            
            # Conexión con el nodo siguiente
            self.manager.topology.add_connection({
                "from": vm,
                "to": next_vm
            })
        
        return new_vms

    def create_star_topology(self, num_vms, vlan_id=100, start_vm_id=None):
        """
        Crea una topología en estrella con el número especificado de VMs
        Retorna una lista de los nombres de las VMs creadas
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
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vlan": vlan_id,
                "vnc_port": vnc_port,
                "mac": mac
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones de la estrella
        center_vm = new_vms[0]  # El primer nodo es el centro
        
        # Conexiones desde el centro a cada extremo
        for i in range(1, num_vms):
            edge_vm = new_vms[i]
            
            # Conexión entre el centro y el extremo
            self.manager.topology.add_connection({
                "from": center_vm,
                "to": edge_vm
            })
            
            # Conexión entre el extremo y el centro (bidireccional)
            self.manager.topology.add_connection({
                "from": edge_vm,
                "to": center_vm
            })
        
        return new_vms

    def create_linear_topology(self, num_vms, vlan_id=100, start_vm_id=None):
        """
        Crea una topología lineal con el número especificado de VMs
        Retorna una lista de los nombres de las VMs creadas
        """
        if start_vm_id is None:
            start_vm_id = self.manager.topology.get_next_vm_id()
        
        # Asegurarse de que la VLAN exista en la topología
        self._ensure_vlan_exists(vlan_id)
        
        # Crear las VMs
        new_vms = []
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vlan": vlan_id,
                "vnc_port": vnc_port,
                "mac": mac
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
        # Crear las conexiones lineales
        for i in range(num_vms - 1):
            # Conexión con el siguiente nodo
            self.manager.topology.add_connection({
                "from": new_vms[i],
                "to": new_vms[i+1]
            })
            
            # Conexión en dirección opuesta (bidireccional)
            self.manager.topology.add_connection({
                "from": new_vms[i+1],
                "to": new_vms[i]
            })
        
        return new_vms

    def create_custom_topology(self, num_vms, vlan_id=100):
        """
        Crea una topología personalizada con conexiones definidas por el usuario
        Retorna una lista de los nombres de las VMs creadas
        """
        from .ui import get_user_input
        
        start_vm_id = self.manager.topology.get_next_vm_id()

        # Asegurarse de que la VLAN exista en la topología
        self._ensure_vlan_exists(vlan_id)

        new_vms = []
        
        # Crear las VMs
        for i in range(num_vms):
            vm_id = start_vm_id + i
            vm_name = f"vm{vm_id}"
            worker_id = (i % 3) + 1  # Distribuir entre los 3 workers
            vnc_port = (i % 5) + 1   # Máximo 5 puertos VNC por worker
            mac = generate_mac(worker_id, vm_id)
            
            # Añadir la VM a la topología
            vm = {
                "name": vm_name,
                "worker": worker_id,
                "vlan": vlan_id,
                "vnc_port": vnc_port,
                "mac": mac
            }
            self.manager.topology.add_vm(vm)
            new_vms.append(vm_name)
        
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
            
            if connections_input.lower() == 'todos':
                # Conectar con todas las VMs
                for available_vm in available_vms:
                    self.manager.topology.add_connection({
                        "from": vm,
                        "to": available_vm
                    })
                    self.manager.topology.add_connection({
                        "from": available_vm,
                        "to": vm
                    })
            else:
                # Conectar con las VMs seleccionadas
                try:
                    selected_indices = [int(idx.strip()) - 1 for idx in connections_input.split(',') if idx.strip()]
                    for idx in selected_indices:
                        if 0 <= idx < len(available_vms):
                            target_vm = available_vms[idx]
                            
                            # Crear conexión bidireccional
                            self.manager.topology.add_connection({
                                "from": vm,
                                "to": target_vm
                            })
                            self.manager.topology.add_connection({
                                "from": target_vm,
                                "to": vm
                            })
                        else:
                            print(f"Índice fuera de rango: {idx+1}")
                except ValueError:
                    print("Entrada inválida. Se esperaban números separados por comas.")
        
        return new_vms
    
    def add_vm_to_topology(self):
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
            
            # Obtener la VLAN predeterminada (la primera VLAN utilizada en la topología existente)
            default_vlan = None
            if self.manager.topology.vms:
                default_vlan = self.manager.topology.vms[0]["vlan"]
            elif self.manager.topology.vlans:
                default_vlan = self.manager.topology.vlans[0]["id"]
            else:
                default_vlan = 100
            
            # Solicitar el ID de VLAN con validación
            vlan_input = input(f"Ingrese el ID de VLAN para las nuevas VMs (Enter para usar {default_vlan}): ")
            vlan_id = validate_vlan_id(vlan_input)
            if not vlan_input:
                vlan_id = default_vlan
            
            # Asegurarse de que la VLAN exista
            self._ensure_vlan_exists(vlan_id)
            
            # Obtener el próximo ID disponible
            start_vm_id = self.manager.topology.get_next_vm_id()
            
            # Mostrar los nombres que tendrán las nuevas VMs
            print("\nLas nuevas VMs tendrán los siguientes nombres:")
            for i in range(num_vms):
                print(f"vm{start_vm_id + i}")
            
            # Crear las VMs
            new_vms = []
            for i in range(num_vms):
                vm_id = start_vm_id + i
                vm_name = f"vm{vm_id}"
                
                worker_id = int(input(f"\nIngrese el número de worker para {vm_name} (1-3): ") or "1")
                if worker_id < 1 or worker_id > 3:
                    worker_id = (i % 3) + 1
                    print(f"Worker inválido. Se asignará automáticamente: {worker_id}")
                
                vnc_port = int(input(f"Ingrese el puerto VNC para {vm_name} (1-3): ") or "1")
                if vnc_port < 1 or vnc_port > 3:
                    vnc_port = (i % 3) + 1
                    print(f"Puerto VNC inválido. Se asignará automáticamente: {vnc_port}")
                
                mac = generate_mac(worker_id, vm_id)
                
                # Añadir la VM a la topología
                vm = {
                    "name": vm_name,
                    "worker": worker_id,
                    "vlan": vlan_id,
                    "vnc_port": vnc_port,
                    "mac": mac
                }
                self.manager.topology.add_vm(vm)
                new_vms.append(vm_name)
                
                print(f"VM {vm_name} creada con éxito.")
            
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
                            
                            # Crear conexión bidireccional
                            self.manager.topology.add_connection({
                                "from": vm,
                                "to": target_vm
                            })
                            self.manager.topology.add_connection({
                                "from": target_vm,
                                "to": vm
                            })
                            
                            print(f"Conexión establecida: {vm} <-> {target_vm}")
                        else:
                            print(f"Índice fuera de rango: {idx+1}")
                except ValueError:
                    print("Entrada inválida. Se esperaban números separados por comas.")
            
            print(f"\n{num_vms} VMs agregadas con éxito a la topología.")
            
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")

    def add_predefined_topology(self):
        """Agrega una topología predefinida a la existente"""
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
            
            # Obtener la VLAN predeterminada (la primera VLAN utilizada en la topología existente)
            default_vlan = None
            if self.manager.topology.vms:
                default_vlan = self.manager.topology.vms[0]["vlan"]
            elif self.manager.topology.vlans:
                default_vlan = self.manager.topology.vlans[0]["id"]
            else:
                default_vlan = 100
            
            # Solicitar el ID de VLAN con validación
            vlan_input = input(f"Ingrese el ID de VLAN para la nueva topología (Enter para usar {default_vlan}): ")
            vlan_id = validate_vlan_id(vlan_input)
            if not vlan_input:
                vlan_id = default_vlan
            
            # Asegurarse de que la VLAN exista
            self._ensure_vlan_exists(vlan_id)
            
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
                new_vms = self.create_ring_topology(num_vms, vlan_id, start_vm_id)
                topology_name = "anillo"
            elif topology_type == 2:
                # Estrella
                new_vms = self.create_star_topology(num_vms, vlan_id, start_vm_id)
                topology_name = "estrella"
            elif topology_type == 3:
                # Lineal
                new_vms = self.create_linear_topology(num_vms, vlan_id, start_vm_id)
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
                        # Crear conexión bidireccional
                        self.manager.topology.add_connection({
                            "from": new_vm,
                            "to": existing_vm
                        })
                        self.manager.topology.add_connection({
                            "from": existing_vm,
                            "to": new_vm
                        })
                        
                        print(f"Conexión establecida: {new_vm} <-> {existing_vm}")
                
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