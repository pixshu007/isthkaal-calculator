from flask import Flask, request, jsonify
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
    swe.set_ephe_path("")  # Use Swiss Ephemeris default data
    jd = swe.julday(year, month, day, hour + (minute / 60.0))  # Julian Day
    _, moon_longitude, _ = swe.calc_ut(jd, swe.MOON)
    return moon_longitude

# 🔹 Function to determine Nakshatra & Pada
def get_nakshatra_details(moon_longitude):
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", 
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", 
        "Anuradha", "Jyeshtha", "Mula", "Purvashadha", "Uttarashadha", 
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", 
        "Uttara Bhadrapada", "Revati"
    ]

    pada_names = ["Pada 1", "Pada 2", "Pada 3", "Pada 4"]

    nakshatra_index = int(moon_longitude // 13.3333)  # Find Nakshatra
    nakshatra_name = nakshatras[nakshatra_index]

    pada_index = int((moon_longitude % 13.3333) // 3.3333)  # Find Pada
    nakshatra_pada = pada_names[pada_index]

    return nakshatra_name, nakshatra_pada

@app.route("/calculate-nakshatra", methods=["POST"])
def calculate_nakshatra():
    data = request.json
    name = data.get("name")
    dob = data.get("dob")
    birth_time = data.get("birthTime")
    birth_place = data.get("birthPlace")

    if not (name and dob and birth_time and birth_place):
        return jsonify({"error": "Missing required fields"}), 400

    lat, lon = get_lat_lon(birth_place)
    if lat is None or lon is None:
        return jsonify({"error": "Invalid birth place"}), 400

    # Convert date & time to Julian format
    dt = datetime.strptime(f"{dob} {birth_time}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone("Asia/Kolkata")
    dt = local_tz.localize(dt)
    
    moon_long = get_moon_longitude(dt.year, dt.month, dt.day, dt.hour, dt.minute, lat, lon)
    nakshatra, pada = get_nakshatra_details(moon_long)

    return jsonify({
        "name": name,
        "dob": dob,
        "nakshatra": nakshatra,
        "nakshatra_pada": pada
    })

if __name__ == "__main__":
    app.run(debug=True)
