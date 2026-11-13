"""Run the agentic pipeline from the command line: python main.py"""
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from pipeline_agent.agent import root_agent


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="earthquake_pipeline")
    session = await runner.session_service.create_session(app_name="earthquake_pipeline", user_id="user")
    message = types.Content(role="user", parts=[types.Part(text="Run the full pipeline.")])

    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
        for part in (event.content.parts if event.content else []) or []:
            if part.function_call:
                print(f"[agent] calling {part.function_call.name}")
            elif part.function_response:
                print(f"[tool]  {part.function_response.name} -> {part.function_response.response}")
            elif part.text:
                print(f"\n{part.text}")


if __name__ == "__main__":
    asyncio.run(main())
