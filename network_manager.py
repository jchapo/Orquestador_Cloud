import subprocess
import xml.etree.ElementTree as ET
import time

class NetworkManager:
    def __init__(self):
        self.ovs_bridge = "br0"
        self.setup_base_bridge()

    def setup_base_bridge(self):
        """Configura el bridge principal de Open vSwitch"""
        subprocess.run(["sudo", "ovs-vsctl", "add-br", self.ovs_bridge], check=True)
        subprocess.run(["sudo", "ip", "link", "set", self.ovs_bridge, "up"], check=True)

    def create_namespace(self, ns_name, dhcp_enabled=True, internet_access=False):
        """Crea un namespace con servidor DHCP opcional"""
        # Crear namespace
        subprocess.run(["sudo", "ip", "netns", "add", ns_name], check=True)
        
        # Configurar interfaz para el namespace
        if dhcp_enabled:
            self._setup_dhcp_server(ns_name)
        
        if internet_access:
            self._enable_internet_access(ns_name)

    def _setup_dhcp_server(self, ns_name):
        """Configura un servidor DHCP en el namespace"""
        # Crear par de interfaces virtuales
        veth_host = f"veth-{ns_name}-h"
        veth_ns = f"veth-{ns_name}-ns"
        
        subprocess.run(["sudo", "ip", "link", "add", veth_host, "type", "veth", "peer", "name", veth_ns], check=True)
        subprocess.run(["sudo", "ip", "link", "set", veth_ns, "netns", ns_name], check=True)
        
        # Configurar IPs
        subnet = "192.168.100"
        subprocess.run(["sudo", "ip", "addr", "add", f"{subnet}.1/24", "dev", veth_host], check=True)
        subprocess.run(["sudo", "ip", "link", "set", veth_host, "up"], check=True)
        
        # En el namespace
        subprocess.run(["sudo", "ip", "netns", "exec", ns_name, "ip", "addr", "add", f"{subnet}.2/24", "dev", veth_ns], check=True)
        subprocess.run(["sudo", "ip", "netns", "exec", ns_name, "ip", "link", "set", veth_ns, "up"], check=True)
        subprocess.run(["sudo", "ip", "netns", "exec", ns_name, "ip", "link", "set", "lo", "up"], check=True)
        
        # Instalar y configurar dnsmasq como DHCP
        subprocess.run(["sudo", "ip", "netns", "exec", ns_name, "apt-get", "install", "-y", "dnsmasq"], check=True)
        
        with open(f"/etc/dnsmasq-{ns_name}.conf", "w") as f:
            f.write(f"""
            interface={veth_ns}
            dhcp-range={subnet}.10,{subnet}.100,255.255.255.0
            dhcp-option=3,{subnet}.1
            """)
        
        subprocess.run(["sudo", "ip", "netns", "exec", ns_name, "dnsmasq", 
                       "--conf-file", f"/etc/dnsmasq-{ns_name}.conf"], check=True)

    def _enable_internet_access(self, ns_name):
        """Habilita NAT para acceso a internet desde el namespace"""
        # Configurar NAT
        subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", 
                       "-s", "192.168.100.0/24", "-j", "MASQUERADE"], check=True)
        subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-i", "br0", 
                       "-j", "ACCEPT"], check=True)

    def create_topology(self, topology_type, vm_count, vlan_id=None):
        """Crea una topología de VMs interconectadas"""
        if topology_type == "lineal":
            return self._create_linear_topology(vm_count, vlan_id)
        elif topology_type == "anillo":
            return self._create_ring_topology(vm_count, vlan_id)
        else:
            raise ValueError("Topología no soportada")

    def _create_linear_topology(self, vm_count, vlan_id):
        """Topología lineal: VM1 <-> VM2 <-> VM3 ..."""
        vms = []
        for i in range(1, vm_count + 1):
            vm_name = f"vm-linear-{i}"
            vm = self._create_vm(vm_name)
            
            # Conectar al bridge
            tap_iface = f"tap-{vm_name}"
            subprocess.run(["sudo", "ovs-vsctl", "add-port", self.ovs_bridge, tap_iface], check=True)
            
            if vlan_id:
                subprocess.run(["sudo", "ovs-vsctl", "set", "port", tap_iface, f"tag={vlan_id}"], check=True)
            
            vms.append(vm)
        
        return vms

    def _create_ring_topology(self, vm_count, vlan_id):
        """Topología en anillo: VM1 <-> VM2 <-> VM3 ... <-> VM1"""
        vms = []
        interfaces = []
        
        # Crear todas las VMs primero
        for i in range(1, vm_count + 1):
            vm_name = f"vm-ring-{i}"
            vm = self._create_vm(vm_name)
            vms.append(vm)
            
            # Crear dos interfaces por VM (excepto la última)
            if i < vm_count:
                iface1 = f"tap-{vm_name}-1"
                iface2 = f"tap-{vm_name}-2"
            else:
                # Conectar la última VM con la primera
                iface1 = f"tap-{vm_name}-1"
                iface2 = f"tap-{vms[0]['name']}-2"
            
            interfaces.append((vm_name, iface1, iface2))
        
        # Configurar conexiones en OVS
        for vm_name, iface1, iface2 in interfaces:
            subprocess.run(["sudo", "ovs-vsctl", "add-port", self.ovs_bridge, iface1], check=True)
            subprocess.run(["sudo", "ovs-vsctl", "add-port", self.ovs_bridge, iface2], check=True)
            
            if vlan_id:
                subprocess.run(["sudo", "ovs-vsctl", "set", "port", iface1, f"tag={vlan_id}"], check=True)
                subprocess.run(["sudo", "ovs-vsctl", "set", "port", iface2, f"tag={vlan_id}"], check=True)
        
        return vms

    def _create_vm(self, name, cpu=1, memory=1024):
        """Crea una VM usando QEMU/KVM"""
        disk_path = f"/var/lib/libvirt/images/{name}.qcow2"
        
        # Crear imagen de disco (si no existe)
        subprocess.run([
            "sudo", "qemu-img", "create", "-f", "qcow2", 
            disk_path, "10G"
        ], check=True)
        
        # Definir XML para Libvirt
        xml_config = f"""
        <domain type='kvm'>
          <name>{name}</name>
          <memory unit='MB'>{memory}</memory>
          <vcpu>{cpu}</vcpu>
          <os>
            <type arch='x86_64'>hvm</type>
            <boot dev='hd'/>
          </os>
          <devices>
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='{disk_path}'/>
              <target dev='vda' bus='virtio'/>
            </disk>
            <interface type='bridge'>
              <source bridge='{self.ovs_bridge}'/>
              <virtualport type='openvswitch'/>
              <model type='virtio'/>
            </interface>
            <graphics type='vnc' port='-1'/>
          </devices>
        </domain>
        """
        
        # Registrar y lanzar la VM
        with open(f"/tmp/{name}.xml", "w") as f:
            f.write(xml_config)
            
        subprocess.run([
            "sudo", "virsh", "define", f"/tmp/{name}.xml"
        ], check=True)
        
        subprocess.run([
            "sudo", "virsh", "start", name
        ], check=True)
        
        return {
            "name": name,
            "status": "running",
            "vnc_port": 5900 + len(subprocess.getoutput("virsh list --all").splitlines()) - 2
        }
