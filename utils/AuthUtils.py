import jwt
from functools import wraps
import os
import sys
from config.conexion import Conexion

JWT_SECRET_KEY = 'jwt-grupo1-cloud-secret-key'

def auth_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.auth_token:
            print("\n❌ Se requiere autenticación para acceder a esta función.")
            return False
        try:
            data = jwt.decode(self.auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
            db = Conexion()
            user = db.select(
                'id_usuario',
                'usuario',
                'id_usuario = %s',
                (data['user_id'],)
            )
            if not user:
                print("\n❌ Usuario no encontrado o token inválido.")
                self.auth_token = None
                self.logged_in = False
                return False
            return func(self, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            print("\n❌ La sesión ha expirado. Por favor, inicie sesión nuevamente.")
            self.auth_token = None
            self.logged_in = False
            return False
        except jwt.InvalidTokenError:
            print("\n❌ Token inválido. Por favor, inicie sesión nuevamente.")
            self.auth_token = None
            self.logged_in = False
            return False
        except Exception as e:
            print(f"\n❌ Error de autenticación: {str(e)}")
            return False
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            data = jwt.decode(self.auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
            db = Conexion()
            role = db.select(
                'r.nombre',
                'rol r JOIN usuario u ON r.id_rol = u.rol_id',
                'u.id_usuario = %s',
                (data['user_id'],)
            )
            if not role or role[0][0].lower() != 'administrador':
                print("\n❌ Se requieren privilegios de administrador para esta función.")
                return False
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"\n❌ Error al verificar privilegios: {str(e)}")
            return False
    return wrapper

def is_admin(token):
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        db = Conexion()
        role = db.select(
            'r.nombre',
            'rol r JOIN usuario u ON r.id_rol = u.rol_id',
            'u.id_usuario = %s',
            (data['user_id'],)
        )
        return role and role[0][0].lower() == 'administrador'
    except Exception:
        return False

def get_user_from_token(token):
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        db = Conexion()
        user = db.select(
            'u.id_usuario, u.username, r.nombre as role',
            'usuario u JOIN rol r ON u.rol_id = r.id_rol',
            'u.id_usuario = %s',
            (data['user_id'],)
        )
        if not user:
            return None
        return {
            "id": user[0][0],
            "username": user[0][1],
            "role": user[0][2]
        }
    except Exception:
        return None