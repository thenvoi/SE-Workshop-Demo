"""Weather agent: AnthropicAdapter + Open-Meteo-backed get_weather tool."""

import asyncio
import logging
import os

from dotenv import load_dotenv

from thenvoi import Agent
from thenvoi.adapters import AnthropicAdapter
from thenvoi.config import load_agent_config
from thenvoi.core.types import AdapterFeatures, Emit

from agents._logging import setup_logging

from .weather_tool import WeatherInput, get_weather

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a weather agent on the band.ai platform.

When a user asks about weather, temperature, rain, wind, or conditions in a
specific place, call the get_weather tool with the city name. Then summarize
the result in one or two friendly sentences.

If the user asks something unrelated to weather, politely redirect them — your
job is weather only."""


async def main() -> None:
    setup_logging()
    load_dotenv()

    ws_url = os.getenv("BAND_WS_URL")
    rest_url = os.getenv("BAND_REST_URL")
    if not ws_url or not rest_url:
        raise SystemExit("BAND_WS_URL and BAND_REST_URL must be set (see .env.example)")

    agent_id, api_key = load_agent_config("weather_agent")

    adapter = AnthropicAdapter(
        model="claude-sonnet-4-6",
        prompt=SYSTEM_PROMPT,
        additional_tools=[(WeatherInput, get_weather)],
        features=AdapterFeatures(emit={Emit.EXECUTION}),
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    log.info("Starting weather agent (id=%s)…", agent_id)
    await agent.run()


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    cli()
