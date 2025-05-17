from conf.conexion import Conexion, DatabasePool

__all__ = ['Conexion', 'DatabasePool']

DB_CONFIG = {
    'host': '10.88.0.6',
    'port': '5432',
    'database': 'db_cloud_g1',
    'user': 'admin@pucp.edu.pe',
    'password': 'grupo1'
}

JWT_SECRET_KEY = 'jwt-grupo1-cloud-secret-key'
JWT_TOKEN_EXPIRY = 24