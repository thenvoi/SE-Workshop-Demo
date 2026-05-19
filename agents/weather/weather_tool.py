"""Open-Meteo backed get_weather tool for the weather agent.

Two HTTP calls per invocation:
  1. Geocoding API → resolve city name to (lat, lon, country)
  2. Forecast API → current conditions at that coordinate

Open-Meteo is free and keyless. https://open-meteo.com/
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes → human description.
# https://open-meteo.com/en/docs#weathervariables
WEATHER_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail",
}


class WeatherInput(BaseModel):
    """Get current weather conditions for a city by name.

    Use this when the user asks about the weather, temperature, rain, snow,
    wind, or general conditions in a specific place.
    """

    city: str = Field(
        description="City name to look up — e.g. 'Tel Aviv', 'San Francisco', 'Tokyo'. May include country for disambiguation, e.g. 'Springfield, IL'."
    )


async def _geocode(client: httpx.AsyncClient, city: str) -> dict[str, Any] | None:
    r = await client.get(GEOCODE_URL, params={"name": city, "count": 1, "language": "en"})
    r.raise_for_status()
    results = r.json().get("results") or []
    return results[0] if results else None


async def _forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict[str, Any]:
    r = await client.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
        },
    )
    r.raise_for_status()
    return r.json()["current"]


async def get_weather(args: WeatherInput) -> str:
    """Tool implementation: geocode → forecast → formatted summary."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        place = await _geocode(client, args.city)
        if place is None:
            return f"Could not find a city matching '{args.city}'."

        current = await _forecast(client, place["latitude"], place["longitude"])

    description = WEATHER_CODES.get(current["weather_code"], "unknown conditions")
    label_parts = [place["name"]]
    if admin1 := place.get("admin1"):
        label_parts.append(admin1)
    if country := place.get("country"):
        label_parts.append(country)
    label = ", ".join(label_parts)

    return (
        f"Weather in {label}: {description}, "
        f"{current['temperature_2m']}°C, "
        f"humidity {current['relative_humidity_2m']}%, "
        f"wind {current['wind_speed_10m']} km/h."
    )
