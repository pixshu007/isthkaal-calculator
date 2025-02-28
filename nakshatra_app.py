﻿from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import requests
import pytz
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔹 Function to get latitude & longitude from OpenStreetMap
def get_lat_lon(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": "NakshatraCalculator/1.0"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

# 🔹 Function to get Moon's position (longitude)
def get_moon_longitude(year, month, day, hour, minute, lat, lon):
    swe.set_ephe_path("")
    jd = swe.julday(year, month, day, hour + (minute / 60.0))
    result = swe.calc_ut(jd, swe.MOON)

    if isinstance(result, tuple) and len(result) >= 2:
        moon_longitude = result[0]  # Extract only the first value
        return float(moon_longitude)  # Ensure it's a float
    return None  # Return None if calculation fails

# 🔹 Function to determine Nakshatra, Pada, Rashi & Rashi Naam
def get_nakshatra_details(moon_longitude):
    if moon_longitude is None:
        return None, None, None, None, "चंद्रमा की स्थिति का निर्धारण नहीं हो सका।"

    nakshatras = [
        "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
        "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्व फाल्गुनी",
        "उत्तर फाल्गुनी", "हस्त", "चित्रा", "स्वाति", "विशाखा",
        "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा",
        "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्व भाद्रपद",
        "उत्तर भाद्रपद", "रेवती"
    ]

    rashi_list = [
        ("मेष", "चू, चे, चो, ला, ली, लू, ले, लो, अ"),
        ("वृषभ", "ई, ऊ, ए, ओ, वा, वी, वू, वे, वो"),
        ("मिथुन", "का, की, कू, घ, ङ, छ, के, को, हा"),
        ("कर्क", "ही, हू, हे, हो, डा, डी, डू, डे, डो"),
        ("सिंह", "मा, मी, मू, मे, मो, टा, टी, टू, टे"),
        ("कन्या", "टो, पा, पी, पू, ष, ण, ठ, पे, पो"),
        ("तुला", "रा, री, रू, रे, रो, ता, ती, तू, ते"),
        ("वृश्चिक", "तो, ना, नी, नू, ने, नो, या, यी, यू"),
        ("धनु", "ये, यो, भा, भी, भू, धा, फा, ढा, भे"),
        ("मकर", "भो, जा, जी, खी, खू, खे, खो, गा, गी"),
        ("कुंभ", "गू, गे, गो, सा, सी, सू, से, सो, दा"),
        ("मीन", "दी, दू, थ, झ, ञ, दे, दो, चा, ची")
    ]

    pada_names = ["चरण 1", "चरण 2", "चरण 3", "चरण 4"]

    nakshatra_index = int(moon_longitude // 13.3333)
    nakshatra_name = nakshatras[nakshatra_index]

    pada_index = int((moon_longitude % 13.3333) // 3.3333)
    nakshatra_pada = pada_names[pada_index]

    rashi_index = int(moon_longitude // 30)
    rashi_name, rashi_naam_akshar = rashi_list[rashi_index]

    reason = f"आपकी राशि {rashi_name} है, इसलिए आपका नाम {rashi_naam_akshar} अक्षर से शुरू होना शुभ माना जाता है।"

    return nakshatra_name, nakshatra_pada, rashi_name, rashi_naam_akshar, reason

# 🔹 API Endpoint for Nakshatra Calculation
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


# 🔹 Start the Flask App on Render
import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
