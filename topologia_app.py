#!/usr/bin/env python3

"""
Gestor de Topologías de Red para Orquestación de Máquinas Virtuales
===================================================================

Este programa permite crear y modificar topologías de red para orquestar 
máquinas virtuales en diferentes configuraciones como anillo, estrella y lineal.

Funcionalidades:
1. Crear topologías predefinidas (anillo, estrella, lineal)
2. Crear topologías personalizadas con conexiones manuales
3. Modificar topologías existentes
   - Añadir VMs individuales
   - Añadir topologías completas
   - Configurar acceso a Internet

El programa genera archivos JSON que pueden ser utilizados por los scripts bash
create_flexible_topology.sh para implementar las topologías en el entorno real.
"""

import sys
import os
from topology_manager import TopologyManager

# Verificar que estamos en el directorio correcto (donde están los scripts bash)
required_files = [
    "create_flexible_topology.sh",
]

for file in required_files:
    if not os.path.exists(file):
        print(f"Error: No se encontró el archivo {file}")
        print("Asegúrese de ejecutar este programa desde el directorio donde están los scripts de orquestación.")
        sys.exit(1)

# Asegurarse de que los scripts tienen permisos de ejecución
for file in required_files:
    if not os.access(file, os.X_OK):
        try:
            os.chmod(file, 0o755)
            print(f"Se añadieron permisos de ejecución a {file}")
        except Exception as e:
            print(f"Advertencia: No se pudieron añadir permisos de ejecución a {file}: {e}")

if __name__ == "__main__":
    try:
        # Iniciar el gestor de topologías
        manager = TopologyManager()
        manager.main_menu()
    except KeyboardInterrupt:
        print("\n\nPrograma terminado por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)
