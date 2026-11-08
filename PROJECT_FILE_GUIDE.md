# PatientFlow — Project File Structure and Documentation Guide

> **Purpose of this document:** Give any new developer a clear, concise understanding of what every important file in the project contains and what responsibility it serves — without needing to open each file individually.

---

## Table of Contents

- [Project Overview](#project-overview)
- [High-Level Directory Map](#high-level-directory-map)
- [Root-Level Files](#root-level-files)
- [`hospital/` — Core Logic Package](#hospital--core-logic-package)
- [`data/` — Datasets and Provenance](#data--datasets-and-provenance)
- [`scripts/` — Utilities and Video Production](#scripts--utilities-and-video-production)
- [`tests/` — Automated Test Suite](#tests--automated-test-suite)
- [`.streamlit/` — Streamlit Configuration](#streamlit--streamlit-configuration)
- [`deliverables/` — Video, Screenshots, and Captions](#deliverables--video-screenshots-and-captions)
- [Overall Architecture](#overall-architecture)
- [Data Flow](#data-flow)
- [Important Files by Category](#important-files-by-category)
- [Excluded from Documentation](#excluded-from-documentation)

---

## Project Overview

**PatientFlow** is a local Python + Streamlit web application that demonstrates two **Operations Research (OR) techniques** to plan outpatient doctor capacity and reduce patient waiting times:

1. **M/M/c Queueing Theory (Erlang C)** — mathematically estimates steady-state waiting times and recommends a doctor count.
2. **Discrete-Event Simulation (DES)** — simulates a first-come-first-served clinic queue on a finite patient cohort and measures actual waiting metrics.

The application supports three data modes: fully synthetic patients, a hybrid mode using real-source Hangu consultation durations with synthetic arrivals, and user-uploaded CSV data.

**Tech stack:** Python 3.12+, Streamlit, NumPy, Pandas, Plotly. No database, cloud service, or external API is required at runtime.

---

## High-Level Directory Map

```
PatientFlow/
├── .streamlit/              # Streamlit theme and server configuration
│   └── config.toml
├── data/                    # Datasets, provenance metadata, and license
│   ├── hangu_service_minutes.csv
│   ├── hangu_provenance.json
│   ├── HANGU_LICENSE.txt
│   └── sample_patients.csv
├── deliverables/            # Video walkthrough, screenshots, captions
│   ├── PatientFlow_walkthrough.mp4
│   ├── video_details.json
│   ├── walkthrough_transcript.txt
│   ├── walkthrough_captions.srt
│   ├── recommendation.png
│   ├── queue.png
│   └── hybrid.png
├── hospital/                # Core logic package (data, queueing, simulation)
│   ├── __init__.py
│   ├── data.py
│   ├── queueing.py
│   └── simulation.py
├── scripts/                 # Utility and video-production scripts
│   ├── import_hangu.py
│   ├── record_walkthrough.py
│   ├── narrate_video.ps1
│   └── video_narration.json
├── tests/                   # Automated test suite
│   ├── test_models.py
│   └── test_app.py
├── app.py                   # Main application entry point (Streamlit dashboard)
├── requirements.txt         # Core runtime dependencies
├── requirements-video.txt   # Optional video-recording dependencies
├── README.md                # Project documentation and usage guide
├── implementation_plan.md   # Detailed design, formulas, and roadmap
├── builder.md               # Step-by-step development guide
├── .gitignore               # Git ignore rules
└── PatientFlow.zip          # Archived copy of the project
```

---

## Root-Level Files

| File | What it contains / does |
|---|---|
| `app.py` | **Main application entry point.** Implements the Streamlit dashboard — sidebar controls (data source, clinic settings, presets), scenario orchestration, KPI metric cards, four tabbed views (Waiting times, Queues & doctors, Patient records, How it works), interactive Plotly charts, CSV export/download buttons, and inline explanations of the OR techniques and Erlang C formulas. Coordinates `hospital.data`, `hospital.queueing`, and `hospital.simulation` to run comparisons. |
| `requirements.txt` | Lists the four core runtime Python dependencies: `streamlit`, `numpy`, `pandas`, and `plotly` with version constraints. Install these to run the dashboard. |
| `requirements-video.txt` | Lists optional dependencies needed only for the automated video walkthrough recording: `playwright`, `imageio-ffmpeg`, and `pillow`. Not required for normal app usage. |
| `README.md` | Comprehensive project documentation including: problem description, feature list, technology stack, installation instructions, usage guide, data provenance and attribution for the Hangu dataset, sample results, screenshot/video references, validation summary, and limitations. |
| `implementation_plan.md` | Detailed beginner-friendly design document explaining the problem, the two OR techniques (M/M/c queueing theory and discrete-event simulation), all mathematical formulas (Erlang C), data contracts, clinic assumptions, step-by-step implementation roadmap, hand-checkable examples, and verified demonstration results. |
| `builder.md` | Step-by-step development guide for building the project. Covers stack choices, folder structure, file responsibilities, implementation order, data contracts, pseudocode for the queueing and simulation algorithms, UI specifications, testing strategy, and instructions for producing the video walkthrough. |
| `.gitignore` | Specifies files and directories excluded from version control: `.venv/`, `__pycache__/`, `*.pyc`, and `.streamlit/secrets.toml`. |
| `PatientFlow.zip` | A ZIP archive of the project for distribution. Contains source code, documentation, data, and deliverables (not dependencies or virtual environments). |

---

## `hospital/` — Core Logic Package

This is the core computational package containing all data handling, mathematical modeling, and simulation logic. It is imported by `app.py`.

| File | What it contains / does |
|---|---|
| `__init__.py` | Empty package initializer. Makes `hospital/` a Python package so that `data.py`, `queueing.py`, and `simulation.py` can be imported as `hospital.data`, `hospital.queueing`, and `hospital.simulation`. |
| `data.py` | **Data generation and validation module.** Contains: (1) `generate_patients()` — creates synthetic patient cohorts with exponential inter-arrival times and either exponential or resampled service durations, using a seeded NumPy RNG for reproducibility. (2) `load_csv()` — parses and validates user-uploaded CSV files with strict size, format, and content checks. (3) `load_hangu_durations()` — loads the bundled Hangu consultation-duration extract with SHA-256 checksum and provenance verification. (4) `validate_patients()` — enforces the data contract (unique IDs, valid arrival/service times, boundary checks). Also provides `require_number()` and `require_integer()` input-validation helpers used across the package. |
| `queueing.py` | **M/M/c queueing theory and staffing recommendation module.** Contains: (1) `erlang_c()` — calculates steady-state queue predictions (utilization, probability of waiting, mean wait, mean queue length) for a given arrival rate, mean service time, and doctor count, using an iterative numerically-stable Erlang C implementation. Returns an `unstable` result when demand exceeds capacity (ρ ≥ 1). (2) `recommend_staffing()` — iterates doctor counts from baseline to maximum and returns the smallest stable count that meets the mean-wait target, or reports infeasibility. Defines `QueuePrediction` and `StaffingRecommendation` frozen dataclasses. |
| `simulation.py` | **Discrete-event simulation module.** Contains the `simulate()` function that runs a first-come-first-served (FCFS) queue simulation using a min-heap (`heapq`) to track doctor availability. For each patient, it computes consultation start/end times, waiting time, and doctor assignment. Calculates time-weighted queue metrics (queue area, mean queue for both the arrival window and full session), per-doctor utilization, and aggregate statistics (mean/median/p95 wait, peak queue, overtime, within-target percentage). Defines the `SimulationResult` frozen dataclass. |

---

## `data/` — Datasets and Provenance

This directory contains the dataset files used by the application. No patient names, diagnoses, or sensitive information is stored.

| File | What it contains / does |
|---|---|
| `sample_patients.csv` | A tiny hand-checkable 3-patient CSV example (`P001`, `P002`, `P003`) with arrival times `0, 2, 4` minutes and service times of `5` minutes each. Used as a downloadable sample in the dashboard's "Upload CSV" mode and for hand-calculated test verification. |
| `hangu_service_minutes.csv` | Contains 6,637 real-source consultation-duration estimates (single column: `service_min`) extracted from the Hangu outpatient dataset. Durations range from 3 to 60 minutes, sorted ascending. No patient identifiers or demographic data is included. Used by the "Hangu hybrid" data mode. |
| `hangu_provenance.json` | Provenance metadata for the Hangu duration extract: academic citation, source repository URL, paper DOI, dataset archive DOI, license (CC BY-NC-SA 4.0), pinned Git revision, source and extract SHA-256 checksums, record count, aggregate statistics (mean/min/max), transformation description, cleaning methodology, and documented limitations. Used for integrity verification at runtime. |
| `HANGU_LICENSE.txt` | Full text of the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** license that governs the Hangu dataset. Bundled for attribution compliance. |

---

## `scripts/` — Utilities and Video Production

These are standalone utility scripts. They are **not imported by the main application** and are not required for normal dashboard usage.

| File | What it contains / does |
|---|---|
| `import_hangu.py` | **One-time data import script.** Downloads the Hangu `Data.csv` and `LICENSE` from a pinned GitHub revision, extracts and validates the `ServTime` column (verifying 180–3600 second bounds), converts seconds to minutes, sorts the values, and writes `hangu_service_minutes.csv`, `hangu_provenance.json`, and `HANGU_LICENSE.txt` to the `data/` directory. Requires internet access only when explicitly run. |
| `record_walkthrough.py` | **Automated video walkthrough recorder.** Uses Playwright to launch a headless Chromium browser, navigates through 13 scripted chapters of the running Streamlit app (loading presets, changing settings, running comparisons, switching tabs, searching patients, exporting CSVs, switching to hybrid mode), overlays chapter-summary captions, records browser video, synchronizes pre-generated speech audio to chapter timings, muxes video and audio with FFmpeg into an MP4, and validates the output (duration 3–5 minutes, 1600×900 resolution, audible narration, complete decode). Generates screenshots, an SRT caption file, a transcript, and a verification JSON. |
| `narrate_video.ps1` | **Windows PowerShell text-to-speech script.** Uses the .NET `System.Speech.Synthesis.SpeechSynthesizer` class with the "Microsoft Zira Desktop" voice to generate WAV audio files for each narration chapter defined in `video_narration.json`. Called by `record_walkthrough.py` during video production. |
| `video_narration.json` | **Video chapter definition file.** A JSON array of 13 chapter objects, each containing: `title` (chapter heading), `caption` (on-screen summary text), `action` (which UI interaction to perform), and `narration` (full speech text for that chapter). Drives both the automated recording actions and the speech synthesis. |

---

## `tests/` — Automated Test Suite

The project contains **41 automated tests** covering mathematical correctness, input validation, simulation invariants, and UI behavior.

| File | What it contains / does |
|---|---|
| `test_models.py` | **Core logic tests (28 tests across 3 test classes).** `QueueingTests` — verifies Erlang C against known M/M/1 and M/M/2 analytical answers, checks the recurrence formula against a direct factorial computation for multiple doctor counts and utilization levels, tests unstable queue detection, zero-arrival edge case, staffing recommendation feasibility, and invalid input rejection. `DataTests` — tests Hangu source conversion (seconds → minutes, sorting), validates the bundled 6,637-row extract (count, mean, bounds, checksum), verifies hybrid mode preserves arrival times while sampling only from the source pool, tests reproducibility with seeded generation, CSV parsing edge cases (string IDs, ties, missing columns, invalid values, row limits, size limits), and DataFrame validation immutability. `SimulationTests` — verifies hand-calculated 1-doctor and 2-doctor FCFS results, tests busy-time clipping at closing, simultaneous departure/arrival handling, seeded simulation invariants (queue non-negativity, queue-area conservation, doctor busy-time conservation, non-overlapping assignments, monotonic wait improvement), and the end-to-end default demonstration scenario. |
| `test_app.py` | **Dashboard UI tests (13 tests).** Uses Streamlit's `AppTest` framework to exercise the real dashboard without a browser. Tests: default dashboard rendering and record switching, invalid doctor-limit error display, infeasible target warning, empty synthetic cohort error, upload mode file prompt, hybrid mode offline rendering with source warning and duration count, missing Hangu source error handling, explicit run requirement with settings-changed detection, pending source change label preservation, preset loading and reproducible reset, patient filter/search isolation from the cohort, and queue/utilization control changes without altering results. |

---

## `.streamlit/` — Streamlit Configuration

| File | What it contains / does |
|---|---|
| `config.toml` | **Streamlit server and theme configuration.** Sets a custom light theme (navy text `#102a43`, teal primary `#0d9488`, light background `#f5f7fb`), disables usage-statistics telemetry (`gatherUsageStats = false`), limits file uploads to 2 MB, binds the server to `127.0.0.1` (localhost only), and uses port `8517` instead of the default `8501` to avoid conflicts. |

---

## `deliverables/` — Video, Screenshots, and Captions

These are pre-generated output assets from the automated video walkthrough recorder. They are not required to run the application.

| File | What it contains / does |
|---|---|
| `PatientFlow_walkthrough.mp4` | A **4-minute 27-second** narrated video walkthrough of the application at 1600×900 resolution. Recorded via automated Playwright browser interaction with chapter-summary caption overlays and Microsoft Zira Desktop computer-generated narration. Demonstrates all major features: configuration, presets, comparisons, charts, patient search, CSV export, hybrid mode, and model explanations. |
| `video_details.json` | Machine-readable verification metadata for the video: duration (267.28s), dimensions (1600×900), video codec (H.264), mean audio volume (−20.8 dB), voice details, capture method, export verification, and the full chapter timeline with start/end timestamps. |
| `walkthrough_transcript.txt` | Plain-text transcript of all 13 narration chapters from the video walkthrough, with chapter titles and full spoken text. |
| `walkthrough_captions.srt` | SubRip (SRT) subtitle file with chapter-summary captions (title + short summary) and their timestamps. These are chapter summaries, not word-for-word subtitles. |
| `recommendation.png` | Screenshot of the dashboard showing the staffing recommendation section (KPI cards, recommendation message, and data summary). |
| `queue.png` | Screenshot of the "Queues & doctors" tab showing the waiting-queue-over-time chart with baseline vs. recommended staffing. |
| `hybrid.png` | Screenshot of the dashboard in Hangu hybrid mode, showing the hybrid data warning, source attribution, and expanded data-sources-and-assumptions panel. |

---

## Overall Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User (Web Browser)                           │
│                     http://127.0.0.1:8517                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     app.py (Streamlit Dashboard)                    │
│  • Sidebar controls (data source, clinic settings, presets)         │
│  • Scenario orchestration and session-state management              │
│  • KPI cards, Plotly charts, tabbed views                           │
│  • CSV export / download buttons                                    │
│  • Inline model explanations and Erlang C formulas                  │
└────────┬──────────────────┬──────────────────┬─────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐
│ hospital/    │  │ hospital/        │  │ hospital/         │
│ data.py      │  │ queueing.py      │  │ simulation.py     │
│              │  │                  │  │                   │
│ • Generate   │  │ • Erlang C       │  │ • FCFS discrete-  │
│   synthetic  │  │   formula        │  │   event simulation│
│   patients   │  │ • Staffing       │  │ • Queue metrics   │
│ • Load CSV   │  │   recommendation │  │ • Doctor util.    │
│ • Load Hangu │  │                  │  │ • Wait statistics │
│ • Validate   │  │                  │  │                   │
└──────┬───────┘  └──────────────────┘  └───────────────────┘
       │
       ▼
┌──────────────┐
│   data/      │
│ • CSV files  │
│ • Hangu      │
│   durations  │
│ • Provenance │
└──────────────┘
```

### How Components Connect

- **No backend server / no database:** The entire application runs as a single-process Streamlit app. All data is held in memory (Pandas DataFrames) and in Streamlit session state. There is no separate backend, API layer, or database.
- **Frontend = Streamlit:** `app.py` serves as both the frontend (UI widgets, charts, layout) and the orchestration layer. Streamlit handles the HTTP server, rendering, and reactivity.
- **Core logic = `hospital/` package:** The computational engine is cleanly separated into three modules — data handling, queueing theory, and simulation — each imported by `app.py`.
- **Data sources:** Patient data comes from one of three sources at runtime: synthetic generation (in-memory), the bundled Hangu CSV extract (`data/`), or user-uploaded CSV. No network access is needed at runtime.
- **Scripts are standalone:** The `scripts/` directory contains optional utilities (data import, video recording) that are never imported by the application or its tests (except `test_models.py` imports `extract_durations` from `import_hangu.py` for unit testing the conversion logic).

### How User Requests Are Handled

1. The user interacts with **sidebar controls** in `app.py` (selecting data source, adjusting clinic parameters).
2. Clicking **"Run comparison"** triggers the orchestration logic in `app.py`:
   - Patient data is generated or loaded via `hospital/data.py`.
   - A staffing recommendation is computed via `hospital/queueing.py`.
   - Two simulations (baseline and recommended) are run via `hospital/simulation.py`.
3. Results are stored in **Streamlit session state** and rendered across four tabs.
4. The user can explore results, filter patients, and download CSVs — all without rerunning the model.

### Data Flow

```
User Settings (sidebar)
        │
        ▼
┌───────────────────┐
│  Data Loading      │   Synthetic → generate_patients()
│  (hospital/data)   │   Hybrid   → load_hangu_durations() + generate_patients()
│                    │   Upload   → load_csv()
└────────┬───────────┘
         │  Validated DataFrame (patient_id, arrival_min, service_min)
         ▼
┌───────────────────┐
│  Staffing Search   │   Estimates λ and μ from the cohort
│  (hospital/queueing)│  Iterates Erlang C from baseline → max doctors
│                    │   Returns smallest feasible doctor count
└────────┬───────────┘
         │  StaffingRecommendation (doctor count, predictions)
         ▼
┌───────────────────┐
│  Simulation × 2   │   simulate(patients, baseline_doctors)
│  (hospital/        │   simulate(patients, recommended_doctors)
│   simulation)      │   Same cohort, different capacity
└────────┬───────────┘
         │  Two SimulationResult objects (patient-level data, queue events, metrics)
         ▼
┌───────────────────┐
│  Dashboard Display │   KPI cards, bar/box charts, queue evolution lines
│  (app.py)          │   Doctor utilization bars, patient record tables
│                    │   CSV download buttons with provenance labels
└───────────────────┘
```

---

## Important Files by Category

### 🚀 Main Application Entry Point

| File | Role |
|---|---|
| `app.py` | The single entry point. Run with `streamlit run app.py`. Starts the web dashboard. |

### 🧮 AI/ML and Operations Research Model Files

| File | Role |
|---|---|
| `hospital/queueing.py` | Implements the M/M/c queueing theory model (Erlang C formula) and the staffing-recommendation search algorithm. |
| `hospital/simulation.py` | Implements the discrete-event simulation engine for FCFS patient queue processing. |

### 📊 Data Handling Files

| File | Role |
|---|---|
| `hospital/data.py` | All data generation (synthetic + hybrid), CSV parsing, input validation, and Hangu data loading with integrity checks. |
| `data/hangu_service_minutes.csv` | Bundled real-source consultation-duration dataset (6,637 records). |
| `data/hangu_provenance.json` | Integrity metadata (checksums, citation, transformation details) for the Hangu extract. |
| `data/sample_patients.csv` | Tiny 3-row example CSV for download and hand verification. |
| `data/HANGU_LICENSE.txt` | CC BY-NC-SA 4.0 license text for the Hangu dataset. |

### 🖥️ Frontend / UI Files

| File | Role |
|---|---|
| `app.py` | Streamlit dashboard — all UI widgets, layout, charts, and interactivity are defined here. |
| `.streamlit/config.toml` | Theme colors, font, server port, upload limit, and telemetry settings. |

### 🔧 Configuration and Dependency Files

| File | Role |
|---|---|
| `requirements.txt` | Core Python dependencies (streamlit, numpy, pandas, plotly). |
| `requirements-video.txt` | Optional dependencies for video recording (playwright, imageio-ffmpeg, pillow). |
| `.streamlit/config.toml` | Streamlit server and theme configuration. |
| `.gitignore` | Git exclusion rules for virtual environments, caches, and secrets. |

### 🧪 Test Files

| File | Role |
|---|---|
| `tests/test_models.py` | Unit tests for queueing theory, data validation, simulation correctness, and Hangu data integrity. |
| `tests/test_app.py` | Integration tests for the Streamlit dashboard UI using AppTest. |

### 🛠️ Utility / Script Files

| File | Role |
|---|---|
| `scripts/import_hangu.py` | One-time network script to download and process the Hangu dataset from GitHub. |
| `scripts/record_walkthrough.py` | Automated browser-based video recorder for producing the project walkthrough. |
| `scripts/narrate_video.ps1` | Windows PowerShell text-to-speech generator for video narration audio. |
| `scripts/video_narration.json` | Chapter definitions (titles, captions, actions, narration text) for the video. |

### 📝 Documentation Files

| File | Role |
|---|---|
| `README.md` | Primary project documentation, installation, usage, data provenance, and results. |
| `implementation_plan.md` | Detailed design document with formulas, assumptions, and implementation roadmap. |
| `builder.md` | Developer-oriented step-by-step construction guide. |

### 🎬 Deliverable / Output Files

| File | Role |
|---|---|
| `deliverables/PatientFlow_walkthrough.mp4` | Narrated video walkthrough of the application. |
| `deliverables/video_details.json` | Video verification metadata (duration, codec, volume, chapter timeline). |
| `deliverables/walkthrough_transcript.txt` | Full narration transcript. |
| `deliverables/walkthrough_captions.srt` | SRT subtitle file with chapter-summary captions. |
| `deliverables/recommendation.png` | Screenshot: staffing recommendation view. |
| `deliverables/queue.png` | Screenshot: queue evolution chart. |
| `deliverables/hybrid.png` | Screenshot: hybrid data mode with attribution. |

---

## Excluded from Documentation

The following are intentionally excluded as they are generated/vendor files, not part of the source:

- `.venv/` — Python virtual environment (created by the user during setup)
- `__pycache__/` — Python bytecode cache (auto-generated)
- `*.pyc` — Compiled Python files (auto-generated)
- `.streamlit/secrets.toml` — Secrets file (excluded via `.gitignore`; not present in the repo)
- `node_modules/` — Not applicable (this is a Python project)

---

*This guide was generated by reviewing the actual implementation of every file in the project. Last updated: November 2026.*

