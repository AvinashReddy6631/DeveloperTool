import asyncio
import difflib
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv


load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_openweather_api_key():
    load_dotenv()
    env_key = os.getenv("OPENWEATHER_API_KEY")
    if env_key and str(env_key).strip():
        return str(env_key).strip().strip('"').strip("'")
    if OPENWEATHER_API_KEY:
        return str(OPENWEATHER_API_KEY).strip().strip('"').strip("'")
    return None

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

COUNTRY_ALIASES = {
    "india": "IN",
    "in": "IN",
    "uk": "GB",
    "unitedkingdom": "GB",
    "greatbritain": "GB",
    "canada": "CA",
    "france": "FR",
    "usa": "US",
    "us": "US",
    "unitedstates": "US",
}

# Canonical city centers used only to resolve geocoding ties.
# Weather values still come from OpenWeather coordinates.
CANONICAL_CITIES = {
    "hyderabad": {
        "country": "IN",
        "states": {"telangana"},
        "lat": 17.385044,
        "lon": 78.486671,
    },
    "mumbai": {
        "country": "IN",
        "states": {"maharashtra"},
        "lat": 19.0760,
        "lon": 72.8777,
    },
    "delhi": {
        "country": "IN",
        "states": {"delhi"},
        "lat": 28.6139,
        "lon": 77.2090,
    },
    "newdelhi": {
        "country": "IN",
        "states": {"delhi"},
        "lat": 28.6139,
        "lon": 77.2090,
    },
    "bengaluru": {
        "country": "IN",
        "states": {"karnataka"},
        "lat": 12.9716,
        "lon": 77.5946,
    },
    "chennai": {
        "country": "IN",
        "states": {"tamilnadu"},
        "lat": 13.0827,
        "lon": 80.2707,
    },
    "pune": {
        "country": "IN",
        "states": {"maharashtra"},
        "lat": 18.5204,
        "lon": 73.8567,
    },
    "kolkata": {
        "country": "IN",
        "states": {"westbengal"},
        "lat": 22.5726,
        "lon": 88.3639,
    },
}

CITY_ALIASES = {
    "hyderabad": "hyderabad",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "delhi": "delhi",
    "newdelhi": "newdelhi",
    "bengaluru": "bengaluru",
    "bangalore": "bengaluru",
    "chennai": "chennai",
    "madras": "chennai",
    "pune": "pune",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
}


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


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Return the great-circle distance between two coordinates."""

    radius_km = 6371.0
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))
    origin_lat = math.radians(float(lat1))
    dest_lat = math.radians(float(lat2))

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(origin_lat)
        * math.cos(dest_lat)
        * math.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(max(0.0, 1 - a)),
    )


def canonical_city_for(location_context: dict):
    """Return a known-city profile when the query names that city."""

    if location_context.get("country_code") not in {None, "IN"}:
        return None

    matched = None
    for part in location_context.get("parts") or []:
        alias = CITY_ALIASES.get(location_key(part))
        if alias:
            matched = CANONICAL_CITIES[alias]
            break

    if not matched:
        return None

    for part in location_context.get("parts") or []:
        part_key = location_key(part)
        if CITY_ALIASES.get(part_key):
            continue
        if any(
            part_key == expected
            or expected in part_key
            or part_key in expected
            for expected in matched["states"]
        ):
            continue
        return None

    return matched


def candidate_matches_canonical(candidate: dict, canonical: dict) -> bool:
    if candidate.get("country") != canonical["country"]:
        return False

    expected_states = canonical.get("states") or set()
    if not expected_states:
        return True

    state_key = location_key(str(candidate.get("state") or ""))
    return any(
        state_key == expected
        or expected in state_key
        or state_key in expected
        for expected in expected_states
    )


def cluster_nearby_candidates(candidates: list[dict], radius_km: float = 30.0):
    """Group same-place geocoding duplicates independently of API order."""

    remaining = sorted(
        candidates,
        key=lambda item: (
            float(item.get("lat") or 0),
            float(item.get("lon") or 0),
            location_key(str(item.get("name") or "")),
        )
    )
    clusters = []

    for candidate in remaining:
        placed = False
        for cluster in clusters:
            if any(
                haversine_km(
                    candidate["lat"],
                    candidate["lon"],
                    member["lat"],
                    member["lon"],
                ) <= radius_km
                for member in cluster
            ):
                cluster.append(candidate)
                placed = True
                break
        if not placed:
            clusters.append([candidate])

    representatives = []
    for cluster in clusters:
        mean_lat = sum(float(item["lat"]) for item in cluster) / len(cluster)
        mean_lon = sum(float(item["lon"]) for item in cluster) / len(cluster)
        representatives.append(
            min(
                cluster,
                key=lambda item: (
                    haversine_km(
                        item["lat"],
                        item["lon"],
                        mean_lat,
                        mean_lon,
                    ),
                    location_key(str(item.get("name") or "")),
                    float(item["lat"]),
                    float(item["lon"]),
                ),
            )
        )

    return representatives


def choose_canonical_candidate(candidates: list[dict], canonical: dict):
    """Pick a uniquely closer match to a known city center, if one exists."""

    matching = [
        candidate
        for candidate in candidates
        if candidate_matches_canonical(candidate, canonical)
    ]
    if not matching:
        return None

    ranked = sorted(
        matching,
        key=lambda item: (
            haversine_km(
                item["lat"],
                item["lon"],
                canonical["lat"],
                canonical["lon"],
            ),
            location_key(str(item.get("name") or "")),
            float(item["lat"]),
            float(item["lon"]),
        ),
    )
    best = ranked[0]
    best_distance = haversine_km(
        best["lat"],
        best["lon"],
        canonical["lat"],
        canonical["lon"],
    )

    if len(ranked) == 1:
        return best if best_distance <= 80 else None

    second_distance = haversine_km(
        ranked[1]["lat"],
        ranked[1]["lon"],
        canonical["lat"],
        canonical["lon"],
    )

    if second_distance - best_distance >= 15:
        return best

    if all(
        haversine_km(
            item["lat"],
            item["lon"],
            canonical["lat"],
            canonical["lon"],
        ) <= 35
        for item in matching
    ):
        return best

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

async def fetch_geocoding_candidates(location: str):
    """Fetch candidate locations from OpenWeather's Direct Geocoding API."""

    params = urllib.parse.urlencode({
        "q": location,
        "limit": 5,
        "appid": get_openweather_api_key(),
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


def parse_location_context(location: str):
    """Split comma-separated location context without assuming city order."""

    parts = [
        normalize_location_text(part)
        for part in location.split(",")
    ]

    parts = [
        part
        for part in parts
        if part
    ]

    country_code = None

    if parts:
        country_code = COUNTRY_ALIASES.get(
            location_key(parts[-1])
        )

        if country_code:
            parts = parts[:-1]

    return {
        "parts": parts,
        "country_code": country_code,
    }


def name_match_score(location_part: str, candidate_key: str):
    """Score exact, near-exact, and typo-tolerant location names."""

    location_part_key = location_key(location_part)

    if not location_part_key or not candidate_key:
        return 0.0

    if location_part_key == candidate_key:
        return 100.0

    if (
        candidate_key.startswith(location_part_key)
        or location_part_key.startswith(candidate_key)
    ):
        return 90.0

    return (
        difflib.SequenceMatcher(
            None,
            location_part_key,
            candidate_key
        ).ratio()
        * 100
    )


def state_matches_location_part(state: str, location_part: str):
    """Check whether a candidate state matches one user-supplied part."""

    state_key = location_key(state)
    location_part_key = location_key(location_part)

    return bool(
        state_key
        and location_part_key
        and (
            state_key == location_part_key
            or state_key in location_part_key
            or location_part_key in state_key
        )
    )


def score_location_candidate(location_context: dict, candidate: dict):
    """Score candidates after country filtering and context extraction."""

    if (
        candidate.get("lat") is None
        or candidate.get("lon") is None
    ):
        return None

    location_parts = location_context["parts"]

    if not location_parts:
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

    name_scores = [
        max(
            name_match_score(location_part, candidate_key)
            for candidate_key in candidate_keys
        )
        for location_part in location_parts
    ]

    best_name_score = max(name_scores)

    state = candidate.get("state")

    state_match_indexes = {
        index
        for index, location_part in enumerate(location_parts)
        if state
        and state_matches_location_part(
            str(state),
            location_part
        )
    }

    score = best_name_score

    if state_match_indexes:
        score += 30

    if any(
        name_score >= 72
        and index not in state_match_indexes
        for index, name_score in enumerate(name_scores)
    ) and state_match_indexes:
        score += 80

    canonical = canonical_city_for(location_context)
    if canonical and candidate_matches_canonical(candidate, canonical):
        distance_km = haversine_km(
            candidate["lat"],
            candidate["lon"],
            canonical["lat"],
            canonical["lon"],
        )
        if distance_km <= 35:
            score += 40
        elif distance_km <= 80:
            score += 10

    return score


def select_best_location_candidate(
    location: str,
    candidates: list[dict]
):
    """Return a confident candidate or a resolution error type."""

    location_context = parse_location_context(location)

    candidates_with_coordinates = [
        candidate
        for candidate in candidates
        if (
            candidate.get("lat") is not None
            and candidate.get("lon") is not None
        )
    ]

    explicit_country = location_context["country_code"]

    if explicit_country:
        scoped_candidates = [
            candidate
            for candidate in candidates_with_coordinates
            if candidate.get("country") == explicit_country
        ]

        if not scoped_candidates:
            return None, "unresolved"

    else:
        indian_candidates = [
            candidate
            for candidate in candidates_with_coordinates
            if candidate.get("country") == "IN"
        ]

        scoped_candidates = (
            indian_candidates
            if indian_candidates
            else candidates_with_coordinates
        )

    def score_candidates(candidates_to_score):
        return [
            (score, candidate)
            for candidate in candidates_to_score
            for score in [
                score_location_candidate(
                    location_context,
                    candidate
                )
            ]
            if score is not None and score >= 72
        ]

    scored_candidates = score_candidates(scoped_candidates)

    if not scored_candidates:
        if (
            not explicit_country
            and scoped_candidates != candidates_with_coordinates
        ):
            scored_candidates = score_candidates(
                candidates_with_coordinates
            )

        if not scored_candidates:
            return None, "unresolved"


    scored_candidates.sort(
        key=lambda item: (
            -item[0],
            location_key(str(item[1].get("name") or "")),
            float(item[1].get("lat") or 0),
            float(item[1].get("lon") or 0),
        )
    )

    top_score = scored_candidates[0][0]

    equally_strong = [
        candidate
        for score, candidate in scored_candidates
        if top_score - score <= 2
    ]

    if len(equally_strong) == 1:
        return equally_strong[0], None

    canonical = canonical_city_for(location_context)
    if canonical:
        canonical_match = choose_canonical_candidate(
            equally_strong,
            canonical
        )
        if canonical_match:
            return canonical_match, None

    nearby_representatives = cluster_nearby_candidates(equally_strong)
    if len(nearby_representatives) == 1:
        return nearby_representatives[0], None

    return None, "ambiguous"


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
        "appid": get_openweather_api_key(),
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

    if not get_openweather_api_key():

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
                f"**{display_location}**."
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