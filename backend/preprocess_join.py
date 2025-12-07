import os
import json

BASE_DIR = os.path.dirname(__file__)

OSM_BUILDINGS_PATH = os.path.join(BASE_DIR, "data", "osm_buildings.json")
PARCELS_PATH = os.path.join(BASE_DIR, "data", "parcels.json")
OUT_BUILDINGS_PATH = os.path.join(BASE_DIR, "data", "buildings.json")


def point_in_polygon(x, y, poly):
    """
    Ray-casting algorithm to test if a point is inside a polygon.
    poly: list of [lon, lat]
    """
    inside = False
    n = len(poly)
    if n < 3:
        return False

    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]

        # Check if the horizontal ray intersects this edge
        if ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
        ):
            inside = not inside

    return inside


def find_parcel_for_building(lon, lat, parcels):
    """
    Find the parcel that contains the building centroid (lon, lat).
    If multiple parcels match, pick the one with the highest assessed_value.
    """
    candidates = []
    for p in parcels:
        if not (
            p["min_lon"] <= lon <= p["max_lon"]
            and p["min_lat"] <= lat <= p["max_lat"]
        ):
            continue

        # Detailed point-in-polygon for each outer ring
        for ring in p["polygons"]:
            if point_in_polygon(lon, lat, ring):
                candidates.append(p)
                break

    if not candidates:
        return None

    best = max(
        candidates,
        key=lambda p: p.get("assessed_value") if p.get("assessed_value") is not None else 0.0,
    )
    return best


def main():
    if not os.path.exists(OSM_BUILDINGS_PATH):
        raise FileNotFoundError(f"[join] {OSM_BUILDINGS_PATH} not found")
    if not os.path.exists(PARCELS_PATH):
        raise FileNotFoundError(f"[join] {PARCELS_PATH} not found")

    print("[join] Loading OSM buildings…")
    with open(OSM_BUILDINGS_PATH) as f:
        buildings = json.load(f)
    print(f"[join] OSM buildings: {len(buildings)}")

    print("[join] Loading parcels…")
    with open(PARCELS_PATH) as f:
        parcels = json.load(f)
    print(f"[join] Parcels: {len(parcels)}")

    enriched = []
    matched_count = 0

    for b in buildings:
        lon = b.get("centroid_lon")
        lat = b.get("centroid_lat")

        parcel = None
        if lon is not None and lat is not None:
            parcel = find_parcel_for_building(lon, lat, parcels)

        merged = dict(b)  # copy base building data

        if parcel:
            matched_count += 1
            merged.update(
                {
                    "roll_number": parcel.get("roll_number"),
                    "address": parcel.get("address"),
                    "assessed_value": parcel.get("assessed_value"),
                    "assessment_class": parcel.get("assessment_class"),
                    "assessment_class_description": parcel.get(
                        "assessment_class_description"
                    ),
                    "community": parcel.get("comm_name"),
                    "land_use_designation": parcel.get("land_use_designation"),
                    "property_type": parcel.get("property_type"),
                    "land_size_sm": parcel.get("land_size_sm"),
                    "land_size_ac": parcel.get("land_size_ac"),
                    "sub_property_use": parcel.get("sub_property_use"),
                }
            )
        else:
            # Still include the building; it just won't have assessment data
            merged.setdefault("assessed_value", None)
            merged.setdefault("address", None)
            merged.setdefault("community", None)
            merged.setdefault("land_use_designation", None)

        enriched.append(merged)

    print(
        f"[join] Enriched {len(enriched)} buildings, "
        f"matched parcels for {matched_count} of them"
    )

    with open(OUT_BUILDINGS_PATH, "w") as f:
        json.dump(enriched, f)

    print(f"[✓] Saved final buildings dataset → {OUT_BUILDINGS_PATH}")


if __name__ == "__main__":
    main()