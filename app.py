import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.Authentication import AuthenticationModule
import getpass
import time
import json

class CloudOrchestrator:
    def __init__(self):
        self.auth_module = AuthenticationModule()
        self.current_user = None
        self.auth_token = None
        self.logged_in = False

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        self.clear_screen()
        print("=" * 70)
        print("               PUCP PRIVATE CLOUD ORCHESTRATOR")
        print("=" * 70)
        if self.logged_in and self.current_user:
            print(f"Usuario: {self.current_user['username']} | Rol: {self.current_user['role']}")
        print("-" * 70)

    def login_menu(self):
        self.print_header()
        print("\nMENU DE AUTENTICACIÓN")
        print("1. Iniciar sesión")
        print("2. Salir")

        option = input("\nIngrese una opción: ")

        if option == "1":
            self.login()
        elif option == "2":
            print("\nSaliendo del sistema...")
            sys.exit(0)
        else:
            print("\nOpción inválida!")
            time.sleep(1)
            self.login_menu()

    def login(self):
        self.print_header()
        print("\nINICIO DE SESIÓN")
        print("-" * 30)

        username = input("Usuario: ")
        password = getpass.getpass("Contraseña: ")

        try:
            result = self.auth_module.login(username, password)
            if result and 'token' in result:
                self.auth_token = result['token']
                self.current_user = result['user']
                self.logged_in = True
                print("\n✅ Inicio de sesión exitoso!")
                time.sleep(1)
                self.main_menu()
            else:
                print("\n❌ Credenciales inválidas. Intente nuevamente.")
                time.sleep(2)
                self.login_menu()
        except Exception as e:
            print(f"\n❌ Error al iniciar sesión: {str(e)}")
            time.sleep(2)
            self.login_menu()

    def main_menu(self):
        while self.logged_in:
            self.print_header()
            print("\nMENU PRINCIPAL")
            if self.current_user and self.current_user['role'] == 'Administrador':
                print("1. Panel de Administración de Slices")
                print("2. Gestión de Usuarios")
                print("3. Configuración de Usuario")
                print("4. Configurar")
                print("5. Listar slices")
                print("6. Borrar slice")
                print("7. Definir zona de disponibilidad")
                print("8. Cerrar sesión")
            else:
                print("1. Panel de Administración de Slices")
                print("2. Configuración de Usuario")
                print("3. Listar slices")
                print("4. Cerrar sesión")

            option = input("\nIngrese una opción: ")

            if self.current_user and self.current_user['role'] == 'Administrador':
                if option == "1":
                    self.slice_management_menu()
                elif option == "2":
                    self.user_management_menu()
                elif option == "3":
                    self.user_settings_menu()
                elif option == "4":
                    self.configuration_menu()
                elif option == "5":
                    self.list_slices()
                elif option == "6":
                    self.delete_slice()
                elif option == "7":
                    self.define_availability_zone()
                elif option == "8":
                    self.logout()
                else:
                    print("\nOpción inválida!")
                    time.sleep(1)
            else:
                if option == "1":
                    self.slice_management_menu()
                elif option == "2":
                    self.user_settings_menu()
                elif option == "3":
                    self.list_slices()
                elif option == "4":
                    self.logout()
                else:
                    print("\nOpción inválida!")
                    time.sleep(1)

    def user_management_menu(self):
        if not self.current_user or self.current_user['role'] != 'Administrador':
            print("\n❌ No tiene permisos para acceder a esta función.")
            time.sleep(2)
            return

        while True:
            self.print_header()
            print("\nGESTIÓN DE USUARIOS")
            print("1. Listar usuarios")
            print("2. Agregar usuario")
            print("3. Eliminar usuario")
            print("4. Editar usuario")
            print("5. Volver al menú principal")

            option = input("\nIngrese una opción: ")

            if option == "1":
                self.list_users()
            elif option == "2":
                self.add_user()
            elif option == "3":
                self.delete_user()
            elif option == "4":
                self.edit_user()
            elif option == "5":
                break
            else:
                print("\nOpción inválida!")
                time.sleep(1)

    def list_users(self):
        self.print_header()
        print("\nLISTADO DE USUARIOS")

        try:
            users = self.auth_module.get_users()
            if not users:
                print("\nNo hay usuarios registrados.")
            else:
                print("-" * 70)
                print(f"{'ID':<5} {'Usuario':<30} {'Rol':<20}")
                print("-" * 70)

                for user in users:
                    print(f"{user['id']:<5} {user['username']:<30} {user['role']:<20}")

                print("-" * 70)
        except Exception as e:
            print(f"\n❌ Error al listar usuarios: {str(e)}")

        input("\nPresione Enter para continuar...")

    def add_user(self):
        self.print_header()
        print("\nAGREGAR NUEVO USUARIO")
        print("-" * 30)

        try:
            roles = self.auth_module.get_roles()

            if not roles:
                print("\n❌ No hay roles disponibles.")
                input("\nPresione Enter para continuar...")
                return

            username = input("Nuevo nombre de usuario: ")
            if not username:
                print("\n❌ El nombre de usuario no puede estar vacío.")
                input("\nPresione Enter para continuar...")
                return

            password = getpass.getpass("Contraseña: ")
            confirm_password = getpass.getpass("Confirmar contraseña: ")

            if password != confirm_password:
                print("\n❌ Las contraseñas no coinciden.")
                input("\nPresione Enter para continuar...")
                return

            print("\nRoles disponibles:")
            for role in roles:
                print(f"{role['id']}. {role['name']} - {role['description']}")

            role_id = input("\nSeleccione un rol (ID): ")
            if not role_id.isdigit():
                print("\n❌ ID de rol inválido.")
                input("\nPresione Enter para continuar...")
                return

            role_exists = False
            for role in roles:
                if str(role['id']) == role_id:
                    role_exists = True
                    role_name = role['name']
                    break

            if not role_exists:
                print("\n❌ El rol seleccionado no existe.")
                input("\nPresione Enter para continuar...")
                return

            print(f"\nSe creará el usuario '{username}' con rol '{role_name}'")
            confirm = input("¿Está seguro? (s/n): ").lower()

            if confirm != 's':
                print("\nOperación cancelada.")
                input("\nPresione Enter para continuar...")
                return

            result = self.auth_module.register(username, password, role_id)

            if result and result.get("success", False):
                print("\n✅ Usuario registrado exitosamente!")
            else:
                error_msg = result.get("error", "Error desconocido")
                print(f"\n❌ Error al registrar usuario: {error_msg}")

            input("\nPresione Enter para continuar...")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresione Enter para continuar...")

    def delete_user(self):
        self.print_header()
        print("\nELIMINAR USUARIO")

        try:
            users = self.auth_module.get_users()

            if not users:
                print("\nNo hay usuarios para eliminar.")
                input("\nPresione Enter para continuar...")
                return

            print("\nUsuarios disponibles:")
            print("-" * 70)
            print(f"{'ID':<5} {'Usuario':<30} {'Rol':<20}")
            print("-" * 70)

            for user in users:
                print(f"{user['id']:<5} {user['username']:<30} {user['role']:<20}")

            print("-" * 70)

            user_id = input("\nIngrese el ID del usuario a eliminar: ")

            if not user_id.isdigit():
                print("\n❌ ID inválido.")
                input("\nPresione Enter para continuar...")
                return

            user_exists = False
            selected_user = None

            for user in users:
                if str(user['id']) == user_id:
                    user_exists = True
                    selected_user = user
                    break

            if not user_exists:
                print("\n❌ El usuario seleccionado no existe.")
                input("\nPresione Enter para continuar...")
                return

            if selected_user['username'] == self.current_user['username']:
                print("\n❌ No puede eliminar su propio usuario.")
                input("\nPresione Enter para continuar...")
                return

            print(f"\n¿Está seguro de eliminar el usuario '{selected_user['username']}' con rol '{selected_user['role']}'?")
            confirm = input("Esta acción no se puede deshacer (s/n): ").lower()

            if confirm != 's':
                print("\nOperación cancelada.")
                input("\nPresione Enter para continuar...")
                return

            result = self.auth_module.delete_user(user_id)

            if result and result.get("success", False):
                print("\n✅ Usuario eliminado exitosamente!")
            else:
                error_msg = result.get("error", "Error desconocido")
                print(f"\n❌ Error al eliminar usuario: {error_msg}")

            input("\nPresione Enter para continuar...")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresione Enter para continuar...")

    def edit_user(self):
        self.print_header()
        print("\nEDITAR USUARIO")

        try:
            users = self.auth_module.get_users()

            if not users:
                print("\nNo hay usuarios para editar.")
                input("\nPresione Enter para continuar...")
                return

            print("\nUsuarios disponibles:")
            print("-" * 70)
            print(f"{'ID':<5} {'Usuario':<30} {'Rol':<20}")
            print("-" * 70)

            for user in users:
                print(f"{user['id']:<5} {user['username']:<30} {user['role']:<20}")

            print("-" * 70)

            user_id = input("\nIngrese el ID del usuario a editar: ")

            if not user_id.isdigit():
                print("\n❌ ID inválido.")
                input("\nPresione Enter para continuar...")
                return

            user_exists = False
            selected_user = None

            for user in users:
                if str(user['id']) == user_id:
                    user_exists = True
                    selected_user = user
                    break

            if not user_exists:
                print("\n❌ El usuario seleccionado no existe.")
                input("\nPresione Enter para continuar...")
                return

            print(f"\nEditando usuario: {selected_user['username']} (Rol: {selected_user['role']})")
            print("\n¿Qué desea modificar?")
            print("1. Nombre de usuario")
            print("2. Contraseña")
            print("3. Rol")
            print("4. Cancelar")

            edit_option = input("\nSeleccione una opción: ")

            if edit_option == "1":
                new_username = input("\nNuevo nombre de usuario: ")

                if not new_username:
                    print("\n❌ El nombre de usuario no puede estar vacío.")
                    input("\nPresione Enter para continuar...")
                    return

                result = self.auth_module.update_user_field(user_id, "username", new_username)

                if result and result.get("success", False):
                    print("\n✅ Nombre de usuario actualizado exitosamente!")
                else:
                    error_msg = result.get("error", "Error desconocido")
                    print(f"\n❌ Error al actualizar usuario: {error_msg}")

            elif edit_option == "2":
                new_password = getpass.getpass("\nNueva contraseña: ")
                confirm_password = getpass.getpass("Confirmar nueva contraseña: ")

                if new_password != confirm_password:
                    print("\n❌ Las contraseñas no coinciden.")
                    input("\nPresione Enter para continuar...")
                    return

                result = self.auth_module.update_user_password(user_id, new_password)

                if result and result.get("success", False):
                    print("\n✅ Contraseña actualizada exitosamente!")
                else:
                    error_msg = result.get("error", "Error desconocido")
                    print(f"\n❌ Error al actualizar contraseña: {error_msg}")

            elif edit_option == "3":
                roles = self.auth_module.get_roles()

                if not roles:
                    print("\n❌ No hay roles disponibles.")
                    input("\nPresione Enter para continuar...")
                    return

                print("\nRoles disponibles:")
                for role in roles:
                    print(f"{role['id']}. {role['name']} - {role['description']}")

                new_role_id = input("\nSeleccione un nuevo rol (ID): ")

                if not new_role_id.isdigit():
                    print("\n❌ ID de rol inválido.")
                    input("\nPresione Enter para continuar...")
                    return

                role_exists = False
                for role in roles:
                    if str(role['id']) == new_role_id:
                        role_exists = True
                        break

                if not role_exists:
                    print("\n❌ El rol seleccionado no existe.")
                    input("\nPresione Enter para continuar...")
                    return

                result = self.auth_module.update_user_field(user_id, "rol_id", new_role_id)

                if result and result.get("success", False):
                    print("\n✅ Rol actualizado exitosamente!")
                else:
                    error_msg = result.get("error", "Error desconocido")
                    print(f"\n❌ Error al actualizar rol: {error_msg}")

            elif edit_option == "4":
                print("\nOperación cancelada.")
            else:
                print("\n❌ Opción inválida!")

            input("\nPresione Enter para continuar...")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            input("\nPresione Enter para continuar...")

    def slice_management_menu(self):
        self.print_header()
        print("\nPANEL DE ADMINISTRACIÓN DE SLICES")
        print("Este módulo aún no está implementado.")
        input("\nPresione Enter para continuar...")

    def user_settings_menu(self):
        self.print_header()
        print("\nCONFIGURACIÓN DE USUARIO")
        print("1. Cambiar contraseña")
        print("2. Volver al menú principal")

        option = input("\nIngrese una opción: ")

        if option == "1":
            self.change_password()
        elif option == "2":
            return
        else:
            print("\nOpción inválida!")
            time.sleep(1)
            self.user_settings_menu()

    def change_password(self):
        self.print_header()
        print("\nCAMBIO DE CONTRASEÑA")
        print("-" * 30)

        current_password = getpass.getpass("Contraseña actual: ")
        new_password = getpass.getpass("Nueva contraseña: ")
        confirm_password = getpass.getpass("Confirmar nueva contraseña: ")

        if new_password != confirm_password:
            print("\n❌ Las contraseñas no coinciden!")
            time.sleep(2)
            self.user_settings_menu()
            return

        try:
            result = self.auth_module.change_password(self.auth_token, current_password, new_password)
            if result and 'success' in result and result['success']:
                print("\n✅ Contraseña cambiada exitosamente!")
            else:
                print("\n❌ Error al cambiar la contraseña.")
                if 'error' in result:
                    print(f"   {result['error']}")

            time.sleep(2)
            self.user_settings_menu()
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            time.sleep(2)
            self.user_settings_menu()

    def configuration_menu(self):
        self.print_header()
        print("\nCONFIGURACIÓN")
        print("1. Configurar desde cero")
        print("2. Continuar configuración")
        print("3. Volver al menú principal")

        option = input("\nIngrese una opción: ")

        if option == "1":
            print("\nFuncionalidad por implementar: Configurar desde cero")
            input("\nPresione Enter para continuar...")
        elif option == "2":
            print("\nFuncionalidad por implementar: Continuar configuración")
            input("\nPresione Enter para continuar...")
        elif option == "3":
            return
        else:
            print("\nOpción inválida!")
            time.sleep(1)
            self.configuration_menu()

    def list_slices(self):
        self.print_header()
        print("\nLISTADO DE SLICES")
        print("Funcionalidad por implementar")
        input("\nPresione Enter para continuar...")

    def delete_slice(self):
        self.print_header()
        print("\nBORRAR SLICE")
        print("Funcionalidad por implementar")
        input("\nPresione Enter para continuar...")

    def define_availability_zone(self):
        self.print_header()
        print("\nDEFINIR ZONA DE DISPONIBILIDAD")
        print("Funcionalidad por implementar")
        input("\nPresione Enter para continuar...")

    def logout(self):
        self.logged_in = False
        self.auth_token = None
        self.current_user = None
        print("\n✅ Sesión cerrada correctamente!")
        time.sleep(1)
        self.login_menu()

    def start(self):
        try:
            self.login_menu()
        except KeyboardInterrupt:
            print("\n\nSaliendo del sistema...")
            sys.exit(0)

if __name__ == "__main__":
    app = CloudOrchestrator()
    app.start()