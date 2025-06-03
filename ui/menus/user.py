import subprocess
import mysql.connector


# Conexión a la base de datos
def get_flavors_from_db():
    """Obtiene los flavors desde la base de datos dependiendo del tipo del usuario."""
    # Conectar a la base de datos MySQL
    conn = mysql.connector.connect(
        user="cloud_admin",  # Usuario de la base de datos
        password="admin123",  # Contraseña del usuario
        database="cloud_orchestrator",  # Nombre de la base de datos
        unix_socket="/var/run/mysqld/mysqld.sock"  # Socket Unix para conexión local
    )
    cursor = conn.cursor()

    # Ejecutar la consulta para obtener los flavors según el tipo del usuario (global_role)
    cursor.execute("SELECT tipo, ram, cpu, almacenamiento FROM flavors WHERE tipo = 'user'")
    flavors = cursor.fetchall()

    cursor.close()
    conn.close()

    return flavors

def show_regular_user_menu():
    """Menú para Usuario Regular"""
    print("1. Crear una nueva topología")
    print("2. Crear una topología preestablecida")
    print("3. Ver las topologías creadas")
    print("4. Eliminar una topología")
    print("Q. Salir")
    return input("\nSeleccione una opción: ")

def handle_user_choice(choice, auth):
    """Manejador de opciones para usuario regular"""
    if choice.lower() == 'q':
        return
    
    # Métodos para crear, ver y eliminar topologías
    options = {
        "1": lambda: crear_topologia(auth),
        "2": lambda: crear_topologia_predefinida(auth),
        "3": lambda: ver_topologias(auth),
        "4": lambda: eliminar_topologia(auth)
    }
    
    if choice in options:
        options[choice]()
    else:
        print("❌ Opción no válida.")
        input("\nPresione Enter para continuar...")

def get_os_images_from_db():
    """Obtiene las imágenes de sistemas operativos disponibles para el usuario."""
    conn = mysql.connector.connect(
        user="cloud_admin",
        password="admin123",
        database="cloud_orchestrator",
        unix_socket="/var/run/mysqld/mysqld.sock"
    )
    cursor = conn.cursor()

    # Consulta a la tabla os_images filtrando por tipo 'user'
    cursor.execute("SELECT nombre, path FROM os_images WHERE tipo = 'user'")
    os_images = cursor.fetchall()

    cursor.close()
    conn.close()

    return os_images

def confirmar_y_crear_topologia(topologia_nombre, topologia_opcion, cantidad_nodos, sistema_operativo, os_path, flavor):
    """Solicita confirmación y luego ejecuta la creación de la topología."""
    print("\n=== Confirmación de la Topología ===")
    print("¿Desea proceder con la creación de la topología?")
    print("1. Sí, crear ahora")
    print("2. No, volver al menú")
    
    while True:
        confirmacion = input("\nSeleccione una opción (1/2): ")
        if confirmacion == "1":
            crear_topologia_vms(
                topologia_nombre,
                topologia_opcion,
                cantidad_nodos,
                sistema_operativo,
                os_path,
                flavor
            )
            break
        elif confirmacion == "2":
            print("❌ Creación cancelada.")
            return
        else:
            print("❌ Opción no válida. Intente nuevamente.")

def crear_topologia_vms(topologia_nombre, topologia_opcion, cantidad_nodos, sistema_operativo, os_path, flavor):
    """Crea una topología con nombres personalizados basados en topologia_nombre"""
    
    # Generar prefijos únicos (eliminando espacios y caracteres especiales)
    nombre_limpio = "".join(c for c in topologia_nombre if c.isalnum())
    prefijo = nombre_limpio.lower()[:8]  # Limita a 8 caracteres
    
    # Nombres personalizados
    ns_dhcp = f"ns-dhcp-{prefijo}"
    ovs_switch = f"ovs-{prefijo}"
    
    try:
        print(f"\n🚀 Creando topología '{topologia_nombre}' (Prefijo: {prefijo})...")
        
        # --- 1. Limpieza previa (por si existe una topología con el mismo nombre) ---
        sudo(f"ip netns del {ns_dhcp} 2>/dev/null || true")
        sudo(f"ovs-vsctl del-br {ovs_switch} 2>/dev/null || true")
        
        # --- 2. Crear namespace para DHCP ---
        print(f"[1/8] Creando namespace {ns_dhcp}...")
        sudo(f"ip netns add {ns_dhcp}")
        
        # --- 3. Crear switch OVS ---
        print(f"[2/8] Creando switch {ovs_switch}...")
        sudo(f"ovs-vsctl add-br {ovs_switch}")
        
        # --- 4. Crear interfaces TAP ---
        print(f"[3/8] Creando {cantidad_nodos} interfaces TAP...")
        for i in range(1, cantidad_nodos + 1):
            tap_name = f"{ovs_switch}-tap{i}"
            sudo(f"ip tuntap add mode tap name {tap_name}")
            sudo(f"ip link set {tap_name} up")
            sudo(f"ovs-vsctl add-port {ovs_switch} {tap_name}")
        
        # --- 5. Configurar interfaz DHCP ---
        print("[4/8] Configurando DHCP...")
        sudo(f"ovs-vsctl add-port {ovs_switch} {ovs_switch}-tap0 -- set interface {ovs_switch}-tap0 type=internal")
        sudo(f"ip link set {ovs_switch}-tap0 netns {ns_dhcp}")
        sudo(f"ip netns exec {ns_dhcp} ip link set dev lo up")
        sudo(f"ip netns exec {ns_dhcp} ip link set dev {ovs_switch}-tap0 up")
        sudo(f"ip netns exec {ns_dhcp} ip address add 10.0.0.14/29 dev {ovs_switch}-tap0")
        
        # --- 6. Levantar VMs ---
        print("[5/8] Iniciando máquinas virtuales...")
        for i in range(1, cantidad_nodos + 1):
            mac = f"00:16:3e:{i:02x}:{i+1:02x}:{i+2:02x}"
            cmd = f"""
            qemu-system-x86_64 \
                -enable-kvm \
                -vnc 0.0.0.0:{i} \
                -netdev tap,id={ovs_switch}-tap{i},ifname={ovs_switch}-tap{i},script=no,downscript=no \
                -device e1000,netdev={ovs_switch}-tap{i},mac={mac} \
                -m {flavor[1]} \
                -smp {flavor[2]} \
                -hda {os_path} \
                -daemonize \
                -snapshot
            """
            subprocess.run(cmd.strip(), shell=True, check=True)
        
        # --- 7. Configurar DHCP y NAT ---
        print("[6/8] Configurando servicios de red...")
        sudo(f"ip netns exec {ns_dhcp} dnsmasq --interface={ovs_switch}-tap0 --dhcp-range=10.0.0.10,10.0.0.13,255.255.255.248 --dhcp-option=3,10.0.0.9")
        sudo(f"ip address add 10.0.0.9/29 dev {ovs_switch}")
        sudo("iptables -t nat -A POSTROUTING -s 10.0.0.8/29 -j MASQUERADE")
        sudo("sysctl -w net.ipv4.ip_forward=1")
        
        print(f"\n✅ ¡Topología '{topologia_nombre}' creada exitosamente!")
        print(f"🔹 Namespace DHCP: {ns_dhcp}")
        print(f"🔹 Switch OVS: {ovs_switch}")
        print(f"🔹 Acceso VNC: Puertos 5901-590{cantidad_nodos}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"Ejecuta esto para limpiar: sudo ip netns del {ns_dhcp} && sudo ovs-vsctl del-br {ovs_switch}")

def sudo(command):
    """Ejecuta un comando con sudo."""
    import subprocess
    subprocess.run(f"sudo {command}", shell=True, check=True)

def crear_topologia_predefinida(auth):
    """Crear una topología preestablecida"""
    auth.clear_screen()
    print("\n=== Crear Topología Preestablecida ===")
    print("Seleccione una topología predefinida:")
    print("1. Lineal")
    print("2. Anillo")
    print("3. Estrella")
    topologia_opcion = input("\nSeleccione una opción (1, 2, 3): ")
    
    # Validar opción seleccionada
    if topologia_opcion not in ["1", "2", "3"]:
        print("❌ Opción no válida.")
        input("\nPresione Enter para continuar...")
        return
    
    # Obtener nombre para la topología
    topologia_nombre = input("\nIngrese el nombre de la topología: ")
    
    # Obtener cantidad de nodos (validación según topología)
    while True:
        try:
            cantidad_nodos = int(input("\nIngrese la cantidad de vm's: "))
            if topologia_opcion == "1" and cantidad_nodos < 2:
                print("❌ La topología lineal requiere al menos 2 nodos.")
            elif topologia_opcion == "2" and cantidad_nodos < 3:
                print("❌ La topología en anillo requiere al menos 3 nodos.")
            elif topologia_opcion == "3" and cantidad_nodos < 2:
                print("❌ La topología en estrella requiere al menos 2 nodos.")
            else:
                break
        except ValueError:
            print("❌ Por favor, ingrese un número válido.")
    
    # Obtener flavors desde la base de datos
    flavors = get_flavors_from_db()

    print("\n=== Configuración de Flavors ===")
    if flavors:
        for index, flavor in enumerate(flavors, start=1):
            tipo, ram, cpu, almacenamiento = flavor
            print(f"{index}. {ram}GB RAM, {cpu} CPU(s), {almacenamiento}GB Disk")
        
        # Selección del flavor
        while True:
            flavor_opcion = input("\nSeleccione el flavor para todas las máquinas virtuales: ")
            try:
                flavor_opcion = int(flavor_opcion) - 1
                if 0 <= flavor_opcion < len(flavors):
                    flavor = flavors[flavor_opcion]
                    break
                else:
                    print("❌ Opción no válida. Intente nuevamente.")
            except ValueError:
                print("❌ Opción no válida. Intente nuevamente.")
    else:
        print("❌ No se encontraron flavors disponibles.")
        return

    # Obtener sistemas operativos desde la base de datos
    os_images = get_os_images_from_db()

    print("\n=== Configuración de Sistema Operativo ===")
    if os_images:
        for index, os_image in enumerate(os_images, start=1):
            nombre, path = os_image
            print(f"{index}. {nombre} (Ruta: {path})")  # Mostrar nombre y ruta
        
        # Selección del SO
        while True:
            os_opcion = input("\nSeleccione el sistema operativo para las máquinas virtuales: ")
            try:
                os_opcion = int(os_opcion) - 1
                if 0 <= os_opcion < len(os_images):
                    sistema_operativo = os_images[os_opcion][0]  # Nombre (ej: "Cirros")
                    os_path = os_images[os_opcion][1]  # Ruta (ej: "/home/ubuntu/vm-images/cirros.img")
                    break
                else:
                    print("❌ Opción no válida. Intente nuevamente.")
            except ValueError:
                print("❌ Opción no válida. Intente nuevamente.")
    else:
        print("❌ No se encontraron imágenes de sistema operativo disponibles.")
        sistema_operativo = "Cirros"  # Valor por defecto
        os_path = "/home/ubuntu/vm-images/cirros.img"  # Ruta por defecto

    # Mostrar resumen de la topología (incluyendo la ruta del SO)
    print("\n=== Resumen de la Topología ===")
    print(f"Nombre de la topología: {topologia_nombre}")
    print(f"Topología seleccionada: {['Lineal', 'Anillo', 'Estrella'][int(topologia_opcion) - 1]}")
    print(f"Cantidad de vm's: {cantidad_nodos}")
    print(f"Sistema operativo: {sistema_operativo}")
    print(f"Ruta del SO: {os_path}")  # Nueva línea: muestra la ruta
    print(f"Flavor seleccionado: {flavor[1]}GB RAM, {flavor[2]} CPU(s), {flavor[3]}GB Disk")

    confirmar_y_crear_topologia(topologia_nombre,topologia_opcion,cantidad_nodos,sistema_operativo,os_path,flavor)