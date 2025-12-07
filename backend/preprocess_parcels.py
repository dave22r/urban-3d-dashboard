import os
import json

BASE_DIR = os.path.dirname(__file__)

RAW_PARCEL_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "Current_Year_Property_Assessments_(Parcel)_20251206.geojson",
)

OUT_PARCELS_PATH = os.path.join(BASE_DIR, "data", "parcels.json")
OSM_BBOX_PATH = os.path.join(BASE_DIR, "data", "osm_bbox.json")


def to_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except Exception:
        return None


def load_osm_bbox():
    if not os.path.exists(OSM_BBOX_PATH):
        print("[parcels] WARNING: OSM bbox not found – keeping ALL parcels")
        return None

    with open(OSM_BBOX_PATH) as f:
        bbox = json.load(f)

    print(
        "[parcels] Using OSM bbox: "
        f"lon [{bbox['min_lon']:.6f}, {bbox['max_lon']:.6f}], "
        f"lat [{bbox['min_lat']:.6f}, {bbox['max_lat']:.6f}]"
    )
    return bbox


def main():
    if not os.path.exists(RAW_PARCEL_PATH):
        raise FileNotFoundError(f"[parcels] {RAW_PARCEL_PATH} not found")

    bbox = load_osm_bbox()

    print("[parcels] Loading raw parcels GeoJSON…")
    with open(RAW_PARCEL_PATH) as f:
        gj = json.load(f)

    features = gj.get("features", [])
    print(f"[parcels] Total raw parcels: {len(features)}")

    parcels = []

    for feat in features:
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue

        # Normalize to list of polygons (each polygon = outer ring only)
        polygons = []

        if gtype == "Polygon":
            # coords: [ [ [lon, lat], ... ] ]  (rings)
            rings = coords
            if rings:
                polygons.append(rings[0])  # outer ring

        elif gtype == "MultiPolygon":
            # coords: [ [ [ [lon, lat], ... ] ], ... ]
            for poly in coords:
                if poly:
                    polygons.append(poly[0])  # outer ring

        else:
            continue  # ignore non-polygon geometries

        if not polygons:
            continue

        # Compute parcel bbox
        all_lons = []
        all_lats = []
        for ring in polygons:
            for lon, lat in ring:
                all_lons.append(lon)
                all_lats.append(lat)

        if not all_lons or not all_lats:
            continue

        min_lon = min(all_lons)
        max_lon = max(all_lons)
        min_lat = min(all_lats)
        max_lat = max(all_lats)

        # If we have an OSM bbox, quickly skip parcels outside it
        if bbox is not None:
            if (
                max_lon < bbox["min_lon"]
                or min_lon > bbox["max_lon"]
                or max_lat < bbox["min_lat"]
                or min_lat > bbox["max_lat"]
            ):
                continue

        props = feat.get("properties", {})

        parcel = {
            "id": len(parcels),
            "roll_number": props.get("roll_number"),
            "address": props.get("address"),
            "assessed_value": to_float(props.get("assessed_value")),
            "assessment_class": props.get("assessment_class"),
            "assessment_class_description": props.get(
                "assessment_class_description"
            ),
            "comm_name": props.get("comm_name"),
            "land_use_designation": props.get("land_use_designation"),
            "property_type": props.get("property_type"),
            "land_size_sm": to_float(props.get("land_size_sm")),
            "land_size_ac": to_float(props.get("land_size_ac")),
            "sub_property_use": props.get("sub_property_use"),
            "min_lon": min_lon,
            "max_lon": max_lon,
            "min_lat": min_lat,
            "max_lat": max_lat,
            # list of rings; each ring is [[lon, lat], ...]
            "polygons": polygons,
        }

        parcels.append(parcel)

    print(f"[parcels] Kept {len(parcels)} parcels after bbox filtering")

    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with open(OUT_PARCELS_PATH, "w") as f:
        json.dump(parcels, f)

    print(f"[✓] Saved simplified parcels → {OUT_PARCELS_PATH}")


if __name__ == "__main__":
    main()