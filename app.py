from flask import Flask
from routes import registrar_rutas

app = Flask(__name__)

# Registrar todas las rutas
registrar_rutas(app)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5000)
