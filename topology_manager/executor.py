"""
Módulo para ejecutar topologías

Este módulo maneja la ejecución de topologías a través de scripts externos.
"""

import subprocess
import os

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
                return True
            else:
                print(f"\nError al ejecutar la topología. Código de retorno: {process.returncode}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar la topología: {e}")
            return False
