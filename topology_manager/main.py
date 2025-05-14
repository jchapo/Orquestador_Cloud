#!/usr/bin/env python3
"""
Punto de entrada principal para el Administrador de Topologías de Red

Este script inicia la aplicación de gestión de topologías.
"""

import sys
import os
from topology_manager import TopologyManager

def main():
    """Función principal"""
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

    try:
        # Iniciar el gestor de topologías
        manager = TopologyManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n\nPrograma terminado por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
