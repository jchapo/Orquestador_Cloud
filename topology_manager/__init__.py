"""
Administrador de Topologías de Red

Este módulo contiene la clase principal que coordina las funcionalidades
de la aplicación.
"""

import os
import json
from .models import Topology
from .ui import TopologyUI
from .io import TopologyIO
from .generators import TopologyGenerator
from .executor import TopologyExecutor
from .connections import manage_connections
from .remover import TopologyRemover

class TopologyManager:
    """Clase principal que coordina la aplicación"""
    
    def __init__(self):
        """Inicializa el administrador de topologías"""
        # Crear una topología vacía
        self.topology = Topology()
        
        # Inicializar componentes
        self.io = TopologyIO(self)
        self.ui = TopologyUI(self)
        self.generator = TopologyGenerator(self)
        self.executor = TopologyExecutor(self)
        self.remover = TopologyRemover(self)
    
    def run(self):
        """Inicia la aplicación"""
        self.ui.main_menu()
    
    def load_topology(self, file_path):
        """Carga una topología desde un archivo"""
        return self.io.load_topology(file_path)
    
    def save_topology(self, file_path=None):
        """Guarda la topología en un archivo"""
        return self.io.save_topology(file_path)
    
    def execute_topology(self):
        """Ejecuta la topología actual"""
        return self.executor.execute_topology()
    
    def remove_topology(self, json_file=None):
        """Elimina una topología definida en un archivo JSON"""
        return self.remover.remove_topology(json_file)
    
    def manage_connections(self):
        """Inicia el menú de gestión de conexiones"""
        manage_connections(self.topology)
    
    def create_ring_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """Crea una topología en anillo"""
        return self.generator.create_ring_topology(num_vms, start_vm_id, default_flavor)
    
    def create_star_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """Crea una topología en estrella"""
        return self.generator.create_star_topology(num_vms, start_vm_id, default_flavor)
    
    def create_linear_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        """Crea una topología lineal"""
        return self.generator.create_linear_topology(num_vms, start_vm_id, default_flavor)
    
    def create_custom_topology(self, num_vms, default_flavor=None):
        """Crea una topología personalizada"""
        return self.generator.create_custom_topology(num_vms, default_flavor)