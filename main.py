"""
Pharma Clinical Data API — FastAPI backend for the Domino client-server demo.

Data is loaded from CSV files under DATA_DIR (default: ./data).
Set the DATA_DIR environment variable to point at a Domino Dataset path.
"""

import csv
import os
import uvicorn
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))

app = FastAPI(
    title="Pharma Clinical Data API",
    description=(
        "REST API exposing clinical trial, drug, patient, and adverse event data "
        "for the AstraZeneca Domino demonstration."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _load_csv(filename: str) -> list[dict]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _save_csv(filename: str, rows: list[dict], fieldnames: list[str]) -> None:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AdverseEventCreate(BaseModel):
    patient_id: str
    drug_id: str
    trial_id: str
    event_type: str
    severity: str          # Mild | Moderate | Severe
    onset_date: str        # YYYY-MM-DD
    causality: str         # Definite | Probable | Possible | Unlikely
    reported_by: str
    serious: str = "No"    # Yes | No


class PatientEnroll(BaseModel):
    trial_id: str
    age: int
    gender: str
    diagnosis: str
    site_id: str
    country: str
    baseline_score: str


# ---------------------------------------------------------------------------
# Root / Health
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    return {
        "service": "Pharma Clinical Data API",
        "version": "2.0.0",
        "data_dir": DATA_DIR,
    }


@app.get("/health", tags=["General"])
def health():
    files = ["drugs.csv", "clinical_trials.csv", "patients.csv",
             "adverse_events.csv", "drug_interactions.csv"]
    status = {f: os.path.exists(os.path.join(DATA_DIR, f)) for f in files}
    healthy = all(status.values())
    return {"status": "healthy" if healthy else "degraded", "data_files": status}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/stats", tags=["Dashboard"])
def dashboard_stats():
    """High-level KPIs shown on the dashboard page."""
    drugs = _load_csv("drugs.csv")
    trials = _load_csv("clinical_trials.csv")
    patients = _load_csv("patients.csv")
    aes = _load_csv("adverse_events.csv")

    approval_counts: dict = {}
    for d in drugs:
        k = d.get("approval_status", "Unknown")
        approval_counts[k] = approval_counts.get(k, 0) + 1

    phase_counts: dict = {}
    for t in trials:
        k = t.get("phase", "Unknown")
        phase_counts[k] = phase_counts.get(k, 0) + 1

    trial_status_counts: dict = {}
    for t in trials:
        k = t.get("status", "Unknown")
        trial_status_counts[k] = trial_status_counts.get(k, 0) + 1

    severity_counts: dict = {}
    for ae in aes:
        k = ae.get("severity", "Unknown")
        severity_counts[k] = severity_counts.get(k, 0) + 1

    serious_aes = sum(1 for ae in aes if ae.get("serious", "No") == "Yes")
    total_enrollment_target = sum(
        int(t.get("enrollment_target", 0)) for t in trials
    )
    total_enrolled = sum(int(t.get("enrolled_count", 0)) for t in trials)

    return {
        "total_drugs": len(drugs),
        "total_trials": len(trials),
        "total_patients": len(patients),
        "total_adverse_events": len(aes),
        "serious_adverse_events": serious_aes,
        "approval_status_breakdown": approval_counts,
        "phase_breakdown": phase_counts,
        "trial_status_breakdown": trial_status_counts,
        "ae_severity_breakdown": severity_counts,
        "total_enrollment_target": total_enrollment_target,
        "total_enrolled": total_enrolled,
        "enrollment_rate_pct": round(
            100 * total_enrolled / total_enrollment_target, 1
        ) if total_enrollment_target else 0,
    }


# ---------------------------------------------------------------------------
# Drugs
# ---------------------------------------------------------------------------

@app.get("/api/drugs", tags=["Drugs"])
def list_drugs(
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    drug_class: Optional[str] = Query(None, description="Filter by drug class"),
    phase: Optional[str] = Query(None, description="Filter by development phase"),
):
    drugs = _load_csv("drugs.csv")
    if approval_status:
        drugs = [d for d in drugs if d.get("approval_status") == approval_status]
    if drug_class:
        drugs = [d for d in drugs if d.get("drug_class") == drug_class]
    if phase:
        drugs = [d for d in drugs if d.get("phase") == phase]
    return {"count": len(drugs), "drugs": drugs}


@app.get("/api/drugs/{drug_id}", tags=["Drugs"])
def get_drug(drug_id: str):
    drugs = _load_csv("drugs.csv")
    for d in drugs:
        if d["drug_id"] == drug_id:
            return d
    raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")


@app.get("/api/drugs/{drug_id}/interactions", tags=["Drugs"])
def get_drug_interactions(drug_id: str):
    """All known interactions involving a specific drug."""
    drug_ids = {d["drug_id"] for d in _load_csv("drugs.csv")}
    if drug_id not in drug_ids:
        raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")

    drugs = {d["drug_id"]: d["name"] for d in _load_csv("drugs.csv")}
    interactions = _load_csv("drug_interactions.csv")

    results = []
    for i in interactions:
        if i["drug_id_1"] == drug_id or i["drug_id_2"] == drug_id:
            other_id = i["drug_id_2"] if i["drug_id_1"] == drug_id else i["drug_id_1"]
            results.append({
                **i,
                "drug_1_name": drugs.get(i["drug_id_1"], i["drug_id_1"]),
                "drug_2_name": drugs.get(i["drug_id_2"], i["drug_id_2"]),
                "other_drug_id": other_id,
                "other_drug_name": drugs.get(other_id, other_id),
            })
    return {"drug_id": drug_id, "count": len(results), "interactions": results}


@app.get("/api/drugs/{drug_id}/adverse-events", tags=["Drugs"])
def get_drug_adverse_events(drug_id: str):
    """All adverse events reported for a specific drug across all trials."""
    drug_ids = {d["drug_id"] for d in _load_csv("drugs.csv")}
    if drug_id not in drug_ids:
        raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")

    aes = [ae for ae in _load_csv("adverse_events.csv") if ae["drug_id"] == drug_id]
    return {"drug_id": drug_id, "count": len(aes), "adverse_events": aes}


# ---------------------------------------------------------------------------
# Clinical Trials
# ---------------------------------------------------------------------------

@app.get("/api/trials", tags=["Clinical Trials"])
def list_trials(
    status: Optional[str] = Query(None, description="Filter by status"),
    phase: Optional[str] = Query(None, description="Filter by phase"),
    drug_id: Optional[str] = Query(None, description="Filter by drug ID"),
):
    trials = _load_csv("clinical_trials.csv")
    drugs = {d["drug_id"]: d["name"] for d in _load_csv("drugs.csv")}

    if status:
        trials = [t for t in trials if t.get("status") == status]
    if phase:
        trials = [t for t in trials if t.get("phase") == phase]
    if drug_id:
        trials = [t for t in trials if t.get("drug_id") == drug_id]

    enriched = [
        {**t, "drug_name": drugs.get(t["drug_id"], t["drug_id"])}
        for t in trials
    ]
    return {"count": len(enriched), "trials": enriched}


@app.get("/api/trials/{trial_id}", tags=["Clinical Trials"])
def get_trial(trial_id: str):
    trials = _load_csv("clinical_trials.csv")
    drugs = {d["drug_id"]: d for d in _load_csv("drugs.csv")}
    for t in trials:
        if t["trial_id"] == trial_id:
            drug = drugs.get(t["drug_id"], {})
            return {**t, "drug_name": drug.get("name", t["drug_id"]), "drug_details": drug}
    raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")


@app.get("/api/trials/{trial_id}/patients", tags=["Clinical Trials"])
def get_trial_patients(trial_id: str):
    trial_ids = {t["trial_id"] for t in _load_csv("clinical_trials.csv")}
    if trial_id not in trial_ids:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")

    patients = [p for p in _load_csv("patients.csv") if p["trial_id"] == trial_id]
    status_counts: dict = {}
    for p in patients:
        k = p.get("status", "Unknown")
        status_counts[k] = status_counts.get(k, 0) + 1

    return {
        "trial_id": trial_id,
        "count": len(patients),
        "status_breakdown": status_counts,
        "patients": patients,
    }


@app.get("/api/trials/{trial_id}/adverse-events", tags=["Clinical Trials"])
def get_trial_adverse_events(trial_id: str):
    trial_ids = {t["trial_id"] for t in _load_csv("clinical_trials.csv")}
    if trial_id not in trial_ids:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")

    aes = [ae for ae in _load_csv("adverse_events.csv") if ae["trial_id"] == trial_id]
    severity_counts: dict = {}
    for ae in aes:
        k = ae.get("severity", "Unknown")
        severity_counts[k] = severity_counts.get(k, 0) + 1

    return {
        "trial_id": trial_id,
        "count": len(aes),
        "severity_breakdown": severity_counts,
        "serious_count": sum(1 for ae in aes if ae.get("serious") == "Yes"),
        "adverse_events": aes,
    }


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

@app.get("/api/patients", tags=["Patients"])
def list_patients(
    trial_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
):
    patients = _load_csv("patients.csv")
    if trial_id:
        patients = [p for p in patients if p.get("trial_id") == trial_id]
    if status:
        patients = [p for p in patients if p.get("status") == status]
    if gender:
        patients = [p for p in patients if p.get("gender") == gender]
    return {"count": len(patients), "patients": patients}


@app.get("/api/patients/{patient_id}", tags=["Patients"])
def get_patient(patient_id: str):
    patients = _load_csv("patients.csv")
    for p in patients:
        if p["patient_id"] == patient_id:
            aes = [ae for ae in _load_csv("adverse_events.csv")
                   if ae["patient_id"] == patient_id]
            return {**p, "adverse_events": aes}
    raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")


@app.post("/api/patients", tags=["Patients"], status_code=201)
def enroll_patient(payload: PatientEnroll):
    """Enroll a new patient into a clinical trial."""
    trial_ids = {t["trial_id"] for t in _load_csv("clinical_trials.csv")}
    if payload.trial_id not in trial_ids:
        raise HTTPException(status_code=404, detail=f"Trial {payload.trial_id} not found")

    patients = _load_csv("patients.csv")
    new_id = f"P{len(patients) + 1:04d}"
    today = datetime.today().strftime("%Y-%m-%d")
    new_patient = {
        "patient_id": new_id,
        "trial_id": payload.trial_id,
        "age": payload.age,
        "gender": payload.gender,
        "diagnosis": payload.diagnosis,
        "enrollment_date": today,
        "status": "Active",
        "last_visit_date": today,
        "site_id": payload.site_id,
        "baseline_score": payload.baseline_score,
        "current_score": payload.baseline_score,
        "country": payload.country,
    }
    patients.append(new_patient)
    fieldnames = list(patients[0].keys())
    _save_csv("patients.csv", patients, fieldnames)
    return {"message": "Patient enrolled successfully", "patient": new_patient}


# ---------------------------------------------------------------------------
# Adverse Events
# ---------------------------------------------------------------------------

@app.get("/api/adverse-events", tags=["Adverse Events"])
def list_adverse_events(
    severity: Optional[str] = Query(None),
    serious: Optional[str] = Query(None, description="Yes or No"),
    trial_id: Optional[str] = Query(None),
    drug_id: Optional[str] = Query(None),
):
    aes = _load_csv("adverse_events.csv")
    if severity:
        aes = [ae for ae in aes if ae.get("severity") == severity]
    if serious:
        aes = [ae for ae in aes if ae.get("serious") == serious]
    if trial_id:
        aes = [ae for ae in aes if ae.get("trial_id") == trial_id]
    if drug_id:
        aes = [ae for ae in aes if ae.get("drug_id") == drug_id]
    return {"count": len(aes), "adverse_events": aes}


@app.post("/api/adverse-events", tags=["Adverse Events"], status_code=201)
def report_adverse_event(payload: AdverseEventCreate):
    """Report a new adverse event."""
    aes = _load_csv("adverse_events.csv")
    new_id = f"AE{len(aes) + 1:03d}"
    new_ae = {
        "event_id": new_id,
        "patient_id": payload.patient_id,
        "drug_id": payload.drug_id,
        "trial_id": payload.trial_id,
        "event_type": payload.event_type,
        "severity": payload.severity,
        "onset_date": payload.onset_date,
        "resolution_date": "",
        "outcome": "Ongoing",
        "causality": payload.causality,
        "reported_by": payload.reported_by,
        "serious": payload.serious,
    }
    aes.append(new_ae)
    fieldnames = list(aes[0].keys())
    _save_csv("adverse_events.csv", aes, fieldnames)
    return {"message": "Adverse event reported successfully", "event": new_ae}


# ---------------------------------------------------------------------------
# Drug Interactions
# ---------------------------------------------------------------------------

@app.get("/api/drug-interactions", tags=["Drug Interactions"])
def list_drug_interactions(
    severity: Optional[str] = Query(None),
    drug_id: Optional[str] = Query(None, description="Filter interactions involving this drug"),
):
    interactions = _load_csv("drug_interactions.csv")
    drugs = {d["drug_id"]: d["name"] for d in _load_csv("drugs.csv")}

    if severity:
        interactions = [i for i in interactions if i.get("severity") == severity]
    if drug_id:
        interactions = [i for i in interactions
                        if i.get("drug_id_1") == drug_id or i.get("drug_id_2") == drug_id]

    enriched = [
        {
            **i,
            "drug_1_name": drugs.get(i["drug_id_1"], i["drug_id_1"]),
            "drug_2_name": drugs.get(i["drug_id_2"], i["drug_id_2"]),
        }
        for i in interactions
    ]
    return {"count": len(enriched), "interactions": enriched}


@app.get("/api/drug-interactions/check", tags=["Drug Interactions"])
def check_interaction(
    drug_id_1: str = Query(..., description="First drug ID"),
    drug_id_2: str = Query(..., description="Second drug ID"),
):
    """Check whether two specific drugs interact."""
    interactions = _load_csv("drug_interactions.csv")
    drugs = {d["drug_id"]: d["name"] for d in _load_csv("drugs.csv")}

    for i in interactions:
        if {i["drug_id_1"], i["drug_id_2"]} == {drug_id_1, drug_id_2}:
            return {
                "interaction_found": True,
                **i,
                "drug_1_name": drugs.get(i["drug_id_1"], i["drug_id_1"]),
                "drug_2_name": drugs.get(i["drug_id_2"], i["drug_id_2"]),
            }
    return {
        "interaction_found": False,
        "drug_id_1": drug_id_1,
        "drug_1_name": drugs.get(drug_id_1, drug_id_1),
        "drug_id_2": drug_id_2,
        "drug_2_name": drugs.get(drug_id_2, drug_id_2),
        "message": "No known interaction between these two drugs.",
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
