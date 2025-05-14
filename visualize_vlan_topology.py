#!/usr/bin/env python3

"""
Visualizador de Topologías VLAN

Este script genera una representación gráfica de una topología basada en VLANs
a partir de un archivo JSON de configuración.
"""

import json
import sys
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import argparse
import random

def generate_color():
    """Genera un color aleatorio brillante para las VLANs"""
    r = random.randint(128, 255)
    g = random.randint(128, 255)
    b = random.randint(128, 255)
    return f"#{r:02x}{g:02x}{b:02x}"

def visualize_vlan_topology(topology_file):
    """Visualiza una topología VLAN a partir de un archivo JSON"""
    # Verificar que el archivo existe
    if not os.path.exists(topology_file):
        print(f"Error: El archivo {topology_file} no existe.")
        return False
    
    # Cargar la topología
    try:
        with open(topology_file, 'r') as f:
            topology = json.load(f)
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return False
    
    # Crear el grafo
    G = nx.Graph()
    
    # Mapear workers a colores
    worker_colors = {
        1: "lightblue",
        2: "lightgreen",
        3: "lightcoral"
    }
    
    # Colores para VLANs
    vlan_colors = {}
    
    # Añadir nodos (VMs)
    for vm in topology.get("vms", []):
        worker = vm.get("worker", 1)
        color = worker_colors.get(worker, "lightgray")
        
        # Comprobar si la VM tiene acceso a Internet
        has_internet = vm["name"] in topology.get("vm_internet_access", [])
        
        # Añadir borde rojo si tiene acceso a Internet
        edge_color = 'red' if has_internet else 'black'
        
        G.add_node(vm["name"], color=color, edge_color=edge_color, worker=worker)
    
    # Mapear conexiones a VLANs
    connection_vlans = {}
    vlan_id = 500  # Comenzar desde VLAN 500
    
    # Primero, identificar pares de conexiones bidireccionales
    connections = topology.get("connections", [])
    processed_pairs = set()
    
    for conn in connections:
        from_vm = conn["from"]
        to_vm = conn["to"]
        pair = tuple(sorted([from_vm, to_vm]))
        
        if pair not in processed_pairs:
            connection_vlans[pair] = vlan_id
            if vlan_id not in vlan_colors:
                vlan_colors[vlan_id] = generate_color()
            vlan_id += 1
            processed_pairs.add(pair)
    
    # Añadir conexiones
    for conn in connections:
        from_vm = conn["from"]
        to_vm = conn["to"]
        pair = tuple(sorted([from_vm, to_vm]))
        
        vlan = connection_vlans[pair]
        color = vlan_colors[vlan]
        
        # Solo añadir el borde si no existe ya
        if not G.has_edge(from_vm, to_vm):
            G.add_edge(from_vm, to_vm, color=color, vlan=vlan, weight=2)
    
    # Dibujar el grafo
    plt.figure(figsize=(12, 10))
    
    # Determinar el layout según la cantidad de nodos
    if len(G.nodes()) <= 10:
        pos = nx.spring_layout(G, seed=42, k=0.5)  # k controla la separación entre nodos
    else:
        pos = nx.kamada_kawai_layout(G)
    
    # Obtener colores de nodos, bordes y aristas
    node_colors = [G.nodes[n]['color'] for n in G.nodes()]
    edge_colors = [G.nodes[n]['edge_color'] for n in G.nodes()]
    edge_vlan_colors = [G.edges[e]['color'] for e in G.edges()]
    
    # Dibujar nodos y conexiones
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, edgecolors=edge_colors, node_size=700)
    nx.draw_networkx_edges(G, pos, width=3, alpha=0.7, edge_color=edge_vlan_colors)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # Añadir etiquetas de VLAN a las aristas
    edge_labels = {(u, v): f"VLAN {d['vlan']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    # Añadir título y leyenda
    plt.title(f"Topología VLAN: {topology.get('name', 'Sin nombre')}")
    
    # Crear leyenda para workers
    worker_patches = []
    for worker_id, color in worker_colors.items():
        worker_patches.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                                      markersize=10, label=f'Worker {worker_id}'))
    
    # Añadir leyenda para acceso a Internet
    internet_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', 
                               markeredgecolor='red', markersize=10, label='Acceso a Internet')
    worker_patches.append(internet_patch)
    
    # Crear leyenda para VLANs
    vlan_patches = []
    for vlan_id, color in vlan_colors.items():
        vlan_patches.append(plt.Line2D([0], [0], color=color, lw=2, label=f'VLAN {vlan_id}'))
    
    # Añadir ambas leyendas
    plt.legend(handles=worker_patches + vlan_patches, loc='upper right')
    
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen
    output_file = f"{os.path.splitext(topology_file)[0]}_vlan_topology.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualización guardada como: {output_file}")
    
    # Intentar mostrar la imagen si estamos en un entorno interactivo
    try:
        plt.figure(figsize=(12, 10))
        img = plt.imread(output_file)
        plt.imshow(img)
        plt.axis('off')
        plt.show()
    except Exception:
        print("No se pudo mostrar la imagen, pero se guardó correctamente.")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualizador de topologías VLAN")
    parser.add_argument("topology_file", help="Archivo JSON de la topología a visualizar")
    
    args = parser.parse_args()
    
    try:
        # Verificar que matplotlib y networkx estén instalados
        import importlib
        for module in ['matplotlib', 'networkx']:
            try:
                importlib.import_module(module)
            except ImportError:
                print(f"Error: Se requiere el módulo '{module}'. Instálelo con 'pip install {module}'")
                sys.exit(1)
        
        visualize_vlan_topology(args.topology_file)
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
