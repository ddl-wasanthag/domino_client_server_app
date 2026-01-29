#!/usr/bin/env python3
"""
Script to create and populate the clinical trials database.
"""
import psycopg2
from datetime import date, timedelta
import random

# Database connection parameters - from environment variables
import os

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "clinicaltrials")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if not all([DB_HOST, DB_USER, DB_PASSWORD]):
    raise ValueError("Missing required environment variables: DB_HOST, DB_USER, DB_PASSWORD")

def create_tables(conn):
    """Create the clinical trial tables."""
    cursor = conn.cursor()

    # Drop tables if they exist (for clean setup)
    cursor.execute("DROP TABLE IF EXISTS adverse_events CASCADE")
    cursor.execute("DROP TABLE IF EXISTS patients CASCADE")
    cursor.execute("DROP TABLE IF EXISTS clinical_trials CASCADE")

    # Create clinical_trials table
    cursor.execute("""
        CREATE TABLE clinical_trials (
            trial_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            phase VARCHAR(10) NOT NULL,
            therapeutic_area VARCHAR(100) NOT NULL,
            start_date DATE NOT NULL,
            status VARCHAR(50) NOT NULL,
            sponsor VARCHAR(100) NOT NULL
        )
    """)

    # Create patients table
    cursor.execute("""
        CREATE TABLE patients (
            patient_id VARCHAR(20) PRIMARY KEY,
            trial_id VARCHAR(20) REFERENCES clinical_trials(trial_id),
            age INTEGER NOT NULL,
            gender VARCHAR(10) NOT NULL,
            treatment_arm VARCHAR(50) NOT NULL,
            enrollment_date DATE NOT NULL,
            site_id VARCHAR(20) NOT NULL
        )
    """)

    # Create adverse_events table
    cursor.execute("""
        CREATE TABLE adverse_events (
            event_id SERIAL PRIMARY KEY,
            patient_id VARCHAR(20) REFERENCES patients(patient_id),
            event_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            event_date DATE NOT NULL,
            resolved BOOLEAN NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    print("Tables created successfully!")

def populate_data(conn):
    """Populate tables with sample clinical trial data."""
    cursor = conn.cursor()

    # Clinical trials data (Vision and Immunology focus)
    trials = [
        ("IMM-2024-001", "Uveitis Treatment Study", "Phase 3", "Immunology/Ophthalmology", "2024-01-15", "Active", "AZ Pharma"),
        ("VIS-2023-042", "Diabetic Retinopathy Prevention", "Phase 2", "Ophthalmology", "2023-06-01", "Active", "AZ Pharma"),
        ("IMM-2024-015", "Rheumatoid Arthritis Biologic", "Phase 3", "Immunology", "2024-03-10", "Active", "AZ Pharma"),
        ("VIS-2024-008", "Age-Related Macular Degeneration", "Phase 2", "Ophthalmology", "2024-02-20", "Recruiting", "AZ Pharma"),
        ("IMM-2023-089", "Psoriasis IL-17 Inhibitor", "Phase 3", "Immunology/Dermatology", "2023-09-15", "Completed", "AZ Pharma"),
    ]

    cursor.executemany(
        "INSERT INTO clinical_trials VALUES (%s, %s, %s, %s, %s, %s, %s)",
        trials
    )
    print(f"Inserted {len(trials)} clinical trials")

    # Generate patients for each trial
    treatment_arms = {
        "IMM-2024-001": ["Adalimumab", "Placebo", "Low Dose", "High Dose"],
        "VIS-2023-042": ["Treatment A", "Treatment B", "Placebo"],
        "IMM-2024-015": ["Biologic 100mg", "Biologic 200mg", "Placebo"],
        "VIS-2024-008": ["Anti-VEGF", "Placebo"],
        "IMM-2023-089": ["IL-17 Inhibitor", "Placebo", "Active Comparator"],
    }

    sites = ["SITE-US-001", "SITE-US-002", "SITE-EU-001", "SITE-EU-002", "SITE-ASIA-001"]

    patients = []
    patient_counter = 1

    for trial_id, arms in treatment_arms.items():
        num_patients = random.randint(80, 150)
        trial_start = date(2024, 1, 1) if "2024" in trial_id else date(2023, 6, 1)

        for _ in range(num_patients):
            patient_id = f"PAT-{patient_counter:05d}"
            age = random.randint(25, 75)
            gender = random.choice(["Male", "Female"])
            treatment_arm = random.choice(arms)
            enrollment_date = trial_start + timedelta(days=random.randint(0, 180))
            site_id = random.choice(sites)

            patients.append((patient_id, trial_id, age, gender, treatment_arm, enrollment_date, site_id))
            patient_counter += 1

    cursor.executemany(
        "INSERT INTO patients VALUES (%s, %s, %s, %s, %s, %s, %s)",
        patients
    )
    print(f"Inserted {len(patients)} patients")

    # Generate adverse events
    adverse_event_types = {
        "Immunology": [
            "Injection site reaction", "Upper respiratory infection", "Headache",
            "Nausea", "Fatigue", "Arthralgia", "Rash", "Elevated liver enzymes"
        ],
        "Ophthalmology": [
            "Eye irritation", "Blurred vision", "Eye pain", "Floaters",
            "Photophobia", "Conjunctivitis", "Dry eye", "Increased intraocular pressure"
        ],
    }

    severities = ["Mild", "Moderate", "Severe"]
    severity_weights = [0.6, 0.3, 0.1]

    adverse_events = []

    for patient_id, trial_id, age, gender, treatment_arm, enrollment_date, site_id in patients:
        # ~30% of patients have adverse events
        if random.random() < 0.3:
            num_events = random.randint(1, 3)

            # Determine therapeutic area for event types
            if "VIS" in trial_id:
                event_types = adverse_event_types["Ophthalmology"]
            else:
                event_types = adverse_event_types["Immunology"]

            for _ in range(num_events):
                event_type = random.choice(event_types)
                severity = random.choices(severities, weights=severity_weights)[0]
                event_date = enrollment_date + timedelta(days=random.randint(7, 120))
                resolved = random.random() < 0.8
                description = f"{severity} {event_type.lower()} reported by patient"

                adverse_events.append((patient_id, event_type, severity, event_date, resolved, description))

    cursor.executemany(
        "INSERT INTO adverse_events (patient_id, event_type, severity, event_date, resolved, description) VALUES (%s, %s, %s, %s, %s, %s)",
        adverse_events
    )
    print(f"Inserted {len(adverse_events)} adverse events")

    conn.commit()

def verify_data(conn):
    """Verify the data was inserted correctly."""
    cursor = conn.cursor()

    print("\n--- Data Summary ---")

    cursor.execute("SELECT COUNT(*) FROM clinical_trials")
    print(f"Clinical Trials: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM patients")
    print(f"Patients: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM adverse_events")
    print(f"Adverse Events: {cursor.fetchone()[0]}")

    print("\n--- Trials by Therapeutic Area ---")
    cursor.execute("""
        SELECT therapeutic_area, COUNT(*) as trial_count,
               (SELECT COUNT(*) FROM patients p WHERE p.trial_id = ct.trial_id) as patient_count
        FROM clinical_trials ct
        GROUP BY therapeutic_area, ct.trial_id
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} trials, {row[2]} patients")

    print("\n--- Adverse Events by Severity ---")
    cursor.execute("SELECT severity, COUNT(*) FROM adverse_events GROUP BY severity ORDER BY severity")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

def main():
    print(f"Connecting to database at {DB_HOST}...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        create_tables(conn)
        populate_data(conn)
        verify_data(conn)
        print("\nDatabase setup complete!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
