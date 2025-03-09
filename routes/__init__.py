from .recepciones import recepciones_bp
from .productos_recepcion import productos_recepcion_bp  # <-- Añadido aquí

def registrar_rutas(app):
    """Registra todas las rutas en la aplicación Flask"""
    app.register_blueprint(recepciones_bp)
    app.register_blueprint(productos_recepcion_bp)  # <-- Añadido aquí
