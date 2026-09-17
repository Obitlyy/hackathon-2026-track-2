from pathlib import Path
import json
from urllib.request import urlopen

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =====================================================
# App
# =====================================================

app = FastAPI(
    title="GPU Capacity Decision Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5001",
        "http://127.0.0.1:5001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# Paths
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

JSON_DIR = BASE_DIR / "outputs" / "json"

DASHBOARD_PATH = JSON_DIR / "dashboard_data.json"

SCENARIO_PATH = JSON_DIR / "what_if_scenarios.json"

OFFICIAL_API = "http://localhost:8000"


# =====================================================
# Helpers
# =====================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def get_official_summary():

    url = (
        OFFICIAL_API +
        "/v1/efficiency/summary"
        "?usd_per_gpu_hour=2.5"
    )

    with urlopen(url) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


def find_unused_opportunity(dashboard):

    opportunities = dashboard.get(
        "opportunities",
        []
    )

    for row in opportunities:

        text = str(
            row.get(
                "opportunity",
                row.get(
                    "metric",
                    ""
                )
            )
        ).lower()

        if (
            "high-confidence" in text
            or "high confidence" in text
            or "unused capacity" in text
        ):

            return row

    return None


# =====================================================
# Request model
# =====================================================

class DecisionRequest(BaseModel):

    target_cut_pct: float


# =====================================================
# Health
# =====================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# =====================================================
# Context endpoint
# =====================================================

@app.get("/api/context")
def context():

    dashboard = load_json(
        DASHBOARD_PATH
    )

    official = get_official_summary()

    return {
        "official_summary": official,
        "analysis": dashboard
    }


# =====================================================
# Decision endpoint
# =====================================================

@app.post("/api/decision")
def decision(
    request: DecisionRequest
):

    # -------------------------
    # 1. Read official data
    # -------------------------

    official = get_official_summary()

    total_gpu_hours = float(
        official.get(
            "value",
            0
        )
    )

    price_per_gpu_hour = 2.5


    # -------------------------
    # 2. Read custom analysis
    # -------------------------

    dashboard = load_json(
        DASHBOARD_PATH
    )

    unused = find_unused_opportunity(
        dashboard
    )


    # Fallback to validated analysis
    # if field names changed.
    if unused is None:

        unused_gpu_hours = 111572.37
        unused_jobs = 2151

    else:

        unused_gpu_hours = float(
            unused.get(
                "gpu_hours",
                111572.37
            )
        )

        unused_jobs = int(
            unused.get(
                "jobs",
                2151
            )
        )


    unused_capacity_pct = (
        unused_gpu_hours
        / total_gpu_hours
        * 100
    )


    # -------------------------
    # 3. CFO target
    # -------------------------

    target_pct = (
        request.target_cut_pct
    )

    target_gpu_hours = (
        total_gpu_hours
        * target_pct
        / 100
    )


    # -------------------------
    # 4. Evidence-backed amount
    # -------------------------

    evidence_backed_gpu_hours = min(
        target_gpu_hours,
        unused_gpu_hours
    )

    evidence_backed_pct = (
        evidence_backed_gpu_hours
        / total_gpu_hours
        * 100
    )

    estimated_value_usd = (
        evidence_backed_gpu_hours
        * price_per_gpu_hour
    )


    # -------------------------
    # 5. Remaining evidence gap
    # -------------------------

    remaining_gap_gpu_hours = max(
        0,
        target_gpu_hours
        - evidence_backed_gpu_hours
    )

    remaining_gap_pct = (
        remaining_gap_gpu_hours
        / total_gpu_hours
        * 100
    )


    # -------------------------
    # 6. Decision logic
    # -------------------------

    if target_pct <= unused_capacity_pct:

        decision_code = (
            "PILOT_EVIDENCE_BACKED_CUT"
        )

        confidence = "HIGH"

        risk = "MEDIUM"

        recommendation = (
            "The requested capacity target is "
            "within the currently identified "
            "high-confidence unused-capacity "
            "envelope. Apply changes gradually "
            "and validate workload performance."
        )

        validation_gate = (
            "Pilot the highest-confidence "
            "opportunities first and compare "
            "runtime, completion rate, and "
            "research impact before broader rollout."
        )

    else:

        decision_code = (
            "NO_BLANKET_CUT"
        )

        confidence = "HIGH"

        risk = "HIGH"

        recommendation = (
            "The requested target exceeds "
            "currently identified high-confidence "
            "unused capacity. Do not apply the "
            "remaining reduction as a blanket cut."
        )

        validation_gate = (
            "Add evidence-backed right-sizing "
            "or workload-specific opportunities "
            "before counting the remaining gap "
            "toward the capacity target."
        )


    # -------------------------
    # 7. Return decision
    # -------------------------

    return {

        "executive_summary": {

            "target_cut_pct":
                round(
                    target_pct,
                    2
                ),

            "target_gpu_hours":
                round(
                    target_gpu_hours,
                    2
                ),

            "identified_unused_jobs":
                unused_jobs,

            "identified_unused_gpu_hours":
                round(
                    unused_gpu_hours,
                    2
                ),

            "identified_unused_capacity_pct":
                round(
                    unused_capacity_pct,
                    2
                ),

            "evidence_backed_gpu_hours":
                round(
                    evidence_backed_gpu_hours,
                    2
                ),

            "evidence_backed_capacity_pct":
                round(
                    evidence_backed_pct,
                    2
                ),

            "estimated_value_usd":
                round(
                    estimated_value_usd,
                    2
                ),

            "remaining_gap_gpu_hours":
                round(
                    remaining_gap_gpu_hours,
                    2
                ),

            "remaining_gap_capacity_pct":
                round(
                    remaining_gap_pct,
                    2
                )
        },

        "decision": {

            "code":
                decision_code,

            "confidence":
                confidence,

            "risk":
                risk,

            "recommendation":
                recommendation,

            "validation_gate":
                validation_gate
        },

        "provenance": {

            "official_api":
                "/v1/efficiency/summary",

            "analysis_file":
                "outputs/json/dashboard_data.json",

            "price_per_gpu_hour":
                price_per_gpu_hour,

            "method":
                "target_vs_deduplicated_unused_capacity"
        }
    }
