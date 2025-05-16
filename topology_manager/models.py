"""
Modelos de datos para la gestión de topologías

Este módulo contiene las clases de datos principales que representan
los componentes de una topología de red.
"""

class VM:
    """Representa una máquina virtual en la topología"""
    
    def __init__(self, name, worker, vnc_port, mac, vlan=None, flavor=None):
        self.name = name
        self.worker = worker
        self.vnc_port = vnc_port
        self.mac = mac
        self.vlan = vlan
        self.flavor = flavor
    
    def to_dict(self):
        """Convierte la VM a un diccionario para serialización"""
        return {
            "name": self.name,
            "worker": self.worker,
            "vlan": self.vlan,
            "vnc_port": self.vnc_port,
            "mac": self.mac,
            "flavor": self.flavor
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una VM a partir de un diccionario"""
        return cls(
            name=data["name"],
            worker=data["worker"],
            vlan=data["vlan"],
            vnc_port=data["vnc_port"],
            mac=data["mac"],
            flavor=data.get("flavor")  # Usar get para compatibilidad con formatos antiguos
        )


class Connection:
    """Representa una conexión entre dos VMs"""
    
    def __init__(self, from_vm, to_vm, vlan_id=None):
        self.from_vm = from_vm
        self.to_vm = to_vm
        self.vlan_id = vlan_id
    
    def to_dict(self):
        """Convierte la conexión a un diccionario para serialización"""
        return {
            "from": self.from_vm,
            "to": self.to_vm,
            "vlan_id": self.vlan_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una conexión a partir de un diccionario"""
        return cls(
            from_vm=data["from"], 
            to_vm=data["to"],
            vlan_id=data.get("vlan_id") # Usar get para compatibilidad con formatos antiguos
        )


class Topology:
    """Representa una topología completa con nodos, VMs y conexiones"""
    
    def __init__(self):
        # Definir una topología vacía con configuración por defecto
        self.name = ""
        self.nodes = {
            "head_node": "localhost",
            "ofs_node": "10.0.10.5",
            "workers": ["10.0.10.2", "10.0.10.3", "10.0.10.4"]
        }
        self.interfaces = {
            "head_internet": "ens3",
            "head_ofs": "ens4",
            "worker_ofs": "ens4"
        }

        self.vlans = []
        self.vms = []
        self.connections = []
        self.settings = {
            "enable_internet": False,
            "enable_vlan_communication": False
        }
        self.vm_internet_access = []
    
    def add_vm(self, vm):
        """Añade una VM a la topología"""
        if isinstance(vm, dict):
            self.vms.append(vm)
        else:
            self.vms.append(vm.to_dict())
    
    def add_connection(self, connection):
        """Añade una conexión a la topología"""
        if isinstance(connection, dict):
            self.connections.append(connection)
        else:
            self.connections.append(connection.to_dict())
    
    def get_vm_by_name(self, name):
        """Busca una VM por su nombre"""
        for vm in self.vms:
            if vm["name"] == name:
                return vm
        return None
    
    def get_next_vm_id(self):
        """Obtiene el siguiente ID disponible para una VM"""
        if not self.vms:
            return 1
        
        vm_ids = []
        for vm in self.vms:
            # Extraer el número de la VM del nombre (asumiendo formato "vmX")
            try:
                vm_id = int(vm["name"][2:])
                vm_ids.append(vm_id)
            except ValueError:
                continue
        
        if not vm_ids:
            return 1
        
        return max(vm_ids) + 1
    
    def to_dict(self):
        """Convierte la topología a un diccionario para serialización"""
        return {
            "name": self.name,
            "nodes": self.nodes,
            "interfaces": self.interfaces,
            "vlans": self.vlans,
            "vms": self.vms,
            "connections": self.connections,
            "settings": self.settings,
            "vm_internet_access": self.vm_internet_access
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una topología a partir de un diccionario"""
        topology = cls()
        topology.name = data.get("name", "")
        topology.nodes = data.get("nodes", topology.nodes)
        topology.interfaces = data.get("interfaces", topology.interfaces)
        topology.vlans = data.get("vlans", topology.vlans)
        topology.vms = data.get("vms", [])
        topology.connections = data.get("connections", [])
        topology.settings = data.get("settings", topology.settings)
        topology.vm_internet_access = data.get("vm_internet_access", [])
        return topology
