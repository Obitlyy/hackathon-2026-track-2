# GPU Capacity Decision Backend

This repository includes a lightweight FastAPI decision backend for the MantisGridAI Hackathon 2026 Track 2.

The backend combines:

1. metrics from the official MantisGrid Track 2 API;
2. our custom GPU capacity analysis;
3. deduplicated opportunity metrics;
4. a user-specified GPU capacity reduction target;

and returns a decision with:

- evidence-backed capacity opportunity;
- remaining target gap;
- estimated observed value;
- risk;
- confidence;
- recommendation;
- validation gate;
- provenance.

---

## Architecture

```text
Official MantisGrid API (:8000)
            +
Custom Analysis Results
(outputs/json/dashboard_data.json)
            ↓
GPU Capacity Decision Backend (:5002)
            ↓
Target Evaluation
            ↓
Decision + Risk + Confidence
            ↓
Frontend / Swagger / API Client
```

The official MantisGrid API remains the source for the cluster-level capacity baseline.

Our custom analysis provides additional job-level and deduplicated opportunity metrics.

The decision backend combines both layers instead of replacing the official API.

---

## Backend File

The backend implementation is:

```text
decision_backend.py
```

Supporting analysis files are located under:

```text
outputs/json/
```

including:

```text
baseline.json
dashboard_data.json
opportunities.json
rightsizing_summary.json
risk_hardware.json
```

---

## Prerequisites

Python 3.10+ is recommended.

Install the backend dependencies:

```bash
pip install fastapi uvicorn
```

The official MantisGrid Track 2 API must also be running locally on:

```text
http://localhost:8000
```

---

## 1. Start the Official MantisGrid API

From the official MantisGridAI Hackathon Track 2 repository:

```bash
cd hackathon-2026-official/track-2
make up
```

Verify that the official API is available at:

```text
http://localhost:8000
```

Official Swagger documentation:

```text
http://localhost:8000/docs
```

The decision backend currently uses the official endpoint:

```text
GET /v1/efficiency/summary
```

with:

```text
usd_per_gpu_hour=2.5
```

---

## 2. Start the Decision Backend

From this repository:

```bash
uvicorn decision_backend:app --host 0.0.0.0 --port 5002
```

For local development with automatic reload:

```bash
uvicorn decision_backend:app --reload --port 5002
```

The backend will run at:

```text
http://localhost:5002
```

---

## 3. Open Swagger

Open:

```text
http://localhost:5002/docs
```

The backend exposes the following endpoints:

```text
GET  /health
GET  /api/context
POST /api/decision
```

---

## 4. Test the Health Endpoint

In Swagger, open:

```text
GET /health
```

Click:

```text
Try it out
```

then:

```text
Execute
```

Expected response:

```json
{
  "status": "ok"
}
```

You can also test from Terminal:

```bash
curl http://localhost:5002/health
```

---

## 5. Test the Decision Endpoint

The main endpoint is:

```text
POST /api/decision
```

Example request:

```json
{
  "target_cut_pct": 20
}
```

The value can be changed to test different CFO capacity-reduction targets.

For example:

```json
{
  "target_cut_pct": 10
}
```

or:

```json
{
  "target_cut_pct": 25
}
```

---

## Example Terminal Request

```bash
curl -X POST "http://localhost:5002/api/decision" \
  -H "Content-Type: application/json" \
  -d '{"target_cut_pct":20}'
```

---

## Example Decision Logic

For a 20% target, the backend:

```text
1. Reads total observed GPU-hours from the official MantisGrid API

2. Reads our deduplicated unused-capacity analysis

3. Converts the requested percentage into target GPU-hours

4. Compares the target with currently identified
   evidence-backed opportunity

5. Calculates the remaining evidence gap

6. Returns a recommendation, confidence level,
   risk level, and validation gate
```

Using the current analysis, approximately:

```text
Observed GPU-hours:
594,004

20% target:
~118,801 GPU-hours

Identified high-confidence unused capacity:
~111,572 GPU-hours
~18.78%

Remaining gap:
~7,228 GPU-hours
~1.22%
```

Because the requested 20% target is larger than the currently identified high-confidence opportunity, the backend does not automatically force the remaining capacity reduction.

Instead, it returns:

```text
NO_BLANKET_CUT
```

and recommends validating additional opportunities before counting them toward the target.

---

## Example Response Structure

```json
{
  "executive_summary": {
    "target_cut_pct": 20.0,
    "target_gpu_hours": 118800.76,
    "identified_unused_jobs": 2151,
    "identified_unused_gpu_hours": 111572.37,
    "identified_unused_capacity_pct": 18.78,
    "evidence_backed_gpu_hours": 111572.37,
    "evidence_backed_capacity_pct": 18.78,
    "estimated_value_usd": 278930.93,
    "remaining_gap_gpu_hours": 7228.39,
    "remaining_gap_capacity_pct": 1.22
  },
  "decision": {
    "code": "NO_BLANKET_CUT",
    "confidence": "HIGH",
    "risk": "HIGH",
    "recommendation": "The requested target exceeds currently identified high-confidence unused capacity.",
    "validation_gate": "Add evidence-backed right-sizing or workload-specific opportunities before counting the remaining gap toward the capacity target."
  },
  "provenance": {
    "official_api": "/v1/efficiency/summary",
    "analysis_file": "outputs/json/dashboard_data.json",
    "price_per_gpu_hour": 2.5,
    "method": "target_vs_deduplicated_unused_capacity"
  }
}
```

Exact numerical formatting may vary slightly depending on the current official API response.

---

## Data and Decision Layers

The project separates four components:

```text
1. Data Layer
   Official Track 2 data and MantisGrid API

2. Analytics Layer
   Job-level analysis, overlap handling,
   opportunity identification, and deduplication

3. Decision Backend
   FastAPI service that combines official metrics
   with custom analysis and evaluates a requested target

4. Frontend
   User-facing interface that can consume the API response
```

The analysis layer was developed separately from the frontend so that the decision logic can be tested directly through the API.

---

## Why a Separate Decision Backend?

The official MantisGrid API provides authoritative infrastructure metrics.

Our decision backend adds a business decision layer on top of those metrics.

For example, the official API can tell us how much GPU capacity was allocated.

Our analysis identifies where capacity may be recoverable.

The decision backend then answers a different question:

> Given a requested capacity reduction target, how much is currently supported by evidence, how large is the remaining gap, and what should be validated before taking additional action?

This keeps observed facts separate from decision logic.

---

## Provenance and Guardrails

The backend includes provenance in its response so that recommendations remain traceable.

Important interpretation rules:

- observed GPU-hours are based on the provided Track 2 sample;
- opportunity values should not automatically be interpreted as guaranteed cash savings;
- overlapping findings must not be naively summed;
- zero utilization alone is not sufficient evidence that a workload was unnecessary;
- a requested CFO target is not treated as evidence that the same percentage can safely be removed;
- additional capacity reductions should be supported by workload-level validation.

---

## Quick Test Checklist

To verify the backend end-to-end:

```text
[1] Start official MantisGrid API on port 8000

[2] Start decision_backend.py on port 5002

[3] Open http://localhost:5002/docs

[4] Test GET /health

[5] Test POST /api/decision

[6] Enter:
    {"target_cut_pct": 20}

[7] Confirm HTTP 200 response

[8] Confirm response contains:
    executive_summary
    decision
    confidence
    risk
    recommendation
    validation_gate
    provenance
```

---

## Main Backend Endpoint

```text
POST http://localhost:5002/api/decision
```

Example input:

```json
{
  "target_cut_pct": 20
}
```

This endpoint is the primary entry point for evaluating GPU capacity reduction scenarios.
