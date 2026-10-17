
import os
from bottle import run, install
from data.config import Config
from datastore.store import Store
from datastore.sqlite_plugin import SQLitePlugin
import api


if __name__ == '__main__':
    print("Starting up...")

    Config()
    Store.migrate_db(Config.config)

    database_filename = os.path.join(
        Config.config.data_directory,
        Config.config.db_filename
    )

    install(SQLitePlugin(dbfile=database_filename))

    run(host='0.0.0.0', port=8080)
