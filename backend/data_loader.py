import json
import os

def load_buildings():
    # Path to your 3D dataset
    data_path = os.path.join("data", "raw", "3D_Buildings_-_Citywide_20251205.geojson")

    with open(data_path, "r") as f:
        gj = json.load(f)

    features = gj["features"]

    # ---- STEP 1: Filter buildings to a small downtown bounding box ----
    # Approximate bounding box near downtown Calgary (adjustable)
    MIN_LON = -114.0725
    MAX_LON = -114.0665
    MIN_LAT = 51.0465
    MAX_LAT = 51.0495

    filtered = []
    for feat in features:
        geom = feat["geometry"]
        if geom["type"] != "Polygon":
            continue

        coords = geom["coordinates"][0]  # outer ring

        # Check if any point in polygon is inside our bounding box
        if any(MIN_LON < lon < MAX_LON and MIN_LAT < lat < MAX_LAT for lon, lat in coords):
            filtered.append(feat)

    print("Filtered buildings count:", len(filtered))

    # Safety fallback
    if len(filtered) == 0:
        print("WARNING: Bounding box returned 0 buildings. Using first 50 instead.")
        filtered = features[:50]

    # ---- STEP 2: Normalize coordinates and compute height ----

    # Choose an origin for coordinate normalization
    first_geom = filtered[0]["geometry"]["coordinates"][0]
    origin_lon, origin_lat = first_geom[0]

    SCALE = 90000  # convert degrees → approximate meters, tweakable

    buildings = []

    for idx, feature in enumerate(filtered):
        geom = feature["geometry"]
        coords = geom["coordinates"][0]  # polygon ring

        props = feature["properties"]

        # Normalize lat/lon → local x/z coordinates
        footprint = []
        for lon, lat in coords:
            x = (lon - origin_lon) * SCALE
            z = (lat - origin_lat) * SCALE
            footprint.append([x, z])

        # Compute height: rooftop - ground elevation
        try:
            ground = float(props.get("grd_elev_min_z", 0))
            roof = float(props.get("rooftop_elev_z", ground))
            height = max(roof - ground, 5.0)
        except:
            height = 10.0

        building = {
            "id": idx,
            "struct_id": props.get("struct_id"),
            "stage": props.get("stage"),
            "height": height,
            "footprint": footprint,
        }

        buildings.append(building)

    return buildings
