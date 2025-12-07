import os
import json
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_loader import load_buildings
from dotenv import load_dotenv

# -------------------------------------
# ENV + APP SETUP
# -------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

app = Flask(__name__)
CORS(app)

# Load buildings once at startup
buildings = load_buildings()

# Which attributes are numeric / string
NUMERIC_ATTRS = {"height", "assessed_value", "land_size_sm"}
STRING_ATTRS = {
    "stage",
    "land_use_designation",
    "community",
    "property_type",
    "address",
}


# -------------------------------------
# LLM INTEGRATION (GROQ)
# -------------------------------------
def query_llm(prompt: str) -> str:
    if not GROQ_API_KEY:
        print("⚠️ No GROQ_API_KEY found – using fallback parser")
        return parse_query_fallback(prompt)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # -------------------------------
    # UPDATED SYSTEM PROMPT (IMPORTANT)
    # -------------------------------
    SYSTEM_PROMPT = (
        "You ONLY output JSON. No explanations. No markdown.\n"
        "Your job is to convert natural language queries into filter JSON.\n\n"

        "SUPPORTED ATTRIBUTES:\n"
        "- \"height\" (meters)\n"
        "- \"assessed_value\" (CAD)\n"
        "- \"land_size_sm\" (square metres)\n"
        "- \"land_use_designation\" (e.g., R-CG, C-COR, etc.)\n"
        "- \"community\" (neighbourhood name)\n"
        "- \"property_type\" (e.g., LI, LO, etc.)\n"
        "- \"address\" (string)\n"
        "- \"stage\" (string)\n\n"

        "SUPPORTED OPERATORS:\n"
        "- numeric: \">\", \"<\", \">=\", \"<=\", \"=\", \"max\", \"min\"\n"
        "- string: \"=\", \"contains\" (case-insensitive)\n\n"

        "SINGLE FILTER FORMAT:\n"
        "{\"attribute\": \"height\", \"operator\": \">\", \"value\": 20}\n\n"

        "MULTI-FILTER FORMAT (AND):\n"
        "{\"filters\": [\n"
        "  {\"attribute\": \"assessed_value\", \"operator\": \">\", \"value\": 1000000},\n"
        "  {\"attribute\": \"height\", \"operator\": \">\", \"value\": 30}\n"
        "]}\n\n"

        "SUPERLATIVES:\n"
        "\"most expensive property\" -> "
        "{\"attribute\": \"assessed_value\", \"operator\": \"max\", \"value\": 0}\n"
        "\"cheapest\" -> "
        "{\"attribute\": \"assessed_value\", \"operator\": \"min\", \"value\": 0}\n"
        "\"largest lot\" -> "
        "{\"attribute\": \"land_size_sm\", \"operator\": \"max\", \"value\": 0}\n"
        "\"smallest lot\" -> "
        "{\"attribute\": \"land_size_sm\", \"operator\": \"min\", \"value\": 0}\n\n"

        "ALWAYS output valid JSON only."
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.15,
        "max_tokens": 300,
    }

    try:
        print("📡 Calling Groq API…")
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            print(f"❌ Groq error {r.status_code}: {r.text}")
            return parse_query_fallback(prompt)

        result = r.json()["choices"][0]["message"]["content"]
        print(f"✅ Groq response: {result[:150]}...")
        return result

    except Exception as e:
        print(f"❌ Groq API exception: {e}")
        return parse_query_fallback(prompt)


# -------------------------------------
# FALLBACK QUERY PARSER
# -------------------------------------
def parse_query_fallback(prompt: str) -> str:
    print("🔧 Using fallback parser…")
    text = prompt.lower()

    # superlatives
    if "most expensive" in text or "highest value" in text:
        return json.dumps({"attribute": "assessed_value", "operator": "max", "value": 0})

    if "cheapest" in text or "least expensive" in text:
        return json.dumps({"attribute": "assessed_value", "operator": "min", "value": 0})

    if "largest lot" in text or "biggest lot" in text:
        return json.dumps({"attribute": "land_size_sm", "operator": "max", "value": 0})

    if "smallest lot" in text:
        return json.dumps({"attribute": "land_size_sm", "operator": "min", "value": 0})

    # numeric threshold → default to height
    nums = re.findall(r"\d+\.?\d*", text)
    num = float(nums[0]) if nums else 0

    if any(x in text for x in ["over", "above", "greater", "more than"]):
        op = ">"
    elif any(x in text for x in ["under", "below", "less than"]):
        op = "<"
    else:
        op = ">"

    return json.dumps({"attribute": "height", "operator": op, "value": num})


# -------------------------------------
# JSON BLOCK EXTRACTION
# -------------------------------------
def extract_json_block(text: str):
    if not isinstance(text, str):
        return None

    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    stack = []
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if start is None:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except:
                        start = None
                        continue

    return None


# -------------------------------------
# FILTER HELPERS
# -------------------------------------
def coerce_number(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except:
            return v
    return v


def apply_numeric(building, attr, op, val):
    raw = building.get(attr)
    if raw is None:
        return False

    try:
        b_val = float(raw)
    except:
        return False  # drop missing vals

    val = coerce_number(val)
    if op == ">": return b_val > val
    if op == "<": return b_val < val
    if op == ">=": return b_val >= val
    if op == "<=": return b_val <= val
    if op in ["=", "=="]: return abs(b_val - val) < 1e-6
    return False


def apply_string(building, attr, op, val):
    raw = building.get(attr)
    if raw is None:
        return False
    field = str(raw).lower()
    val = str(val).lower()

    if op in ["=", "=="]:
        return field == val
    if op == "contains":
        return val in field
    return False


def apply_single_filter(building, attribute, operator, value):
    if attribute in NUMERIC_ATTRS:
        return apply_numeric(building, attribute, operator, value)
    if attribute in STRING_ATTRS:
        return apply_string(building, attribute, operator, value)
    return False


def handle_compound_query(filters):
    matches = []
    for b in buildings:
        if all(apply_single_filter(b, f["attribute"], f["operator"], f["value"]) for f in filters):
            matches.append(b["id"])

    return jsonify({"ids": matches, "count": len(matches), "filters": filters})


def handle_superlative(attribute, operator):
    values = []
    for b in buildings:
        raw = b.get(attribute)
        if raw is None:
            continue
        try:
            v = float(raw)
            values.append((b["id"], v))
        except:
            continue

    if not values:
        return jsonify({"ids": [], "count": 0})

    best = max(v for _, v in values) if operator == "max" else min(v for _, v in values)
    ids = [bid for bid, v in values if abs(v - best) < 1e-6]

    return jsonify({
        "ids": ids,
        "count": len(ids),
        "filter": {"attribute": attribute, "operator": operator, "value": best}
    })


# -------------------------------------
# API ENDPOINT — NATURAL LANGUAGE QUERY
# -------------------------------------
@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(force=True, silent=True) or {}
    user_query = (data.get("query") or "").strip()

    if not user_query:
        return jsonify({"ids": [], "count": 0, "error": "Empty query"})

    prompt = f"Convert this query into JSON.\nQuery: \"{user_query}\"\nJSON:"
    llm_output = query_llm(prompt)
    filt = extract_json_block(llm_output)

    if not filt:
        return jsonify({"ids": [], "count": 0, "error": "Query parsing failed"})

    # Multi-filter
    if "filters" in filt:
        return handle_compound_query(filt["filters"])

    # Single filter
    attr = filt.get("attribute")
    op = (filt.get("operator") or "").lower()
    val = filt.get("value")

    if op in ["max", "min"]:
        return handle_superlative(attr, op)

    matches = [b["id"] for b in buildings if apply_single_filter(b, attr, op, val)]
    return jsonify({"ids": matches, "count": len(matches), "filter": filt})


# -------------------------------------
# API: BUILDINGS
# -------------------------------------
@app.route("/api/buildings")
def api_buildings():
    return jsonify(buildings)


# -------------------------------------
# HEALTH
# -------------------------------------
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "buildings_loaded": len(buildings),
        "llm_available": bool(GROQ_API_KEY),
        "provider": "Groq" if GROQ_API_KEY else "Fallback",
    })


# -------------------------------------
# ENTRY POINT
# -------------------------------------
if __name__ == "__main__":
    print("🏙️ URBAN 3D DASHBOARD BACKEND")
    print(f"📊 Loaded: {len(buildings)} buildings")
    app.run(host="0.0.0.0", port=5000, debug=True)