from flask import Flask, request, jsonify, render_template, send_from_directory
from main import generate_ndvi
import os

app = Flask(__name__, template_folder="templates")
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run_ndvi", methods=["POST"])
def run_ndvi():
    try:
        data = request.get_json()
        print("📦 Received request data:", data)


        min_lat = data.get("min_lat")
        max_lat = data.get("max_lat")
        min_lon = data.get("min_lon")
        max_lon = data.get("max_lon")
        print(f"📍 BBOX: {min_lon}, {min_lat}, {max_lon}, {max_lat}")


        if None in [min_lat, max_lat, min_lon, max_lon]:
            return jsonify({"error": "Bounding box (min_lat, min_lon, max_lat, max_lon) is required"}), 400

        result = generate_ndvi(min_lon, min_lat, max_lon, max_lat)
        if "error" in result:
            return jsonify({"error": result["error"]}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Route to serve the GeoTIFF (for leaflet-geotiff display)
@app.route("/results/<path:filename>")
def serve_raster(filename):
    return send_from_directory(RESULTS_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
