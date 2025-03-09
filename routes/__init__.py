from flask import Blueprint
from .recepciones import recepciones_bp  # Importar la ruta de recepciones

def registrar_rutas(app):
    """Registra todas las rutas en la aplicación Flask"""
    app.register_blueprint(recepciones_bp)
