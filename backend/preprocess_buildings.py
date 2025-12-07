import json
import os

# Because you run the script from inside backend/, paths start with data/
RAW_PATH = "data/raw/3D_Buildings_-_Citywide_20251205.geojson"
OUT_PATH = "data/buildings.json"

def preprocess():
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"[ERROR] Raw file not found: {RAW_PATH}")

    print("[preprocess] Loading raw GeoJSON…")
    with open(RAW_PATH) as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"[preprocess] Total raw features: {len(features)}")

    buildings = []
    next_id = 0

    for feat in features:
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})

        # Only polygons
        if geom.get("type") != "Polygon":
            continue

        coords = geom.get("coordinates", [])
        if not coords:
            continue

        footprint = coords[0]

        # Height = rooftop_z - ground_z
        try:
            ground_z = float(props.get("grd_elev_min_z", 0))
            roof_z = float(props.get("rooftop_elev_z", ground_z))
            height = max(roof_z - ground_z, 0)
        except:
            continue

        stage = props.get("stage", "UNKNOWN")

        buildings.append({
            "id": next_id,
            "footprint": footprint,
            "height": round(height, 2),
            "stage": stage,
            "struct_id": props.get("struct_id")
        })

        next_id += 1

    print(f"[preprocess] Processed buildings: {len(buildings)}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    with open(OUT_PATH, "w") as f:
        json.dump(buildings, f)

    print(f"[✓] Saved cleaned dataset → {OUT_PATH}")

if __name__ == "__main__":
    preprocess()