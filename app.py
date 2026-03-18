"""
Pharma Clinical Data — Streamlit frontend for the Domino client-server demo.

Communicates with the FastAPI backend running on localhost:8000.
"""

import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"
TIMEOUT = 8

st.set_page_config(
    page_title="Pharma Clinical Data Platform",
    page_icon="",
    layout="wide",
)

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API error: {exc}")
        return None


def _post(path: str, payload: dict):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc))
        st.error(f"API error: {detail}")
        return None
    except Exception as exc:
        st.error(f"API error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Sidebar navigation + health check
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Pharma Clinical Data")
    st.caption("Domino Demo — FastAPI + Streamlit")
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "Dashboard",
            "Drug Catalog",
            "Clinical Trials",
            "Patient Registry",
            "Adverse Events",
            "Drug Interactions",
            "System Info",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    health = _get("/health")
    if health and health.get("status") == "healthy":
        st.success("API healthy")
    elif health:
        st.warning(f"API: {health.get('status')}")
    else:
        st.error("API offline")


# ---------------------------------------------------------------------------
# Helper: colour-code severity / status badges
# ---------------------------------------------------------------------------

SEVERITY_COLOUR = {"Mild": "green", "Moderate": "orange", "Severe": "red"}
STATUS_COLOUR = {
    "Recruiting": "blue", "Active": "green",
    "Completed": "gray", "Discontinued": "red",
}


def badge(text: str, colour_map: dict) -> str:
    colour = colour_map.get(text, "gray")
    return f":{colour}[{text}]"


# ---------------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------------

if page == "Dashboard":
    st.header("Dashboard")
    data = _get("/api/dashboard/stats")
    if data:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Drugs", data["total_drugs"])
        c2.metric("Trials", data["total_trials"])
        c3.metric("Patients", data["total_patients"])
        c4.metric("Adverse Events", data["total_adverse_events"])
        c5.metric("Serious AEs", data["serious_adverse_events"])

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Enrollment Progress")
            enrolled = data["total_enrolled"]
            target = data["total_enrollment_target"]
            st.metric(
                "Overall Enrollment",
                f"{enrolled:,} / {target:,}",
                f"{data['enrollment_rate_pct']}%",
            )
            st.progress(min(data["enrollment_rate_pct"] / 100, 1.0))

            st.subheader("Trial Status")
            for k, v in data["trial_status_breakdown"].items():
                st.write(f"- **{k}**: {v}")

        with col_right:
            st.subheader("Drug Approval Status")
            for k, v in data["approval_status_breakdown"].items():
                st.write(f"- **{k}**: {v}")

            st.subheader("AE Severity Breakdown")
            for sev in ["Mild", "Moderate", "Severe"]:
                count = data["ae_severity_breakdown"].get(sev, 0)
                st.write(f"- **{sev}**: {count}")

# ---------------------------------------------------------------------------
# Page: Drug Catalog
# ---------------------------------------------------------------------------

elif page == "Drug Catalog":
    st.header("Drug Catalog")

    with st.expander("Filters", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        f_approval = fc1.selectbox(
            "Approval Status",
            ["All", "Approved", "Under Review", "In Trial"],
        )
        f_phase = fc2.selectbox(
            "Phase",
            ["All", "Phase I", "Phase II", "Phase III", "Phase IV"],
        )
        f_class = fc3.text_input("Drug Class (partial match)", "")

    params = {}
    if f_approval != "All":
        params["approval_status"] = f_approval
    if f_phase != "All":
        params["phase"] = f_phase

    data = _get("/api/drugs", params=params)
    if data:
        drugs = data["drugs"]
        if f_class:
            drugs = [d for d in drugs if f_class.lower() in d.get("drug_class", "").lower()]

        st.caption(f"{len(drugs)} drug(s) found")
        for d in drugs:
            with st.expander(f"**{d['name']}** ({d['drug_id']}) — {d['drug_class']}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Compound:** {d['compound_name']}")
                c1.write(f"**Indication:** {d['indication']}")
                c1.write(f"**Phase:** {d['phase']}")
                c1.write(f"**Approval Status:** {d['approval_status']}")
                c2.write(f"**Mechanism:** {d['moa']}")
                c2.write(f"**Molecular Weight:** {d['molecular_weight']} Da")
                c2.write(f"**Half-life:** {d['half_life_hours']} h")
                c2.write(f"**Manufacturer:** {d['manufacturer']}")

                if st.button("View Interactions", key=f"ix_{d['drug_id']}"):
                    ix = _get(f"/api/drugs/{d['drug_id']}/interactions")
                    if ix and ix["count"]:
                        st.dataframe(
                            [
                                {
                                    "Other Drug": r["other_drug_name"],
                                    "Type": r["interaction_type"],
                                    "Severity": r["severity"],
                                    "Effect": r["clinical_effect"],
                                    "Management": r["management"],
                                }
                                for r in ix["interactions"]
                            ],
                            use_container_width=True,
                        )
                    else:
                        st.info("No known interactions on record.")

# ---------------------------------------------------------------------------
# Page: Clinical Trials
# ---------------------------------------------------------------------------

elif page == "Clinical Trials":
    st.header("Clinical Trials")

    fc1, fc2 = st.columns(2)
    f_status = fc1.selectbox(
        "Status", ["All", "Recruiting", "Active", "Completed", "Suspended"]
    )
    f_phase = fc2.selectbox(
        "Phase", ["All", "Phase I", "Phase II", "Phase III", "Phase IV"]
    )

    params = {}
    if f_status != "All":
        params["status"] = f_status
    if f_phase != "All":
        params["phase"] = f_phase

    data = _get("/api/trials", params=params)
    if data:
        st.caption(f"{data['count']} trial(s) found")
        for t in data["trials"]:
            enrolled = int(t.get("enrolled_count", 0))
            target = int(t.get("enrollment_target", 1))
            pct = round(100 * enrolled / target) if target else 0

            label = (
                f"**{t['trial_id']}** — {t['trial_name']} | "
                f"{t['drug_name']} | {t['phase']} | {t['status']}"
            )
            with st.expander(label):
                c1, c2 = st.columns(2)
                c1.write(f"**Principal Investigator:** {t['principal_investigator']}")
                c1.write(f"**Country:** {t['country']}")
                c1.write(f"**Sites:** {t['site_count']}")
                c1.write(f"**Start:** {t['start_date']}  |  **End:** {t['end_date']}")
                c2.write(f"**Primary Endpoint:** {t['primary_endpoint']}")
                c2.write(f"**Enrollment:** {enrolled} / {target} ({pct}%)")
                c2.progress(min(pct / 100, 1.0))

                tab_p, tab_ae = st.tabs(["Patients", "Adverse Events"])
                with tab_p:
                    pd = _get(f"/api/trials/{t['trial_id']}/patients")
                    if pd:
                        st.caption(
                            f"{pd['count']} patients  |  "
                            + "  ".join(f"{k}: {v}" for k, v in pd["status_breakdown"].items())
                        )
                        if pd["patients"]:
                            st.dataframe(
                                [
                                    {
                                        "ID": p["patient_id"],
                                        "Age": p["age"],
                                        "Gender": p["gender"],
                                        "Diagnosis": p["diagnosis"],
                                        "Status": p["status"],
                                        "Enrolled": p["enrollment_date"],
                                        "Country": p["country"],
                                    }
                                    for p in pd["patients"]
                                ],
                                use_container_width=True,
                            )

                with tab_ae:
                    aed = _get(f"/api/trials/{t['trial_id']}/adverse-events")
                    if aed:
                        sc = aed.get("severity_breakdown", {})
                        st.caption(
                            f"{aed['count']} AE(s) | Serious: {aed['serious_count']}  |  "
                            + "  ".join(f"{k}: {v}" for k, v in sc.items())
                        )
                        if aed["adverse_events"]:
                            st.dataframe(
                                [
                                    {
                                        "Event": ae["event_type"],
                                        "Severity": ae["severity"],
                                        "Patient": ae["patient_id"],
                                        "Onset": ae["onset_date"],
                                        "Serious": ae["serious"],
                                        "Outcome": ae["outcome"],
                                        "Causality": ae["causality"],
                                    }
                                    for ae in aed["adverse_events"]
                                ],
                                use_container_width=True,
                            )

# ---------------------------------------------------------------------------
# Page: Patient Registry
# ---------------------------------------------------------------------------

elif page == "Patient Registry":
    st.header("Patient Registry")

    tab_browse, tab_enroll = st.tabs(["Browse Patients", "Enroll New Patient"])

    with tab_browse:
        fc1, fc2, fc3 = st.columns(3)
        f_trial = fc1.text_input("Trial ID", "")
        f_status = fc2.selectbox("Status", ["All", "Active", "Completed", "Discontinued"])
        f_gender = fc3.selectbox("Gender", ["All", "Male", "Female"])

        params = {}
        if f_trial:
            params["trial_id"] = f_trial
        if f_status != "All":
            params["status"] = f_status
        if f_gender != "All":
            params["gender"] = f_gender

        data = _get("/api/patients", params=params)
        if data:
            st.caption(f"{data['count']} patient(s)")
            if data["patients"]:
                st.dataframe(
                    [
                        {
                            "Patient ID": p["patient_id"],
                            "Trial": p["trial_id"],
                            "Age": p["age"],
                            "Gender": p["gender"],
                            "Diagnosis": p["diagnosis"],
                            "Status": p["status"],
                            "Enrolled": p["enrollment_date"],
                            "Last Visit": p["last_visit_date"],
                            "Country": p["country"],
                        }
                        for p in data["patients"]
                    ],
                    use_container_width=True,
                )

        st.subheader("Patient Detail Lookup")
        pid = st.text_input("Enter Patient ID (e.g. P0001)")
        if pid:
            pd = _get(f"/api/patients/{pid}")
            if pd:
                c1, c2 = st.columns(2)
                c1.write(f"**Trial:** {pd['trial_id']}")
                c1.write(f"**Age / Gender:** {pd['age']} / {pd['gender']}")
                c1.write(f"**Diagnosis:** {pd['diagnosis']}")
                c1.write(f"**Status:** {pd['status']}")
                c2.write(f"**Enrolled:** {pd['enrollment_date']}")
                c2.write(f"**Last Visit:** {pd['last_visit_date']}")
                c2.write(f"**Baseline Score:** {pd['baseline_score']}")
                c2.write(f"**Current Score:** {pd['current_score']}")

                if pd.get("adverse_events"):
                    st.subheader("Adverse Events for this Patient")
                    st.dataframe(pd["adverse_events"], use_container_width=True)
                else:
                    st.info("No adverse events on record for this patient.")

    with tab_enroll:
        st.subheader("Enroll a New Patient")
        with st.form("enroll_form"):
            c1, c2 = st.columns(2)
            trial_id = c1.text_input("Trial ID *", placeholder="e.g. T001")
            age = c2.number_input("Age *", min_value=18, max_value=100, value=50)
            gender = c1.selectbox("Gender *", ["Male", "Female", "Other"])
            diagnosis = c2.text_input("Primary Diagnosis *")
            site_id = c1.text_input("Site ID *", placeholder="e.g. S001")
            country = c2.text_input("Country *")
            baseline_score = st.text_input(
                "Baseline Score (numeric or descriptive)",
                placeholder="e.g. 72 or CHADS2=3",
            )
            submitted = st.form_submit_button("Enroll Patient", type="primary")

        if submitted:
            if not all([trial_id, diagnosis, site_id, country, baseline_score]):
                st.warning("Please fill in all required fields.")
            else:
                result = _post(
                    "/api/patients",
                    {
                        "trial_id": trial_id,
                        "age": age,
                        "gender": gender,
                        "diagnosis": diagnosis,
                        "site_id": site_id,
                        "country": country,
                        "baseline_score": baseline_score,
                    },
                )
                if result:
                    st.success(
                        f"Patient **{result['patient']['patient_id']}** enrolled successfully!"
                    )

# ---------------------------------------------------------------------------
# Page: Adverse Events
# ---------------------------------------------------------------------------

elif page == "Adverse Events":
    st.header("Adverse Events")

    tab_browse, tab_report = st.tabs(["Browse Events", "Report New Event"])

    with tab_browse:
        fc1, fc2, fc3 = st.columns(3)
        f_sev = fc1.selectbox("Severity", ["All", "Mild", "Moderate", "Severe"])
        f_serious = fc2.selectbox("Serious", ["All", "Yes", "No"])
        f_drug = fc3.text_input("Drug ID", "")

        params = {}
        if f_sev != "All":
            params["severity"] = f_sev
        if f_serious != "All":
            params["serious"] = f_serious
        if f_drug:
            params["drug_id"] = f_drug

        data = _get("/api/adverse-events", params=params)
        if data:
            st.caption(f"{data['count']} adverse event(s)")
            if data["adverse_events"]:
                st.dataframe(
                    [
                        {
                            "Event ID": ae["event_id"],
                            "Type": ae["event_type"],
                            "Severity": ae["severity"],
                            "Serious": ae["serious"],
                            "Patient": ae["patient_id"],
                            "Drug": ae["drug_id"],
                            "Trial": ae["trial_id"],
                            "Onset": ae["onset_date"],
                            "Outcome": ae["outcome"],
                            "Causality": ae["causality"],
                        }
                        for ae in data["adverse_events"]
                    ],
                    use_container_width=True,
                )

    with tab_report:
        st.subheader("Report an Adverse Event")
        with st.form("ae_form"):
            c1, c2 = st.columns(2)
            patient_id = c1.text_input("Patient ID *", placeholder="e.g. P0001")
            drug_id = c2.text_input("Drug ID *", placeholder="e.g. D001")
            trial_id = c1.text_input("Trial ID *", placeholder="e.g. T001")
            event_type = c2.text_input("Event Type *", placeholder="e.g. Nausea")
            severity = c1.selectbox("Severity *", ["Mild", "Moderate", "Severe"])
            serious = c2.selectbox("Serious AE?", ["No", "Yes"])
            onset_date = c1.date_input("Onset Date *")
            causality = c2.selectbox(
                "Causality *", ["Probable", "Definite", "Possible", "Unlikely"]
            )
            reported_by = st.text_input("Reported By *", placeholder="e.g. Dr. Smith")
            submitted = st.form_submit_button("Submit Report", type="primary")

        if submitted:
            if not all([patient_id, drug_id, trial_id, event_type, reported_by]):
                st.warning("Please fill in all required fields.")
            else:
                result = _post(
                    "/api/adverse-events",
                    {
                        "patient_id": patient_id,
                        "drug_id": drug_id,
                        "trial_id": trial_id,
                        "event_type": event_type,
                        "severity": severity,
                        "serious": serious,
                        "onset_date": str(onset_date),
                        "causality": causality,
                        "reported_by": reported_by,
                    },
                )
                if result:
                    st.success(
                        f"Adverse event **{result['event']['event_id']}** reported successfully!"
                    )
                    if serious == "Yes":
                        st.warning(
                            "This is a **Serious Adverse Event**. "
                            "Ensure expedited reporting per regulatory requirements."
                        )

# ---------------------------------------------------------------------------
# Page: Drug Interactions
# ---------------------------------------------------------------------------

elif page == "Drug Interactions":
    st.header("Drug Interactions")

    tab_all, tab_check = st.tabs(["Browse Interactions", "Check Two Drugs"])

    with tab_all:
        fc1, fc2 = st.columns(2)
        f_sev = fc1.selectbox("Severity", ["All", "Mild", "Moderate", "Severe"])
        f_drug = fc2.text_input("Drug ID (filter)", "")

        params = {}
        if f_sev != "All":
            params["severity"] = f_sev
        if f_drug:
            params["drug_id"] = f_drug

        data = _get("/api/drug-interactions", params=params)
        if data:
            st.caption(f"{data['count']} interaction(s)")
            for ix in data["interactions"]:
                sev_color = {"Mild": "green", "Moderate": "orange", "Severe": "red"}.get(
                    ix["severity"], "gray"
                )
                label = (
                    f":{sev_color}[{ix['severity']}] | "
                    f"**{ix['drug_1_name']}** + **{ix['drug_2_name']}** — "
                    f"{ix['interaction_type']}"
                )
                with st.expander(label):
                    st.write(f"**Mechanism:** {ix['mechanism']}")
                    st.write(f"**Clinical Effect:** {ix['clinical_effect']}")
                    st.write(f"**Management:** {ix['management']}")

    with tab_check:
        st.subheader("Check Interaction Between Two Drugs")

        drug_list_data = _get("/api/drugs")
        drug_options = {}
        if drug_list_data:
            drug_options = {
                f"{d['drug_id']} — {d['name']}": d["drug_id"]
                for d in drug_list_data["drugs"]
            }

        if drug_options:
            c1, c2 = st.columns(2)
            sel1 = c1.selectbox("First Drug", list(drug_options.keys()), key="ix_d1")
            sel2 = c2.selectbox("Second Drug", list(drug_options.keys()), key="ix_d2")

            if st.button("Check Interaction", type="primary"):
                d1 = drug_options[sel1]
                d2 = drug_options[sel2]
                if d1 == d2:
                    st.warning("Please select two different drugs.")
                else:
                    result = _get(
                        "/api/drug-interactions/check",
                        params={"drug_id_1": d1, "drug_id_2": d2},
                    )
                    if result:
                        if result["interaction_found"]:
                            sev = result.get("severity", "")
                            if sev == "Severe":
                                st.error(f"Interaction found — **{sev}**")
                            elif sev == "Moderate":
                                st.warning(f"Interaction found — **{sev}**")
                            else:
                                st.info(f"Interaction found — **{sev}**")
                            st.write(f"**Type:** {result['interaction_type']}")
                            st.write(f"**Mechanism:** {result['mechanism']}")
                            st.write(f"**Clinical Effect:** {result['clinical_effect']}")
                            st.write(f"**Management:** {result['management']}")
                        else:
                            st.success("No known interaction between these two drugs.")
        else:
            st.info("Could not load drug list from API.")

# ---------------------------------------------------------------------------
# Page: System Info
# ---------------------------------------------------------------------------

elif page == "System Info":
    st.header("System Information")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Configuration")
        st.write(f"- **Backend URL:** `{BACKEND_URL}`")
        st.write("- **Backend Port:** 8000 (FastAPI / Uvicorn)")
        st.write("- **Frontend Port:** 8888 (Streamlit)")
        st.write("- **Platform:** Domino")

    with col2:
        st.subheader("API Routes")
        routes = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/api/dashboard/stats"),
            ("GET", "/api/drugs"),
            ("GET", "/api/drugs/{id}"),
            ("GET", "/api/drugs/{id}/interactions"),
            ("GET", "/api/drugs/{id}/adverse-events"),
            ("GET", "/api/trials"),
            ("GET", "/api/trials/{id}"),
            ("GET", "/api/trials/{id}/patients"),
            ("GET", "/api/trials/{id}/adverse-events"),
            ("GET", "/api/patients"),
            ("GET", "/api/patients/{id}"),
            ("POST", "/api/patients"),
            ("GET", "/api/adverse-events"),
            ("POST", "/api/adverse-events"),
            ("GET", "/api/drug-interactions"),
            ("GET", "/api/drug-interactions/check"),
        ]
        for method, path in routes:
            colour = "green" if method == "GET" else "blue"
            st.write(f":{colour}[{method}] `{path}`")

    st.divider()
    if st.button("Test Backend Connection"):
        with st.spinner("Connecting..."):
            data = _get("/")
            if data:
                st.success("Backend connection successful!")
                st.json(data)

    if st.button("View OpenAPI Docs URL"):
        st.code(f"{BACKEND_URL}/docs")
        st.caption("Open the above URL in your browser to access the interactive API docs.")
