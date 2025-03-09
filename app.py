from flask import Flask
from routes import recepciones_bp

app = Flask(__name__)

# Registrar el blueprint de recepciones
app.register_blueprint(recepciones_bp)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
