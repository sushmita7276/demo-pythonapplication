
import os
import pyodbc


class Connection:
    def __init__(self, conf):
        self.config = conf
        self.db_connection = None

    def __enter__(self):
        self.db_connection = self.create_connection()
        return self.db_connection

    def __exit__(self, exc_type, exc_value, traceback):
        if self.db_connection:
            try:
                if exc_type:
                    self.db_connection.rollback()
                else:
                    self.db_connection.commit()
            finally:
                self.db_connection.close()

    def create_connection(self):
        server = os.environ["SQL_SERVER"]
        database = os.environ["SQL_DATABASE"]
        username = os.environ["SQL_USERNAME"]
        password = os.environ["SQL_PASSWORD"]

        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER=tcp:{server},1433;"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

        return pyodbc.connect(connection_string)
