# Frontend JSON Data Guide

This folder contains the frontend-ready JSON files generated from the Track 2 GPU analysis.

The purpose of this document is to help the frontend team understand:

- what each JSON file contains;
- what each metric means;
- which values can be used as dashboard headlines;
- which values should **not** be interpreted as guaranteed savings;
- which dataset should be used for each dashboard section.

---

## Folder Structure

```text
outputs/json/
├── baseline.json
├── opportunities.json
├── rightsizing_summary.json
├── risk_hardware.json
└── dashboard_data.json
```

For most frontend development, use:

```text
dashboard_data.json
```

It combines the four individual JSON files into one object.

---

# 1. `baseline.json`

## Purpose

`baseline.json` shows where observed GPU capacity and cost went, grouped by final job state.

Use this dataset for:

```text
Where did GPU capacity / cost go?
```

## Main Fields

| Field | Meaning |
|---|---|
| `state_name` | Final scheduler state |
| `jobs` | Number of jobs in that state |
| `gpu_hours` | Total GPU-hours associated with that state |
| `share_pct` | Share of total observed allocated GPU-hours |
| `usd` | GPU-hours × $2.50 per GPU-hour |

## Main Values

| State | Jobs | GPU-hours | Share | USD |
|---|---:|---:|---:|---:|
| COMPLETED | 45,334 | 229,040.57 | 38.56% | $572,601 |
| CANCELLED | 9,290 | 203,929.58 | 34.33% | $509,824 |
| TIMEOUT | 1,544 | 107,951.52 | 18.17% | $269,879 |
| FAILED | 18,587 | 50,033.16 | 8.42% | $125,083 |
| NODE_FAIL | 10 | 2,027.89 | 0.34% | $5,070 |

Total observed allocation:

```text
~594,004 GPU-hours
~$1.485M
```

## Recommended Frontend Use

Use `baseline.json` for:

- total GPU-hours;
- total observed GPU cost;
- GPU-hours by final state;
- cost by final state;
- state distribution charts.

## Important Interpretation

Do **not** interpret final job states directly as waste.

```text
CANCELLED ≠ waste
FAILED ≠ hardware failure
```

A cancelled workload may reflect normal or responsible operating behavior.

A failed workload may be caused by workload configuration, user code, or other non-hardware issues.

---

# 2. `opportunities.json`

## Purpose

`opportunities.json` summarizes the major optimization and investigation opportunities identified in the analysis.

Use this dataset for:

```text
Where should we cut first?
```

Important:

```text
The opportunity categories overlap.
Do NOT sum all rows together.
```

---

## High-Confidence Unused Capacity

This is the strongest optimization headline in the analysis.

### Metrics

```text
2,151 unique jobs
~111,572 GPU-hours
18.78% of observed GPU capacity
~$278,931 identified capacity opportunity
```

This bucket was deduplicated across:

```text
gpu-not-needed
idle-interactive-session
slow-cancel-of-idle-job
```

### Meaning

These workloads represent comparatively actionable unused GPU capacity.

### Suggested Actions

```text
Move CPU-suitable workloads off GPUs
Add idle-session timeouts
Cancel idle jobs earlier
```

### Recommended Dashboard Label

```text
High-confidence unused capacity
```

### Important Interpretation

Do not display `$278.9k` as guaranteed realized savings.

Recommended wording:

```text
Identified unused-capacity opportunity
```

or:

```text
Observed capacity exposure
```

---

## Zero-Compute Unsuccessful Jobs

### Metrics

```text
1,459 jobs
~81,887 GPU-hours
~$204,718 observed GPU allocation
```

### Meaning

These jobs did not perform meaningful GPU compute and did not complete successfully.

They can include final states such as:

```text
CANCELLED
TIMEOUT
FAILED
NODE_FAIL
```

### Recommended Interpretation

Treat this as:

```text
Investigation opportunity
```

not as direct recoverable savings.

The full GPU-hour amount represents observed allocation associated with these jobs.

---

## Large Low-Utilization Jobs

### Metrics

```text
95 jobs
~61,063 GPU-hours
~$152,657 observed GPU allocation
```

### Meaning

These are large workloads with very low average GPU compute utilization.

The rule identifies workloads approximately matching:

```text
Average SM utilization < 10%
GPU-hours > 250
```

### Recommended Frontend Use

Use this group to identify expensive workloads that deserve further investigation or right-sizing review.

Do not interpret the full `$152.7k` as recoverable savings.

---

# 3. `rightsizing_summary.json`

## Purpose

`rightsizing_summary.json` identifies completed workloads that may be suitable for targeted GPU right-sizing.

Use it for:

```text
Targeted right-sizing
```

## Headline Metrics

```text
20 completed jobs
~8,960 GPU-hours of workload exposure
~$22,400 of full observed spend
8 dual-signal jobs
```

## Candidate Types

The candidates are grouped using signals such as:

```text
Low-util only
Memory-oversized only
Both signals
```

### Low-util only

Completed workloads with low GPU compute utilization.

### Memory-oversized only

Completed workloads using only a small fraction of available GPU memory.

### Both signals

Jobs showing both:

```text
low GPU utilization
+
oversized GPU-memory allocation
```

These are the strongest right-sizing candidates.

## Recommended Dashboard Emphasis

```text
8 dual-signal jobs
```

Suggested label:

```text
Highest-priority right-sizing candidates
```

## Suggested Actions

```text
Reduce GPU allocation
Use shared / fractional GPUs
Adjust workload placement
Right-size based on observed compute and memory demand
```

## Important Interpretation

The approximately `$22.4k` value represents:

```text
Full observed workload spend
```

It does **not** represent guaranteed savings.

Recommended frontend wording:

```text
Workload exposure
```

rather than:

```text
Savings
```

---

# 4. `risk_hardware.json`

## Purpose

`risk_hardware.json` contains hardware-related failure and loss metrics.

Use it for:

```text
What happens if we cut the wrong thing?
```

or:

```text
Operational / hardware risk
```

## Main Metrics

```text
18,587 final FAILED jobs
31 jobs hit scheduler-recorded node failure
~7,772 GPU-hours of scheduler-recorded failed-attempt loss
~$19,430 associated observed cost
```

A separate silent hardware issue was also detected:

```text
1 faulty node
140 failed jobs out of 144 jobs
~76.62 GPU-hours of attributed loss
~$191.55
```

## Key Interpretation

The most important message is:

```text
Raw failed-job count is not a valid hardware-waste estimate.
```

A job can:

```text
fail on one node
→ get requeued
→ later complete successfully
```

Therefore, the final job state does not always show the full hardware history.

## Recommended Frontend Comparison

A useful comparison is:

```text
18,587 final FAILED jobs
vs.
31 jobs with scheduler-recorded node failure
```

This demonstrates why raw failure counts should not be used directly as hardware-waste estimates.

Suggested message:

```text
Failure ≠ hardware failure
```

---

# 5. `dashboard_data.json`

## Purpose

`dashboard_data.json` combines all four datasets into one frontend-ready file.

Structure:

```json
{
  "baseline": [],
  "opportunities": [],
  "rightsizing_summary": [],
  "risk_hardware": []
}
```

This is the recommended file for the frontend to fetch.

## Frontend Example

```javascript
const response = await fetch(
  "https://raw.githubusercontent.com/Obitlyy/hackathon-2026-track-2/main/outputs/json/dashboard_data.json"
);

const data = await response.json();

const baseline = data.baseline;
const opportunities = data.opportunities;
const rightsizing = data.rightsizing_summary;
const hardwareRisk = data.risk_hardware;
```

The frontend can then access:

```javascript
data.baseline
data.opportunities
data.rightsizing_summary
data.risk_hardware
```

---

# Recommended Dashboard Mapping

## Section 1 — Where the Money Went

Use:

```javascript
data.baseline
```

Recommended displays:

```text
Total GPU-hours
Total observed GPU cost
GPU-hours by final state
Cost by final state
```

Suggested headline:

```text
~594,004 GPU-hours
~$1.485M observed allocation
```

---

## Section 2 — Where to Cut First

Use:

```javascript
data.opportunities
data.rightsizing_summary
```

Primary headline:

```text
2,151 jobs
~111,572 GPU-hours
18.78% of observed capacity
~$278.9k identified unused-capacity opportunity
```

Secondary right-sizing callout:

```text
20 completed right-sizing candidates
8 dual-signal jobs
```

The `$278.9k` high-confidence unused-capacity metric should be the main optimization headline because it is explicitly deduplicated.

---

## Section 3 — What If the Cut Is Wrong?

Use:

```javascript
data.risk_hardware
```

Suggested headline:

```text
18,587 final FAILED jobs
but only 31 jobs hit scheduler-recorded node failure
```

Suggested message:

```text
Use hardware-attributed evidence rather than raw failure counts before removing capacity.
```

---

# Frontend Guardrails

## 1. Do Not Sum All Opportunity Categories

Many findings overlap.

Do not calculate:

```text
unused capacity
+ zero-compute unsuccessful
+ low utilization
+ right-sizing
= total savings
```

This would double-count workloads.

For the main optimization headline, use:

```text
High-confidence unused capacity
```

which has already been deduplicated.

---

## 2. Do Not Treat All Cancelled Jobs as Waste

```text
CANCELLED ≠ waste
```

Cancellation may be expected or responsible behavior.

---

## 3. Do Not Treat All Failed Jobs as Hardware Failures

```text
FAILED ≠ hardware failure
```

Use scheduler-recorded node-failure and hardware-attributed evidence instead.

---

## 4. Do Not Present Workload Exposure as Guaranteed Savings

Values associated with:

```text
rightsizing
zero-compute unsuccessful jobs
low-utilization jobs
```

represent workload exposure or investigation opportunities.

They are not automatically recoverable savings.

---

## 5. Use the Sample-Window Framing

These results describe the observed dataset window.

Do not automatically annualize the values or present them as full-cluster yearly totals.

Recommended wording:

```text
Within the observed sample window
```

---

## 6. Cost Assumption

The default cost assumption used in the analysis is:

```text
$2.50 per GPU-hour
```

---

# Quick Reference

## Observed Allocation

```text
~594,004 GPU-hours
~$1.485M
```

## High-Confidence Unused Capacity

```text
2,151 jobs
~111,572 GPU-hours
18.78%
~$278.9k identified opportunity
```

## Completed Right-Sizing

```text
20 jobs
~8,960 GPU-hours of workload exposure
8 dual-signal jobs
~$22.4k full observed spend
```

## Zero-Compute Unsuccessful Jobs

```text
1,459 jobs
~81,887 GPU-hours
~$204.7k observed allocation
```

## Large Low-Utilization Jobs

```text
95 jobs
~61,063 GPU-hours
~$152.7k observed allocation
```

## Hardware Risk

```text
18,587 final FAILED jobs
31 jobs hit scheduler-recorded node failure
~7,772 GPU-hours scheduler-recorded failed-attempt loss
~$19.4k associated observed cost
```

---

# Most Important Interpretation Rules

```text
Opportunity ≠ guaranteed savings
Failure ≠ hardware failure
Cancelled ≠ waste
Do not sum overlapping findings
```

For the main dashboard optimization headline, use the deduplicated high-confidence unused-capacity metric instead of adding all opportunity categories together.
