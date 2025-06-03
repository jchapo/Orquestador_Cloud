def gestionar_usuarios(auth):
    while True:
        auth.clear_screen()
        print("\n=== Gestión de Usuarios y Roles ===")
        print("1. Mostrar usuarios")
        print("2. Agregar usuario")
        print("3. Eliminar usuario")
        print("4. Editar usuario")
        print("Q. Volver al menú anterior")

        sub_choice = input("\nSeleccione una opción: ").strip()

        if sub_choice == "1":
            auth.list_users()
            input("\nPresione Enter para continuar...")
        elif sub_choice == "2":
            auth.add_user()
            input("\nPresione Enter para continuar...")
        elif sub_choice == "3":
            auth.delete_user()
            input("\nPresione Enter para continuar...")
        elif sub_choice == "4":
            auth.edit_user()
            input("\nPresione Enter para continuar...")
        elif sub_choice.lower() == "q":
            break
        else:
            print("❌ Opción no válida.")
            input("\nPresione Enter para continuar...")

def configurar_zonas(auth):
    while True:
        auth.clear_screen()
        print("\n=== Configuración de Zonas de Disponibilidad ===")
        print("1. Ver zonas actuales")
        print("2. Crear nueva zona")
        print("3. Modificar zona existente")
        print("4. Asignar recursos a zona")
        print("Q. Volver al menú anterior")
        
        sub_choice = input("\nSeleccione una opción: ").strip()
        
        if sub_choice == "1":
            print("Mostrando zonas actuales...")
            input("\nPresione Enter para continuar...")
        elif sub_choice == "2":
            print("Creando nueva zona...")
            input("\nPresione Enter para continuar...")
        elif sub_choice == "3":
            print("Modificando zona existente...")
            input("\nPresione Enter para continuar...")
        elif sub_choice == "4":
            print("Asignando recursos a zona...")
            input("\nPresione Enter para continuar...")
        elif sub_choice.lower() == "q":
            break
        else:
            print("❌ Opción no válida.")
            input("\nPresione Enter para continuar...")