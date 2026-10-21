
import os
import hmac
import hashlib
import secrets
from contextlib import contextmanager
from html import escape

import pyodbc
from bottle import Bottle, request, response, redirect, run
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

app = Bottle()
LOGIN_ATTEMPTS = Counter(
    "python_app_login_attempts_total",
    "Login attempts by result",
    ["result"]
)
REGISTRATIONS = Counter(
    "python_app_registrations_total",
    "Registration attempts by result",
    ["result"]
)

SERVER = os.environ["SQL_SERVER"]
DATABASE = os.environ["SQL_DATABASE"]
USERNAME = os.environ["SQL_USERNAME"]
PASSWORD = os.environ["SQL_PASSWORD"]
APP_SECRET = os.environ["APP_SECRET"]
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def odbc_value(value):
    return "{" + value.replace("}", "}}") + "}"


@contextmanager
def get_db():
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{SERVER},1433;"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={odbc_value(PASSWORD)};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200000
    ).hex()


def page(content):
    return f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Azure SQL Login POC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial; max-width: 420px;
                   margin: 50px auto; padding: 20px; }}
            input, button {{ box-sizing: border-box; width: 100%;
                           padding: 12px; margin: 8px 0; }}
            button {{ background: #1769aa; color: white;
                     border: 0; cursor: pointer; }}
        </style>
    </head>
    <body>{content}</body>
    </html>"""


@app.get("/metrics")
def metrics():
    response.content_type = CONTENT_TYPE_LATEST
    return generate_latest()


@app.get("/")
def home():
    return page("""
        <h2>Login</h2>
        <form method="post" action="/login">
            <input name="username" placeholder="Username" required>
            <input name="password" type="password"
                   placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>New user? <a href="/register">Register here</a></p>
    """)


@app.get("/register")
def register_page():
    return page("""
        <h2>Create account</h2>
        <form method="post" action="/register">
            <input name="display_name" placeholder="Your name" required>
            <input name="username" placeholder="Username"
                   maxlength="100" required>
            <input name="password" type="password"
                   placeholder="Password (minimum 8 characters)" required>
            <button type="submit">Register</button>
        </form>
        <a href="/">Back to login</a>
    """)


@app.post("/register")
def register():
    name = request.forms.get("display_name", "").strip()
    username = request.forms.get("username", "").strip()
    password = request.forms.get("password", "")

    if (not name or not username or len(username) > 100
            or len(name) > 150 or len(password) < 8):
        REGISTRATIONS.labels(result="invalid").inc()
        response.status = 400
        return page(
            "<h3>Enter valid details and a password of at least 8 characters.</h3>"
            "<a href='/register'>Try again</a>"
        )

    salt = secrets.token_bytes(16)

    try:
        with get_db() as db:
            db.cursor().execute("""
                INSERT INTO dbo.app_users
                    (username, display_name, password_salt, password_hash)
                VALUES (?, ?, ?, ?);
            """, (username, name, salt.hex(), hash_password(password, salt)))

        REGISTRATIONS.labels(result="created").inc()
        return page(
            "<h3>Registration successful!</h3><a href='/'>Login now</a>"
        )

    except pyodbc.IntegrityError:
        REGISTRATIONS.labels(result="duplicate").inc()
        response.status = 409
        return page(
            "<h3>Username already exists.</h3><a href='/register'>Try again</a>"
        )


@app.post("/login")
def login():
    username = request.forms.get("username", "").strip()
    password = request.forms.get("password", "")

    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT display_name, password_salt, password_hash
            FROM dbo.app_users
            WHERE username = ?;
        """, (username,))
        user = cursor.fetchone()

    if user:
        salt = bytes.fromhex(user.password_salt)
        candidate_hash = hash_password(password, salt)

        if hmac.compare_digest(candidate_hash, user.password_hash):
            LOGIN_ATTEMPTS.labels(result="success").inc()
            response.set_cookie(
                "account",
                username,
                secret=APP_SECRET,
                httponly=True,
                secure=COOKIE_SECURE,
                samesite="Lax",
                path="/",
                max_age=3600
            )
            redirect("/welcome")

    LOGIN_ATTEMPTS.labels(result="failure").inc()
    response.status = 401
    return page(
        "<h3>Invalid username or password.</h3><a href='/'>Try again</a>"
    )


@app.get("/welcome")
def welcome():
    username = request.get_cookie("account", secret=APP_SECRET)

    if not username:
        redirect("/")

    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT display_name
            FROM dbo.app_users
            WHERE username = ?;
        """, (username,))
        user = cursor.fetchone()

    if not user:
        redirect("/")

    return page(f"""
        <h1>Welcome, {escape(user.display_name)}!</h1>
        <p>Your credentials were verified against Azure SQL Database.</p>
        <p>Database: {escape(DATABASE)}</p>
        <a href="/logout">Logout</a>
    """)


@app.get("/logout")
def logout():
    response.delete_cookie("account", path="/")
    redirect("/")


@app.error(500)
def server_error(error):
    return page(
        "<h3>Something went wrong. Check the application logs.</h3>"
        "<a href='/'>Home</a>"
    )


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080)
