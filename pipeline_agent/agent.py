"""ADK agent that orchestrates the data pipeline."""
from dotenv import load_dotenv
from google.adk.agents import Agent

from .tools import (fetch_earthquake_data, generate_html_report,
                    transform_data, upload_to_cloud_storage)

load_dotenv()

root_agent = Agent(
    name="pipeline_agent",
    model="gemini-3.5-flash-lite",
    description="Runs an earthquake data engineering pipeline.",
    instruction=(
        "You are a data engineering agent. When asked to run the pipeline, call these tools "
        "in order, one at a time: fetch_earthquake_data, transform_data, "
        "upload_to_cloud_storage, generate_html_report. If a step returns an error, stop and "
        "report it. Do not skip steps. When finished, give a short summary: records fetched, "
        "top region, where files were stored, and the report file path."
    ),
    tools=[fetch_earthquake_data, transform_data, upload_to_cloud_storage, generate_html_report],
)
