# Topology Manager

Este repositorio contiene una aplicación para la gestión y creación de topologías de red.

## Estructura del Proyecto

```
cloud-orchestrator/
├── README.md
├── add_interface.sh
├── ana
├── ana_vlan_topology.png
├── auth.py
├── cleanup_topology.sh
├── connect_vlans.sh
├── correo.py
├── create_flexible_topology.sh
├── create_network.sh
├── create_vm.sh
├── flavors/
├── images/
├── initialize_headnode.sh
├── initialize_worker.sh
├── internet_access.sh
├── main.py
├── menus/
├── main.py
├── network_manager.py
├── quick_cleanup.sh
├── topologia_app.py
├── topology_manager/
├── visualize_vlan_topology.py
└── vm_topology_creator.py
```

## Características Principales

### Interfaz de Usuario
Para verificar la interfaz de usuario, se pueden utilizar los siguientes archivos Python:

1. **main.py**:
   ```
   python3 main.py 
   ```
   - Implementa la autenticación con base de datos MySQL
   - Para probar la autenticación, usar:
     - Usuario: `user`
     - Contraseña: `user`

3. **topologia_app.py**:
   ```
   python3 topologia_app.py
   ```
   - Contiene el desarrollo del menú de opciones para la creación de topologías
   ![image](https://github.com/user-attachments/assets/9e59f687-224d-4f62-8294-1c74580c79f3)

   - Permite la gestión completa de diferentes configuraciones de red
   ![ana_vlan_topology](https://github.com/user-attachments/assets/19df1326-44c2-4768-b595-673f14cc6ab7)


### Conexión a Base de Datos
Para verificar la conexión con la base de datos, utilizar el siguiente comando:
```
mysql -u root -p
show databases;
```
Contraseña: `3534061`

![image](https://github.com/user-attachments/assets/e382d6a9-2832-4363-8acb-16734d6c4a63)

## Scripts de Utilidad

El proyecto incluye varios scripts para:
- Creación de topologías
- Limpieza de configuraciones
- Inicialización de nodos
- Visualización de redes
- Configuración de máquinas virtuales
- Gestión de VLANs

## Ejemplos de Topologías

En los directorios `ana/`, `anapaula/`, `anillo_topo/`, `juan/` y `topo_exa/` se encuentran ejemplos de diferentes configuraciones de topologías.
