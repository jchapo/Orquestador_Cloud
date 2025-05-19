"""
Módulo para ejecutar topologías

Este módulo maneja la ejecución de topologías a través de scripts externos.
"""

import subprocess
import os
import time

class TopologyExecutor:
    """Clase para ejecutar topologías"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def execute_topology(self):
        """Ejecuta la topología usando el script create_flexible_topology.sh"""
        # Verificar que la topología esté guardada
        current_file = self.manager.io.get_current_file()
        if current_file is None:
            print("Debe guardar la topología antes de ejecutarla.")
            return False
        
        # Verificar que el script existe
        script_path = "./create_flexible_topology.sh"
        if not os.path.exists(script_path):
            print(f"Error: No se encontró el script {script_path}")
            return False
        
        # Asegurarse de que el script tiene permisos de ejecución
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
                print(f"Se añadieron permisos de ejecución a {script_path}")
            except Exception as e:
                print(f"Advertencia: No se pudieron añadir permisos de ejecución a {script_path}: {e}")
        
        try:
            # Construir el comando
            #cmd = f"sudo {script_path} {current_file}"
            cmd = f"{script_path} {current_file}"
            print(f"\nEjecutando: {cmd}")
            
            # Pedir confirmación al usuario
            result = input("¿Desea ejecutar ahora la topología? (s/n): ")
            if result.lower() != 's':
                print("\nEjecución cancelada.")
                return False
            
            # Ejecutar el comando
            process = subprocess.run(cmd, shell=True, check=True)
            
            if process.returncode == 0:
                print("\nTopología ejecutada con éxito.")
                # Ofrecer conexión SSH a las VMs con acceso a internet
                self.offer_ssh_connection()
                return True
            else:
                print(f"\nError al ejecutar la topología. Código de retorno: {process.returncode}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar la topología: {e}")
            return False
    
    def offer_ssh_connection(self):
        """Ofrece opciones para conectarse por SSH a las VMs con acceso a internet"""
        # Verificar si hay VMs con acceso a internet
        vms_with_internet = self.manager.topology.vm_internet_access
        if not vms_with_internet or not self.manager.topology.settings.get("enable_internet", False):
            print("\nNo hay VMs con acceso a internet configuradas.")
            return
        
        print("\n===== Conexión SSH a VMs con acceso a internet =====")
        print("Las siguientes VMs tienen acceso a internet (VLAN 10):")
        
        for i, vm_name in enumerate(vms_with_internet):
            # Buscar la VM en la topología
            vm = None
            for v in self.manager.topology.vms:
                if v["name"] == vm_name:
                    vm = v
                    break
            
            if vm:
                worker_id = vm.get("worker", "N/A")
                flavor = vm.get("flavor", {})
                if isinstance(flavor, dict):
                    flavor_name = flavor.get("name", "N/A")
                else:
                    flavor_name = str(flavor)
                
                print(f"{i+1}. {vm_name} (Worker: {worker_id}, Flavor: {flavor_name})")
        
        print(f"{len(vms_with_internet)+1}. Volver al menú principal")
        
        # Solicitar selección al usuario
        try:
            option = int(input("\nSeleccione una VM para conectarse por SSH (número): "))
            
            if option == len(vms_with_internet) + 1:
                return  # Volver al menú principal
            
            if 1 <= option <= len(vms_with_internet):
                selected_vm = vms_with_internet[option-1]
                self.connect_ssh_to_vm(selected_vm)
            else:
                print("Opción inválida.")
        except ValueError:
            print("Entrada inválida. Se espera un número entero.")
    
    def connect_ssh_to_vm(self, vm_name):
        """Intenta establecer una conexión SSH a una VM específica"""
        # Buscar la información de la VM
        vm = None
        for v in self.manager.topology.vms:
            if v["name"] == vm_name:
                vm = v
                break
        
        if not vm:
            print(f"Error: No se encontró la VM {vm_name}")
            return
        
        # La IP se asigna en la VLAN 10 (internet) en el rango 192.168.10.X
        # Donde X es el ID numérico de la VM (asumiendo formato vmX)
        try:
            vm_id = int(vm_name[2:])  # Extraer número de vm1, vm2, etc.
            ip_address = f"192.168.10.{100 + vm_id}"  # Asumiendo que la IP es 192.168.10.(100+vm_id)
            
            print(f"\nIntentando conexión SSH a {vm_name} ({ip_address})...")
            print("Usuario por defecto: ubuntu")
            print("Contraseña por defecto: ubuntu")
            print("\nComando SSH a ejecutar:")
            print(f"ssh ubuntu@{ip_address}")
            
            # Preguntar si desea ejecutar el comando SSH ahora
            execute = input("\n¿Desea ejecutar el comando SSH ahora? (s/n): ").lower() == 's'
            
            if execute:
                # Dar tiempo a que la VM termine de iniciar si es necesario
                print("\nEsperando a que la VM esté lista para conexiones SSH...")
                time.sleep(5)  # Esperar 5 segundos
                
                # Ejecutar el comando SSH
                try:
                    # Construir comando con opciones para primera conexión (sin validación de host)
                    cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@{ip_address}"
                    print(f"\nEjecutando: {cmd}")
                    
                    # Usar subprocess.call para mantener la interactividad
                    subprocess.call(cmd, shell=True)
                    
                    # Ofrecer conectarse a otra VM después
                    reconnect = input("\n¿Desea conectarse a otra VM? (s/n): ").lower() == 's'
                    if reconnect:
                        self.offer_ssh_connection()
                    
                except Exception as e:
                    print(f"Error al ejecutar SSH: {e}")
            else:
                # Si el usuario decide no ejecutar el comando ahora, volver a mostrar la lista
                self.offer_ssh_connection()
                
        except ValueError:
            print(f"Error: No se puede determinar la IP para {vm_name}. El nombre debe ser 'vmX' donde X es un número.")
            self.offer_ssh_connection()