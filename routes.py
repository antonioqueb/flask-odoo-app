from flask import Blueprint
from routes.recepciones import recepciones_bp

def registrar_rutas(app):
    """Registra todas las rutas en la aplicación Flask"""
    app.register_blueprint(recepciones_bp)
