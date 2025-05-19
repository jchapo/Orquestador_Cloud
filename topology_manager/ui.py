"""
Interfaz de usuario para la gestión de topologías

Este módulo implementa la interfaz de usuario para interactuar con el sistema.
"""

import sys
import os
import subprocess
from .utils import clear_screen, print_header, print_vms, print_connections
from .connections import manage_connections  # Importar el módulo de conexiones
from .flavor_manager import manage_flavors, verify_flavor_exists, select_flavor  # Importar funciones de flavor

class TopologyUI:
    """Clase que implementa la interfaz de usuario para la gestión de topologías"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def main_menu(self):
        """Muestra el menú principal de la aplicación"""
        while True:
            print_header("Administrador de Topologías de Red")
            
            print("Menú Principal:")
            print("1. Crear nueva topología predefinida")
            print("2. Crear nueva topología personalizada")
            print("3. Modificar topología existente")
            print("4. Eliminar topología existente")
            print("5. Gestionar flavors")
            print("6. Salir")
            
            try:
                option = int(input("\nSeleccione una opción (1-6): "))
                
                if option == 1:
                    self.create_new_predefined_topology()
                
                elif option == 2:
                    self.create_new_custom_topology()
                
                elif option == 3:
                    self.modify_existing_topology()
                
                elif option == 4:
                    # Eliminar topología existente
                    self.manager.remove_topology()
                    input("\nPresione Enter para continuar...")
                
                elif option == 5:
                    # Gestionar flavors
                    manage_flavors()
                    input("\nPresione Enter para continuar...")
                
                elif option == 6:
                    print("\n¡Hasta luego!")
                    sys.exit(0)
                
                else:
                    print("Opción inválida.")
                    input("\nPresione Enter para continuar...")
            
            except ValueError:
                print("Entrada inválida. Se espera un número entero.")
                input("\nPresione Enter para continuar...")
            except KeyboardInterrupt:
                print("\n\nOperación cancelada por el usuario.")
                sys.exit(0)
    
    def visualize_topology(self, topology_file):
        """Visualiza la topología usando visualize_vlan_topology.py"""
        try:
            script_path = "visualize_vlan_topology.py"
            if not os.path.exists(script_path):
                print(f"Advertencia: No se encuentra el visualizador {script_path}.")
                return False
            
            # Verificar que el script tenga permisos de ejecución
            if not os.access(script_path, os.X_OK):
                os.chmod(script_path, 0o755)
                print(f"Se añadieron permisos de ejecución a {script_path}")
            
            # Ejecutar el script de visualización
            print(f"\nGenerando visualización de la topología...")
            cmd = f"python3 {script_path} {topology_file}"
            
            # Ejecutar en modo no bloqueante para mostrar la visualización mientras continúa la ejecución
            subprocess.Popen(cmd, shell=True)
            print(f"Visualización generada en {os.path.splitext(topology_file)[0]}_vlan_topology.png")
            return True
        except Exception as e:
            print(f"Error al visualizar la topología: {e}")
            return False
    
    def save_and_post_actions(self, topology_name):
        """Guarda la topología y ofrece visualizar y ejecutar"""
        # Usar el nombre de la topología como nombre de archivo
        file_name = f"{topology_name}.json"
        result = self.manager.save_topology(file_name)
        
        if result:
            print_vms(self.manager.topology)
            print_connections(self.manager.topology)
            
            # Visualizar la topología
            self.visualize_topology(file_name)
            
            # Preguntar si se quiere ejecutar la topología
            execute = input("\n¿Desea ejecutar la topología ahora? (s/n): ").lower() == 's'
            if execute:
                self.manager.execute_topology()
    
    def create_new_predefined_topology(self):
        """Crea una nueva topología predefinida desde cero"""
        from .utils import print_header, print_vms, print_connections, validate_vlan_id
        
        print_header("Crear nueva topología predefinida")
        
        # Verificar que exista al menos un flavor
        if not verify_flavor_exists():
            print("Error: No se pueden crear VMs sin flavors definidos.")
            print("Por favor, cree al menos un flavor primero.")
            input("\nPresione Enter para continuar...")
            return
        
        # Inicializar una nueva topología
        self.manager.topology = self.manager.topology.__class__()
        self.manager.io.current_topology_file = None
        
        # Solicitar nombre para la topología
        self.manager.topology.name = input("Ingrese un nombre para la topología: ") or "nueva_topologia"
        
        print("\nSeleccione el tipo de topología a crear:")
        print("1. Anillo")
        print("2. Estrella")
        print("3. Lineal")
        
        try:
            topology_type = int(input("\nIngrese su elección (1-3): "))
            if topology_type < 1 or topology_type > 3:
                print("Opción inválida.")
                input("\nPresione Enter para continuar...")
                return
            
            num_vms = int(input("\n¿Cuántas VMs tendrá la topología? "))
            if num_vms <= 0:
                print("Debe crear al menos una VM.")
                input("\nPresione Enter para continuar...")
                return
            
            # Preguntar si se usará el mismo flavor para todas las VMs
            same_flavor = input("\n¿Usar el mismo flavor para todas las VMs? (s/n): ").lower() == 's'
            selected_flavor = None
            
            if same_flavor:
                print("\nSeleccione el flavor para todas las VMs:")
                selected_flavor = select_flavor()
                if not selected_flavor:
                    print("Operación cancelada.")
                    input("\nPresione Enter para continuar...")
                    return
            
            # Crear la topología seleccionada
            if topology_type == 1:
                # Anillo
                self.manager.create_ring_topology(num_vms, start_vm_id=None, default_flavor=selected_flavor)
                topology_name = "anillo"
            elif topology_type == 2:
                # Estrella
                self.manager.create_star_topology(num_vms, start_vm_id=None, default_flavor=selected_flavor)
                topology_name = "estrella"
            elif topology_type == 3:
                # Lineal
                self.manager.create_linear_topology(num_vms, start_vm_id=None, default_flavor=selected_flavor)
                topology_name = "lineal"
            
            print(f"\nTopología de {topology_name} con {num_vms} VMs creada con éxito.")

            # Configurar opciones de red
            enable_internet = input("\n¿Habilitar acceso a Internet para alguna vm? (s/n): ").lower() == 's'
            self.manager.topology.settings["enable_internet"] = enable_internet
            
            # Configurar acceso a Internet para VMs específicas (solo si el acceso a Internet está habilitado)
            if enable_internet:
                internet_access = input("\n¿Configurar acceso a Internet para todas las VMs? (s/n): ").lower()
                if internet_access == 's':
                    self.manager.topology.vm_internet_access = [vm["name"] for vm in self.manager.topology.vms]
                    print("Todas las VMs tienen acceso a Internet.")
                else:
                    print("\nSeleccione las VMs que tendrán acceso a Internet:")
                    for i, vm in enumerate(self.manager.topology.vms):
                        print(f"{i+1}. {vm['name']}")
                    
                    vm_indices = input("\nIngrese los números de las VMs (separados por coma) o dejar vacío para ninguna: ")
                    if vm_indices.strip():
                        try:
                            selected_indices = [int(idx.strip()) - 1 for idx in vm_indices.split(',') if idx.strip()]
                            self.manager.topology.vm_internet_access = [
                                self.manager.topology.vms[idx]["name"] 
                                for idx in selected_indices 
                                if 0 <= idx < len(self.manager.topology.vms)
                            ]
                            print("\nVMs con acceso a Internet:")
                            for vm in self.manager.topology.vm_internet_access:
                                print(f"- {vm}")
                        except ValueError:
                            print("Entrada inválida. Ninguna VM tendrá acceso a Internet.")
                            self.manager.topology.vm_internet_access = []
                    else:
                        print("Ninguna VM tendrá acceso a Internet.")
                        self.manager.topology.vm_internet_access = []
            else:
                print("El acceso a Internet está deshabilitado para esta topología.")
                self.manager.topology.vm_internet_access = []
            
            # Guardar y ofrecer ejecutar
            self.save_and_post_actions(self.manager.topology.name)
            
            input("\nPresione Enter para continuar...")
            
        except ValueError as e:
            if "entre" in str(e):
                print(f"Error de rango: {e}")
            else:
                print(f"Entrada inválida: {e}")
            input("\nPresione Enter para continuar...")


    def create_new_custom_topology(self):
        """Crea una nueva topología personalizada desde cero"""
        from .utils import print_header, print_vms, print_connections, validate_vlan_id
        
        print_header("Crear nueva topología personalizada")
        
        # Verificar que exista al menos un flavor
        if not verify_flavor_exists():
            print("Error: No se pueden crear VMs sin flavors definidos.")
            print("Por favor, cree al menos un flavor primero.")
            input("\nPresione Enter para continuar...")
            return
        
        # Inicializar una nueva topología
        self.manager.topology = self.manager.topology.__class__()
        self.manager.io.current_topology_file = None
        
        # Solicitar nombre para la topología
        self.manager.topology.name = input("Ingrese un nombre para la topología: ") or "topologia_personalizada"
        
        try:
            num_vms = int(input("\n¿Cuántas VMs tendrá la topología? "))
            if num_vms <= 0:
                print("Debe crear al menos una VM.")
                input("\nPresione Enter para continuar...")
                return
            
            # Preguntar si se usará el mismo flavor para todas las VMs
            same_flavor = input("\n¿Usar el mismo flavor para todas las VMs? (s/n): ").lower() == 's'
            selected_flavor = None
            
            if same_flavor:
                print("\nSeleccione el flavor para todas las VMs:")
                selected_flavor = select_flavor()
                if not selected_flavor:
                    print("Operación cancelada.")
                    input("\nPresione Enter para continuar...")
                    return
            
            # Crear topología personalizada
            self.manager.create_custom_topology(num_vms, default_flavor=selected_flavor)

            # Configurar opciones de red
            enable_internet = input("\n¿Habilitar acceso a Internet para la topología? (s/n): ").lower() == 's'
            self.manager.topology.settings["enable_internet"] = enable_internet
            
            # Configurar acceso a Internet para VMs específicas (solo si el acceso a Internet está habilitado)
            if enable_internet:
                internet_access = input("\n¿Configurar acceso a Internet para todas las VMs? (s/n): ").lower()
                if internet_access == 's':
                    self.manager.topology.vm_internet_access = [vm["name"] for vm in self.manager.topology.vms]
                    print("Todas las VMs tienen acceso a Internet.")
                else:
                    print("\nSeleccione las VMs que tendrán acceso a Internet:")
                    for i, vm in enumerate(self.manager.topology.vms):
                        print(f"{i+1}. {vm['name']}")
                    
                    vm_indices = input("\nIngrese los números de las VMs (separados por coma) o dejar vacío para ninguna: ")
                    if vm_indices.strip():
                        try:
                            selected_indices = [int(idx.strip()) - 1 for idx in vm_indices.split(',') if idx.strip()]
                            self.manager.topology.vm_internet_access = [
                                self.manager.topology.vms[idx]["name"] 
                                for idx in selected_indices 
                                if 0 <= idx < len(self.manager.topology.vms)
                            ]
                            print("\nVMs con acceso a Internet:")
                            for vm in self.manager.topology.vm_internet_access:
                                print(f"- {vm}")
                        except ValueError:
                            print("Entrada inválida. Ninguna VM tendrá acceso a Internet.")
                            self.manager.topology.vm_internet_access = []
                    else:
                        print("Ninguna VM tendrá acceso a Internet.")
                        self.manager.topology.vm_internet_access = []
            else:
                print("El acceso a Internet está deshabilitado para esta topología.")
                self.manager.topology.vm_internet_access = []
            
            # Guardar y ofrecer ejecutar
            self.save_and_post_actions(self.manager.topology.name)
            
            input("\nPresione Enter para continuar...")
            
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")
            input("\nPresione Enter para continuar...")


    def modify_existing_topology(self):
        """Modifica una topología existente"""
        from .utils import print_header, print_vms, print_connections
        
        print_header("Modificar topología existente")
        
        # Solicitar el archivo de la topología a modificar
        file_path = input("Ingrese la ruta del archivo de topología a modificar: ")
        if not file_path:
            print("Operación cancelada.")
            input("\nPresione Enter para continuar...")
            return
            
        if not self.manager.load_topology(file_path):
            input("\nPresione Enter para continuar...")
            return
        
        print("\nTopología cargada con éxito.")
        print_vms(self.manager.topology)
        print_connections(self.manager.topology)
        
        # Mostrar configuración actual
        print("\nConfiguración actual de la topología:")
        print(f"- Acceso a Internet: {'Habilitado' if self.manager.topology.settings.get('enable_internet', False) else 'Deshabilitado'}")
        print(f"- Comunicación entre VLANs: {'Habilitada' if self.manager.topology.settings.get('enable_vlan_communication', False) else 'Deshabilitada'}")
        print(f"- VMs con acceso a Internet: {', '.join(self.manager.topology.vm_internet_access) if self.manager.topology.vm_internet_access else 'Ninguna'}")
        
        # Menú de modificación
        while True:
            print("\nOpciones de modificación:")
            print("1. Agregar VMs individuales")
            print("2. Agregar topología predefinida")
            print("3. Configurar acceso a Internet")
            print("4. Configurar comunicación entre VLANs")
            print("5. Configurar flavors de VMs")
            print("6. Gestionar conexiones")
            print("7. Guardar cambios")
            print("8. Ejecutar topología")
            print("9. Volver al menú principal")
            
            try:
                option = int(input("\nSeleccione una opción (1-9): "))
                
                if option == 1:
                    # Agregar VMs individuales
                    self.manager.generator.add_vm_to_topology()
                    
                    # Guardar y ofrecer visualizar/ejecutar
                    self.save_and_post_actions(self.manager.topology.name)
                
                elif option == 2:
                    # Agregar topología predefinida
                    self.manager.generator.add_predefined_topology()
                    
                    # Guardar y ofrecer visualizar/ejecutar
                    self.save_and_post_actions(self.manager.topology.name)
                
                elif option == 3:
                    self.set_internet_access()
                
                elif option == 4:
                    self.set_vlan_communication()
                
                elif option == 5:
                    self.configure_vm_flavors()
                
                elif option == 6:
                    self.manager.manage_connections()
                
                elif option == 7:
                    # Guardar y ofrecer visualizar/ejecutar
                    self.save_and_post_actions(self.manager.topology.name)
                
                elif option == 8:
                    self.manager.execute_topology()
                
                elif option == 9:
                    break
                
                else:
                    print("Opción inválida.")
            
            except ValueError:
                print("Entrada inválida. Se espera un número entero.")
    
    def configure_vm_flavors(self):
        """Configura los flavors de las VMs existentes"""
        from .utils import print_header
        from .flavor_manager import select_flavor, get_flavor_data
        
        if not self.manager.topology.vms:
            print("No hay VMs definidas. Cree una topología primero.")
            return
        
        print_header("Configurar Flavors de VMs")
        
        # Verificar que existan flavors
        if not verify_flavor_exists():
            print("Error: No hay flavors disponibles.")
            print("Por favor, cree al menos un flavor primero.")
            return
        
        # Mostrar configuración actual de flavors
        print("\nConfiguración actual de flavors:")
        print("-" * 70)
        print(f"{'VM':<10} {'Flavor':<15} {'CPU':<5} {'RAM (MB)':<10} {'Disco (GB)':<10}")
        print("-" * 70)
        
        for vm in self.manager.topology.vms:
            flavor_name = vm.get("flavor", "No definido")
            if flavor_name and flavor_name != "No definido":
                flavor_data = get_flavor_data(flavor_name)
                if flavor_data:
                    print(f"{vm['name']:<10} {flavor_name:<15} {flavor_data['cpu']:<5} {flavor_data['ram']:<10} {flavor_data['disk']:<10}")
                else:
                    print(f"{vm['name']:<10} {flavor_name:<15} (Flavor no encontrado)")
            else:
                print(f"{vm['name']:<10} No definido")
        
        print("-" * 70)
        
        # Menú de configuración
        print("\nOpciones de configuración:")
        print("1. Asignar el mismo flavor a todas las VMs")
        print("2. Configurar flavor para cada VM individualmente")
        print("3. Volver al menú anterior")
        
        try:
            option = int(input("\nSeleccione una opción (1-3): "))
            
            if option == 1:
                # Asignar el mismo flavor a todas las VMs
                print("\nSeleccione el flavor para asignar a todas las VMs:")
                flavor_name = select_flavor()
                
                if flavor_name:
                    # Actualizar todas las VMs
                    for vm in self.manager.topology.vms:
                        vm["flavor"] = flavor_name
                    
                    print(f"\nTodas las VMs ahora tienen asignado el flavor '{flavor_name}'.")
                else:
                    print("Operación cancelada.")
            
            elif option == 2:
                # Configurar flavor para cada VM individualmente
                for i, vm in enumerate(self.manager.topology.vms):
                    current_flavor = vm.get("flavor", "No definido")
                    print(f"\nVM: {vm['name']} (Flavor actual: {current_flavor})")
                    
                    change = input("¿Cambiar el flavor de esta VM? (s/n): ").lower() == 's'
                    if change:
                        print(f"Seleccione el nuevo flavor para {vm['name']}:")
                        new_flavor = select_flavor()
                        
                        if new_flavor:
                            vm["flavor"] = new_flavor
                            print(f"Flavor de {vm['name']} actualizado a '{new_flavor}'.")
                        else:
                            print("No se realizó ningún cambio.")
            
            elif option == 3:
                # Volver al menú anterior
                return
            
            else:
                print("Opción inválida.")
        
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")

    def set_internet_access(self):
        """Configura qué VMs tendrán acceso a Internet"""
        from .utils import print_header
        
        if not self.manager.topology.vms:
            print("No hay VMs definidas. Cree una topología primero.")
            return
        
        print_header("Configurar acceso a Internet")
        
        # Comprobar la configuración global de Internet primero
        current_setting = self.manager.topology.settings.get("enable_internet", False)
        print(f"\nEstado actual del acceso a Internet: {'Habilitado' if current_setting else 'Deshabilitado'}")
        
        # Preguntar si quiere cambiar la configuración global
        change_global = input("¿Desea cambiar la configuración global de acceso a Internet? (s/n): ").lower() == 's'
        
        if change_global:
            enable_internet = input("¿Habilitar acceso a Internet para la topología? (s/n): ").lower() == 's'
            self.manager.topology.settings["enable_internet"] = enable_internet
            
            if not enable_internet:
                print("\nAcceso a Internet deshabilitado para toda la topología.")
                self.manager.topology.vm_internet_access = []
                return
        elif not current_setting:
            print("\nEl acceso a Internet está deshabilitado globalmente.")
            print("Debe habilitarlo primero para configurar VMs específicas.")
            return
        
        # Configuración por VM (solo si el Internet está habilitado globalmente)
        current_access = self.manager.topology.vm_internet_access
        if current_access:
            print("\nVMs con acceso a Internet actualmente:")
            for vm in current_access:
                print(f"- {vm}")
        else:
            print("\nActualmente ninguna VM tiene acceso a Internet configurado.")
        
        print("\nOpciones de configuración:")
        print("1. Dar acceso a todas las VMs")
        print("2. Restringir acceso a todas las VMs")
        print("3. Configurar acceso para VMs específicas")
        
        try:
            option = int(input("\nSeleccione una opción (1-3): "))
            
            if option == 1:
                # Dar acceso a todas las VMs
                self.manager.topology.vm_internet_access = [vm["name"] for vm in self.manager.topology.vms]
                print("\nTodas las VMs tienen ahora acceso a Internet.")
            
            elif option == 2:
                # Restringir acceso a todas las VMs
                self.manager.topology.vm_internet_access = []
                print("\nNinguna VM tiene ahora acceso a Internet.")
            
            elif option == 3:
                # Configurar acceso para VMs específicas
                print("\nSeleccione las VMs que tendrán acceso a Internet:")
                for i, vm in enumerate(self.manager.topology.vms):
                    print(f"{i+1}. {vm['name']}")
                
                vm_indices = input("\nIngrese los números de las VMs (separados por coma): ")
                try:
                    selected_indices = [int(idx.strip()) - 1 for idx in vm_indices.split(',') if idx.strip()]
                    selected_vms = [self.manager.topology.vms[idx]["name"] for idx in selected_indices if 0 <= idx < len(self.manager.topology.vms)]
                    
                    self.manager.topology.vm_internet_access = selected_vms
                    
                    print("\nConfiguración de acceso a Internet actualizada:")
                    for vm in selected_vms:
                        print(f"- {vm}")
                
                except (ValueError, IndexError):
                    print("Entrada inválida o índice fuera de rango.")
            
            else:
                print("Opción inválida.")
        
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")
    

    def set_vlan_communication(self):
        """Configura la comunicación entre VLANs"""
        from .utils import print_header
        
        print_header("Configurar comunicación entre VLANs")
        
        # Mostrar la configuración actual
        current_status = self.manager.topology.settings.get("enable_vlan_communication", False)
        print(f"\nEstado actual: {'Habilitado' if current_status else 'Deshabilitado'}")
        
        # Solicitar la nueva configuración
        enable = input("\n¿Habilitar la comunicación entre VLANs? (s/n): ").lower() == 's'
        
        # Actualizar la configuración
        self.manager.topology.settings["enable_vlan_communication"] = enable
        
        if enable:
            print("\nComunicación entre VLANs habilitada.")
            
            # Si hay varias VLANs, preguntar cuáles deben comunicarse
            vlan_ids = set(vm["vlan"] for vm in self.manager.topology.vms if "vlan" in vm)
            if len(vlan_ids) > 1:
                print("\nVLANs disponibles en la topología:")
                for vlan_id in sorted(vlan_ids):
                    print(f"- VLAN {vlan_id}")
                
                print("\nPor defecto, todas las VLANs podrán comunicarse entre sí.")
                custom_config = input("¿Desea especificar qué VLANs pueden comunicarse? (s/n): ").lower() == 's'
                
                if custom_config:
                    # Implementar la lógica para configurar conexiones específicas entre VLANs
                    print("\nIngrese las conexiones entre VLANs (ejemplo: 100-200,200-300):")
                    connections_input = input("Conexiones: ")
                    
                    try:
                        # Parsear las conexiones
                        if connections_input.strip():
                            connections = []
                            pairs = connections_input.split(',')
                            for pair in pairs:
                                if '-' in pair:
                                    vlan1, vlan2 = map(int, pair.split('-'))
                                    if vlan1 in vlan_ids and vlan2 in vlan_ids:
                                        connections.append((vlan1, vlan2))
                                    else:
                                        print(f"Advertencia: VLAN {vlan1} o {vlan2} no existe en la topología.")
                            
                            # Almacenar las conexiones en la configuración
                            if connections:
                                self.manager.topology.settings["vlan_connections"] = connections
                                print("\nConexiones entre VLANs configuradas:")
                                for vlan1, vlan2 in connections:
                                    print(f"- VLAN {vlan1} <-> VLAN {vlan2}")
                            else:
                                print("No se configuraron conexiones específicas.")
                                self.manager.topology.settings.pop("vlan_connections", None)
                    except ValueError:
                        print("Formato inválido. No se aplicaron cambios específicos.")
                        self.manager.topology.settings.pop("vlan_connections", None)
        else:
            print("\nComunicación entre VLANs deshabilitada.")
            # Eliminar cualquier configuración específica de conexiones entre VLANs
            self.manager.topology.settings.pop("vlan_connections", None)