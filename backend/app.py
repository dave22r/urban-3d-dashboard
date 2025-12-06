import os
import json
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_loader import load_buildings
from dotenv import load_dotenv

# Load .env vars
load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"


app = Flask(__name__)
CORS(app)

# Load buildings once
buildings = load_buildings()


# -------------------------------------------------------
# LLM CALL (2025 updated HF API)
# -------------------------------------------------------
def query_llm(prompt):
    url = "https://router.huggingface.co/v1/text-generation"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.1,
            "return_full_text": False
        }
    }

    print("USING HF URL:", url)

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        print("LLM REQUEST FAILED:", e)
        return ""

    if r.status_code != 200:
        print("LLM ERROR:", r.text)
        return ""

    try:
        data = r.json()
    except Exception as e:
        print("LLM PARSE ERROR:", e)
        print("RAW:", r.text)
        return ""

    # Router returns different structures depending on model
    if isinstance(data, dict):
        if "generated_text" in data:
            return data["generated_text"]

    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict) and "generated_text" in first:
            return first["generated_text"]

    return ""

# -------------------------------------------------------
# EXTRACT JSON FROM LLM OUTPUT
# -------------------------------------------------------
def extract_json_block(text):
    """
    Extracts the FIRST {...} block from an LLM response.
    Works even if LLM adds text before or after.
    """
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group())
    except:
        return None


# -------------------------------------------------------
# /api/query endpoint
# -------------------------------------------------------
@app.route("/api/query", methods=["POST"])
def api_query():
    user_query = request.json.get("query", "")

    prompt = f"""
    Convert this natural language query into JSON.
    Only return a JSON object. No explanation.

    Example:
    "show buildings over 50 meters" ->
    {{"attribute": "height", "operator": ">", "value": 50}}

    "show buildings under 20 meters" ->
    {{"attribute": "height", "operator": "<", "value": 20}}

    Query: "{user_query}"
    """

    llm_output = query_llm(prompt)

    print("\n------------------------")
    print("RAW LLM OUTPUT:")
    print(llm_output)
    print("------------------------\n")

    filt = extract_json_block(llm_output)
    if not filt:
        return jsonify({"ids": []})

    attribute = filt.get("attribute")
    operator = filt.get("operator")
    value = filt.get("value")

    # Attempt to clean value into float
    try:
        value = float(str(value).replace("meters", "").strip())
    except:
        return jsonify({"ids": []})

    # Filtering
    matches = []
    for b in buildings:
        if attribute == "height":
            h = b["height"]

            if operator == ">" and h > value:
                matches.append(b["id"])
            elif operator == "<" and h < value:
                matches.append(b["id"])
            elif operator == ">=" and h >= value:
                matches.append(b["id"])
            elif operator == "<=" and h <= value:
                matches.append(b["id"])

    return jsonify({"ids": matches})


# -------------------------------------------------------
# /api/buildings endpoint
# -------------------------------------------------------
@app.route("/api/buildings")
def api_buildings():
    return jsonify(buildings)


# -------------------------------------------------------
# Main
# -------------------------------------------------------
if __name__ == "__main__":
    print("Filtered buildings count:", len(buildings))
    app.run(host="0.0.0.0", port=5000, debug=True)
