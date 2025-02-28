from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import requests
import pytz
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "Nakshatra API is running!", 200

@app.route("/calculate-nakshatra", methods=["POST"])
def calculate_nakshatra():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input. Please send JSON data."}), 400

        name = data.get("name")
        dob = data.get("dob")
        birth_time = data.get("birthTime")
        birth_place = data.get("birthPlace")

        if not (name and dob and birth_time and birth_place):
            return jsonify({"error": "कृपया सभी आवश्यक फ़ील्ड भरें।"}), 400

        lat, lon = get_lat_lon(birth_place)
        if lat is None or lon is None:
            return jsonify({"error": "अमान्य जन्म स्थान।"}), 400

        dt = datetime.strptime(f"{dob} {birth_time}", "%Y-%m-%d %H:%M")
        local_tz = pytz.timezone("Asia/Kolkata")
        dt = local_tz.localize(dt)

        moon_long = get_moon_longitude(dt.year, dt.month, dt.day, dt.hour, dt.minute, lat, lon)
        if moon_long is None:
            return jsonify({"error": "चंद्रमा की स्थिति निर्धारित नहीं हो सकी।"}), 500

        nakshatra, pada, rashi, rashi_naam, reason = get_nakshatra_details(moon_long)

        return jsonify({
            "name": name,
            "dob": dob,
            "nakshatra": nakshatra,
            "nakshatra_pada": pada,
            "rashi": rashi,
            "rashi_naam": rashi_naam,
            "rashi_reason": reason
        })

    except Exception as e:
        return jsonify({"error": f"सर्वर त्रुटि: {str(e)}"}), 500

def get_lat_lon(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": "NakshatraCalculator/1.0"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

def get_moon_longitude(year, month, day, hour, minute, lat, lon):
    swe.set_ephe_path("")
    jd = swe.julday(year, month, day, hour + (minute / 60.0))
    result = swe.calc_ut(jd, swe.MOON)
    if isinstance(result, tuple) and len(result) >= 2:
        moon_longitude = result[0]
        return float(moon_longitude)
    return None

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
