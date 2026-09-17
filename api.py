from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MGAI Track 2 Dashboard API",
    version="1.0.0"
)

# 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent


def read_csv(filename):
    path = BASE_DIR / filename

    if not path.exists():
        return []

    df = pd.read_csv(path)

    # 把 NaN 转成 None，保证 JSON 正常
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/baseline")
def baseline():
    return read_csv("baseline.csv")


@app.get("/api/opportunities")
def opportunities():
    return read_csv("opportunities.csv")


@app.get("/api/rightsizing")
def rightsizing():
    return read_csv("rightsizing_summary.csv")


@app.get("/api/hardware-risk")
def hardware_risk():
    return read_csv("risk_hardware.csv")


@app.get("/api/dashboard")
def dashboard():
    return {
        "baseline": read_csv("baseline.csv"),
        "opportunities": read_csv("opportunities.csv"),
        "rightsizing": read_csv("rightsizing_summary.csv"),
        "hardware_risk": read_csv("risk_hardware.csv"),
    }
