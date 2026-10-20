
import os
import pyodbc
from bottle import PluginError


class SQLServerPlugin:
    name = "sqlserver"
    api = 2

    def setup(self, app):
        for plugin in app.plugins:
            if isinstance(plugin, SQLServerPlugin):
                raise PluginError("SQLServerPlugin already installed")

    def apply(self, callback, route):
        import inspect

        if "db" not in inspect.signature(callback).parameters:
            return callback

        def wrapper(*args, **kwargs):
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

            connection = pyodbc.connect(connection_string)
            try:
                kwargs["db"] = connection
                return callback(*args, **kwargs)
            finally:
                connection.close()

        return wrapper
