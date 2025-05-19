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

    scripts_dir = os.path.join(os.getcwd(), "scripts")

    required_files = [
        "create_flexible_topology.sh",
    ]

    # for file in required_files:
    #     full_path = os.path.join(scripts_dir, file)
    #     if not os.path.exists(full_path):
    #         print(f"Error: No se encontró el archivo {file} en la carpeta 'scripts/'")
    #         print("Asegúrese de ejecutar este programa desde el directorio base del proyecto donde exista la carpeta 'scripts/'.")
    #         sys.exit(1)

    #     if not os.access(full_path, os.X_OK):
    #         try:
    #             os.chmod(full_path, 0o755)
    #             print(f"Se añadieron permisos de ejecución a {file}")
    #         except Exception as e:
    #             print(f"Advertencia: No se pudieron añadir permisos de ejecución a {file}: {e}")

    try:
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
