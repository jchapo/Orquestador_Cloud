import mysql.connector
from getpass import getpass
import hashlib
import os
import time



class Authenticator:
    def __init__(self):
        self.db = mysql.connector.connect(
            user="cloud_admin",
            password="admin123",
            database="cloud_orchestrator",
            unix_socket="/var/run/mysqld/mysqld.sock"
        )
        self.current_user = None

    def login(self):
        frames = [
            "=== PUCP Private Cloud Orchestrator ==="
        ]
         # Mostrar cada frame centrado con pausa
        for frame in frames:
            print("\n"*2)
            print(frame.center(50))
            print("\n")
            username = input("Usuario: ")
            password = getpass("Contraseña: ")        

        cursor = self.db.cursor()
        query = """
            SELECT u.id, u.password_hash, r.nombre 
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
            WHERE u.username = %s
        """
        try:
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if not result:
                print("❌ Usuario no encontrado")
                return False

            user_id, stored_hash, role = result
            input_hash = hashlib.sha256(password.encode()).hexdigest()

            if input_hash == stored_hash:
                self.current_user = {
                    "id": user_id,
                    "username": username,
                    "role": role
                }
                self.show_login_animation(username)
                return True
            else:
                self.show_login_failure_animation()
                return False
        except mysql.connector.Error as e:
            self.show_login_failure_animation()
            print(f"Error de base de datos: {e}")
            return False

    def check_permission(self, required_role):
        if not self.current_user:
            return False
        return self.current_user["role"] == required_role

    def logout(self):
        self.current_user = None
        print("🔑 Has cerrado sesión.")

    def list_users(self):
        cursor = self.db.cursor()
        query = """
            SELECT u.id, u.username, r.nombre AS rol
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
        """
        try:
            cursor.execute(query)
            users = cursor.fetchall()
            print("\n=== Lista de Usuarios ===")
            for user in users:
                print(f"{user[0]}. Usuario: {user[1]} - Rol: {user[2]}")
        except mysql.connector.Error as e:
            print(f"Error al listar usuarios: {e}")

    def add_user(self):
        username = input("Nuevo nombre de usuario: ")
        password = getpass("Contraseña: ")
        confirm = getpass("Confirmar contraseña: ")

        if password != confirm:
            print("❌ Las contraseñas no coinciden.")
            return

        # Mostrar roles disponibles ordenados por ID
        cursor = self.db.cursor()
        cursor.execute("SELECT id, nombre FROM roles ORDER BY id")  # Añadido ORDER BY
        roles = cursor.fetchall()
        print("\nRoles disponibles:")
        for role in roles:
            print(f"{role[0]}. {role[1]}")

        role_id = input("Seleccione el ID del rol: ")

        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insertar en la base de datos
        try:
            query = """
                INSERT INTO usuarios (username, password_hash, rol_id, fecha_creacion)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(query, (username, password_hash, role_id))
            self.db.commit()
            print(f"✅ Usuario '{username}' creado exitosamente.")
        except mysql.connector.Error as e:
            print(f"Error al crear usuario: {e}")

    def delete_user(self):
        user_id = input("ID del usuario a eliminar: ")

        try:
            cursor = self.db.cursor()
            query = "DELETE FROM usuarios WHERE id = %s"
            cursor.execute(query, (user_id,))
            self.db.commit()
            if cursor.rowcount:
                print("✅ Usuario eliminado.")
            else:
                print("❌ Usuario no encontrado.")
        except mysql.connector.Error as e:
            print(f"Error al eliminar usuario: {e}")

    def edit_user(self):
        """Edita un usuario existente"""
        self.clear_screen()
        print("\n=== Editar Usuario ===")
        
        # Primero listamos los usuarios disponibles
        self.list_users()
        
        try:
            user_id = int(input("\nOrden del usuario a editar: ").strip())
        except ValueError:
            print("❌ ID inválido. Debe ser un número.")
            input("\nPresione Enter para continuar...")
            return

        # Verificar si el usuario existe
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.username, r.nombre as rol 
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
            WHERE u.id = %s
        """, (user_id,))
        usuario = cursor.fetchone()

        if not usuario:
            print("❌ Usuario no encontrado")
            input("\nPresione Enter para continuar...")
            return

        print(f"\nEditando usuario: {usuario['username']} (Rol actual: {usuario['rol']})")
        
        # Menú de opciones de edición
        print("\n¿Qué desea modificar?")
        print("1. Nombre de usuario")
        print("2. Contraseña")
        print("3. Rol")
        print("4. Cancelar")
        
        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":  # Cambiar nombre de usuario
            nuevo_username = input("Nuevo nombre de usuario: ").strip()
            try:
                cursor.execute(
                    "UPDATE usuarios SET username = %s WHERE id = %s",
                    (nuevo_username, user_id)
                )
                self.db.commit()
                print("✅ Nombre de usuario actualizado correctamente")
            except mysql.connector.Error as err:
                print(f"❌ Error al actualizar: {err}")

        elif opcion == "2":  # Cambiar contraseña
            nueva_password = getpass("Nueva contraseña: ")
            confirm_password = getpass("Confirmar contraseña: ")

            if nueva_password != confirm_password:
                print("❌ Las contraseñas no coinciden")
            else:
                password_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
                try:
                    cursor.execute(
                        "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                        (password_hash, user_id)
                    )
                    self.db.commit()
                    print("✅ Contraseña actualizada correctamente")
                except mysql.connector.Error as err:
                    print(f"❌ Error al actualizar contraseña: {err}")

        elif opcion == "3":  # Cambiar rol
            # Mostrar roles disponibles
            cursor.execute("SELECT id, nombre FROM roles")
            roles = cursor.fetchall()
            
            print("\nRoles disponibles:")
            for rol in roles:
                print(f"{rol['id']}. {rol['nombre']}")
            
            try:
                nuevo_rol = int(input("Seleccione el nuevo ID de rol: ").strip())
                # Verificar que el rol existe
                if not any(rol['id'] == nuevo_rol for rol in roles):
                    print("❌ Rol no válido")
                else:
                    cursor.execute(
                        "UPDATE usuarios SET rol_id = %s WHERE id = %s",
                        (nuevo_rol, user_id)
                    )
                    self.db.commit()
                    print("✅ Rol actualizado correctamente")
            except ValueError:
                print("❌ ID de rol inválido. Debe ser un número.")

        elif opcion == "4":  # Cancelar
            print("Operación cancelada")
            return

        else:
            print("❌ Opción no válida")
       

    def clear_screen(self):
        """Limpia la pantalla dependiendo del sistema operativo"""
        # Para Windows
        if os.name == 'nt':
            os.system('cls')
        # Para macOS y Linux
        else:
            os.system('clear')

    def show_max_attempts_animation(self):
        """Animación para cuando se exceden los intentos máximos"""
        self.clear_screen()
        frames = [
            "🔍 Verificando último intento...",
            "❌ Bloqueando acceso temporal..."
        ]
        
        for frame in frames:
            self.clear_screen()
            print("\n"*5)  # Centrar verticalmente
            print(frame.center(50))
            print("\n"*5)
            time.sleep(0.5)

    def show_login_failure_animation(self):
        """Animación para cuando falla el inicio de sesión"""
        self.clear_screen()
        
        # Frames de la animación progresiva
        frames = [
            "🔍 Verificando credenciales...",
            "❌ Autenticación fallida..."
        ]
        
        # Mostrar cada frame centrado con pausa
        for frame in frames:
            self.clear_screen()
            print("\n"*5)  # Espacio vertical para centrar
            print(frame.center(50))
            time.sleep(0.7)
            print("\n"*5)

    def show_login_animation(self, username):
        """Animación para inicio de sesión exitoso"""
        self.clear_screen()
        
        # Frames de la animación progresiva
        frames = [
            "🔍 Verificando credenciales...",
            "👤 Bienvenido, {}".format(username)
        ]
         # Mostrar cada frame centrado con pausa
        for frame in frames:
            self.clear_screen()
            print("\n"*5)  # Espacio vertical para centrar
            print(frame.center(50))
            time.sleep(0.7)
            print("\n"*5)