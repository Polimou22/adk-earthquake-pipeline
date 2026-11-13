# Agentic Earthquake Data Pipeline (Google ADK)

An end-to-end data engineering pipeline driven by a Google ADK agent. The agent calls four tools in order:

1. **Ingest** `fetch_earthquake_data` pulls the last 7 days of M2.5+ earthquakes from the public USGS API (no key needed).
2. **Process** `transform_data` flattens the GeoJSON, drops records with no magnitude, and aggregates by region (count, average/max magnitude, average depth).
3. **Store** `upload_to_cloud_storage` uploads the raw JSON and processed CSV to Google Cloud Storage under `raw/` and `processed/`, with a timestamped run ID.
4. **Visualize** `generate_html_report` writes `data/report.html` with a bar chart and summary table.

## Project structure

```
pipeline_agent/
  agent.py    # ADK agent definition (root_agent)
  tools.py    # the four pipeline steps
main.py       # runs the agent from the command line
requirements.txt
.env.example
```

## Setup

Requires Python 3.10+.

```bash
git clone <this-repo-url>
cd adk-earthquake-pipeline
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in:

- `GOOGLE_API_KEY`: a free Gemini API key from https://aistudio.google.com/apikey
- `GCS_BUCKET`: the name of a GCS bucket you can write to

Authenticate to Google Cloud so the storage client can find credentials:

```bash
gcloud auth application-default login
```

If `GCS_BUCKET` is left blank, the storage step is skipped and files stay in `data/`, so the rest of the pipeline still runs.

## Run

```bash
python main.py
```

Then open `data/report.html` in a browser.

You can also chat with the agent in ADK's dev UI:

```bash
adk web
```

Select `pipeline_agent` and type "Run the full pipeline."

## Security

No credentials are committed. `.env` and `data/` are in `.gitignore`.
