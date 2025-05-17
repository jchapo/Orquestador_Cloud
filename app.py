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
        print("2. Configurar usuario administrador (primera vez)")
        print("3. Salir")

        option = input("\nIngrese una opción: ")

        if option == "1":
            self.login()
        elif option == "2":
            self.setup_admin()
        elif option == "3":
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

    def setup_admin(self):
        self.print_header()
        print("\nCONFIGURACIÓN INICIAL DE ADMINISTRADOR")
        print("-" * 40)

        try:
            result = self.auth_module.setup()
            if result and 'admin_user' in result:
                print("\n✅ Configuración inicial completada!")
                print(f"Usuario admin: {result['admin_user']['username']}")
                print(f"Contraseña: {result['admin_user']['password']}")
                print("\nPor favor guarde estas credenciales y cambie la contraseña después de iniciar sesión.")
            else:
                print("\n⚠️ La configuración inicial ya fue realizada o hubo un error.")

            input("\nPresione Enter para continuar...")
            self.login_menu()
        except Exception as e:
            print(f"\n❌ Error en la configuración inicial: {str(e)}")
            input("\nPresione Enter para continuar...")
            self.login_menu()

    def main_menu(self):
        while self.logged_in:
            self.print_header()
            print("\nMENU PRINCIPAL")
            print("1. Panel de Administración de Slices")
            print("2. Configuración de Usuario")
            print("3. Configurar")
            print("4. Listar slices")
            print("5. Borrar slice")
            print("6. Definir zona de disponibilidad")
            print("7. Cerrar sesión")

            option = input("\nIngrese una opción: ")

            if option == "1":
                self.slice_management_menu()
            elif option == "2":
                self.user_settings_menu()
            elif option == "3":
                self.configuration_menu()
            elif option == "4":
                self.list_slices()
            elif option == "5":
                self.delete_slice()
            elif option == "6":
                self.define_availability_zone()
            elif option == "7":
                self.logout()
            else:
                print("\nOpción inválida!")
                time.sleep(1)

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