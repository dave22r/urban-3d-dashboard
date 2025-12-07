import os
import json

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "buildings.json")


def load_buildings():
    """
    Load the preprocessed + joined buildings dataset.

    Run in this order before starting app.py:
      1) python preprocess_osm.py
      2) python preprocess_parcels.py
      3) python preprocess_join.py
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"[data_loader] ERROR: {DATA_PATH} not found.\n"
            "Run preprocess_osm.py, preprocess_parcels.py, and preprocess_join.py first."
        )

    with open(DATA_PATH) as f:
        buildings = json.load(f)

    # Ensure expected fields exist
    for b in buildings:
        b.setdefault("stage", "Unknown")
        # height should already be numeric from preprocessing

    print(f"[data_loader] Loaded {len(buildings)} buildings from {DATA_PATH}")
    return buildings