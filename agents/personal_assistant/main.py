"""Personal-assistant agent: LangGraphAdapter + ChatAnthropic.

A basic general-purpose assistant. No custom tools — relies on the LLM and
whatever platform tools the SDK injects (send_message, etc.).
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

from thenvoi import Agent
from thenvoi.adapters import LangGraphAdapter
from thenvoi.config import load_agent_config

from agents._logging import setup_logging

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a friendly, knowledgeable personal assistant on the band.ai platform.

Help users with general questions: explanations, brainstorming, writing help,
quick research, planning. Be concise by default; expand when asked.

You work alongside other agents, and which agents are available can change at
any moment — new help may arrive between one message and the next. So your
view of "who can help with what" is never final. When the user asks for
something outside what you can do alone, look around for help in the moment,
based on the current state of the world, not what was true earlier in the
conversation. If you couldn't find help for something before and the user
asks again, that is a reason to look again, not a reason to repeat your
previous answer. Only tell the user something is out of reach after checking
fresh — never from memory."""


async def main() -> None:
    setup_logging()
    load_dotenv()

    ws_url = os.getenv("BAND_WS_URL")
    rest_url = os.getenv("BAND_REST_URL")
    if not ws_url or not rest_url:
        raise SystemExit("BAND_WS_URL and BAND_REST_URL must be set (see .env.example)")

    agent_id, api_key = load_agent_config("personal_assistant")

    adapter = LangGraphAdapter(
        llm=ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4096),
        checkpointer=InMemorySaver(),
        custom_section=SYSTEM_PROMPT,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    log.info("Starting personal assistant agent (id=%s)…", agent_id)
    await agent.run()


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    cli()
