from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

PHASES = [
    "Preconstruction",
    "Design Development",
    "Procurement",
    "Construction",
    "Commissioning",
    "Closeout",
]

ISSUES = [
    "Design ambiguity",
    "Specification conflict",
    "Code compliance issue",
    "Dimensional inconsistency",
    "Material substitution",
    "Coordination error",
    "Constructability issue",
]


TRADE_KEYWORDS = {
    "Electrical": ["electrical", "lighting", "power", "panel", "conduit"],
    "Plumbing": ["plumbing", "domestic water", "sanitary", "waste", "vent", "water heater"],
    "HVAC": ["hvac", "mechanical", "duct", "vav", "rtu", "diffuser"],
    "Fire Protection": ["fire", "sprinkler", "standpipe"],
    "Structural": ["structural", "beam", "column", "rebar", "steel", "concrete"],
    "Architectural": ["architectural", "partition", "door", "finish", "ceiling", "wall type"],
    "Civil": ["civil", "site", "grading", "storm", "utilities"],
}


def classify_phase(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["bid", "rfi during bidding", "pre-bid", "addendum", "proposal"]):
        return "Preconstruction"
    if any(k in t for k in ["design development", "dd set", "schematic", "concept"]):
        return "Design Development"
    if any(k in t for k in ["lead time", "procure", "procurement", "submittal", "long-lead", "purchase order"]):
        return "Procurement"
    if any(k in t for k in ["commission", "startup", "testing", "balancing", "tab"]):
        return "Commissioning"
    if any(k in t for k in ["closeout", "as-built", "o&m", "warranty", "punchlist"]):
        return "Closeout"
    return "Construction"


def classify_issue(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["code", "ibc", "nfpa", "ada", "compliance"]):
        return "Code compliance issue"
    if any(k in t for k in ["dimension", "dimensional", "measure", "elevation", "height", "width", "length"]):
        return "Dimensional inconsistency"
    if "spec" in t and any(k in t for k in ["conflict", "contradict", "mismatch", "inconsistent"]):
        return "Specification conflict"
    if any(k in t for k in ["clarify", "not clear", "ambiguous", "interpretation"]):
        return "Design ambiguity"
    if any(k in t for k in ["substitute", "alternate", "equal", "approved equal"]):
        return "Material substitution"
    if any(k in t for k in ["clash", "conflict", "coordination", "interfere", "overlap"]):
        return "Coordination error"
    if any(k in t for k in ["constructability", "field condition", "means and methods", "access"]):
        return "Constructability issue"
    return "Design ambiguity"


def extract_trade(text: str) -> Optional[str]:
    t = text.lower()
    for trade, keys in TRADE_KEYWORDS.items():
        if any(k in t for k in keys):
            return trade
    return None


DRAWING_REF_RE = re.compile(r"\b([A-Z]{1,3})-?(\d{2,4})\b")
GRID_RE = re.compile(r"\bgrid(?:line)?\s*([A-Z]{1,2}\-?\d{1,2}|\d{1,2}\-?[A-Z]{1,2})\b", re.IGNORECASE)
ROOM_RE = re.compile(r"\b(room|rm)\s*([A-Z]?\d{1,4}[A-Z]?)\b", re.IGNORECASE)
SPEC_RE = re.compile(r"\b(\d{2}\s?\d{2}\s?\d{2})\b")


def analyze_rfi(text: str) -> Tuple[str, str, Dict, Dict]:
    '''
    Heuristic classification + entity extraction.
    Replace this module later with:
    - fine-tuned transformer classifier (phase + issue)
    - spaCy NER (trade, CSI, drawing ref, gridline, room, spec section, cost/schedule impact)
    '''
    t = text or ""
    phase = classify_phase(t)
    issue = classify_issue(t)

    trade = extract_trade(t)
    drawing = None
    m = DRAWING_REF_RE.search(t.upper())
    if m:
        drawing = f"{m.group(1)}-{m.group(2)}"

    grid = None
    mg = GRID_RE.search(t)
    if mg:
        grid = mg.group(1).upper()

    room = None
    mr = ROOM_RE.search(t)
    if mr:
        room = mr.group(2).upper()

    spec = None
    ms = SPEC_RE.search(t)
    if ms:
        spec = ms.group(1).replace(" ", "")

    # CSI division (simple): "Division 03", "Div 26"
    csi = None
    mdiv = re.search(r"\b(div(?:ision)?\.?\s*)(\d{2})\b", t, re.IGNORECASE)
    if mdiv:
        csi = f"Division {mdiv.group(2)}"

    # cost impact like $1,200
    cost = None
    mcost = re.search(r"\$\s*([0-9][0-9,]*\.?\d*)", t)
    if mcost:
        try:
            cost = float(mcost.group(1).replace(",", ""))
        except Exception:
            cost = None

    # schedule impact like "3 days"
    sched_days = None
    msd = re.search(r"\b(\d{1,3})\s*(day|days)\b", t.lower())
    if msd:
        try:
            sched_days = int(msd.group(1))
        except Exception:
            sched_days = None

    entities = {
        "trade_name": trade,
        "drawing_reference": drawing,
        "gridline_reference": grid,
        "room_number": room,
        "spec_section": spec,
        "csi_division": csi,
        "cost_impact": cost,
        "schedule_impact_days": sched_days,
    }

    fields = dict(entities)
    return phase, issue, entities, fields
