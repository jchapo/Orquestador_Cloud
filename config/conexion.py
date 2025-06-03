import psycopg2
from psycopg2 import pool

class DatabasePool:
    _instance = None
    _connection_pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            cls._create_pool()
        return cls._instance

    @classmethod
    def _create_pool(cls):
        try:
            cls._connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host="10.88.0.6",
                port="5432",
                database="db_cloud_g1",
                user="admin@pucp.edu.pe",
                password="grupo1"
            )
            print("PostgreSQL connection pool created successfully")
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL:", error)

    def get_connection(self):
        return self._connection_pool.getconn()

    def release_connection(self, connection):
        self._connection_pool.putconn(connection)

    def close_all_connections(self):
        if self._connection_pool:
            self._connection_pool.closeall()
            print("All connections closed")

class Conexion:
    def __init__(self):
        self.db_pool = DatabasePool()

    def execute_query(self, query, params=None, fetch=True):
        connection = None
        cursor = None
        result = None

        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()

            cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
            else:
                connection.commit()
                if cursor.rowcount > 0:
                    result = cursor.rowcount
                if hasattr(cursor, 'lastrowid'):
                    result = cursor.lastrowid

            return result

        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db_pool.release_connection(connection)

    def select(self, columns, table, condition=None, params=None):
        query = f"SELECT {columns} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        return self.execute_query(query, params)

    def insert(self, table, columns, values, params=None, return_id=True):
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        if return_id:
            query += " RETURNING id"
        return self.execute_query(query, params, fetch=return_id)

    def update(self, table, values, condition, params=None):
        query = f"UPDATE {table} SET {values} WHERE {condition}"
        return self.execute_query(query, params, fetch=False)

    def delete(self, table, condition, params=None):
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_query(query, params, fetch=False)