import asyncio
import difflib
import json
import os
import re
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
        "current weather in ",
        "current weather for ",
        "current weather at ",
        "is it raining in ",
        "raining in ",
    ]

    for pattern in patterns:
        index = lower_query.find(pattern)

        if index != -1:
            city = normalize_location_text(query[
                index + len(pattern):
            ])

            if city:
                if is_generic_location_reference(city):
                    return None

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
            remainder = normalize_location_text(query[
                index + len(word):
            ])

            remainder = remainder.lstrip(
                " inat:,-"
            ).strip()

            if (
                remainder
                and not is_generic_location_reference(remainder)
            ):
                return remainder.rstrip("?.!, ")

    return None


def normalize_location_text(location: str) -> str:
    """Normalize user-entered location text before geocoding."""

    normalized = re.sub(
        r"\s+",
        " ",
        str(location or "").strip()
    )

    normalized = re.sub(
        r"\s*,\s*",
        ", ",
        normalized
    )

    return normalized.strip(" ,.;:!?")


def is_generic_location_reference(location: str) -> bool:
    """Reject location references that need user-provided context."""

    normalized = re.sub(
        r"\s+",
        " ",
        location.casefold().strip()
    )

    return normalized in {
        "my village",
        "my town",
        "my city",
        "my area",
        "my location",
        "here",
        "there",
    }


def location_key(location: str) -> str:
    """Build a comparison key that ignores case and punctuation."""

    return re.sub(
        r"[^\w]",
        "",
        normalize_location_text(location).casefold()
    )


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

async def fetch_geocoding_candidates(location: str):
    """Fetch candidate locations from OpenWeather's Direct Geocoding API."""

    params = urllib.parse.urlencode({
        "q": location,
        "limit": 5,
        "appid": OPENWEATHER_API_KEY,
    })

    url = (
        f"{GEOCODING_URL}?{params}"
    )

    data = await fetch_json(url)

    if not isinstance(data, list):
        return []

    return [
        candidate
        for candidate in data
        if isinstance(candidate, dict)
    ]


def candidate_names(candidate: dict) -> list[str]:
    """Return the canonical and localized names for one candidate."""

    names = []

    if candidate.get("name"):
        names.append(str(candidate["name"]))

    local_names = candidate.get("local_names")

    if isinstance(local_names, dict):
        names.extend(
            str(name)
            for name in local_names.values()
            if name
        )

    return names


def score_location_candidate(location: str, candidate: dict):
    """Score a geocoder candidate without inventing a location match."""

    if (
        candidate.get("lat") is None
        or candidate.get("lon") is None
    ):
        return None

    primary_location = normalize_location_text(
        location.split(",", 1)[0]
    )

    primary_key = location_key(primary_location)

    if not primary_key:
        return None

    candidate_keys = [
        location_key(name)
        for name in candidate_names(candidate)
    ]

    candidate_keys = [
        key
        for key in candidate_keys
        if key
    ]

    if not candidate_keys:
        return None

    if primary_key in candidate_keys:
        score = 100.0

    elif any(
        key.startswith(primary_key)
        or primary_key.startswith(key)
        for key in candidate_keys
    ):
        score = 90.0

    else:
        score = max(
            difflib.SequenceMatcher(
                None,
                primary_key,
                candidate_key
            ).ratio()
            * 100
            for candidate_key in candidate_keys
        )

    location_context = location_key(location)

    state = candidate.get("state")

    if state and location_key(str(state)) in location_context:
        score += 15

    if (
        candidate.get("country") == "IN"
        and "india" in location_context
    ):
        score += 20

    return score


def select_best_location_candidate(
    location: str,
    candidates: list[dict]
):
    """Return a confident candidate or a resolution error type."""

    scored_candidates = []

    for candidate in candidates:
        score = score_location_candidate(
            location,
            candidate
        )

        if score is not None and score >= 72:
            scored_candidates.append((score, candidate))

    if not scored_candidates:
        return None, "unresolved"

    scored_candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    top_score = scored_candidates[0][0]

    equally_strong = [
        candidate
        for score, candidate in scored_candidates
        if top_score - score <= 2
    ]

    if len(equally_strong) > 1:
        india_candidates = [
            candidate
            for candidate in equally_strong
            if candidate.get("country") == "IN"
        ]

        if (
            "india" in location_key(location)
            and len(india_candidates) == 1
        ):
            return india_candidates[0], None

        return None, "ambiguous"

    return scored_candidates[0][1], None


async def resolve_location(location: str):
    """Geocode normalized location text and select a safe best match."""

    candidates = await fetch_geocoding_candidates(location)

    return select_best_location_candidate(
        location,
        candidates
    )


async def geocode_location(location: str):
    """Return the best candidate for existing direct geocoding callers."""

    candidate, _ = await resolve_location(location)

    return candidate


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

    location = normalize_location_text(location)

    mcp_calls = []

    try:

        # ----------------------------------------------------
        # 1. GEOCODING
        # ----------------------------------------------------

        geocode_start = time.perf_counter()

        resolved, resolution_error = await resolve_location(
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
            "status": "success" if resolved else "error",
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
                    f"Multiple locations match '{location}'. "
                    "Please add the district, state, or country."
                    if resolution_error == "ambiguous"
                    else f"I couldn't confidently locate "
                    f"'{location}'. Try adding the district or "
                    f"state, for example '{location}, Telangana, "
                    "India'."
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
                "India"
                if country == "IN"
                else str(country)
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