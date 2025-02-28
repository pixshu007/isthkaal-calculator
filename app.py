from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from datetime import datetime
import requests
import pytz

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Function to get latitude & longitude from OpenStreetMap
def get_lat_lon(place):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": "IsthkaalCalculator/1.0"}
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        if data and isinstance(data, list):
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Error fetching lat/lon: {e}")
    
    return None, None

# Function to get sunrise time
def get_sunrise_time(latitude, longitude, date):
    url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&date={date}&formatted=0"
    
    try:
        response = requests.get(url).json()
        if "results" in response:
            return response["results"]["sunrise"]
    except Exception as e:
        print(f"Error fetching sunrise time: {e}")
    
    return None

# Function to convert UTC sunrise time to local time
def convert_utc_to_local(utc_time, timezone="Asia/Kolkata"):
    try:
        utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S%z")
        local_tz = pytz.timezone(timezone)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime("%H:%M:%S")
    except Exception as e:
        print(f"Error converting time: {e}")
        return None

# Function to calculate Isthkaal
def calculate_isthkaal(sunrise_time, birth_time):
    try:
        sunrise = datetime.strptime(sunrise_time, "%H:%M:%S")
        
        # Handle both HH:MM and HH:MM:SS formats for birth time
        try:
            birth = datetime.strptime(birth_time, "%H:%M:%S")
        except ValueError:
            birth = datetime.strptime(birth_time, "%H:%M")

        time_diff_minutes = (birth - sunrise).seconds / 60
        ghati = int(time_diff_minutes / 24)
        pal = int((time_diff_minutes % 24) * 2.5)
        return f"{ghati} घटी {pal} पल"
    except Exception as e:
        print(f"Error calculating Isthkaal: {e}")
        return "Calculation Error"

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    name = data.get("name")
    dob = data.get("dob")
    birth_time = data.get("birthTime")
    birth_place = data.get("birthPlace")

    if not (name and dob and birth_time and birth_place):
        return jsonify({"error": "Missing required fields"}), 400

    latitude, longitude = get_lat_lon(birth_place)
    if latitude is None or longitude is None:
        return jsonify({"error": "Invalid birth place"}), 400

    sunrise_utc = get_sunrise_time(latitude, longitude, dob)
    if not sunrise_utc:
        return jsonify({"error": "Could not fetch sunrise time"}), 400

    local_sunrise_time = convert_utc_to_local(sunrise_utc)
    if local_sunrise_time is None:
        return jsonify({"error": "Time conversion error"}), 400

    isthkaal = calculate_isthkaal(local_sunrise_time, birth_time)

    return jsonify({
        "name": name,
        "dob": dob,
        "isthkaal": isthkaal,
        "sunrise": local_sunrise_time
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use Render’s assigned port (default to 10000)
    app.run(host="0.0.0.0", port=port, debug=True)

