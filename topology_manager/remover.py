"""
Módulo para eliminar topologías

Este módulo contiene funciones para eliminar topologías definidas en archivos JSON.
"""

import os
import json
import subprocess

class TopologyRemover:
    """Clase para eliminar topologías existentes"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def remove_topology(self, json_file=None):
        """
        Elimina una topología basada en un archivo JSON
        
        Args:
            json_file: Ruta al archivo JSON de la topología a eliminar
        
        Returns:
            True si la eliminación se completó con éxito, False en caso contrario
        """
        if json_file is None:
            # Si no se proporciona un archivo, solicitar uno
            json_file = input("Ingrese la ruta del archivo JSON de la topología a eliminar: ")
            if not json_file.strip():
                print("Operación cancelada.")
                return False
        
        # Verificar que el archivo existe
        if not os.path.exists(json_file):
            print(f"Error: El archivo {json_file} no existe.")
            return False
        
        try:
            # Cargar el archivo JSON
            with open(json_file, 'r') as f:
                topology_data = json.load(f)
            
            # Mostrar información sobre la topología que se va a eliminar
            print("\nInformación de la topología a eliminar:")
            print(f"Nombre: {topology_data.get('name', 'No definido')}")
            print(f"VMs: {len(topology_data.get('vms', []))}")
            print(f"Conexiones: {len(topology_data.get('connections', []))}")
            print(f"VLANs configuradas: {len(set([conn.get('vlan_id') for conn in topology_data.get('connections', []) if 'vlan_id' in conn]))}")
            
            # Configuración de nodos
            print("\nNodos utilizados:")
            nodes_info = topology_data.get('nodes', {})
            print(f"- Head Node: {nodes_info.get('head_node', 'No definido')}")
            print(f"- OFS Node: {nodes_info.get('ofs_node', 'No definido')}")
            workers = nodes_info.get('workers', [])
            for i, worker in enumerate(workers):
                print(f"- Worker {i+1}: {worker}")
            
            # Mostrar lista de VMs
            if topology_data.get('vms'):
                print("\nLista de VMs:")
                for i, vm in enumerate(topology_data['vms']):
                    print(f"{i+1}. {vm['name']} (Worker: {vm['worker']}, VNC Port: {vm['vnc_port']})")
            
            # Internet settings
            internet_enabled = topology_data.get('settings', {}).get('enable_internet', False)
            vlan_comm_enabled = topology_data.get('settings', {}).get('enable_vlan_communication', False)
            print(f"\nAcceso a Internet: {'Habilitado' if internet_enabled else 'Deshabilitado'}")
            print(f"Comunicación entre VLANs: {'Habilitada' if vlan_comm_enabled else 'Deshabilitada'}")
            
            if internet_enabled:
                vm_internet_access = topology_data.get('vm_internet_access', [])
                if vm_internet_access:
                    print("VMs con acceso a Internet:")
                    for vm in vm_internet_access:
                        print(f"- {vm}")
            
            # Solicitar confirmación
            confirm = input("\n¿Está seguro de que desea eliminar esta topología? (s/n): ").lower() == 's'
            if not confirm:
                print("Operación cancelada.")
                return False
            
            # Ejecutar el script de eliminación
            print("\nEliminando topología...")
            
            # Verificar si existe un script de eliminación
            script_path = "./destroy_topology.sh"
            if not os.path.exists(script_path):
                print(f"Error: No se encontró el script {script_path}")
                print("Por favor, cree el script de eliminación primero.")
                return False
            
            # Asegurarse de que el script tiene permisos de ejecución
            if not os.access(script_path, os.X_OK):
                try:
                    os.chmod(script_path, 0o755)
                    print(f"Se añadieron permisos de ejecución a {script_path}")
                except Exception as e:
                    print(f"Advertencia: No se pudieron añadir permisos de ejecución a {script_path}: {e}")
                    return False
            
            # Ejecutar el script de eliminación
            cmd = f"{script_path} {json_file}"
            print(f"Ejecutando: {cmd}")
            
            # Utilizamos Popen para poder ver la salida en tiempo real
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Mostrar la salida en tiempo real
            for line in process.stdout:
                print(line, end='')
            
            # Esperar a que termine el proceso
            process.wait()
            
            # Verificar el código de retorno
            if process.returncode == 0:
                print("\nTopología eliminada con éxito.")
                return True
            else:
                print(f"\nError al eliminar la topología. Código de retorno: {process.returncode}")
                return False
                
        except json.JSONDecodeError:
            print(f"Error: El archivo {json_file} no es un archivo JSON válido.")
            return False
        except Exception as e:
            print(f"Error al eliminar la topología: {e}")
            return False