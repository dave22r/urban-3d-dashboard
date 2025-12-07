# backend/parcel_loader.py

import os
import json
from typing import List, Dict, Tuple, Optional

from shapely.geometry import shape, Polygon, MultiPolygon  # pip install shapely


# Path to your parcel assessment GeoJSON
# 👉 Rename your downloaded file to this, or update the path below.
PARCEL_GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "raw",
    "Current_Year_Property_Assessments_(Parcel)_20251206.geojson",
)


def _to_float(props: Dict, key: str) -> Optional[float]:
    val = props.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except Exception:
        return None


def _geom_intersects_bbox(geom_bounds: Tuple[float, float, float, float],
                          bbox: Tuple[float, float, float, float]) -> bool:
    """
    Cheap bbox intersection test:
    geom_bounds = (minx, miny, maxx, maxy)
    bbox        = (min_lon, min_lat, max_lon, max_lat)
    """
    minx, miny, maxx, maxy = geom_bounds
    bminx, bminy, bmaxx, bmaxy = bbox

    if maxx < bminx:
        return False
    if minx > bmaxx:
        return False
    if maxy < bminy:
        return False
    if miny > bmaxy:
        return False
    return True


def load_parcels_in_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> List[Dict]:
    """
    Load parcel assessment polygons that intersect the given bounding box.

    Returns a list of dicts with:
      - id
      - geom (shapely geometry)
      - area
      - assessed_value
      - roll_number, address, land_use_designation, etc.
    """
    bbox = (min_lon, min_lat, max_lon, max_lat)

    if not os.path.exists(PARCEL_GEOJSON_PATH):
        print(f"[parcel_loader] WARNING: Parcel file not found: {PARCEL_GEOJSON_PATH}")
        return []

    with open(PARCEL_GEOJSON_PATH, "r") as f:
        data = json.load(f)

    features = data.get("features", [])
    parcels: List[Dict] = []

    for idx, feat in enumerate(features):
        geom = shape(feat.get("geometry"))
        if geom.is_empty:
            continue

        # Quick bbox filter
        if not _geom_intersects_bbox(geom.bounds, bbox):
            continue

        props = feat.get("properties", {})

        assessed_value = _to_float(props, "assessed_value") or 0.0
        # You can still use parcels with 0 value (parks, roads, etc.), but they
        # won't contribute money to buildings.

        parcel = {
            "id": idx,
            "geom": geom,
            "area": float(geom.area),
            "assessed_value": assessed_value,
            "roll_number": props.get("roll_number"),
            "address": props.get("address"),
            "assessment_class": props.get("assessment_class"),
            "assessment_class_description": props.get("assessment_class_description"),
            "land_use_designation": props.get("land_use_designation"),
            "property_type": props.get("property_type"),
            "land_size_sm": _to_float(props, "land_size_sm"),
            "land_size_ac": _to_float(props, "land_size_ac"),
            "comm_name": props.get("comm_name"),
            "year_of_construction": props.get("year_of_construction"),
        }

        parcels.append(parcel)

    print(f"[parcel_loader] Loaded {len(parcels)} parcels in bbox {bbox}")
    return parcels