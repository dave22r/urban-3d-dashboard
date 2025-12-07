import os
import json
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_loader import load_buildings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

app = Flask(__name__)
CORS(app)

# Load buildings once at startup
buildings = load_buildings()


# -------------------------------------------------------
# 🔥 LLM Integration (Groq)
# -------------------------------------------------------
def query_llm(prompt):
    if not GROQ_API_KEY:
        print("⚠️ No GROQ_API_KEY found — using fallback parser")
        return parse_query_fallback(prompt)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You ONLY output JSON. No text. No explanation.\n"
                    "Supported attributes: height, stage, assessed_value\n"
                    "Supported operators: >, <, >=, <=, =, contains, max, min\n"
                    "Use {\"filters\": [...] } if multiple filters are needed."
                )
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }

    try:
        print("📡 Calling Groq API…")
        r = requests.post(url, headers=headers, json=payload, timeout=30)

        if r.status_code != 200:
            print(f"❌ Groq API error {r.status_code}: {r.text}")
            return parse_query_fallback(prompt)

        result = r.json()["choices"][0]["message"]["content"]
        print(f"✅ Groq response: {result[:100]}...")
        return result

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return parse_query_fallback(prompt)


# -------------------------------------------------------
# 🔧 FALLBACK PARSER
# -------------------------------------------------------
def parse_query_fallback(text):
    text = text.lower()
    print("🔧 Using fallback parser…")

    if "constructed" in text:
        return json.dumps({"attribute": "stage", "operator": "=", "value": "Constructed"})

    if "approved" in text:
        return json.dumps({"attribute": "stage", "operator": "=", "value": "Approved"})

    # numeric extraction
    nums = re.findall(r"\d+\.?\d*", text)
    num = float(nums[0]) if nums else 0

    if any(k in text for k in ["over", "greater", "above"]):
        op = ">"
    elif any(k in text for k in ["under", "below", "less"]):
        op = "<"
    else:
        op = ">"

    return json.dumps({"attribute": "height", "operator": op, "value": num})


# -------------------------------------------------------
# 🧠 JSON Extractor — robust
# -------------------------------------------------------
def extract_json_block(text):
    text = text.strip()

    # 1) Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # Remove markdown
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # 2) Extract largest { ... }
    brace_stack, start = [], None

    for i, ch in enumerate(text):
        if ch == "{":
            if start is None:
                start = i
            brace_stack.append("{")
        elif ch == "}":
            if brace_stack:
                brace_stack.pop()
                if not brace_stack:
                    block = text[start:i+1]
                    try:
                        return json.loads(block)
                    except:
                        pass

    # 3) Extract array if present
    try:
        s = text.index("[")
        e = text.rindex("]") + 1
        return json.loads(text[s:e])
    except:
        return None


# -------------------------------------------------------
# FILTER HELPERS
# -------------------------------------------------------
def coerce_number(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            return float(v)
        except:
            return v
    return v


def apply_single_filter(b, attribute, operator, value):
    value = coerce_number(value)

    # ------ HEIGHT ------
    if attribute == "height":
        h = b["height"]
        if operator == ">": return h > value
        if operator == "<": return h < value
        if operator == ">=": return h >= value
        if operator == "<=": return h <= value
        if operator in ["=", "=="]: return abs(h - value) < 1.0
        return False

    # ------ STAGE ------
    if attribute == "stage":
        stage = b.get("stage", "").lower()
        val = str(value).lower()
        if operator == "=": return stage == val
        if operator == "contains": return val in stage
        return False

    # ------ ASSESSED VALUE ------
    if attribute == "assessed_value":
        v = b.get("assessed_value")
        if v is None:
            return False
        if operator == ">": return v > value
        if operator == "<": return v < value
        if operator == ">=": return v >= value
        if operator == "<=": return v <= value
        if operator in ["=", "=="]: return abs(v - value) < 1
        return False

    return False


# Multi-filter
def handle_compound_query(filters):
    print(f"🔗 Compound query with {len(filters)} filters")

    matches = []
    for b in buildings:
        if all(apply_single_filter(b, f["attribute"], f["operator"], f["value"]) for f in filters):
            matches.append(b["id"])

    print(f"✅ Compound returned {len(matches)} matches")

    return jsonify({
        "ids": matches,
        "count": len(matches),
        "filters": filters
    })


# -------------------------------------------------------
# 📌 QUERY API (LLM-powered)
# -------------------------------------------------------
@app.route("/api/query", methods=["POST"])
def api_query():
    user_query = request.json.get("query", "").strip()

    if not user_query:
        return jsonify({"ids": [], "count": 0, "error": "Empty query"})

    prompt = f"""
Convert this natural language query into JSON.

Supported attributes:
- height (meters)
- stage ("Constructed", "Approved", etc.)
- assessed_value (numeric property value)

Supported operators:
- >, <, >=, <=, =, contains
- max (for tallest / most expensive)
- min (for shortest / cheapest)

Examples:
"taller than 50m" →
  {{"attribute": "height", "operator": ">", "value": 50}}

"constructed and over 100 meters" →
  {{"filters": [
      {{"attribute": "stage", "operator": "=", "value": "Constructed"}},
      {{"attribute": "height", "operator": ">", "value": 100}}
  ]}}

"most expensive property" →
  {{"attribute": "assessed_value", "operator": "max", "value": 0}}

Query: "{user_query}"
JSON:
"""

    llm_output = query_llm(prompt)
    print("LLM RAW:", llm_output)

    filt = extract_json_block(llm_output)
    if not filt:
        return jsonify({"ids": [], "count": 0, "error": "JSON parse failed"})

    # ❗ Compound query
    if "filters" in filt:
        return handle_compound_query(filt["filters"])

    # Single filter
    attribute = filt.get("attribute")
    operator = filt.get("operator")
    value = coerce_number(filt.get("value"))

    # ----- SUPERLATIVES -----

    # Most expensive
    if attribute == "assessed_value" and operator == "max":
        vals = [b.get("assessed_value") or 0 for b in buildings]
        max_val = max(vals)
        ids = [b["id"] for b in buildings if (b.get("assessed_value") or 0) == max_val]
        return jsonify({"ids": ids, "count": len(ids), "filter": filt})

    # Cheapest
    if attribute == "assessed_value" and operator == "min":
        vals = [b.get("assessed_value") for b in buildings if b.get("assessed_value") is not None]
        if vals:
            min_val = min(vals)
            ids = [b["id"] for b in buildings if b.get("assessed_value") == min_val]
            return jsonify({"ids": ids, "count": len(ids), "filter": filt})

    # Tallest
    if attribute == "height" and operator == "max":
        max_h = max(b["height"] for b in buildings)
        ids = [b["id"] for b in buildings if b["height"] == max_h]
        return jsonify({"ids": ids, "count": len(ids), "filter": filt})

    # Shortest
    if attribute == "height" and operator == "min":
        min_h = min(b["height"] for b in buildings)
        ids = [b["id"] for b in buildings if b["height"] == min_h]
        return jsonify({"ids": ids, "count": len(ids), "filter": filt})

    # ----- NORMAL FILTER -----
    matches = [
        b["id"]
        for b in buildings
        if apply_single_filter(b, attribute, operator, value)
    ]

    return jsonify({
        "ids": matches,
        "count": len(matches),
        "filter": filt
    })


# -------------------------------------------------------
# Return all buildings
# -------------------------------------------------------
@app.route("/api/buildings")
def api_buildings():
    return jsonify(buildings)


# -------------------------------------------------------
# Health
# -------------------------------------------------------
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "buildings_loaded": len(buildings),
        "llm_available": bool(GROQ_API_KEY),
        "provider": "Groq"
    })


# -------------------------------------------------------
# Main
# -------------------------------------------------------
if __name__ == "__main__":
    print("🏙️ BUILDINGS LOADED:", len(buildings))
    app.run(host="0.0.0.0", port=5000, debug=True)