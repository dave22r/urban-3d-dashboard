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
# LLM Integration with Groq API
# -------------------------------------------------------
def query_llm(prompt):
    """
    Queries Groq's LLM API for natural language processing.
    Falls back to regex parser if API is unavailable.
    """
    if not GROQ_API_KEY:
        print("⚠️  No GROQ_API_KEY found - using fallback parser")
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
                "content": "You are a JSON generator. Always respond with valid JSON only, no explanation or markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 150
    }
    
    try:
        print("📡 Calling Groq API...")
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if r.status_code != 200:
            print(f"❌ Groq API error {r.status_code}: {r.text}")
            return parse_query_fallback(prompt)
        
        data = r.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            result = data["choices"][0]["message"]["content"]
            print(f"✅ Groq response received: {result[:100]}...")
            return result
        
        print("⚠️  Unexpected Groq response format")
        return parse_query_fallback(prompt)
        
    except requests.exceptions.Timeout:
        print("⏱️  Groq API timeout - using fallback")
        return parse_query_fallback(prompt)
    except Exception as e:
        print(f"❌ Groq API exception: {e}")
        return parse_query_fallback(prompt)


def parse_query_fallback(prompt):
    """
    Fallback regex-based query parser.
    Handles common natural language patterns without requiring LLM.
    """
    print("🔧 Using fallback regex parser")
    query = prompt.lower()
    
    # Check for stage-based queries
    if any(word in query for word in ["constructed", "construction"]):
        if "under construction" in query:
            result = {
                "attribute": "stage",
                "operator": "=",
                "value": "Under Construction"
            }
        else:
            result = {
                "attribute": "stage",
                "operator": "=",
                "value": "Constructed"
            }
        print(f"🎯 Fallback parsed (stage): {result}")
        return json.dumps(result)
    
    if "approved" in query:
        result = {
            "attribute": "stage",
            "operator": "=",
            "value": "Approved"
        }
        print(f"🎯 Fallback parsed (stage): {result}")
        return json.dumps(result)
    
    # Check for superlative queries
    if any(word in query for word in ["tallest", "highest", "maximum", "max"]):
        result = {
            "attribute": "height",
            "operator": "max",
            "value": 0
        }
        print(f"🎯 Fallback parsed (superlative): {result}")
        return json.dumps(result)
    
    if any(word in query for word in ["shortest", "lowest", "minimum", "min", "smallest"]):
        result = {
            "attribute": "height",
            "operator": "min",
            "value": 0
        }
        print(f"🎯 Fallback parsed (superlative): {result}")
        return json.dumps(result)
    
    # Extract numeric values
    numbers = re.findall(r'\d+\.?\d*', query)
    if not numbers:
        print("⚠️  No numeric value found in query")
        return json.dumps({"attribute": "height", "operator": ">", "value": 0})
    
    value = float(numbers[0])
    
    # Determine operator from keywords
    if any(word in query for word in ["over", "above", "more than", "greater than", "taller than", "higher than"]):
        operator = ">"
    elif any(word in query for word in ["under", "below", "less than", "shorter than", "lower than"]):
        operator = "<"
    elif any(word in query for word in ["at least", "minimum", "min"]):
        operator = ">="
    elif any(word in query for word in ["at most", "maximum", "max"]):
        operator = "<="
    elif any(word in query for word in ["exactly", "equal", "equals"]):
        operator = "="
    else:
        # Default to "greater than" if unclear
        operator = ">"
    
    result = {
        "attribute": "height",
        "operator": operator,
        "value": value
    }
    
    print(f"🎯 Fallback parsed: {result}")
    return json.dumps(result)


def extract_json_block(text):
    """
    Extract ANY valid JSON object from the LLM output.
    Handles nested structures, arrays, and markdown wrappers.
    """

    text = text.strip()

    # First attempt: text is pure JSON
    try:
        return json.loads(text)
    except:
        pass

    # Remove markdown code fences
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # Attempt to extract the *largest* JSON object (handles nested)
    brace_stack = []
    start_index = None

    for i, char in enumerate(text):
        if char == "{":
            if start_index is None:
                start_index = i
            brace_stack.append("{")
        elif char == "}":
            if brace_stack:
                brace_stack.pop()
                if not brace_stack:
                    # Try parsing full block
                    candidate = text[start_index:i+1]
                    try:
                        return json.loads(candidate)
                    except:
                        continue

    return None



def apply_single_filter(building, attribute, operator, value):
    """
    Apply a single filter condition to a building.
    Returns True if building matches the condition.
    """
    if attribute == "height":
        h = building["height"]
        
        if operator == ">":
            return h > value
        elif operator == "<":
            return h < value
        elif operator == ">=":
            return h >= value
        elif operator == "<=":
            return h <= value
        elif operator in ["==", "="]:
            return abs(h - value) < 1.0
        
    elif attribute == "stage":
        stage = building.get("stage", "").lower()
        value_lower = str(value).lower()
        
        if operator == "=":
            return stage == value_lower
        elif operator == "contains":
            return value_lower in stage
    
    return False


def handle_compound_query(filters):
    """
    Handle queries with multiple filter conditions (AND logic).
    """
    print(f"🔗 Processing compound query with {len(filters)} conditions")
    
    matches = []
    for b in buildings:
        # Building must match ALL filters
        if all(apply_single_filter(b, f.get("attribute"), f.get("operator"), f.get("value")) for f in filters):
            matches.append(b["id"])
    
    print(f"✅ Found {len(matches)} buildings matching all conditions")
    
    return jsonify({
        "ids": matches,
        "count": len(matches),
        "filters": filters
    })


# -------------------------------------------------------
# API Endpoints
# -------------------------------------------------------

@app.route("/api/query", methods=["POST"])
def api_query():
    """
    Process natural language query to filter buildings.
    
    Expected input:
        {"query": "show buildings over 50 meters"}
    
    Returns:
        {"ids": [3, 7, 12], "count": 3, "filter": {...}}
    """
    user_query = request.json.get("query", "").strip()
    
    if not user_query:
        return jsonify({"ids": [], "error": "Empty query", "count": 0})

    # Create prompt for LLM
    prompt = f"""Convert this natural language query into a JSON filter object.

Return ONLY a JSON object. For single conditions use this format:
{{"attribute": "height", "operator": ">", "value": 50}}

For multiple conditions (AND logic), use this format:
{{"filters": [{{"attribute": "height", "operator": ">", "value": 100}}, {{"attribute": "stage", "operator": "=", "value": "Constructed"}}]}}

Supported attributes:
- "height" (number in meters)
- "stage" (text: "Constructed", "Approved", "Under Construction", etc.)

Supported operators:
- For numbers: ">", "<", ">=", "<=", "=", "max", "min"
- For text: "=", "contains"

Examples:
Query: "show buildings over 50 meters"
JSON: {{"attribute": "height", "operator": ">", "value": 50}}

Query: "show me the tallest building"
JSON: {{"attribute": "height", "operator": "max", "value": 0}}

Query: "show all constructed buildings"
JSON: {{"attribute": "stage", "operator": "=", "value": "Constructed"}}

Query: "constructed buildings taller than 100 meters"
JSON: {{"filters": [{{"attribute": "stage", "operator": "=", "value": "Constructed"}}, {{"attribute": "height", "operator": ">", "value": 100}}]}}

Query: "approved buildings under 50m"
JSON: {{"filters": [{{"attribute": "stage", "operator": "=", "value": "Approved"}}, {{"attribute": "height", "operator": "<", "value": 50}}]}}

Now convert this query:
Query: "{user_query}"
JSON:"""

    # Get LLM response (or fallback)
    llm_output = query_llm(prompt)

    print("\n" + "="*60)
    print(f"USER QUERY: {user_query}")
    print(f"LLM OUTPUT: {llm_output}")
    print("="*60 + "\n")

    # Extract and parse JSON
    filt = extract_json_block(llm_output)
    if not filt:
        print("❌ Failed to extract valid JSON from response")
        return jsonify({
            "ids": [], 
            "error": "Could not parse query - try rephrasing",
            "count": 0
        })

    # Check if it's a compound query (multiple filters)
    if "filters" in filt:
        return handle_compound_query(filt["filters"])

    # Extract filter parameters for single query
    attribute = filt.get("attribute", "height")
    operator = filt.get("operator", ">")
    value = filt.get("value", 0)

    # Handle superlative queries (tallest, shortest, etc.)
    if operator in ["max", "tallest", "highest", "maximum"]:
        # Find the tallest building(s)
        if attribute == "height":
            max_height = max(b["height"] for b in buildings)
            matches = [b["id"] for b in buildings if b["height"] == max_height]
            print(f"✅ Found tallest building(s) with height {max_height}m: {matches}")
            return jsonify({
                "ids": matches,
                "count": len(matches),
                "filter": {
                    "attribute": attribute,
                    "operator": "max",
                    "value": max_height
                }
            })
    
    if operator in ["min", "shortest", "lowest", "minimum"]:
        # Find the shortest building(s)
        if attribute == "height":
            min_height = min(b["height"] for b in buildings)
            matches = [b["id"] for b in buildings if b["height"] == min_height]
            print(f"✅ Found shortest building(s) with height {min_height}m: {matches}")
            return jsonify({
                "ids": matches,
                "count": len(matches),
                "filter": {
                    "attribute": attribute,
                    "operator": "min",
                    "value": min_height
                }
            })

    # Apply single filter
    matches = [b["id"] for b in buildings if apply_single_filter(b, attribute, operator, value)]

    print(f"✅ Found {len(matches)} matching buildings")
    
    return jsonify({
        "ids": matches, 
        "count": len(matches),
        "filter": {
            "attribute": attribute,
            "operator": operator,
            "value": value
        }
    })


@app.route("/api/buildings")
def api_buildings():
    """
    Return all loaded buildings with their properties.
    """
    return jsonify(buildings)


@app.route("/api/health")
def health():
    """
    Health check endpoint - verify server and data are loaded.
    """
    return jsonify({
        "status": "ok",
        "buildings_loaded": len(buildings),
        "llm_available": bool(GROQ_API_KEY),
        "llm_provider": "Groq (Llama 3.3 70B)" if GROQ_API_KEY else "Fallback Parser"
    })


# -------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏙️  URBAN 3D DASHBOARD - Backend Server")
    print("="*60)
    print(f"📊 Buildings loaded: {len(buildings)}")
    
    if GROQ_API_KEY:
        print("✅ LLM: Groq API (Llama 3.3 70B)")
        print(f"   API Key: {GROQ_API_KEY[:8]}...{GROQ_API_KEY[-4:]}")
    else:
        print("⚠️  LLM: Fallback regex parser (no API key)")
        print("   Add GROQ_API_KEY to .env for better results")
    
    print("\n🚀 Starting server on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)