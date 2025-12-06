from flask import Flask, jsonify, request
from flask_cors import CORS
from data_loader import load_buildings

app = Flask(__name__)
CORS(app)

# Load once at startup
BUILDINGS = load_buildings()

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/buildings")
def get_buildings():
    return jsonify(BUILDINGS)

if __name__ == "__main__":
    app.run(debug=True)

