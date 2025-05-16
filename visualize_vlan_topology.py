#!/usr/bin/env python3

"""
Visualizador de Topologías VLAN

Este script genera una representación gráfica de una topología basada en VLANs
a partir de un archivo JSON de configuración, utilizando los IDs de VLAN definidos
en las conexiones.
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
    if not os.path.exists(topology_file):
        print(f"Error: El archivo {topology_file} no existe.")
        return False

    try:
        with open(topology_file, 'r') as f:
            topology = json.load(f)
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return False

    G = nx.Graph()

    worker_colors = {
        1: "lightblue",
        2: "lightgreen",
        3: "lightcoral"
    }

    vlan_colors = {}

    for vm in topology.get("vms", []):
        worker = vm.get("worker", 1)
        color = worker_colors.get(worker, "lightgray")
        has_internet = vm["name"] in topology.get("vm_internet_access", [])
        edge_color = 'red' if has_internet else 'black'

        flavor = vm.get("flavor")
        #print(f"DEBUG: {vm['name']} flavor = {flavor} (type: {type(flavor)})")

        flavor_name = flavor["name"] if isinstance(flavor, dict) else "No definido"

        G.add_node(vm["name"], color=color, edge_color=edge_color, worker=worker, flavor=flavor_name)

    connection_vlans = {}
    default_vlan_id = 100
    connections = topology.get("connections", [])
    processed_pairs = set()

    for conn in connections:
        from_vm = conn["from"]
        to_vm = conn["to"]
        pair = tuple(sorted([from_vm, to_vm]))
        vlan_id = conn.get("vlan_id", default_vlan_id)

        if pair not in processed_pairs:
            connection_vlans[pair] = vlan_id
            if vlan_id not in vlan_colors:
                vlan_colors[vlan_id] = generate_color()
            processed_pairs.add(pair)

    for conn in connections:
        from_vm = conn["from"]
        to_vm = conn["to"]
        pair = tuple(sorted([from_vm, to_vm]))
        vlan = connection_vlans[pair]
        color = vlan_colors[vlan]

        if not G.has_edge(from_vm, to_vm):
            G.add_edge(from_vm, to_vm, color=color, vlan=vlan, weight=2)

    plt.figure(figsize=(12, 10))
    if len(G.nodes()) <= 10:
        pos = nx.spring_layout(G, seed=42, k=0.35)
    else:
        pos = nx.kamada_kawai_layout(G)

    node_colors = [G.nodes[n]['color'] for n in G.nodes()]
    edge_colors = [G.nodes[n]['edge_color'] for n in G.nodes()]
    edge_vlan_colors = [G.edges[e]['color'] for e in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, edgecolors=edge_colors, node_size=6000)
    nx.draw_networkx_edges(G, pos, width=3, alpha=0.7, edge_color=edge_vlan_colors)

    node_labels = {node: f"{node}\n({G.nodes[node]['flavor']})" for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=18, font_weight='bold')

    edge_labels = {(u, v): f"VLAN {d['vlan']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=16)

    plt.title(f"Topología VLAN: {topology.get('name', 'Sin nombre')}")

    worker_patches = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                   markersize=10, label=f'Worker {worker_id}')
        for worker_id, color in worker_colors.items()
    ]
    internet_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', 
                                 markeredgecolor='red', markersize=10, label='Acceso a Internet')
    worker_patches.append(internet_patch)

    vlan_patches = [
        plt.Line2D([0], [0], color=color, lw=2, label=f'VLAN {vlan_id}')
        for vlan_id, color in sorted(vlan_colors.items())
    ]

    unique_flavors = set(nx.get_node_attributes(G, 'flavor').values())
    flavor_patches = [
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10, 
                label=f'Flavor: {flavor}')
        for flavor in sorted(unique_flavors)
    ]


    plt.legend(handles=worker_patches + vlan_patches + flavor_patches, loc='upper right', fontsize=8)

    plt.axis('off')
    plt.tight_layout()

    output_file = f"{os.path.splitext(topology_file)[0]}_vlan_topology.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Visualización guardada como: {output_file}")

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
