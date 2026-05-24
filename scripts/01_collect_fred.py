import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

series_map = {
    "FEDFUNDS": "미국 기준금리",
    "DGS10": "미국 10년물 국채금리",
    "CPIAUCSL": "미국 소비자물가지수",
    "UNRATE": "미국 실업률",
    "GDP": "미국 GDP",
}

rows = []

for series_id, series_name in series_map.items():
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": "2015-01-01",
    }

    res = requests.get(url, params=params)
    res.raise_for_status()

    observations = res.json()["observations"]

    for item in observations:
        if item["value"] == ".":
            continue

        rows.append({
            "date": item["date"],
            "series_id": series_id,
            "series_name": series_name,
            "value": float(item["value"]),
            "source": "FRED",
        })

df = pd.DataFrame(rows)
df.to_csv("data/processed/fred_indicators.csv", index=False, encoding="utf-8-sig")

print("FRED 데이터 저장 완료:", df.shape)