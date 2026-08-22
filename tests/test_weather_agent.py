import asyncio
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import weather_agent


def run_async(coro):
    return asyncio.run(coro)


def make_weather_payload():
    return {
        "weather": [{"description": "light rain"}],
        "main": {
            "temp": 28.5,
            "feels_like": 30.0,
            "humidity": 72,
            "pressure": 1009,
        },
        "wind": {"speed": 4.2},
    }


def mock_openweather(monkeypatch, candidates):
    calls = []

    async def fake_fetch_json(url):
        calls.append(url)

        if url.startswith(weather_agent.GEOCODING_URL):
            return candidates

        if url.startswith(weather_agent.CURRENT_WEATHER_URL):
            return make_weather_payload()

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(
        weather_agent,
        "OPENWEATHER_API_KEY",
        "test-key"
    )

    monkeypatch.setattr(
        weather_agent,
        "fetch_json",
        fake_fetch_json
    )

    return calls


def indian_candidate(name, latitude, longitude, state):
    return {
        "name": name,
        "lat": latitude,
        "lon": longitude,
        "state": state,
        "country": "IN",
    }


def assert_coordinate_weather_request(calls, latitude, longitude):
    assert len(calls) == 2

    geocode_params = parse_qs(urlparse(calls[0]).query)
    weather_params = parse_qs(urlparse(calls[1]).query)

    assert geocode_params["limit"] == ["5"]
    assert weather_params["lat"] == [str(float(latitude))]
    assert weather_params["lon"] == [str(float(longitude))]
    assert weather_params["units"] == ["metric"]
    assert "q" not in weather_params


def test_telangana_hyderabad_prefers_city_over_generic_state(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            indian_candidate(
                "Telangana NGOs Colony",
                17.4,
                78.5,
                "Telangana"
            ),
            indian_candidate(
                "Hyderabad",
                17.385,
                78.4867,
                "Telangana"
            ),
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "weather at telangana,hyderabad"
        )
    )

    assert result["status"] == "success"
    assert "**Weather in Hyderabad, Telangana, India**" in result["answer"]
    assert_coordinate_weather_request(calls, 17.385, 78.4867)
    assert parse_qs(urlparse(calls[0]).query)["q"] == ["telangana, hyderabad"]


def test_indian_small_town_is_resolved(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Karimnagar", 18.4386, 79.1288, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Karimnagar?"
        )
    )

    assert result["status"] == "success"
    assert "Karimnagar, Telangana, India" in result["answer"]
    assert_coordinate_weather_request(calls, 18.4386, 79.1288)


def test_indian_village_prefers_matching_state_and_country(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            {
                "name": "Kothapally",
                "lat": 40.0,
                "lon": -75.0,
                "state": "Pennsylvania",
                "country": "US",
            },
            indian_candidate("Kothapally", 18.0, 79.0, "Telangana"),
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Kothapally, Telangana, India?"
        )
    )

    assert result["status"] == "success"
    assert "Kothapally, Telangana, India" in result["answer"]
    assert_coordinate_weather_request(calls, 18.0, 79.0)


def test_misspelled_city_uses_geocoder_candidate(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Hyderabad", 17.385, 78.4867, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Hyderbad?"
        )
    )

    assert result["status"] == "success"
    assert (
        "Location resolved from **Hyderbad** to "
        "**Hyderabad, Telangana, India**."
        in result["answer"]
    )
    assert_coordinate_weather_request(calls, 17.385, 78.4867)


def test_misspelled_chennai_prefers_indian_candidate(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            {
                "name": "Anhui",
                "lat": 31.0,
                "lon": 117.0,
                "state": "Anhui",
                "country": "CN",
            },
            indian_candidate("Chennai", 13.0827, 80.2707, "Tamil Nadu"),
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "weather at chenni"
        )
    )

    assert result["status"] == "success"
    assert "Chennai, Tamil Nadu, India" in result["answer"]
    assert_coordinate_weather_request(calls, 13.0827, 80.2707)


def test_unknown_location_returns_resolution_guidance(monkeypatch):
    calls = mock_openweather(monkeypatch, [])

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Nowhereville?"
        )
    )

    assert result["status"] == "error"
    assert "couldn't confidently locate 'Nowhereville'" in result["error"]
    assert "district or state" in result["error"]
    assert len(calls) == 1


def test_equally_strong_locations_request_clarification(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            indian_candidate("Rampur", 28.0, 79.0, "Uttar Pradesh"),
            indian_candidate("Rampur", 22.0, 88.0, "West Bengal"),
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Rampur?"
        )
    )

    assert result["status"] == "error"
    assert "Multiple locations match 'Rampur'" in result["error"]
    assert len(calls) == 1


def test_telangana_tarnaka_prefers_area_over_generic_state(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            indian_candidate(
                "Telangana NGOs Colony",
                17.4,
                78.5,
                "Telangana"
            ),
            indian_candidate("Tarnaka", 17.4239, 78.5383, "Telangana"),
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "temperature in Telangana, Tarnaka"
        )
    )

    assert result["status"] == "success"
    assert "Tarnaka, Telangana, India" in result["answer"]
    assert_coordinate_weather_request(calls, 17.4239, 78.5383)


def test_explicit_uk_location_overrides_india_default(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            indian_candidate("London", 28.0, 77.0, "Delhi"),
            {
                "name": "London",
                "lat": 51.5072,
                "lon": -0.1276,
                "state": "England",
                "country": "GB",
            },
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "weather in London, UK"
        )
    )

    assert result["status"] == "success"
    assert "London, England, GB" in result["answer"]
    assert_coordinate_weather_request(calls, 51.5072, -0.1276)


def test_explicit_canada_location_overrides_india_default(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [
            indian_candidate("London", 28.0, 77.0, "Delhi"),
            {
                "name": "London",
                "lat": 42.9849,
                "lon": -81.2453,
                "state": "Ontario",
                "country": "CA",
            },
        ]
    )

    result = run_async(
        weather_agent.weather_agent(
            "weather in London, Canada"
        )
    )

    assert result["status"] == "success"
    assert "London, Ontario, CA" in result["answer"]
    assert_coordinate_weather_request(calls, 42.9849, -81.2453)


def test_rain_conditions_query_uses_shared_location_resolution(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Kothapally", 18.0, 79.0, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "Is it raining in Kothapally?"
        )
    )

    assert result["status"] == "success"
    assert "**Condition:** Light Rain" in result["answer"]
    assert_coordinate_weather_request(calls, 18.0, 79.0)


def test_generic_village_reference_requests_a_specific_location(monkeypatch):
    calls = mock_openweather(monkeypatch, [])

    result = run_async(
        weather_agent.weather_agent(
            "Is it raining in my village?"
        )
    )

    assert result["status"] == "error"
    assert "Please include a city, area, district, or location name." in result["error"]
    assert calls == []
