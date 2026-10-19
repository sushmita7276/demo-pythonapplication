# Azure SQL Login POC

A small Bottle web app with registration, login, a welcome page, and logout. User passwords are salted and hashed with PBKDF2-HMAC-SHA256 before they are stored in Azure SQL.

## Database setup

Create the Azure SQL server and `demoappdb` database with Terraform. After deployment, connect to `demoappdb` and run [sql/setup.sql](sql/setup.sql). The script creates `dbo.app_users` and a sample account:

- Username: `demo`
- Password: `DemoPass123!`

The app does not create database objects at startup.

## Local run

Install the Microsoft ODBC Driver 18 for SQL Server, then install Python dependencies:

```powershell
python -m pip install -r requirements.txt
$env:SQL_SERVER = "<server-name>.database.windows.net"
$env:SQL_DATABASE = "demoappdb"
$env:SQL_USERNAME = "sqladminuser"
$env:SQL_PASSWORD = "<SQL-admin-password>"
$env:APP_SECRET = "<long-random-cookie-secret>"
python main.py
```

Open `http://localhost:8080`. The SQL server firewall must allow the client network for local development.

## AKS deployment

The Helm chart reads SQL server/database names from a ConfigMap and reads SQL username, password, and `APP_SECRET` from the Key Vault CSI provider's synced Kubernetes Secret. Terraform creates the Key Vault secrets and the AKS Key Vault Secrets Provider identity access policy. The deployment pipeline supplies the Key Vault tenant and CSI identity client IDs.

The Terraform state contains secret values and must be protected accordingly. The POC's Azure-services SQL firewall rule permits connections from Azure services broadly; restrict it before production use.