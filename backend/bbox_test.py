# import json

# path = "backend/data/raw/3D_Buildings_-_Citywide_20251205.geojson"
# with open(path) as f:
#     data = json.load(f)

# # GeoJSON FeatureCollection → buildings are inside "features"
# features = data["features"]

# print("Total Features:", len(features))

# example = features[0]
# print("\nExample feature:")
# print(json.dumps(example, indent=2))

# # Convert the polygon into usable footprint points
# coords = example["geometry"]["coordinates"][0]  # Polygon → outer ring
# print("\nFootprint coords:")
# print(coords)

import json

path = "backend/data/raw/3D_Buildings_-_Citywide_20251205.geojson"

with open(path) as f:
    data = json.load(f)

features = data["features"]

min_lon = min(pt[0] for f in features for pt in f["geometry"]["coordinates"][0])
max_lon = max(pt[0] for f in features for pt in f["geometry"]["coordinates"][0])
min_lat = min(pt[1] for f in features for pt in f["geometry"]["coordinates"][0])
max_lat = max(pt[1] for f in features for pt in f["geometry"]["coordinates"][0])

print("min_lon =", min_lon)
print("max_lon =", max_lon)
print("min_lat =", min_lat)
print("max_lat =", max_lat)