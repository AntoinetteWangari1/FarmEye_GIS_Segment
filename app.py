from flask import Flask, request, jsonify, render_template, send_from_directory
from main import generate_ndvi
import os
import pyproj
print(pyproj.datadir.get_data_dir())


# Setup
app = Flask(__name__, template_folder="templates")
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# Index page
@app.route("/")
def index():
    return render_template("index.html")

# NDVI generation endpoint
@app.route("/run_ndvi", methods=["POST"])
def run_ndvi():
    try:
        data = request.get_json()
        print("📦 Received request data:", data)

        # Parse bounding box from the request
        min_lat = data.get("min_lat")
        max_lat = data.get("max_lat")
        min_lon = data.get("min_lon")
        max_lon = data.get("max_lon")
        print(f"📍 BBOX: {min_lon}, {min_lat}, {max_lon}, {max_lat}")

        if None in [min_lat, max_lat, min_lon, max_lon]:
            return jsonify({"error": "Bounding box (min_lat, min_lon, max_lat, max_lon) is required"}), 400

        # Call generate_ndvi function
        result = generate_ndvi(min_lon, min_lat, max_lon, max_lat)

        # Debug the result
        print("🎯 generate_ndvi result:", result)

        # Check for errors in the result
        if "error" in result:
            return jsonify({"error": result["error"]}), 404

        # Ensure filename is returned
        if "filename" not in result:
            return jsonify({"error": "No filename returned by generate_ndvi"}), 500

        # Return result to frontend
        return jsonify({
            "filename": result["filename"],
            "status": "success"
        })

    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({"error": str(e)}), 500

# Route to serve the GeoTIFF for Leaflet
@app.route("/results/<path:filename>")
def serve_raster(filename):
    return send_from_directory(RESULTS_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
