import jwt
from datetime import datetime, timedelta
import bcrypt
import json
from conf.conexion import Conexion

JWT_SECRET_KEY = 'jwt-grupo1-cloud-secret-key'

class AuthenticationModule:
    def __init__(self):
        self.db_connection = Conexion()

    def login(self, username, password):
        try:
            user = self.db_connection.select(
                'id_usuario, username, password_hash, rol_id',
                'usuario',
                'username = %s',
                (username,)
            )

            if not user:
                return {"error": "Invalid credentials"}

            stored_password = user[0][2]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                token = jwt.encode(
                    {
                        'user_id': user[0][0],
                        'username': user[0][1],
                        'rol_id': user[0][3],
                        'exp': datetime.utcnow() + timedelta(minutes=60)
                    },
                    JWT_SECRET_KEY,
                    algorithm="HS256"
                )

                role = self.db_connection.select(
                    'nombre',
                    'rol',
                    'id_rol = %s',
                    (user[0][3],)
                )

                role_name = role[0][0] if role else "Desconocido"

                return {
                    "success": True,
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": user[0][0],
                        "username": user[0][1],
                        "role": role_name,
                        "rol_id": user[0][3]
                    }
                }

            return {"error": "Invalid credentials"}

        except Exception as e:
            return {"error": f"Login error: {str(e)}"}

    def verify_token(self, token):
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

            user = self.db_connection.select(
                'id_usuario, username, rol_id',
                'usuario',
                'id_usuario = %s',
                (data['user_id'],)
            )

            if not user:
                return {"error": "User not found"}

            role = self.db_connection.select(
                'nombre',
                'rol',
                'id_rol = %s',
                (user[0][2],)
            )

            role_name = role[0][0] if role else "Desconocido"

            return {
                "valid": True,
                "user": {
                    "id": user[0][0],
                    "username": user[0][1],
                    "role": role_name,
                    "rol_id": user[0][2]
                }
            }

        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}
        except Exception as e:
            return {"error": f"Token verification error: {str(e)}"}

    def register(self, username, password, rol_id):
        try:
            existing_user = self.db_connection.select(
                'id_usuario',
                'usuario',
                'username = %s',
                (username,)
            )

            if existing_user:
                return {"error": "User already exists"}

            role = self.db_connection.select(
                'id_rol',
                'rol',
                'id_rol = %s',
                (rol_id,)
            )

            if not role:
                return {"error": "Invalid role ID"}

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            self.db_connection.execute_query(
                "INSERT INTO usuario (username, password_hash, rol_id) VALUES (%s, %s, %s)",
                (username, hashed_password.decode('utf-8'), rol_id),
                fetch=False
            )

            return {"success": True, "message": "User registered successfully"}

        except Exception as e:
            return {"error": f"Registration error: {str(e)}"}

    def delete_user(self, user_id):
        try:
            existing_user = self.db_connection.select(
                'id_usuario, username',
                'usuario',
                'id_usuario = %s',
                (user_id,)
            )

            if not existing_user:
                return {"error": "User not found"}

            self.db_connection.execute_query(
                "DELETE FROM usuario WHERE id_usuario = %s",
                (user_id,),
                fetch=False
            )

            return {
                "success": True,
                "message": f"User {existing_user[0][1]} deleted successfully"
            }

        except Exception as e:
            return {"error": f"User deletion error: {str(e)}"}

    def update_user_field(self, user_id, field, value):
        try:
            existing_user = self.db_connection.select(
                'id_usuario',
                'usuario',
                'id_usuario = %s',
                (user_id,)
            )

            if not existing_user:
                return {"error": "User not found"}

            valid_fields = ["username", "rol_id"]
            if field not in valid_fields:
                return {"error": f"Invalid field: {field}"}

            if field == "rol_id":
                try:
                    value = int(value)
                    # Verificar que el rol existe
                    role = self.db_connection.select(
                        'id_rol',
                        'rol',
                        'id_rol = %s',
                        (value,)
                    )
                    if not role:
                        return {"error": "Invalid role ID"}
                except ValueError:
                    return {"error": "Role ID must be a number"}

            if field == "username":
                existing_username = self.db_connection.select(
                    'id_usuario',
                    'usuario',
                    'username = %s AND id_usuario != %s',
                    (value, user_id)
                )
                if existing_username:
                    return {"error": "Username already in use"}

            self.db_connection.execute_query(
                f"UPDATE usuario SET {field} = %s WHERE id_usuario = %s",
                (value, user_id),
                fetch=False
            )

            return {
                "success": True,
                "message": f"User {field} updated successfully to '{value}'"
            }

        except Exception as e:
            return {"error": f"User update error: {str(e)}"}

    def update_user_password(self, user_id, new_password):
        try:
            existing_user = self.db_connection.select(
                'id_usuario',
                'usuario',
                'id_usuario = %s',
                (user_id,)
            )

            if not existing_user:
                return {"error": "User not found"}

            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            self.db_connection.execute_query(
                "UPDATE usuario SET password_hash = %s WHERE id_usuario = %s",
                (hashed_password.decode('utf-8'), user_id),
                fetch=False
            )

            return {
                "success": True,
                "message": "User password updated successfully"
            }

        except Exception as e:
            return {"error": f"Password update error: {str(e)}"}

    def change_password(self, token, current_password, new_password):
        try:
            token_data = self.verify_token(token)
            if "error" in token_data:
                return {"error": token_data["error"]}

            user_id = token_data["user"]["id"]

            user = self.db_connection.select(
                'password_hash',
                'usuario',
                'id_usuario = %s',
                (user_id,)
            )

            if not bcrypt.checkpw(current_password.encode('utf-8'), user[0][0].encode('utf-8')):
                return {"error": "Current password is incorrect"}

            new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            self.db_connection.execute_query(
                "UPDATE usuario SET password_hash = %s WHERE id_usuario = %s",
                (new_hashed_password.decode('utf-8'), user_id),
                fetch=False
            )

            return {"success": True, "message": "Password changed successfully"}

        except Exception as e:
            return {"error": f"Password change error: {str(e)}"}

    def setup(self):
        try:
            admin_exists = self.db_connection.select(
                'id_usuario',
                'usuario',
                "username = 'admin@pucp.edu.pe'"
            )

            if admin_exists:
                return {"message": "Setup already completed", "already_setup": True}

            zones = self.db_connection.select('idzona_disponibilidad', 'zona_disponibilidad', 'idzona_disponibilidad = 1')

            if not zones:
                self.db_connection.execute_query(
                    "INSERT INTO zona_disponibilidad (nombre, descripcion) VALUES ('Zona Default', 'Zona creada durante la configuración inicial')",
                    fetch=False
                )

            roles = [
                ('Administrador', 'Administrador con acceso completo al sistema', 1),
                ('Operador', 'Usuario con privilegios operativos', 1),
                ('Usuario', 'Usuario básico con acceso limitado', 1)
            ]

            for role_name, description, zone_id in roles:
                existing_role = self.db_connection.select('id_rol', 'rol', "nombre = %s", (role_name,))

                if not existing_role:
                    self.db_connection.execute_query(
                        "INSERT INTO rol (nombre, descripcion, zona_id) VALUES (%s, %s, %s)",
                        (role_name, description, zone_id),
                        fetch=False
                    )

            admin_role = self.db_connection.select('id_rol', 'rol', "nombre = 'Administrador'")

            if not admin_role:
                return {"error": "Failed to create admin role"}

            admin_role_id = admin_role[0][0]

            default_password = 'Admin123'
            hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

            self.db_connection.execute_query(
                "INSERT INTO usuario (username, password_hash, rol_id) VALUES (%s, %s, %s)",
                ('admin@pucp.edu.pe', hashed_password.decode('utf-8'), admin_role_id),
                fetch=False
            )

            return {
                "success": True,
                "message": "Setup completed successfully",
                "admin_user": {
                    "username": "admin@pucp.edu.pe",
                    "password": default_password,
                    "role": "Administrador"
                }
            }

        except Exception as e:
            return {"error": f"Setup error: {str(e)}"}

    def get_roles(self):
        try:
            roles = self.db_connection.select(
                'id_rol, nombre, descripcion',
                'rol',
                None
            )

            if not roles:
                return []

            result = []
            for role in roles:
                result.append({
                    "id": role[0],
                    "name": role[1],
                    "description": role[2]
                })

            return result

        except Exception as e:
            print(f"Error getting roles: {str(e)}")
            return []

    def get_users(self):
        try:
            users = self.db_connection.select(
                'u.id_usuario, u.username, r.nombre as rol_nombre',
                'usuario u JOIN rol r ON u.rol_id = r.id_rol',
                None
            )

            if not users:
                return []

            result = []
            for user in users:
                result.append({
                    "id": user[0],
                    "username": user[1],
                    "role": user[2]
                })

            return result

        except Exception as e:
            print(f"Error getting users: {str(e)}")
            return []
