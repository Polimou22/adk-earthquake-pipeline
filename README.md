# Agentic Earthquake Data Pipeline (Google ADK)
**Before you run:** this repo contains no API keys. You need your own free Gemini API key from https://aistudio.google.com/apikey, added to a `.env` file as shown in Setup below. Without it, `python main.py` stops with a "Missing Gemini API key" message.

An end-to-end data engineering pipeline driven by a Google ADK agent. The agent calls four tools in order:
Ingest `fetch_earthquake_data` pulls the last 7 days of M2.5+ earthquakes from the public USGS API (no key needed).

Process `transform_data` flattens the GeoJSON, drops records with no magnitude, and aggregates by region (count, average/max magnitude, average depth).
Store `upload_to_cloud_storage` uploads the raw JSON and processed CSV to Google Cloud Storage under `raw/` and `processed/`, with a timestamped run ID.
Visualize `generate_html_report` writes `data/report.html` with a bar chart and summary table.
Project structure
```
pipeline_agent/
  agent.py    # ADK agent definition (root_agent)
  tools.py    # the four pipeline steps
main.py       # runs the agent from the command line
requirements.txt
.env.example
```
Setup
Requires Python 3.10+. The quickest way to run it is a GitHub Codespace (green Code button, Codespaces tab), which has Python ready.
```bash
git clone https://github.com/Polimou22/adk-earthquake-pipeline.git
cd adk-earthquake-pipeline
pip install -r requirements.txt
cp .env.example .env
```
Open `.env` and set:
`GOOGLE_API_KEY`: your Gemini API key. Use a key from a project without billing enabled to stay on the free tier.
`GCS_BUCKET` (optional): a Google Cloud Storage bucket you can write to. Leave it blank to skip the upload step and keep files in `data/`.
`GOOGLE_APPLICATION_CREDENTIALS` (only if `GCS_BUCKET` is set): path to a service account JSON key with the Storage Object Admin role on that bucket. Alternatively, delete this line and run `gcloud auth application-default login`.
Run `cp .env.example .env` only once. Running it again overwrites your edits.
Run
```bash
python main.py
```
You will see the agent call each tool in turn, then a summary. Open `data/report.html` in a browser to view the chart.
You can also chat with the agent in ADK's dev UI with `adk web`. Select `pipeline_agent` and type "Run the full pipeline."
Troubleshooting
Missing Gemini API key / API key not valid: check `GOOGLE_API_KEY` in `.env`.
503 model overloaded: temporary on Google's side. Wait a few minutes, or change the `model` in `pipeline_agent/agent.py` to another current Gemini model.
402 prepayment credits depleted: the key's project has billing enabled. Create a key in a separate project without billing.
Security
No credentials are committed. `.env`, `data/`, and `gcs-key.json` are in `.gitignore`.
