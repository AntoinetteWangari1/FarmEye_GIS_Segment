import os
import pyproj
import ee
import geemap
import datetime
import time
from google.oauth2 import service_account
os.environ['PROJ_LIB'] = r"C:/Users/pc/AppData/Local/Programs/Python/Python312/Lib/site-packages/pyproj/proj_dir/share/proj"


from pyproj import CRS
print(CRS.from_epsg(4326))

# ✅ Setup output directory
OUT_DIR = './results'
os.makedirs(OUT_DIR, exist_ok=True)

# 🔄 Reusable NDVI function for a bounding box
def generate_ndvi(min_lon, min_lat, max_lon, max_lat):
    print("🔄 Starting NDVI generation...")

    # Generate a unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'NDVI_{timestamp}.tif'
    out_file = os.path.join(OUT_DIR, filename)

    # Authenticate Earth Engine
    service_account_email = 'earthengineaccess@ee-avantgiske.iam.gserviceaccount.com'
    key_file = 'EarthEngineApiKey.json'
    credentials = service_account.Credentials.from_service_account_file(
        key_file,
        scopes=['https://www.googleapis.com/auth/earthengine']
    )
    ee.Initialize(credentials)

    print(f"📍 Received bounding box:\n"
          f"  min_lon={min_lon}, min_lat={min_lat}\n"
          f"  max_lon={max_lon}, max_lat={max_lat}")

    roi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

    # Search for recent Sentinel-2 imagery
    day_windows = [14, 30, 60, 90]
    image_found = False
    for days in day_windows:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        s2_filtered = (
            ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
            .filterBounds(roi)
            .filterDate(str(start_date), str(end_date))
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        )
        image_count = s2_filtered.size().getInfo()
        print(f"📅 Checking last {days} days: Found {image_count} image(s).")

        if image_count > 0:
            image_found = True
            break

    if not image_found:
        print("❌ No suitable Sentinel-2 imagery found in the last 90 days.")
        return {"error": "No imagery found"}

    # Calculate NDVI
    s2_median = s2_filtered.median().clip(roi)
    ndvi = s2_median.normalizedDifference(['B8', 'B4'])

    # Save to disk
    print("⬇️ Downloading NDVI GeoTIFF locally...")
    geemap.download_ee_image(
        image=ndvi,
        filename=out_file,
        region=roi,
        scale=10,
        crs='EPSG:4326'
    )
    print(f"✅ NDVI GeoTIFF saved to: {out_file}")

    # Optional EE export (can be removed if not needed)
    asset_id = f'projects/ee-avantgiske/assets/ndvi-exports/NDVI_{timestamp}'
    export_task = ee.batch.Export.image.toAsset(
        image=ndvi,
        description='NDVI_Live_to_Asset',
        assetId=asset_id,
        region=roi.bounds(),
        scale=10,
        crs='EPSG:4326',
        maxPixels=1e13
    )
    export_task.start()
    print("🚀 Earth Engine asset export started.")

    while export_task.active():
        print("⏳ Exporting NDVI to EE asset... status:", export_task.status()['state'])
        time.sleep(10)

    print("✅ EE Export complete:", export_task.status().get('state'))

    # ✅ Return filename to Flask app
    return {
        "filename": filename,
        "bbox": [min_lon, min_lat, max_lon, max_lat]
    }

# ✅ Allow standalone execution for testing
# if __name__ == "__main__":
#     # Sample bounding box for Nairobi (1 km x 1 km)
#     min_lon = 36.813
#     min_lat = -1.294
#     max_lon = 36.823
#     max_lat = -1.284

#     result = generate_ndvi(min_lon, min_lat, max_lon, max_lat)
#     print("🎉 NDVI Generation Result:", result)
