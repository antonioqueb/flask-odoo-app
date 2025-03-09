import xmlrpc.client
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Odoo desde .env
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

if not all([ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD]):
    raise ValueError("Faltan variables de entorno en el archivo .env")

# Conexión a Odoo
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

if not uid:
    raise Exception("Error de autenticación con Odoo")

# Conectar con los modelos de Odoo
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
