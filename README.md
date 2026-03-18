# Pharma Clinical Data Platform

A pharma-themed client/server demo application running on the Domino Apps platform.
It shows how to run a **FastAPI backend** and a **Streamlit frontend** as a single Domino App,
communicating over localhost.

## Architecture

```
┌─────────────────┐    HTTP     ┌─────────────────┐
│   Streamlit     │────────────▶│    FastAPI      │
│   Frontend      │             │    Backend      │
│   (port 8888)   │◀────────────│   (port 8000)   │
└─────────────────┘    JSON     └────────┬────────┘
                                         │ reads/writes
                                  ┌──────▼──────┐
                                  │  CSV Data   │
                                  │  (./data or │
                                  │  Domino DS) │
                                  └─────────────┘
         │
  ┌──────▼──────┐
  │    Nginx    │
  │ Reverse     │
  │   Proxy     │
  └──────┬──────┘
         │
  ┌──────▼──────┐
  │ Kubernetes  │
  │    Pod      │
  └─────────────┘
```

## File Structure

```
domino_client_server_app/
├── app.py              # Streamlit frontend (7-page sidebar UI)
├── main.py             # FastAPI backend (18 routes)
├── requirements.txt    # Python dependencies
├── app.sh              # Domino App startup script
├── README.md           # This file
└── data/               # Synthetic pharma dataset (copy to Domino Dataset)
    ├── drugs.csv
    ├── clinical_trials.csv
    ├── patients.csv
    ├── adverse_events.csv
    └── drug_interactions.csv
```

## Dataset

The `data/` directory contains a synthetic pharma dataset. To use it with a Domino Dataset:

1. Copy the CSV files from the `data/` folder into your Domino Dataset using the workspace terminal or the Domino Datasets UI.
2. Set the `DATA_DIR` environment variable so the API knows where to find them. The easiest way is to add it as a **project environment variable** under **Domino project settings**.

Use the path that matches your project type:

| Project type | `DATA_DIR` value |
|---|---|
| Git-based Domino project | `/mnt/data/<project-name>` |
| Domino filesystem-based project | `/domino/datasets/local/<project-name>` |

If `DATA_DIR` is not set, the app falls back to the bundled `./data` folder.

| File | Description |
|---|---|
| `drugs.csv` | 12 drugs — compound name, drug class, MoA, phase, approval status |
| `clinical_trials.csv` | 12 trials across Phase I–IV with enrollment progress |
| `patients.csv` | 38 patients enrolled across those trials |
| `adverse_events.csv` | 30 adverse events with severity, causality, and seriousness flag |
| `drug_interactions.csv` | 15 drug-drug interactions with severity and management guidance |

## API Endpoints (FastAPI — port 8000)

### General
| Method | Path | Description |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check + data file status |

### Dashboard
| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/stats` | KPI aggregation (counts, breakdowns, enrollment rate) |

### Drugs
| Method | Path | Description |
|---|---|---|
| GET | `/api/drugs` | List drugs (filter by `approval_status`, `drug_class`, `phase`) |
| GET | `/api/drugs/{id}` | Drug detail |
| GET | `/api/drugs/{id}/interactions` | All interactions for a drug |
| GET | `/api/drugs/{id}/adverse-events` | All AEs across trials for a drug |

### Clinical Trials
| Method | Path | Description |
|---|---|---|
| GET | `/api/trials` | List trials (filter by `status`, `phase`, `drug_id`) |
| GET | `/api/trials/{id}` | Trial detail including drug info |
| GET | `/api/trials/{id}/patients` | Patients enrolled in a trial |
| GET | `/api/trials/{id}/adverse-events` | AEs reported within a trial |

### Patients
| Method | Path | Description |
|---|---|---|
| GET | `/api/patients` | List patients (filter by `trial_id`, `status`, `gender`) |
| GET | `/api/patients/{id}` | Patient detail including their AEs |
| POST | `/api/patients` | Enroll a new patient |

### Adverse Events
| Method | Path | Description |
|---|---|---|
| GET | `/api/adverse-events` | List AEs (filter by `severity`, `serious`, `trial_id`, `drug_id`) |
| POST | `/api/adverse-events` | Report a new adverse event |

### Drug Interactions
| Method | Path | Description |
|---|---|---|
| GET | `/api/drug-interactions` | List all interactions (filter by `severity`, `drug_id`) |
| GET | `/api/drug-interactions/check` | Check if two specific drugs interact (`?drug_id_1=D001&drug_id_2=D009`) |

Interactive API docs available at `http://localhost:8000/docs` when running locally.

## Frontend Pages (Streamlit — port 8888)

| Page | Description |
|---|---|
| Dashboard | KPI metrics, enrollment progress, trial status and AE severity breakdowns |
| Drug Catalog | Browse and filter drugs, view interactions inline |
| Clinical Trials | Browse trials with nested patient and AE views |
| Patient Registry | Browse patients, lookup by ID, enroll new patients |
| Adverse Events | Browse and filter AEs, report new events |
| Drug Interactions | Browse all interactions, pairwise interaction checker |
| System Info | Configuration, route reference, backend connectivity test |

## Setup on Domino

1. Add all files to your Domino project.
2. Optionally copy the `data/` CSVs into a Domino Dataset and set `DATA_DIR`.
3. Create a Domino App pointing at `app.sh` as the startup command.
4. Access the app through the Domino Apps interface.
