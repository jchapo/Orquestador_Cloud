"""
Módulo de entrada/salida para topologías

Este módulo maneja la carga y guardado de topologías en archivos JSON.
"""

import json
import os
import datetime
from .models import Topology

class TopologyIO:
    """Clase para manejar la entrada/salida de topologías"""
    
    def __init__(self, manager):
        self.manager = manager
        self.current_topology_file = None
    
    def load_topology(self, file_path):
        """Carga una topología desde un archivo JSON"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Crear una nueva topología a partir de los datos
            self.manager.topology = Topology.from_dict(data)
            self.current_topology_file = file_path
            return True
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return False
    
    def save_topology(self, file_path=None):
        """Guarda la topología en un archivo JSON"""
        if file_path is None and self.current_topology_file is not None:
            file_path = self.current_topology_file
        elif file_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"topology_{timestamp}.json"
        
        try:
            # Convertir la topología a un diccionario
            data = self.manager.topology.to_dict()
            
            # Guardar el diccionario en un archivo JSON
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.current_topology_file = file_path
            print(f"\nTopología guardada como: {file_path}")
            return True
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
            return False
    
    def get_current_file(self):
        """Obtiene el archivo actual de la topología"""
        return self.current_topology_file
