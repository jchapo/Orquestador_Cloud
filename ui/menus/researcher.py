def show_researcher_menu():
    """Menú para Administrador del Sistema"""
    print("1. Gestionar usuarios y roles")
    print("2. Configurar zonas de disponibilidad")
    print("3. Monitorizar recursos del cluster")
    print("4. Acceder a logs y auditoría")
    print("5. Gestionar imágenes base de VMs")
    print("6. Reiniciar servicios")
    print("Q. Salir")
    return input("\nSeleccione una opción: ")

def handle_researcher_choice(choice, auth):
    """Manejador de opciones para administrador"""
    if choice.lower() == 'q':
        return
    
    from .common import gestionar_usuarios, configurar_zonas
    
    options = {
        "1": lambda: gestionar_usuarios(auth),
        "2": lambda: configurar_zonas(auth),
        "3": lambda: monitorizar_recursos(auth),
        "4": lambda: acceder_logs(auth),
        "5": lambda: gestionar_imagenes(auth),
        "6": lambda: reiniciar_servicios(auth)
    }
    
    if choice in options:
        options[choice]()
    else:
        print("❌ Opción no válida.")
        input("\nPresione Enter para continuar...")

def monitorizar_recursos(auth):
    auth.clear_screen()
    print("\n=== Monitorización de Recursos del Cluster ===")
    print("\nMonitorizando recursos del cluster...")
    # Implementar monitorización
    input("\nPresione Enter para continuar...")

def acceder_logs(auth):
    auth.clear_screen()
    print("\n=== Logs y Auditoría ===")
    print("\nAccediendo a logs y auditoría...")
    # Implementar acceso a logs
    input("\nPresione Enter para continuar...")

def gestionar_imagenes(auth):
    auth.clear_screen()
    print("\n=== Gestión de Imágenes Base ===")
    print("\nGestionando imágenes base de VMs...")
    # Implementar gestión de imágenes
    input("\nPresione Enter para continuar...")

def reiniciar_servicios(auth):
    auth.clear_screen()
    print("\n=== Reinicio de Servicios ===")
    print("\nReiniciando servicios...")
    # Implementar reinicio de servicios
    input("\nPresione Enter para continuar...")