import json
import os

def load_buildings():
    data_path = os.path.join("data", "raw", "3D_Buildings_-_Citywide_20251205.geojson")
    with open(data_path, "r") as f:
        gj = json.load(f)

    features = gj["features"]

    buildings = []

    # We'll pick an origin from the first feature to make coords small
    first_geom = features[0]["geometry"]
    first_coords = first_geom["coordinates"][0]  # outer ring
    origin_lon, origin_lat = first_coords[0]

    # scale factor to convert degrees to "meters-ish" for Three.js
    SCALE = 100000  # tweak later if needed

    for i, feature in enumerate(features):
        geom = feature["geometry"]
        props = feature["properties"]

        if geom["type"] != "Polygon":
            continue  # keep it simple for now

        coords = geom["coordinates"][0]  # outer ring

        # Normalize lon/lat to local x/z for Three.js (y will be height)
        # x = (lon - origin_lon) * SCALE
        # z = (lat - origin_lat) * SCALE
        footprint = []
        for lon, lat in coords:
            x = (lon - origin_lon) * SCALE
            z = (lat - origin_lat) * SCALE
            footprint.append([x, z])

        # Height: rooftop_elev_z - grd_elev_min_z
        try:
            grd_min = float(props.get("grd_elev_min_z", 0))
            roof = float(props.get("rooftop_elev_z", grd_min))
            height = max(roof - grd_min, 3.0)  # at least some height
        except (TypeError, ValueError):
            height = 10.0  # fallback

        building = {
            "id": i,
            "struct_id": props.get("struct_id"),
            "stage": props.get("stage"),
            "height": height,
            "footprint": footprint,  # list of [x, z] points
        }

        buildings.append(building)

    # Optionally: limit to first N buildings so frontend isn't overloaded
    # For now, maybe ~300–400 buildings is enough
    return buildings[:400]
