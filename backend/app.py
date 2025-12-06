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
    Extracts JSON object from LLM response.
    Handles responses with or without markdown formatting.
    """
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try to find JSON object
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if not match:
        print("⚠️  No JSON found in LLM output")
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"   Attempted to parse: {match.group()[:100]}")
        return None


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

Return ONLY a JSON object in this exact format:
{{"attribute": "height", "operator": ">", "value": 50}}

Supported attributes: "height" (building height in meters)
Supported operators: ">", "<", ">=", "<=", "="
Value must be a number.

Examples:
Query: "show buildings over 50 meters"
JSON: {{"attribute": "height", "operator": ">", "value": 50}}

Query: "buildings under 20 meters"
JSON: {{"attribute": "height", "operator": "<", "value": 20}}

Query: "buildings taller than 100"
JSON: {{"attribute": "height", "operator": ">", "value": 100}}

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

    # Extract filter parameters
    attribute = filt.get("attribute", "height")
    operator = filt.get("operator", ">")
    value = filt.get("value", 0)

    # Clean and validate value
    try:
        if isinstance(value, str):
            # Remove common suffixes
            value = value.replace("meters", "").replace("metre", "").replace("m", "").strip()
        value = float(value)
    except (ValueError, TypeError) as e:
        print(f"❌ Invalid numeric value: {value} ({e})")
        return jsonify({
            "ids": [], 
            "error": f"Invalid numeric value: {value}",
            "count": 0
        })

    # Filter buildings based on criteria
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
            elif operator in ["==", "="] and abs(h - value) < 1.0:
                matches.append(b["id"])

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