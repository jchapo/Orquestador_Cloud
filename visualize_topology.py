#!/usr/bin/env python3

"""
Visualizador de Topologías
==========================

Esta herramienta permite visualizar topologías existentes en formato gráfico.
Genera una representación visual de la topología a partir del archivo JSON de configuración.
"""

import json
import sys
import os
import matplotlib.pyplot as plt
import networkx as nx
import argparse

def visualize_topology(topology_file):
    """Visualiza una topología a partir de un archivo JSON."""
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
    
    # Colores para VMs según VLAN
    vlan_colors = {
        100: 'lightblue',
        200: 'lightgreen',
        300: 'lightcoral',
        400: 'lightyellow',
        500: 'lightpink'
    }
    
    # Añadir nodos (VMs)
    for vm in topology.get("vms", []):
        vlan_id = vm.get("vlan", 100)
        color = vlan_colors.get(vlan_id, 'lightgray')
        
        # Comprobar si la VM tiene acceso a Internet
        has_internet = vm["name"] in topology.get("vm_internet_access", [])
        
        # Añadir borde rojo si tiene acceso a Internet
        edge_color = 'red' if has_internet else 'black'
        
        G.add_node(vm["name"], color=color, edge_color=edge_color)
    
    # Añadir conexiones
    for conn in topology.get("connections", []):
        G.add_edge(conn["from"], conn["to"])
    
    # Dibujar el grafo
    plt.figure(figsize=(12, 8))
    
    # Usar un layout apropiado
    if len(G.nodes()) <= 10:
        pos = nx.spring_layout(G, seed=42)  # Disposición de resorte para grafos pequeños
    else:
        pos = nx.kamada_kawai_layout(G)  # Mejor para grafos más grandes
    
    # Obtener colores de nodos y bordes
    node_colors = [G.nodes[n]['color'] for n in G.nodes()]
    edge_colors = [G.nodes[n]['edge_color'] for n in G.nodes()]
    
    # Dibujar nodos y conexiones
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, edgecolors=edge_colors, node_size=700)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # Añadir título y leyenda
    plt.title(f"Topología: {topology.get('name', 'Sin nombre')}")
    
    # Crear leyenda para VLANs
    vlan_patches = []
    for vlan_id, color in vlan_colors.items():
        if any(vm.get("vlan") == vlan_id for vm in topology.get("vms", [])):
            vlan_patches.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                                          markersize=10, label=f'VLAN {vlan_id}'))
    
    # Añadir leyenda para acceso a Internet
    internet_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', 
                               markeredgecolor='red', markersize=10, label='Acceso a Internet')
    vlan_patches.append(internet_patch)
    
    plt.legend(handles=vlan_patches, loc='upper right')
    
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen
    output_file = f"{os.path.splitext(topology_file)[0]}_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualización guardada como: {output_file}")
    
    # Intentar mostrar la imagen si estamos en un entorno interactivo
    try:
        plt.figure(figsize=(12, 8))
        img = plt.imread(output_file)
        plt.imshow(img)
        plt.axis('off')
        plt.show()
    except Exception:
        print("No se pudo mostrar la imagen, pero se guardó correctamente.")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualizador de topologías de red")
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
        
        visualize_topology(args.topology_file)
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
