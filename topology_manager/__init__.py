"""
Paquete de administración de topologías de red

Este paquete proporciona herramientas para crear, modificar y gestionar
topologías de red para entornos virtualizados.
"""

from .models import Topology, VM, Connection
from .ui import TopologyUI
from .generators import TopologyGenerator
from .io import TopologyIO
from .executor import TopologyExecutor
from .connections import manage_connections  # Importar el módulo de conexiones
from .flavor_manager import manage_flavors   # Importar el nuevo módulo de flavors

# Clase principal que integra todos los componentes
class TopologyManager:
    def __init__(self):
        self.topology = Topology()
        self.ui = TopologyUI(self)
        self.generator = TopologyGenerator(self)
        self.io = TopologyIO(self)
        self.executor = TopologyExecutor(self)
    
    def run(self):
        """Inicia la aplicación"""
        self.ui.main_menu()
    
    # Métodos de conveniencia para delegar a los módulos específicos
    def create_ring_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        return self.generator.create_ring_topology(num_vms, start_vm_id, default_flavor)

    def create_star_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        return self.generator.create_star_topology(num_vms, start_vm_id, default_flavor)

    def create_linear_topology(self, num_vms, start_vm_id=None, default_flavor=None):
        return self.generator.create_linear_topology(num_vms, start_vm_id, default_flavor)

    def create_custom_topology(self, num_vms, default_flavor=None):
        return self.generator.create_custom_topology(num_vms, default_flavor)
    
    def load_topology(self, file_path):
        return self.io.load_topology(file_path)
    
    def save_topology(self, file_path=None):
        return self.io.save_topology(file_path)
    
    def execute_topology(self):
        return self.executor.execute_topology()
    
    # Métodos para gestionar conexiones
    def manage_connections(self):
        manage_connections(self.topology)
        
    # Métodos para gestionar flavors
    def manage_flavors(self):
        manage_flavors()