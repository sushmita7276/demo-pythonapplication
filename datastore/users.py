import hashlib


def calculate_password_hash(config, password):
    secret = config.password_secret
    module = hashlib.md5()
    string = f'{password}+{secret}'
    module.update(bytes(string, encoding='utf-8'))
    return module.hexdigest()


def _row_to_dict(cursor, row):
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def create_user(db, config, firstname, lastname, username, password):
    password_hash = calculate_password_hash(config, password)

    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO users (firstname, lastname, created_at, is_admin)
        OUTPUT INSERTED.id
        VALUES (?, ?, CURRENT_TIMESTAMP, 0);
        """,
        (firstname, lastname)
    )

    row = cursor.fetchone()
    if row is None:
        return False

    user_id = row[0]

    cursor.execute(
        """
        INSERT INTO auth_methods (user_id, username, password, type)
        VALUES (?, ?, ?, 'USERNAME_AND_PASSWORD');
        """,
        (user_id, username, password_hash)
    )

    return cursor.rowcount > 0


def check_login(db, config, username, password):
    password_hash = calculate_password_hash(config, password)

    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user_id
        FROM auth_methods
        WHERE username = ? AND password = ?
          AND type = 'USERNAME_AND_PASSWORD';
        """,
        (username, password_hash)
    )

    row = cursor.fetchone()
    return int(row[0]) if row else -1


def check_admin(db, username):
    user = user_by_username(db, username)
    return bool(user["is_admin"]) if user else False


def get_user_by_id(db, user_id):
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE id = ?;",
        (user_id,)
    )
    return _row_to_dict(cursor, cursor.fetchone())


def user_by_username(db, username):
    user_id = user_id_by_username(db, username)
    return get_user_by_id(db, user_id) if user_id is not None else None


def user_id_by_username(db, username):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user_id
        FROM auth_methods
        WHERE username = ? AND type = 'USERNAME_AND_PASSWORD';
        """,
        (username,)
    )

    row = cursor.fetchone()
    return int(row[0]) if row else None
