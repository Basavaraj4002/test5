"""
Domain 5: Processing Speed & Attention
FastAPI backend for:
  - Sub-test A: Simple Reaction Time
  - Sub-test B: Digit Span (Working Memory + Attention)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import statistics
import random
import math
import uuid
from datetime import datetime

app = FastAPI(
    title="Domain 5: Processing Speed & Attention API",
    description="Cognitive assessment API for Simple Reaction Time and Digit Span tests",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def classify_rt_median(median_ms: float, age_group: str) -> dict:
    """Return severity label and description for a reaction-time median."""
    age_group = age_group.lower()

    if age_group in ("50-64", "50_64"):
        col = 0
    elif age_group in ("65-74", "65_74"):
        col = 1
    elif age_group in ("75+", "75_plus", "75plus"):
        col = 2
    else:
        raise ValueError(f"Unknown age_group: {age_group!r}. Use '50-64', '65-74', or '75+'")

    table = [
        (280,  ["normal",   "normal",   "normal"]),
        (350,  ["normal",   "normal",   "watch"]),
        (450,  ["watch",    "watch",    "concern"]),
        (600,  ["concern",  "concern",  "critical"]),
        (math.inf, ["critical", "critical", "critical"]),
    ]

    for upper, labels in table:
        if median_ms < upper:
            severity = labels[col]
            break

    descriptions = {
        "normal":   "✅ Normal",
        "watch":    "🟡 Watch",
        "concern":  "🔴 Concern",
        "critical": "🚨 Critical",
    }
    return {"severity": severity, "label": descriptions[severity]}


def classify_rt_variability(sd_ms: float) -> dict:
    if sd_ms < 50:
        return {"severity": "normal",  "label": "✅ Consistent, normal"}
    elif sd_ms < 100:
        return {"severity": "watch",   "label": "🟡 Mildly inconsistent"}
    else:
        return {"severity": "concern", "label": "🔴 Attention lapses — significant concern"}


def classify_forward_span(span: int) -> dict:
    table = {
        7: ("normal",   "✅ Above average"),
        6: ("normal",   "✅ Normal"),
        5: ("normal",   "✅ Normal"),
        4: ("watch",    "🟡 Low normal — watch"),
        3: ("concern",  "🔴 Concern"),
    }
    if span >= 7:
        s, l = "normal", "✅ Above average"
    elif span in table:
        s, l = table[span]
    else:
        s, l = "critical", "🚨 Critical"
    return {"severity": s, "label": l}


def classify_backward_span(span: int) -> dict:
    if span >= 5:
        return {"severity": "normal",   "label": "✅ Normal"}
    elif span == 4:
        return {"severity": "normal",   "label": "✅ Low normal"}
    elif span == 3:
        return {"severity": "watch",    "label": "🟡 Watch"}
    elif span == 2:
        return {"severity": "concern",  "label": "🔴 Concern"}
    else:
        return {"severity": "critical", "label": "🚨 Critical"}


def classify_span_gap(gap: int) -> dict:
    if gap <= 2:
        return {"severity": "normal",  "label": "✅ Normal gap (1–2)"}
    else:
        return {"severity": "concern", "label": "🔴 Disproportionate gap — working memory dysfunction"}


# ---------------------------------------------------------------------------
# Sub-test A  –  Simple Reaction Time
# ---------------------------------------------------------------------------

class RTSubmitRequest(BaseModel):
    patient_id: str
    age_group: str = Field(..., description="One of: '50-64', '65-74', '75+'")
    reaction_times_ms: List[float] = Field(
        ..., min_length=5, max_length=5,
        description="Exactly 5 reaction-time readings in milliseconds"
    )

    @field_validator("reaction_times_ms")
    @classmethod
    def validate_rt_values(cls, v):
        for rt in v:
            if rt <= 0 or rt > 10_000:
                raise ValueError("Each RT must be between 1 ms and 10 000 ms")
        return v


class RTResult(BaseModel):
    patient_id: str
    age_group: str
    reaction_times_ms: List[float]
    median_ms: float
    mean_ms: float
    sd_ms: float
    min_ms: float
    max_ms: float
    median_classification: dict
    variability_classification: dict
    timestamp: str


@app.post("/api/v1/reaction-time/submit", response_model=RTResult, tags=["Sub-test A"])
def submit_reaction_time(req: RTSubmitRequest):
    """
    Submit 5 reaction-time readings (ms) and receive a full analysis.

    - **median_ms** – primary metric (robust to outliers)
    - **sd_ms** – variability; elevated SD can flag attention lapses before the median rises
    """
    rts = req.reaction_times_ms
    median_ms = statistics.median(rts)
    mean_ms   = statistics.mean(rts)
    # stdev requires n >= 2; with exactly 5 samples this is always safe
    sd_ms     = statistics.stdev(rts)

    try:
        median_cls = classify_rt_median(median_ms, req.age_group)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    variability_cls = classify_rt_variability(sd_ms)

    return RTResult(
        patient_id=req.patient_id,
        age_group=req.age_group,
        reaction_times_ms=rts,
        median_ms=round(median_ms, 1),
        mean_ms=round(mean_ms, 1),
        sd_ms=round(sd_ms, 1),
        min_ms=round(min(rts), 1),
        max_ms=round(max(rts), 1),
        median_classification=median_cls,
        variability_classification=variability_cls,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


class TrialTimingResponse(BaseModel):
    trial_number: int
    delay_ms: int
    description: str


@app.get("/api/v1/reaction-time/trial-timing", response_model=TrialTimingResponse, tags=["Sub-test A"])
def get_trial_timing(trial_number: int = 1):
    """
    Get a random pre-stimulus delay (2 000 – 6 000 ms) for a given trial.
    Call this before showing the stimulus circle in Flutter so the delay
    is server-authoritative (prevents cheating / logging).
    """
    if not 1 <= trial_number <= 5:
        raise HTTPException(status_code=422, detail="trial_number must be 1–5")
    delay_ms = random.randint(2000, 6000)
    return TrialTimingResponse(
        trial_number=trial_number,
        delay_ms=delay_ms,
        description=f"Wait {delay_ms} ms before displaying the stimulus circle."
    )


# ---------------------------------------------------------------------------
# Sub-test B  –  Digit Span
# ---------------------------------------------------------------------------

class DigitSpanRequest(BaseModel):
    patient_id: str
    forward_span: int = Field(..., ge=0, le=10, description="Highest forward span achieved")
    backward_span: int = Field(..., ge=0, le=10, description="Highest backward span achieved")


class DigitSpanResult(BaseModel):
    patient_id: str
    forward_span: int
    backward_span: int
    gap: int
    forward_classification: dict
    backward_classification: dict
    gap_classification: dict
    summary: str
    timestamp: str


@app.post("/api/v1/digit-span/submit", response_model=DigitSpanResult, tags=["Sub-test B"])
def submit_digit_span(req: DigitSpanRequest):
    """
    Submit forward and backward digit-span scores.
    Returns per-score classifications plus gap analysis.

    **Gap rule**: forward − backward should be 1–2.
    A gap ≥ 3 indicates specific working-memory dysfunction.
    """
    gap = req.forward_span - req.backward_span

    fwd_cls = classify_forward_span(req.forward_span)
    bwd_cls = classify_backward_span(req.backward_span)
    gap_cls = classify_span_gap(gap)

    severities = {fwd_cls["severity"], bwd_cls["severity"], gap_cls["severity"]}
    if "critical" in severities:
        overall = "🚨 Critical — immediate clinical follow-up recommended"
    elif "concern" in severities:
        overall = "🔴 Concern — further evaluation advised"
    elif "watch" in severities:
        overall = "🟡 Watch — monitor at next visit"
    else:
        overall = "✅ Within normal limits"

    return DigitSpanResult(
        patient_id=req.patient_id,
        forward_span=req.forward_span,
        backward_span=req.backward_span,
        gap=gap,
        forward_classification=fwd_cls,
        backward_classification=bwd_cls,
        gap_classification=gap_cls,
        summary=overall,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


class DigitSequenceResponse(BaseModel):
    length: int
    sequence: List[int]
    display_string: str
    description: str


@app.get("/api/v1/digit-span/sequence", response_model=DigitSequenceResponse, tags=["Sub-test B"])
def get_digit_sequence(length: int = 3):
    """
    Generate a random digit sequence of the requested length (2–10).
    Digits are 1–9 (0 avoided — looks like letter O).
    No two adjacent digits are the same.
    """
    if not 2 <= length <= 10:
        raise HTTPException(status_code=422, detail="length must be 2–10")

    seq = []
    for _ in range(length):
        choices = [d for d in range(1, 10) if not seq or d != seq[-1]]
        seq.append(random.choice(choices))

    return DigitSequenceResponse(
        length=length,
        sequence=seq,
        display_string=" – ".join(str(d) for d in seq),
        description=f"Read or display each digit with ~1 s gap between them."
    )


# ---------------------------------------------------------------------------
# Combined / Domain-level endpoints
# ---------------------------------------------------------------------------

class Domain5FullRequest(BaseModel):
    patient_id: str
    age_group: str
    reaction_times_ms: List[float] = Field(..., min_length=5, max_length=5)
    forward_span: int = Field(..., ge=0, le=10)
    backward_span: int = Field(..., ge=0, le=10)


class Domain5FullResult(BaseModel):
    patient_id: str
    age_group: str
    reaction_time: RTResult
    digit_span: DigitSpanResult
    domain_summary: str
    timestamp: str


@app.post("/api/v1/domain5/submit", response_model=Domain5FullResult, tags=["Domain 5 Combined"])
def submit_domain5(req: Domain5FullRequest):
    """
    Submit all Domain 5 data in a single call.
    Returns reaction-time analysis, digit-span analysis, and a combined domain summary.
    """
    rt_result = submit_reaction_time(
        RTSubmitRequest(
            patient_id=req.patient_id,
            age_group=req.age_group,
            reaction_times_ms=req.reaction_times_ms,
        )
    )
    ds_result = submit_digit_span(
        DigitSpanRequest(
            patient_id=req.patient_id,
            forward_span=req.forward_span,
            backward_span=req.backward_span,
        )
    )

    all_severities = [
        rt_result.median_classification["severity"],
        rt_result.variability_classification["severity"],
        ds_result.forward_classification["severity"],
        ds_result.backward_classification["severity"],
        ds_result.gap_classification["severity"],
    ]

    if "critical" in all_severities:
        domain_summary = "🚨 Domain 5 Critical — urgent clinical review needed"
    elif "concern" in all_severities:
        domain_summary = "🔴 Domain 5 Concern — further evaluation advised"
    elif "watch" in all_severities:
        domain_summary = "🟡 Domain 5 Watch — monitor at next visit"
    else:
        domain_summary = "✅ Domain 5 Normal — processing speed & attention within expected range"

    return Domain5FullResult(
        patient_id=req.patient_id,
        age_group=req.age_group,
        reaction_time=rt_result,
        digit_span=ds_result,
        domain_summary=domain_summary,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok", "service": "domain5-api", "version": "1.0.0"}


@app.get("/", tags=["Meta"])
def root():
    return {
        "message": "Domain 5: Processing Speed & Attention API",
        "docs": "/docs",
        "health": "/health",
    }
