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
    response = requests.get(base_url, params=params, headers=headers)

    if response.status_code != 200 or response.text.strip() == "":
        return None, None
    data = response.json()
    if data and isinstance(data, list):
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon
    return None, None

# Function to get sunrise time
def get_sunrise_time(latitude, longitude, date):
    url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&date={date}&formatted=0"
    response = requests.get(url).json()
    return response["results"]["sunrise"] if "results" in response else None

# Function to convert UTC sunrise time to local time
def convert_utc_to_local(utc_time, timezone):
    utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S%z")
    local_tz = pytz.timezone(timezone)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime("%H:%M:%S")

# Function to calculate Isthkaal
def calculate_isthkaal(sunrise_time, birth_time):
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

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json
    name = data.get("name")
    dob = data.get("dob")
    birth_time = data.get("birthTime")
    birth_place = data.get("birthPlace")

    latitude, longitude = get_lat_lon(birth_place)
    if latitude is None or longitude is None:
        return jsonify({"error": "Invalid birth place"}), 400

    sunrise_utc = get_sunrise_time(latitude, longitude, dob)
    if not sunrise_utc:
        return jsonify({"error": "Could not fetch sunrise time"}), 400

    local_sunrise_time = convert_utc_to_local(sunrise_utc, "Asia/Kolkata")
    isthkaal = calculate_isthkaal(local_sunrise_time, birth_time)

    return jsonify({"name": name, "dob": dob, "isthkaal": isthkaal, "sunrise": local_sunrise_time})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
