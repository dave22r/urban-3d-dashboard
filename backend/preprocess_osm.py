import os
import json
import xml.etree.ElementTree as ET

OSM_PATH = "backend/data/raw/map.osm"
PARCEL_PATH = "backend/data/raw/Current_Year_Property_Assessments_(Parcel)_20251206.geojson"
OUTPUT_PATH = "backend/data/buildings.json"


# ----------------------------------------
# LOAD PARCELS FIRST (assessed values, zoning, lot size, address…)
# ----------------------------------------
def load_parcels():
    print("[PARCEL] Loading parcel dataset...")

    with open(PARCEL_PATH) as f:
        gj = json.load(f)

    parcel_polygons = []
    for feat in gj["features"]:
        geom = feat["geometry"]
        props = feat["properties"]

        # Skip weird zero-value parcels
        assessed = props.get("assessed_value")
        if assessed is None:
            continue

        parcel_polygons.append({
            "geometry": geom,
            "assessed_value": float(props.get("assessed_value", 0) or 0),
            "land_use_designation": props.get("land_use_designation"),
            "community": props.get("comm_name"),
            "roll_number": props.get("roll_number"),
            "address": props.get("address"),
            "property_type": props.get("property_type"),
            "sub_property_use": props.get("sub_property_use"),
            "land_size_sm": float(props.get("land_size_sm") or 0),
        })

    print(f"[PARCEL] Loaded {len(parcel_polygons)} parcels")
    return parcel_polygons



# ----------------------------------------
# PARSE OSM BUILDINGS (with height)
# ----------------------------------------
def load_osm_buildings():
    print("[OSM] Parsing buildings from OSM...")

    tree = ET.parse(OSM_PATH)
    root = tree.getroot()

    nodes = {}
    buildings = []

    # Node lookup
    for node in root.findall("node"):
        nid = node.get("id")
        lat = float(node.get("lat"))
        lon = float(node.get("lon"))
        nodes[nid] = (lon, lat)

    # Ways = building footprints
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}

        if "building" not in tags:
            continue

        # Collect coords
        coords = []
        for nd in way.findall("nd"):
            ref = nd.get("ref")
            if ref in nodes:
                coords.append(nodes[ref])

        if len(coords) < 3:
            continue

        height = tags.get("height") or tags.get("building:height")
        if height:
            try:
                height = float(height.replace("m", ""))
            except:
                height = 5.0
        else:
            height = 5.0  # default

        buildings.append({
            "osm_id": way.get("id"),
            "footprint": coords,
            "height": height
        })

    print(f"[OSM] Parsed {len(buildings)} raw buildings")
    return buildings


# ----------------------------------------
# POINT-IN-POLYGON (simple bounding box filter)
# ----------------------------------------
def bbox_contains(poly, point):
    (x, y) = point
    minx = min(p[0] for p in poly)
    maxx = max(p[0] for p in poly)
    miny = min(p[1] for p in poly)
    maxy = max(p[1] for p in poly)
    return (minx <= x <= maxx) and (miny <= y <= maxy)



# ----------------------------------------
# MATCH BUILDING TO PARCEL
# ----------------------------------------
def match_parcel_to_building(building, parcels):
    bx, by = building["footprint"][0]

    for p in parcels:
        geom = p["geometry"]

        if geom["type"] == "MultiPolygon":
            polygons = geom["coordinates"][0]  # outer shell

            for poly in polygons:
                poly2d = [(pt[0], pt[1]) for pt in poly]

                if bbox_contains(poly2d, (bx, by)):
                    return p

        elif geom["type"] == "Polygon":
            poly = geom["coordinates"][0]
            poly2d = [(pt[0], pt[1]) for pt in poly]

            if bbox_contains(poly2d, (bx, by)):
                return p

    return None



# ----------------------------------------
# MAIN PROCESSOR
# ----------------------------------------
if __name__ == "__main__":
    parcels = load_parcels()
    buildings = load_osm_buildings()

    output = []
    kept = 0
    dropped = 0

    for b in buildings:
        match = match_parcel_to_building(b, parcels)

        if not match:
            dropped += 1
            continue  # remove buildings with no parcel info

        # Merge parcel attributes
        b.update({
            "assessed_value": match["assessed_value"],
            "land_use_designation": match["land_use_designation"],
            "community": match["community"],
            "address": match["address"],
            "roll_number": match["roll_number"],
            "property_type": match["property_type"],
            "sub_property_use": match["sub_property_use"],
            "land_size_sm": match["land_size_sm"],
            "stage": None  # REMOVE stage entirely
        })

        output.append(b)
        kept += 1

    print(f"[DONE] Kept {kept} OSM buildings with parcel data")
    print(f"[DONE] Dropped {dropped} buildings without parcel match")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f)

    print(f"[✓] Buildings saved → {OUTPUT_PATH}")