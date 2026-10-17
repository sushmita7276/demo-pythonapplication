
import sqlite3
from bottle import PluginError


class SQLitePlugin:
    name = 'sqlite'
    api = 2

    def __init__(self, dbfile):
        self.dbfile = dbfile

    def setup(self, app):
        for other in app.plugins:
            if isinstance(other, SQLitePlugin):
                raise PluginError("SQLitePlugin already installed")

    def apply(self, callback, route):
        import inspect

        signature = inspect.signature(callback)
        if 'db' not in signature.parameters:
            return callback

        def wrapper(*args, **kwargs):
            connection = sqlite3.connect(self.dbfile)
            connection.row_factory = sqlite3.Row
            try:
                kwargs['db'] = connection
                return callback(*args, **kwargs)
            finally:
                connection.close()

        return wrapper
