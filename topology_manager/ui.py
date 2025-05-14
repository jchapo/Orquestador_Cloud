"""
Interfaz de usuario para la gestión de topologías

Este módulo implementa la interfaz de usuario para interactuar con el sistema.
"""

import sys
from .utils import clear_screen, print_header, print_vms, print_connections
from .connections import manage_connections  # Importar el nuevo módulo

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
            print("4. Salir")
            
            try:
                option = int(input("\nSeleccione una opción (1-4): "))
                
                if option == 1:
                    self.create_new_predefined_topology()
                    input("\nPresione Enter para continuar...")
                
                elif option == 2:
                    self.create_new_custom_topology()
                    input("\nPresione Enter para continuar...")
                
                elif option == 3:
                    self.modify_existing_topology()
                
                elif option == 4:
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
                
    def create_new_predefined_topology(self):
        """Crea una nueva topología predefinida desde cero"""
        from .utils import print_header, print_vms, print_connections, validate_vlan_id
        
        print_header("Crear nueva topología predefinida")
        
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
                return
            
            num_vms = int(input("\n¿Cuántas VMs tendrá la topología? "))
            if num_vms <= 0:
                print("Debe crear al menos una VM.")
                return
            
            # Solicitar el ID de VLAN con validación y permitir reintentos
            while True:
                vlan_input = input("Ingrese el ID de VLAN para la topología (Enter para usar 100): ")
                try:
                    vlan_id = validate_vlan_id(vlan_input)
                    break  # Salir del bucle si es válido
                except ValueError as e:
                    print(f"❌ Entrada inválida: {e}")

            #enable_vlan_comm = input("¿Habilitar comunicación entre VLANs? (s/n): ").lower() == 's'
            #self.manager.topology.settings["enable_vlan_communication"] = enable_vlan_comm
            
            # Crear la topología seleccionada
            if topology_type == 1:
                # Anillo
                self.manager.create_ring_topology(num_vms, vlan_id)
                topology_name = "anillo"
            elif topology_type == 2:
                # Estrella
                self.manager.create_star_topology(num_vms, vlan_id)
                topology_name = "estrella"
            elif topology_type == 3:
                # Lineal
                self.manager.create_linear_topology(num_vms, vlan_id)
                topology_name = "lineal"
            
            print(f"\nTopología de {topology_name} con {num_vms} VMs creada con éxito.")

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
            
            # Guardar la topología
            save_file = input("\nIngrese el nombre del archivo para guardar la topología (o Enter para usar un nombre automático): ")
            if save_file:
                self.manager.save_topology(save_file)
            else:
                self.manager.save_topology()
            
            # Mostrar resumen
            print_vms(self.manager.topology)
            print_connections(self.manager.topology)
            
        except ValueError as e:
            if "entre" in str(e):
                print(f"Error de rango: {e}")
            else:
                print(f"Entrada inválida: {e}")


    def create_new_custom_topology(self):
        """Crea una nueva topología personalizada desde cero"""
        from .utils import print_header, print_vms, print_connections, validate_vlan_id
        
        print_header("Crear nueva topología personalizada")
        
        # Inicializar una nueva topología
        self.manager.topology = self.manager.topology.__class__()
        self.manager.io.current_topology_file = None
        
        # Solicitar nombre para la topología
        self.manager.topology.name = input("Ingrese un nombre para la topología: ") or "topologia_personalizada"
        
        try:
            num_vms = int(input("\n¿Cuántas VMs tendrá la topología? "))
            if num_vms <= 0:
                print("Debe crear al menos una VM.")
                return
            
            # Solicitar el ID de VLAN con validación y permitir reintentos
            while True:
                vlan_input = input("Ingrese el ID de VLAN para la topología (Enter para usar 100): ")
                try:
                    vlan_id = validate_vlan_id(vlan_input)
                    break  # Salir del bucle si es válido
                except ValueError as e:
                    print(f"❌ Entrada inválida: {e}")
            
            #enable_vlan_comm = input("¿Habilitar comunicación entre VLANs? (s/n): ").lower() == 's'
            #self.manager.topology.settings["enable_vlan_communication"] = enable_vlan_comm
            
            # Crear topología personalizada
            self.manager.create_custom_topology(num_vms, vlan_id)

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
            
            # Guardar la topología
            save_file = input("\nIngrese el nombre del archivo para guardar la topología (o Enter para usar un nombre automático): ")
            if save_file:
                self.manager.save_topology(save_file)
            else:
                self.manager.save_topology()
            
            # Mostrar resumen
            print_vms(self.manager.topology)
            print_connections(self.manager.topology)
            
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")


    def modify_existing_topology(self):
        """Modifica una topología existente"""
        from .utils import print_header, print_vms, print_connections
        
        print_header("Modificar topología existente")
        
        # Solicitar el archivo de la topología a modificar
        file_path = input("Ingrese la ruta del archivo de topología a modificar: ")
        if not file_path:
            print("Operación cancelada.")
            return
            
        if not self.manager.load_topology(file_path):
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
            print("5. Guardar cambios")
            print("6. Ejecutar topología")
            print("7. Volver al menú principal")
            
            try:
                option = int(input("\nSeleccione una opción (1-7): "))
                
                if option == 1:
                    self.manager.generator.add_vm_to_topology()
                
                elif option == 2:
                    self.manager.generator.add_predefined_topology()
                
                elif option == 3:
                    self.set_internet_access()
                
                elif option == 4:
                    self.set_vlan_communication()
                
                elif option == 5:
                    save_file = input("\nIngrese el nombre del archivo para guardar la topología (o Enter para usar el mismo archivo): ")
                    if save_file:
                        self.manager.save_topology(save_file)
                    else:
                        self.manager.save_topology()
                
                elif option == 6:
                    self.manager.execute_topology()
                
                elif option == 7:
                    break
                
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
