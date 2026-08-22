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


def test_hyderabad_weather_uses_geocoding_then_coordinates(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Hyderabad", 17.385, 78.4867, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in   hyderabad!!!"
        )
    )

    assert result["status"] == "success"
    assert "**Weather in Hyderabad, Telangana, India**" in result["answer"]
    assert_coordinate_weather_request(calls, 17.385, 78.4867)
    assert parse_qs(urlparse(calls[0]).query)["q"] == ["hyderabad"]


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
    assert "Location resolved from **Hyderbad** to **Hyderabad**." in result["answer"]
    assert_coordinate_weather_request(calls, 17.385, 78.4867)


def test_misspelled_small_town_uses_geocoder_candidate(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Warangal", 17.9689, 79.5941, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the weather in Warngal?"
        )
    )

    assert result["status"] == "success"
    assert "Location resolved from **Warngal** to **Warangal**." in result["answer"]
    assert_coordinate_weather_request(calls, 17.9689, 79.5941)


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


def test_temperature_query_uses_shared_location_resolution(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Nalgonda", 17.0575, 79.2684, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the temperature in Nalgonda?"
        )
    )

    assert result["status"] == "success"
    assert "**Temperature:** 28.5°C" in result["answer"]
    assert_coordinate_weather_request(calls, 17.0575, 79.2684)


def test_humidity_query_uses_shared_location_resolution(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Warangal", 17.9689, 79.5941, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the humidity in Warangal?"
        )
    )

    assert result["status"] == "success"
    assert "**Humidity:** 72%" in result["answer"]
    assert_coordinate_weather_request(calls, 17.9689, 79.5941)


def test_wind_query_uses_shared_location_resolution(monkeypatch):
    calls = mock_openweather(
        monkeypatch,
        [indian_candidate("Secunderabad", 17.4399, 78.4983, "Telangana")]
    )

    result = run_async(
        weather_agent.weather_agent(
            "What is the wind in Secunderabd?"
        )
    )

    assert result["status"] == "success"
    assert "**Wind speed:** 4.2 m/s" in result["answer"]
    assert_coordinate_weather_request(calls, 17.4399, 78.4983)


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
