#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import random
import time
import ipaddress
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Set, Tuple

class VMTopologyCreator:
    def __init__(self):
        self.vlan_id = 110  # Default VLAN ID
        self.vm_count = 0
        self.connections = {}  # VM connections: {vm_id: [connected_vm_ids]}
        self.internet_vms = set()  # VMs with internet access
        self.ovs_bridge = "br-int"  # Default OVS bridge
        self.internet_iface = self._get_default_internet_iface()
        self.base_vnc_port = 1  # Starting VNC port
        self.vm_ips = {}  # To track assigned IPs
        self.vm_tap_interfaces = {}  # Track tap interfaces for each VM
        
        # Network configuration
        self.network_cidr = "192.168.110.0/24"  # VLAN 110 subnet
        self.gateway_ip = "192.168.110.1"
        self.network = ipaddress.IPv4Network(self.network_cidr)
        self.available_ips = list(self.network.hosts())[2:]  # Skip .1 (gateway) and .2 (DHCP)
    
    def _get_default_internet_iface(self) -> str:
        """Get the default internet interface of the system"""
        try:
            # Get the interface with default route
            cmd = "ip route | grep default | awk '{print $5}'"
            result = subprocess.check_output(cmd, shell=True, text=True).strip()
            return result
        except subprocess.SubprocessError:
            # If command fails, try common interface names
            for iface in ["eth0", "ens3", "ens4", "enp0s3"]:
                try:
                    subprocess.check_output(f"ip link show {iface}", shell=True)
                    return iface
                except subprocess.SubprocessError:
                    continue
            return "eth0"  # Default fallback
    
    def _is_valid_vm_id(self, vm_id: int) -> bool:
        """Check if VM ID is valid"""
        return 1 <= vm_id <= self.vm_count
    
    def _generate_mac_address(self, vm_id: int) -> str:
        """Generate a unique MAC address for a VM"""
        return f"52:54:00:11:10:{vm_id:02x}"
    
    def _assign_ip_to_vm(self, vm_id: int) -> str:
        """Assign an IP address to a VM"""
        if vm_id in self.vm_ips:
            return self.vm_ips[vm_id]
        
        if not self.available_ips:
            raise ValueError("No more IP addresses available in the subnet!")
        
        ip = str(self.available_ips.pop(0))
        self.vm_ips[vm_id] = ip
        return ip
    
    def _create_network(self) -> bool:
        """Create the VLAN network if it doesn't exist"""
        print(f"Creating VLAN {self.vlan_id} network...")
        
        # Check if VLAN interface already exists
        cmd = f"ip link show vlan{self.vlan_id} 2>/dev/null"
        if os.system(cmd) == 0:
            print(f"VLAN {self.vlan_id} interface already exists.")
            return True
        
        # Create network using the create_network.sh script
        network_name = f"vlan{self.vlan_id}"
        dhcp_range = f"192.168.{self.vlan_id}.10,192.168.{self.vlan_id}.200"
        
        cmd = f"sudo ./scripts/network/create_network.sh {network_name} {self.vlan_id} {self.network_cidr} {dhcp_range}"
        print(f"Running: {cmd}")
        if os.system(cmd) != 0:
            print("Failed to create network!")
            return False
        
        return True
    
    def _setup_internet_access(self) -> bool:
        """Configure internet access for the VLAN"""
        print(f"Setting up internet access for VLAN {self.vlan_id}...")
        cmd = f"sudo ./scripts/network/internet_access.sh {self.vlan_id} {self.internet_iface}"
        print(f"Running: {cmd}")
        if os.system(cmd) != 0:
            print("Failed to configure internet access!")
            return False
        return True
    
    def _create_vm(self, vm_id: int) -> bool:
        """Create a single VM"""
        vm_name = f"vm{vm_id}"
        mac_address = self._generate_mac_address(vm_id)
        vnc_port = self.base_vnc_port + vm_id - 1
        
        print(f"Creating VM {vm_name}...")
        cmd = f"sudo ./scripts/vm_management/create_vm.sh {vm_name} {self.ovs_bridge} {self.vlan_id} {vnc_port} {mac_address}"
        print(f"Running: {cmd}")
        
        if os.system(cmd) != 0:
            print(f"Failed to create VM {vm_name}!")
            return False
        
        # Store the tap interface name for this VM
        self.vm_tap_interfaces[vm_id] = f"tap_{vm_name}"
        return True
    
    def _configure_network_restrictions(self) -> bool:
        """Configure OVS flow rules to implement the network topology restrictions"""
        print("Configuring network restrictions based on VM connections...")
        
        # Create graph from connections to validate reachability
        G = nx.Graph()
        for vm_id in range(1, self.vm_count + 1):
            G.add_node(vm_id)
        
        for vm_id, connected_vms in self.connections.items():
            for connected_vm in connected_vms:
                G.add_edge(vm_id, connected_vm)
        
        # Visualize the network topology
        self._visualize_topology(G)
        
        # Drop all traffic between VMs by default
        cmd = f"sudo ovs-ofctl del-flows {self.ovs_bridge} 'table=0,priority=1'"
        os.system(cmd)
        
        # Allow ARP and DHCP traffic
        cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=100,arp,actions=normal'"
        os.system(cmd)
        cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=100,udp,tp_dst=67,actions=normal'"
        os.system(cmd)
        cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=100,udp,tp_dst=68,actions=normal'"
        os.system(cmd)
        
        # Allow VM to gateway traffic
        for vm_id in range(1, self.vm_count + 1):
            tap_interface = self.vm_tap_interfaces.get(vm_id)
            if tap_interface:
                # VM to gateway
                cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=50,dl_src={self._generate_mac_address(vm_id)},dl_dst=ff:ff:ff:ff:ff:ff,actions=normal'"
                os.system(cmd)
        
        # Allow traffic between connected VMs
        for vm_id, connected_vms in self.connections.items():
            src_mac = self._generate_mac_address(vm_id)
            
            for dst_vm_id in connected_vms:
                dst_mac = self._generate_mac_address(dst_vm_id)
                
                # Allow traffic from source to destination
                cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=50,dl_src={src_mac},dl_dst={dst_mac},actions=normal'"
                print(f"Allowing traffic from VM{vm_id} to VM{dst_vm_id}: {cmd}")
                os.system(cmd)
        
        # Allow internet access for designated VMs
        for vm_id in self.internet_vms:
            src_mac = self._generate_mac_address(vm_id)
            
            # VM to internet (gateway)
            cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=40,dl_src={src_mac},actions=normal'"
            print(f"Allowing internet access for VM{vm_id}: {cmd}")
            os.system(cmd)
        
        # Set default rule to drop other traffic
        cmd = f"sudo ovs-ofctl add-flow {self.ovs_bridge} 'table=0,priority=1,actions=drop'"
        os.system(cmd)
        
        return True
    
    def _visualize_topology(self, G):
        """Visualize the network topology"""
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)
        
        # Draw regular nodes
        regular_nodes = [n for n in G.nodes() if n not in self.internet_vms]
        nx.draw_networkx_nodes(G, pos, nodelist=regular_nodes, node_color='lightblue', 
                              node_size=500, alpha=0.8)
        
        # Draw internet-connected nodes
        internet_nodes = [n for n in G.nodes() if n in self.internet_vms]
        nx.draw_networkx_nodes(G, pos, nodelist=internet_nodes, node_color='lightgreen', 
                              node_size=500, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
        
        # Draw labels
        labels = {n: f"VM{n}" for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=12)
        
        plt.title("VM Network Topology")
        plt.axis('off')
        
        # Save the visualization
        plt.savefig("vm_topology.png")
        print("Network topology visualization saved as vm_topology.png")
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        dependencies = ["qemu-system-x86_64", "ovs-vsctl", "ovs-ofctl", "ip"]
        
        for dep in dependencies:
            try:
                subprocess.check_output(["which", dep])
            except subprocess.SubprocessError:
                print(f"Required dependency '{dep}' not found. Please install it.")
                return False
        
        # Check if required scripts exist
        required_scripts = ["create_network.sh", "create_vm.sh", "internet_access.sh"]
        for script in required_scripts:
            if not os.path.isfile(script):
                print(f"Required script '{script}' not found in current directory.")
                return False
            
            # Make script executable
            os.system(f"chmod +x {script}")
        
        return True
    
    def run(self):
        """Main execution method"""
        print("=== VM Topology Creator ===")
        
        # Check dependencies
        if not self._check_dependencies():
            print("Missing dependencies. Please install them and try again.")
            return
        
        # Initialize OVS bridge
        print(f"Initializing OVS bridge {self.ovs_bridge}...")
        cmd = f"sudo ovs-vsctl --may-exist add-br {self.ovs_bridge}"
        os.system(cmd)
        
        # Get number of VMs
        while True:
            try:
                self.vm_count = int(input("Enter the number of VMs to create: "))
                if self.vm_count < 1:
                    print("Please enter a positive number.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        # Get VM connections
        print("\nDefine VM connections:")
        print("For each VM, enter the VM numbers it should connect to (space-separated).")
        print("Example: For VM1, entering '2 3' means VM1 connects to VM2 and VM3.")
        
        for i in range(1, self.vm_count + 1):
            while True:
                connections_input = input(f"VM{i} connections: ")
                if not connections_input.strip():
                    self.connections[i] = []
                    break
                
                try:
                    connections = [int(x) for x in connections_input.split()]
                    
                    # Validate connections
                    invalid_connections = [x for x in connections if not self._is_valid_vm_id(x) or x == i]
                    if invalid_connections:
                        print(f"Invalid connections: {invalid_connections}. Please try again.")
                        continue
                    
                    self.connections[i] = connections
                    break
                except ValueError:
                    print("Please enter valid VM numbers separated by spaces.")
        
        # Make connections bidirectional
        for vm_id, connected_vms in list(self.connections.items()):
            for connected_vm in connected_vms:
                if connected_vm not in self.connections:
                    self.connections[connected_vm] = []
                if vm_id not in self.connections[connected_vm]:
                    self.connections[connected_vm].append(vm_id)
        
        # Get internet access
        print("\nDefine VMs with internet access:")
        while True:
            internet_input = input("Enter VM numbers that should have internet access (space-separated): ")
            if not internet_input.strip():
                break
            
            try:
                internet_vms = [int(x) for x in internet_input.split()]
                
                # Validate VM IDs
                invalid_vms = [x for x in internet_vms if not self._is_valid_vm_id(x)]
                if invalid_vms:
                    print(f"Invalid VM numbers: {invalid_vms}. Please try again.")
                    continue
                
                self.internet_vms = set(internet_vms)
                break
            except ValueError:
                print("Please enter valid VM numbers separated by spaces.")
        
        # Create network
        if not self._create_network():
            print("Failed to create network. Exiting.")
            return
        
        # Setup internet access for the VLAN
        if not self._setup_internet_access():
            print("Failed to configure internet access. Exiting.")
            return
        
        # Create VMs
        for i in range(1, self.vm_count + 1):
            if not self._create_vm(i):
                print(f"Failed to create VM{i}. Exiting.")
                return
        
        # Configure network restrictions
        if not self._configure_network_restrictions():
            print("Failed to configure network restrictions. Exiting.")
            return
        
        print("\n=== Topology Creation Complete ===")
        print(f"Created {self.vm_count} VMs in VLAN {self.vlan_id}")
        print("VM connections:")
        for vm_id, connections in self.connections.items():
            print(f"VM{vm_id} -> {', '.join(f'VM{c}' for c in connections)}")
        
        print("\nVMs with internet access:")
        if self.internet_vms:
            print(', '.join(f"VM{vm}" for vm in self.internet_vms))
        else:
            print("None")
        
        print("\nVNC access:")
        for i in range(1, self.vm_count + 1):
            vnc_port = self.base_vnc_port + i - 1
            print(f"VM{i}: localhost:590{vnc_port}")
        
        print("\nTo verify connectivity between VMs, you can login to the VMs and use ping.")
        print("CirrOS login: 'cirros' with password 'gocubsgo'")
        print("\nNote: The network topology visualization has been saved as 'vm_topology.png'")

if __name__ == "__main__":
    creator = VMTopologyCreator()
    creator.run()
