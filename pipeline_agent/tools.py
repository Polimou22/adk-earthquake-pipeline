"""Pipeline steps exposed to the ADK agent as tools."""
import json
import os
from datetime import datetime, timezone

import pandas as pd
import requests

DATA_DIR = "data"
RAW_FILE = os.path.join(DATA_DIR, "raw_earthquakes.json")
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_summary.csv")
REPORT_FILE = os.path.join(DATA_DIR, "report.html")
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson"


def fetch_earthquake_data() -> dict:
    """Ingest: download the last 7 days of M2.5+ earthquakes from the USGS public API."""
    os.makedirs(DATA_DIR, exist_ok=True)
    resp = requests.get(USGS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    with open(RAW_FILE, "w") as f:
        json.dump(data, f)
    return {"status": "success", "records": len(data["features"]), "raw_file": RAW_FILE}


def transform_data() -> dict:
    """Process: flatten the raw data, filter, and aggregate quakes by region."""
    with open(RAW_FILE) as f:
        features = json.load(f)["features"]

    rows = []
    for feat in features:
        p = feat["properties"]
        place = p.get("place") or "Unknown"
        rows.append({
            "magnitude": p.get("mag"),
            "region": place.split(", ")[-1].strip(),  # "10 km N of X, Alaska" -> "Alaska"
            "depth_km": feat["geometry"]["coordinates"][2],
        })
    df = pd.DataFrame(rows).dropna(subset=["magnitude"])

    summary = (
        df.groupby("region")
        .agg(quake_count=("magnitude", "size"),
             avg_magnitude=("magnitude", "mean"),
             max_magnitude=("magnitude", "max"),
             avg_depth_km=("depth_km", "mean"))
        .round(2)
        .sort_values("quake_count", ascending=False)
        .reset_index()
    )
    summary.to_csv(PROCESSED_FILE, index=False)
    return {"status": "success", "regions": len(summary),
            "top_region": summary.iloc[0]["region"], "processed_file": PROCESSED_FILE}


def upload_to_cloud_storage() -> dict:
    """Store: upload raw and processed files to Google Cloud Storage (bucket from GCS_BUCKET)."""
    bucket_name = os.getenv("GCS_BUCKET", "").strip()
    if not bucket_name or bucket_name == "your-bucket-name":
        return {"status": "skipped", "message": "GCS_BUCKET not set, files kept locally in data/"}

    try:
        from google.cloud import storage
        bucket = storage.Client().bucket(bucket_name)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        uploaded = []
        for local, prefix in [(RAW_FILE, "raw"), (PROCESSED_FILE, "processed")]:
            blob_name = f"{prefix}/{run_id}_{os.path.basename(local)}"
            bucket.blob(blob_name).upload_from_filename(local)
            uploaded.append(f"gs://{bucket_name}/{blob_name}")
        return {"status": "success", "uploaded": uploaded}
    except Exception as e:
        return {"status": "error",
                "message": f"Upload failed, files kept locally in data/. Check GCS_BUCKET and credentials. Details: {e}"}


def generate_html_report() -> dict:
    """Visualize: build an HTML page with a bar chart and summary table of the top regions."""
    df = pd.read_csv(PROCESSED_FILE).head(15)
    labels = json.dumps(df["region"].tolist())
    counts = json.dumps(df["quake_count"].tolist())
    table = df.to_html(index=False, border=0, classes="tbl")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Earthquake Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
 body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; color: #222; }}
 .tbl {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
 .tbl th, .tbl td {{ padding: 6px 10px; border-bottom: 1px solid #ddd; text-align: left; }}
 .tbl th {{ background: #f2f2f2; }}
</style></head>
<body>
<h1>Earthquakes by Region (M2.5+, last 7 days)</h1>
<p>Source: USGS Earthquake API. Generated {generated}.</p>
<canvas id="chart" height="120"></canvas>
{table}
<script>
new Chart(document.getElementById('chart'), {{
  type: 'bar',
  data: {{ labels: {labels}, datasets: [{{ label: 'Quake count', data: {counts}, backgroundColor: '#3b6ea5' }}] }},
  options: {{ plugins: {{ legend: {{ display: false }} }} }}
}});
</script>
</body></html>"""
    with open(REPORT_FILE, "w") as f:
        f.write(html)
    return {"status": "success", "report_file": os.path.abspath(REPORT_FILE)}
