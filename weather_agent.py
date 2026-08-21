import asyncio
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv


load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def extract_city(query: str) -> str | None:
    """
    Extract a location from common weather questions.

    Supports examples such as:
      - weather in Hyderabad
      - temperature in Chennai
      - humidity in Mumbai
      - forecast for Delhi
      - rain in Bangalore
      - wind at Pune
      - weather Hyderabad
    """

    query = query.strip()

    if not query:
        return None

    lower_query = query.lower()

    # Most natural-language patterns.
    patterns = [
        "weather in ",
        "weather for ",
        "weather at ",
        "temperature in ",
        "temperature for ",
        "temperature at ",
        "forecast in ",
        "forecast for ",
        "forecast at ",
        "rain in ",
        "rain for ",
        "rain at ",
        "humidity in ",
        "humidity for ",
        "humidity at ",
        "wind in ",
        "wind for ",
        "wind at ",
        "conditions in ",
        "conditions for ",
        "conditions at ",
    ]

    for pattern in patterns:
        index = lower_query.find(pattern)

        if index != -1:
            city = query[
                index + len(pattern):
            ].strip()

            if city:
                return city.rstrip("?.!, ")

    # Fallback:
    # "What is the weather Hyderabad?"
    # "Tell me weather Mumbai"
    weather_words = [
        "weather",
        "temperature",
        "forecast",
        "humidity",
        "rain",
        "wind",
        "conditions",
    ]

    for word in weather_words:
        index = lower_query.find(word)

        if index != -1:
            remainder = query[
                index + len(word):
            ].strip()

            remainder = remainder.lstrip(
                " inat:,-"
            ).strip()

            if remainder:
                return remainder.rstrip("?.!, ")

    return None


# ============================================================
# HTTP HELPER
# ============================================================

async def fetch_json(url: str) -> dict | list:
    """
    Run a blocking urllib request in a worker thread so the
    async Weather Agent does not block the event loop.
    """

    def make_request():
        with urllib.request.urlopen(
            url,
            timeout=10
        ) as response:

            return json.loads(
                response.read().decode("utf-8")
            )

    return await asyncio.to_thread(
        make_request
    )


# ============================================================
# OPENWEATHER GEOCODING
# ============================================================

async def geocode_location(location: str):
    """
    Convert an arbitrary location name into coordinates using
    OpenWeather's Direct Geocoding API.

    Returns the best matching location dictionary.
    """

    params = urllib.parse.urlencode({
        "q": location,
        "limit": 5,
        "appid": OPENWEATHER_API_KEY,
    })

    url = (
        f"{GEOCODING_URL}?{params}"
    )

    data = await fetch_json(url)

    if not isinstance(data, list) or not data:
        return None

    # OpenWeather returns the best matches first. Use the
    # first result and preserve the returned canonical name.
    best = data[0]

    if not isinstance(best, dict):
        return None

    return best


# ============================================================
# CURRENT WEATHER
# ============================================================

async def fetch_current_weather(
    latitude: float,
    longitude: float
):
    """
    Fetch current weather using coordinates.

    OpenWeather recommends coordinates for the weather request
    after geocoding a location name.
    """

    params = urllib.parse.urlencode({
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    })

    url = (
        f"{CURRENT_WEATHER_URL}?{params}"
    )

    return await fetch_json(url)


# ============================================================
# WEATHER AGENT
# ============================================================

async def weather_agent(query: str):

    start_time = time.perf_counter()

    if not OPENWEATHER_API_KEY:

        return {
            "agent": "weather_agent",
            "status": "error",
            "answer": None,
            "tool_calls": 0,
            "execution_time": round(
                time.perf_counter() - start_time,
                3
            ),
            "error": (
                "OPENWEATHER_API_KEY is not configured."
            ),
        }

    location = extract_city(query)

    if not location:

        return {
            "agent": "weather_agent",
            "status": "error",
            "answer": None,
            "tool_calls": 0,
            "execution_time": round(
                time.perf_counter() - start_time,
                3
            ),
            "error": (
                "Could not determine the location from "
                "the query. Please include a city, area, "
                "district, or location name."
            ),
        }

    mcp_calls = []

    try:

        # ----------------------------------------------------
        # 1. GEOCODING
        # ----------------------------------------------------

        geocode_start = time.perf_counter()

        resolved = await geocode_location(
            location
        )

        geocode_time = round(
            time.perf_counter() - geocode_start,
            3
        )

        mcp_calls.append({
            "tool": "geocode_location",
            "arguments": {
                "location": location
            },
            "status": (
                "success"
                if resolved
                else "error"
            ),
            "execution_time": geocode_time,
        })

        if not resolved:

            execution_time = round(
                time.perf_counter() - start_time,
                3
            )

            return {
                "agent": "weather_agent",
                "status": "error",
                "answer": None,
                "tool_calls": len(mcp_calls),
                "execution_time": execution_time,
                "error": (
                    f"I could not find a location matching "
                    f"'{location}'. Please check the spelling "
                    f"or try a nearby city."
                ),
                "mcp_calls": mcp_calls,
            }

        latitude = resolved.get("lat")
        longitude = resolved.get("lon")

        resolved_name = (
            resolved.get("name")
            or location
        )

        state = resolved.get(
            "state"
        )

        country = resolved.get(
            "country"
        )

        if latitude is None or longitude is None:

            execution_time = round(
                time.perf_counter() - start_time,
                3
            )

            return {
                "agent": "weather_agent",
                "status": "error",
                "answer": None,
                "tool_calls": len(mcp_calls),
                "execution_time": execution_time,
                "error": (
                    "The geocoding service returned an "
                    "invalid location."
                ),
                "mcp_calls": mcp_calls,
            }

        # ----------------------------------------------------
        # 2. CURRENT WEATHER
        # ----------------------------------------------------

        weather_start = time.perf_counter()

        data = await fetch_current_weather(
            float(latitude),
            float(longitude)
        )

        weather_time = round(
            time.perf_counter() - weather_start,
            3
        )

        weather = (
            data.get("weather", [{}])[0]
            if isinstance(data, dict)
            else {}
        )

        main = (
            data.get("main", {})
            if isinstance(data, dict)
            else {}
        )

        wind = (
            data.get("wind", {})
            if isinstance(data, dict)
            else {}
        )

        temperature = main.get(
            "temp"
        )

        feels_like = main.get(
            "feels_like"
        )

        humidity = main.get(
            "humidity"
        )

        pressure = main.get(
            "pressure"
        )

        condition = weather.get(
            "description",
            "Unknown"
        )

        wind_speed = wind.get(
            "speed",
            0
        )

        mcp_calls.append({
            "tool": "get_current_weather",
            "arguments": {
                "latitude": float(latitude),
                "longitude": float(longitude),
            },
            "status": "success",
            "execution_time": weather_time,
        })

        # ----------------------------------------------------
        # 3. FORMATTED ANSWER
        # ----------------------------------------------------

        location_parts = [
            str(resolved_name)
        ]

        if state:
            location_parts.append(
                str(state)
            )

        if country:
            location_parts.append(
                str(country)
            )

        display_location = ", ".join(
            location_parts
        )

        correction_note = ""

        normalized_input = (
            location.strip().lower()
        )

        normalized_resolved = (
            str(resolved_name).strip().lower()
        )

        if (
            normalized_input
            != normalized_resolved
        ):

            correction_note = (
                f"\n\n"
                f"Location resolved from "
                f"**{location}** to "
                f"**{resolved_name}**."
            )

        answer = (
            f"**Weather in {display_location}**\n\n"
            f"- **Temperature:** {temperature}°C\n"
            f"- **Feels like:** {feels_like}°C\n"
            f"- **Condition:** {condition.title()}\n"
            f"- **Humidity:** {humidity}%\n"
            f"- **Wind speed:** {wind_speed} m/s\n"
            f"- **Pressure:** {pressure} hPa"
            f"{correction_note}"
        )

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        return {
            "agent": "weather_agent",
            "status": "success",
            "answer": answer,
            "tool_calls": len(mcp_calls),
            "execution_time": execution_time,
            "error": None,
            "mcp_calls": mcp_calls,
        }

    except urllib.error.HTTPError as exc:

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        if exc.code == 401:
            error_message = (
                "OpenWeather authentication failed. "
                "Please check your OPENWEATHER_API_KEY."
            )

        elif exc.code == 429:
            error_message = (
                "OpenWeather request limit reached. "
                "Please try again later."
            )

        elif exc.code == 404:
            error_message = (
                f"Weather data was not found for "
                f"'{location}'."
            )

        else:
            error_message = (
                f"OpenWeather request failed "
                f"with HTTP {exc.code}."
            )

        return {
            "agent": "weather_agent",
            "status": "error",
            "answer": None,
            "tool_calls": len(mcp_calls),
            "execution_time": execution_time,
            "error": error_message,
            "mcp_calls": mcp_calls,
        }

    except urllib.error.URLError as exc:

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        return {
            "agent": "weather_agent",
            "status": "error",
            "answer": None,
            "tool_calls": len(mcp_calls),
            "execution_time": execution_time,
            "error": (
                "Could not connect to OpenWeather. "
                f"Network error: {exc.reason}"
            ),
            "mcp_calls": mcp_calls,
        }

    except Exception as exc:

        execution_time = round(
            time.perf_counter() - start_time,
            3
        )

        # Preserve an execution record for the weather call
        # if it failed before being added.
        if not any(
            call.get("tool") == "get_current_weather"
            for call in mcp_calls
        ):
            mcp_calls.append({
                "tool": "get_current_weather",
                "arguments": {
                    "location": location
                },
                "status": "error",
                "execution_time": 0.0,
            })

        return {
            "agent": "weather_agent",
            "status": "error",
            "answer": None,
            "tool_calls": len(mcp_calls),
            "execution_time": execution_time,
            "error": str(exc),
            "mcp_calls": mcp_calls,
        }