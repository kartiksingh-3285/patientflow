# Purpose and Actual Use of Every Project File

> **How to use this guide:** Pick any file in the project. Read its entry below and you will be able to confidently explain to your teacher: *"What is this file, why did we create it, what does it do, and where is it used in our application."*

---

## Table of Contents

- [File Classification Legend](#file-classification-legend)
- [Root-Level Files](#root-level-files)
  - [app.py](#apppy)
  - [requirements.txt](#requirementstxt)
  - [requirements-video.txt](#requirements-videotxt)
  - [README.md](#readmemd)
  - [implementation_plan.md](#implementation_planmd)
  - [builder.md](#buildermd)
  - [.gitignore](#gitignore)
  - [PatientFlow.zip](#patientflowzip)
  - [PROJECT_FILE_GUIDE.md](#project_file_guidemd)
- [hospital/ — Core Logic Package](#hospital--core-logic-package)
  - [hospital/\_\_init\_\_.py](#hospital__init__py)
  - [hospital/data.py](#hospitaldatapy)
  - [hospital/queueing.py](#hospitalqueueingpy)
  - [hospital/simulation.py](#hospitalsimulationpy)
- [data/ — Datasets and Provenance](#data--datasets-and-provenance)
  - [data/sample_patients.csv](#datasample_patientscsv)
  - [data/hangu_service_minutes.csv](#datahangu_service_minutescsv)
  - [data/hangu_provenance.json](#datahangu_provenancejson)
  - [data/HANGU_LICENSE.txt](#datahangu_licensetxt)
- [scripts/ — Utilities and Video Production](#scripts--utilities-and-video-production)
  - [scripts/import_hangu.py](#scriptsimport_hangupy)
  - [scripts/record_walkthrough.py](#scriptsrecord_walkthroughpy)
  - [scripts/narrate_video.ps1](#scriptsnarrate_videops1)
  - [scripts/video_narration.json](#scriptsvideo_narrationjson)
- [tests/ — Automated Test Suite](#tests--automated-test-suite)
  - [tests/test_models.py](#teststest_modelspy)
  - [tests/test_app.py](#teststest_apppy)
- [.streamlit/ — Streamlit Configuration](#streamlit--streamlit-configuration)
  - [.streamlit/config.toml](#streamlitconfigtoml)
- [deliverables/ — Generated Outputs](#deliverables--generated-outputs)
  - [deliverables/PatientFlow_walkthrough.mp4](#deliverablespatientflow_walkthroughmp4)
  - [deliverables/video_details.json](#deliverablesvideo_detailsjson)
  - [deliverables/walkthrough_transcript.txt](#deliverableswalkthrough_transcripttxt)
  - [deliverables/walkthrough_captions.srt](#deliverableswalkthrough_captionssrt)
  - [deliverables/recommendation.png](#deliverablesrecommendationpng)
  - [deliverables/queue.png](#deliverablsqueuepng)
  - [deliverables/hybrid.png](#deliverableshybridpng)
- [Summary Classification Table](#summary-classification-table)

---

## File Classification Legend

Each file is tagged with one of these categories:

| Tag | Meaning |
|---|---|
| 🟢 **Essential** | Application cannot run without this file. |
| 🔵 **Testing** | Used during development and testing; not needed at runtime. |
| 🟡 **Configuration** | Configures how the application looks or behaves; app runs with defaults without it. |
| 🟠 **Dataset** | Contains input data consumed by the application. |
| 🟣 **Utility** | A helper script run manually for a specific one-time or optional task. |
| ⚪ **Documentation** | Explains the project to humans; the application ignores it entirely. |
| 🔘 **Generated Output** | A file produced by a script or tool; not hand-written source code. |

---

## Root-Level Files

---

### `app.py`

**Classification:** 🟢 **Essential — Main Application Entry Point**

#### Why does this file exist?

Every application needs a starting point — the file you actually run. In a Streamlit project, that file is the one you pass to `streamlit run`. This file exists because the project needs a single place that wires together the UI controls, the OR models, and the result displays.

Without a separate dashboard file, there would be no way for a user to interact with the queueing theory and simulation logic. The mathematical modules (`queueing.py`, `simulation.py`) are computation-only — they have no user interface. `app.py` is the bridge between the user and the mathematics.

#### What does it contain?

- **Sidebar controls** (lines 42–76): radio buttons for data source (Synthetic demo / Hangu hybrid / Upload CSV), number inputs for arrival window, current doctors, max doctors, mean-wait target, arrival rate, mean service time, random seed, and two preset buttons ("Load demo" and "Busy clinic").
- **Scenario orchestration** (lines 90–116): when "Run comparison" is clicked, it generates/loads patients, computes the staffing recommendation, and runs two simulations (baseline and recommended) — then caches everything in `st.session_state`.
- **KPI metric cards** (lines 184–197): four Streamlit metric widgets showing patient count, current average wait, recommended average wait, and percentage reduction.
- **Four tabs**:
  - *Waiting times* (lines 235–263): grouped bar chart comparing mean/median/p95 wait, box plot of patient wait distributions, detailed comparison table.
  - *Queues & doctors* (lines 265–310): queue-over-time step chart, doctor utilization bar chart with arrival-window/full-session toggle, staffing prediction table showing why a specific doctor count was chosen.
  - *Patient records* (lines 312–360): patient search by ID, staffing-plan switcher, wait-target filter, three CSV download buttons (visible patients, paired comparison, input cohort) with provenance labels.
  - *How it works* (lines 362–412): plain-language explanation of the two OR techniques, rendered LaTeX formulas for Erlang C, and a detailed assumptions/scope section.
- **Custom CSS** (lines 14–27): light background, navy headings, and styled metric cards.
- **Helper functions**: `show_chart()` for consistent Plotly styling, `comparison_table()` for building the metrics DataFrame, `load_preset()` for populating session state, `export_csv()` for adding provenance columns to downloads.

#### What is its use?

It is the file you execute to start the application:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
It accepts user input, calls the three `hospital/` modules, and displays all results.

#### Where is it used?

- **Directly by the user** via `streamlit run app.py`.
- **Imported by `tests/test_app.py`** — the UI tests load this file through Streamlit's `AppTest.from_file()` to simulate user interactions.
- **Recorded by `scripts/record_walkthrough.py`** — the video recorder navigates the running app served by this file.

#### How does it contribute?

It is the entire user-facing surface of the project. Without it, the `hospital/` modules would be usable only from Python scripts — there would be no dashboard, no charts, no interactivity.

#### Is it essential?

**Yes, absolutely.** Removing this file makes the application impossible to run. The `hospital/` package would still work as a library, but there would be no way to use it without writing your own script.

---

### `requirements.txt`

**Classification:** 🟡 **Configuration — Dependency Specification**

#### Why does this file exist?

Python projects need a way to tell other developers exactly which libraries are required. Without this file, a new developer would have to guess which packages to install, what versions are compatible, and might install wrong or conflicting versions.

#### What does it contain?

Four lines specifying the core runtime libraries with version ranges:
```
streamlit>=1.51,<2
numpy>=1.26,<3
pandas>=2.2,<3
plotly>=5.24,<7
```

#### What is its use?

A developer runs `pip install -r requirements.txt` once to install everything needed. The version constraints prevent breaking changes from future library updates.

#### Where is it used?

- By developers during initial setup.
- Referenced in `README.md` and `builder.md` installation instructions.
- Not read by any application code at runtime.

#### How does it contribute?

It makes the project reproducibly installable. Any developer on any machine gets a working environment with one command.

#### Is it essential?

**Not for execution** — if the packages are already installed, the app runs fine without this file. But **essential for setup** — without it, a new developer cannot know what to install.

---

### `requirements-video.txt`

**Classification:** 🟡 **Configuration — Optional Dependency Specification**

#### Why does this file exist?

The video walkthrough recorder (`scripts/record_walkthrough.py`) needs three additional libraries that the main application does not. Separating them into their own file means most users never need to install these heavier packages (Playwright alone downloads a Chromium browser).

#### What does it contain?

```
playwright>=1.48,<2
imageio-ffmpeg>=0.6,<1
pillow>=11,<13
```

#### What is its use?

Only installed when someone wants to re-record the project walkthrough video. Keeps the main `requirements.txt` lean.

#### Where is it used?

- Referenced in `README.md` video-regeneration instructions.
- Only the `scripts/record_walkthrough.py` script needs these packages.

#### Is it essential?

**No.** The dashboard runs perfectly without these. Only needed if you want to produce a new video.

---

### `README.md`

**Classification:** ⚪ **Documentation**

#### Why does this file exist?

Every project needs a README. It is the first file a teacher, evaluator, or new developer reads. It answers "What is this project, how do I run it, and what does it do?"

#### What does it contain?

- Problem description and feature list.
- Technology stack and folder structure overview.
- Step-by-step installation and run instructions for Windows PowerShell.
- Complete usage guide with all three data modes.
- CSV format specification.
- Detailed Hangu data provenance, attribution (Feng et al., 2023), license (CC BY-NC-SA 4.0), and honest assumptions.
- Measured sample results with actual numbers (e.g., 80.80 → 2.31 min mean wait).
- Links to screenshots and the narrated walkthrough video.
- Validation summary (41 automated tests).
- Limitations and future improvements.

#### Where is it used?

- Read by humans (teachers, evaluators, developers).
- Displayed by GitHub/GitLab as the project landing page.
- Not imported or read by any application code.

#### Is it essential?

**No, for execution.** The app runs without it. **Yes, for the project as a whole** — a project without a README is incomplete.

---

### `implementation_plan.md`

**Classification:** ⚪ **Documentation**

#### Why does this file exist?

This project applies two Operations Research techniques. The implementation plan exists to explain those techniques in beginner-friendly language *before* looking at code. It answers "What problem are we solving, what math are we using, and how does everything fit together?" — making the project presentable in a viva or classroom setting.

#### What does it contain?

- The problem statement (clinic queues and doctor capacity).
- Explanation of M/M/c queueing theory with the full Erlang C formula in both mathematical and pseudocode form.
- Explanation of discrete-event simulation with a hand-checkable 3-patient example.
- Data contract (what columns a patient DataFrame must have).
- All clinic assumptions listed explicitly (one queue, equal-speed doctors, no breaks, etc.).
- A 10-step implementation roadmap.
- Verified demonstration results.
- Presentation/viva talking points.

#### Where is it used?

- Read by humans for understanding the design.
- Cross-referenced from `builder.md` and `README.md`.

#### Is it essential?

**No, for execution.** Purely a design document. But it is the intellectual backbone of the project — understanding the plan makes the code understandable.

---

### `builder.md`

**Classification:** ⚪ **Documentation**

#### Why does this file exist?

While `implementation_plan.md` explains *what* and *why*, `builder.md` explains *how* — the step-by-step order of building the project. It exists so a developer can reconstruct the project from scratch or understand the design decisions behind the code structure.

#### What does it contain?

- Stack and folder-structure decisions.
- Each file's exact responsibility in a table.
- Implementation order (design docs → data validation → queueing → simulation → tests → dashboard → video).
- Data contract details with validation pseudocode.
- Queueing theory pseudocode (iterative Erlang C, staffing search).
- DES pseudocode (min-heap approach, queue-area calculation).
- UI specification (sidebar controls, tabs, session-state management, pending-settings behavior).
- Testing strategy with known-answer references.
- Video production workflow.

#### Where is it used?

- Read by developers during development or study.
- Not imported by any code.

#### Is it essential?

**No, for execution.** A developer guide only.

---

### `.gitignore`

**Classification:** 🟡 **Configuration — Version Control**

#### Why does this file exist?

Git would otherwise track generated files (Python bytecode, virtual environments) and potentially sensitive files (secrets). This file tells Git to ignore them.

#### What does it contain?

```
.venv/
__pycache__/
*.pyc
.streamlit/secrets.toml
```

#### Where is it used?

Automatically read by Git during `git add` / `git status` operations.

#### Is it essential?

**No, for execution.** Only matters for Git version control. But essential for keeping the repository clean.

---

### `PatientFlow.zip`

**Classification:** 🔘 **Generated Output — Distribution Archive**

#### Why does this file exist?

A pre-packaged ZIP makes it easy to submit or share the complete project (source, data, documentation, video) without requiring Git or dependency installation beforehand.

#### What does it contain?

An archived copy of the project directory (source code, data files, documentation, deliverables — but not `.venv/` or `__pycache__/`).

#### Is it essential?

**No.** It is a convenience for distribution. The project runs from the extracted source files.

---

### `PROJECT_FILE_GUIDE.md`

**Classification:** ⚪ **Documentation**

#### Why does this file exist?

Created as a structural reference so a new developer can see every file's purpose at a glance — organized by folder with concise tables and an architecture diagram.

#### Is it essential?

**No, for execution.** Documentation only.

---

## `hospital/` — Core Logic Package

This folder contains the computational engine of the project. It is a **Python package** — a folder with an `__init__.py` that lets you write `from hospital.data import generate_patients`. The logic is separated from the UI (`app.py`) so it can be tested independently and reused without Streamlit.

---

### `hospital/__init__.py`

**Classification:** 🟢 **Essential — Package Marker**

#### Why does this file exist?

Python requires an `__init__.py` file inside a folder to treat it as an importable package. Without it, `from hospital.data import generate_patients` would fail with a `ModuleNotFoundError`.

#### What does it contain?

Nothing — it is an empty file. Its mere existence is what matters.

#### What is its use?

It enables Python's import system to recognize `hospital/` as a package.

#### Where is it used?

Implicitly by every `import` statement that references the `hospital` package:
- `app.py` → `from hospital.data import generate_patients, load_csv, load_hangu_durations`
- `app.py` → `from hospital.queueing import recommend_staffing`
- `app.py` → `from hospital.simulation import SimulationResult, simulate`
- `hospital/queueing.py` → `from hospital.data import require_integer, require_number`
- `hospital/simulation.py` → `from hospital.data import require_integer, require_number, validate_patients`
- `tests/test_models.py` → imports from all three hospital modules

#### Is it essential?

**Yes.** Delete this file and every import from `hospital` breaks. The entire application crashes on startup.

---

### `hospital/data.py`

**Classification:** 🟢 **Essential — Data Layer**

#### Why does this file exist?

The application needs patient data to work, and that data can come from three sources (synthetic generation, Hangu hybrid, user CSV). Each source needs different handling: generation needs random numbers, CSV needs parsing and validation, Hangu needs checksum verification. Putting all of this in `app.py` would make the dashboard code enormous and untestable. This file exists to **separate data concerns from UI concerns**.

It also enforces a strict data contract: every patient DataFrame must have `patient_id`, `arrival_min`, and `service_min` with specific constraints. This prevents garbage data from reaching the simulation.

#### What does it contain?

| Function/Constant | What it does |
|---|---|
| `MAX_PATIENTS = 10_000` | Hard limit on rows to keep the educational app responsive. |
| `MAX_UPLOAD_BYTES = 2_000_000` | 2 MB upload size limit. |
| `REQUIRED_COLUMNS` | Tuple of the three required column names. |
| `generate_patients()` | Creates synthetic patient data using NumPy's seeded RNG. Generates exponential inter-arrival times, and either exponential service durations or resamples from a provided pool (for hybrid mode). Returns a validated, sorted DataFrame. |
| `load_csv()` | Parses uploaded CSV bytes. First pass uses Python's `csv` module for strict structural validation (field counts, row limits); second pass uses Pandas for data parsing. Returns a validated DataFrame. |
| `load_hangu_durations()` | Reads `data/hangu_service_minutes.csv`, verifies its SHA-256 checksum against `data/hangu_provenance.json`, validates duration bounds (3–60 min), and returns a NumPy array of 6,637 duration values. |
| `validate_patients()` | Enforces the data contract on any DataFrame: checks for missing columns, duplicate IDs, blank IDs, non-numeric values, NaN/Inf, out-of-range arrivals, non-positive service times. Sorts by arrival time. |
| `require_number()` | Input validator — ensures a value is a finite positive (or nonneg) number. |
| `require_integer()` | Input validator — ensures a value is a whole number within bounds. |

#### Where is it used?

- **`app.py`** imports `generate_patients`, `load_csv`, and `load_hangu_durations` to obtain patient data based on the user's data-source selection.
- **`hospital/queueing.py`** imports `require_number` and `require_integer` for parameter validation.
- **`hospital/simulation.py`** imports `require_number`, `require_integer`, and `validate_patients` for parameter and cohort validation.
- **`tests/test_models.py`** imports all public functions for thorough testing.

#### How does it contribute?

It is the **data gateway** of the entire application. Every patient that enters the simulation — whether synthetic, hybrid, or uploaded — passes through this file's validation. It guarantees that downstream modules (queueing, simulation) never receive malformed data.

#### Is it essential?

**Yes.** Without it, the application has no way to obtain or validate patient data. Both the queueing module and the simulation module also depend on its validation helpers. Removing it crashes the entire application.

---

### `hospital/queueing.py`

**Classification:** 🟢 **Essential — OR Technique #1**

#### Why does this file exist?

This is where **Operations Research Technique #1** lives. The project needs a mathematical way to estimate how long patients will wait and how many doctors are needed. This file implements the Erlang C formula and uses it to search for the optimal staffing level.

Separating this from `app.py` means the queueing math can be tested with known analytical answers (M/M/1: Wq = 40 min, M/M/2: Wq = 16 min) without starting a dashboard.

#### What does it contain?

| Component | What it does |
|---|---|
| `QueuePrediction` (dataclass) | Immutable result of one Erlang C calculation: doctor count, utilization (ρ), stability flag, probability of waiting, mean wait (min), mean queue length, mean system time. |
| `StaffingRecommendation` (dataclass) | Immutable result of the staffing search: recommended doctor count, whether the target was met, and the tuple of all predictions evaluated. |
| `erlang_c()` | **The core formula.** Takes arrival rate (λ), mean service time, and doctor count (c). Computes μ = 60/service, offered load a = λ/μ, utilization ρ = a/c. If ρ ≥ 1, returns unstable (infinite wait). Otherwise, iteratively computes partial sums (avoiding raw factorials for numerical stability), calculates the Erlang C probability P(wait), and derives mean wait Wq = P(wait)/(cμ − λ). |
| `recommend_staffing()` | **The decision rule.** Loops doctor counts from baseline to maximum. For each, calls `erlang_c()`. Stops at the first stable count with predicted mean wait ≤ target. If none qualifies, returns the maximum count with `target_met=False`. |

#### Where is it used?

- **`app.py`** (line 105–108) calls `recommend_staffing()` with the cohort's observed arrival rate, mean service time, baseline doctors, max doctors, and target — to determine how many doctors to recommend.
- **`tests/test_models.py`** tests both `erlang_c()` and `recommend_staffing()` against known mathematical answers.

#### How does it contribute?

It provides the **analytical brain** of the project. Without it, the application would have no mathematical basis for recommending a doctor count. The user would have to guess.

#### Is it essential?

**Yes.** Without this file, `app.py` line 105 (`recommend_staffing(...)`) immediately crashes with an `ImportError`. The application cannot compute a recommendation or show the staffing prediction table.

---

### `hospital/simulation.py`

**Classification:** 🟢 **Essential — OR Technique #2**

#### Why does this file exist?

Queueing theory gives an *estimate* (long-run average under ideal assumptions). But the project needs to *measure* what actually happens when a specific set of patients visits the clinic. This file implements **OR Technique #2: discrete-event simulation** — it processes each patient through a virtual clinic and records exact wait times.

Separating it from the UI means simulation correctness can be verified with hand-calculable examples (3 patients, known waits of [0, 3, 6] with 1 doctor).

#### What does it contain?

| Component | What it does |
|---|---|
| `SimulationResult` (dataclass) | Immutable container holding four outputs: per-patient results DataFrame, queue-event DataFrame, per-doctor utilization DataFrame, and a metrics dictionary. |
| `simulate()` | **The simulation engine.** Takes a patient DataFrame, doctor count, closing time, and target. Uses a min-heap (Python `heapq`) where each entry is `(next_available_time, doctor_id)`. For each patient (in arrival order), pops the earliest-available doctor, computes `start = max(arrival, doctor_available)`, `wait = start − arrival`, `end = start + service`, pushes the doctor back with new availability. Then computes: (1) queue events by tracking +1 at arrival and −1 at service-start for waiting patients, (2) time-weighted queue area using `numpy.dot(diffs, lengths)`, (3) per-doctor busy time and utilization for both the arrival window and full session, (4) aggregate metrics: mean/median/p95 wait, within-target %, max queue, mean queue, overtime, horizon. |

#### Where is it used?

- **`app.py`** (lines 109–110) calls `simulate()` twice — once with the baseline doctor count and once with the recommended count — using the *same* patient cohort for a fair comparison.
- **`app.py`** also imports `SimulationResult` for type annotation in the comparison table function.
- **`tests/test_models.py`** tests `simulate()` with hand-calculated examples and checks invariants (queue-area = sum of waits, busy time = sum of service, non-overlapping doctor assignments).

#### How does it contribute?

It turns the abstract recommendation into **measurable patient-level evidence**. The charts, KPI cards, patient records, and CSV downloads all show data produced by this module. It is what makes the comparison tangible.

#### Is it essential?

**Yes.** Without it, `app.py` lines 109–110 crash. There would be no simulation results, no charts, no patient records, no downloads — the entire dashboard beyond the sidebar would be empty.

---

## `data/` — Datasets and Provenance

This folder holds the input data files that the application reads at runtime. It is **not a Python package** (no `__init__.py`) — it contains data files, not code.

---

### `data/sample_patients.csv`

**Classification:** 🟠 **Dataset — Example Input**

#### Why does this file exist?

When a user selects "Upload CSV" mode, they need to know the expected format. Instead of just documenting it, the app offers a downloadable example. This file *is* that example. It also serves as the hand-checkable test case described in the implementation plan (3 patients, known wait results).

#### What does it contain?

```csv
patient_id,arrival_min,service_min
P001,0,5
P002,2,5
P003,4,5
```

Three patients arriving at minutes 0, 2, and 4, each needing a 5-minute consultation.

#### Where is it used?

- **`app.py`** (lines 69–74): read as bytes and offered via `st.download_button("Download sample input", ...)` when the user is in Upload CSV mode.
- **Not directly used by tests**, but the same 3-patient data is recreated in `tests/test_models.py`'s `tiny_cohort()` helper.

#### Is it essential?

**Partially.** Removing it causes a `FileNotFoundError` when a user clicks "Download sample input" in Upload CSV mode. The Synthetic demo and Hangu hybrid modes are unaffected. The sample download button would crash, but the core application still functions.

---

### `data/hangu_service_minutes.csv`

**Classification:** 🟠 **Dataset — Real-Source Duration Extract**

#### Why does this file exist?

The project claims to support a "real-source hybrid" mode using actual consultation-duration data. This file is the **cleaned, privacy-safe extract** of 6,637 duration values from the Hangu outpatient dataset (Feng et al., 2023). It exists so the hybrid mode can run **offline** — the original dataset does not need to be re-downloaded every time.

Only the `service_min` column is kept. All patient identifiers, demographics, and diagnoses from the original dataset are discarded.

#### What does it contain?

A single-column CSV with 6,637 rows of consultation durations in minutes (range: 3.0 to ~57.6 minutes, mean ≈ 13.365 minutes), sorted ascending.

#### Where is it used?

- **`hospital/data.py`** → `load_hangu_durations()` reads this file, verifies its SHA-256 checksum against `hangu_provenance.json`, and returns the values as a NumPy array.
- The array is then passed to `generate_patients(..., service_samples_min=pool)` which samples durations from it (instead of generating exponential durations).

#### Is it essential?

**For Hangu hybrid mode, yes.** Removing it causes `load_hangu_durations()` to raise a `ValueError("Cannot read Hangu data.")`, and hybrid mode displays a clear error. **Synthetic demo and Upload CSV modes are unaffected.**

---

### `data/hangu_provenance.json`

**Classification:** 🟠 **Dataset — Integrity and Attribution Metadata**

#### Why does this file exist?

When you bundle data from an external source, you need to answer: *Where exactly did this data come from? Has it been tampered with? What transformations were applied?* This file answers all of those questions. It also enables **runtime integrity verification** — the app checks the SHA-256 hash of the duration CSV against the hash recorded here.

#### What does it contain?

A JSON object with:
- `citation` — full academic reference (Feng et al., 2023).
- `paper_url`, `repository_url`, `archive_url` — links to the original source.
- `license` — "CC BY-NC-SA 4.0".
- `source_revision` — exact Git commit hash of the source repo used.
- `source_sha256` — hash of the original `Data.csv` as downloaded.
- `extract_sha256` — hash of the produced `hangu_service_minutes.csv`.
- `records` — expected row count (6,637).
- `mean_service_min`, `min_service_min`, `max_service_min` — aggregate statistics.
- `transformation` — description of how the extract was produced.
- `source_cleaning` — what the original authors did to clean the data.
- `limitations` — honest disclosure of what the data does and does not represent.

#### Where is it used?

- **`hospital/data.py`** → `load_hangu_durations()` reads this file, extracts `extract_sha256` and `records`, and uses them to verify that `hangu_service_minutes.csv` hasn't been corrupted or tampered with.
- **`tests/test_models.py`** → indirectly tested through `load_hangu_durations()` calls.

#### Is it essential?

**For Hangu hybrid mode, yes.** If this file is missing or contains a wrong hash, `load_hangu_durations()` raises a `ValueError` and hybrid mode refuses to run — this is a deliberate safety check.

---

### `data/HANGU_LICENSE.txt`

**Classification:** 🟠 **Dataset — Legal Requirement**

#### Why does this file exist?

The Hangu dataset is licensed under CC BY-NC-SA 4.0, which **requires** that the license text be included when the data is redistributed. This file satisfies that legal obligation.

#### What does it contain?

The full text of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license (437 lines).

#### Where is it used?

- **`scripts/import_hangu.py`** downloads this file from the source repository and writes it here.
- **Not read by any application code at runtime.** It exists solely for legal compliance.
- Referenced in `README.md` attribution section.

#### Is it essential?

**Not for execution.** The application ignores it. But **legally required** when distributing the Hangu data extract.

---

## `scripts/` — Utilities and Video Production

These are standalone scripts that are **never imported by `app.py`**. They solve specific one-off tasks: importing external data and recording the project video.

---

### `scripts/import_hangu.py`

**Classification:** 🟣 **Utility — One-Time Data Import**

#### Why does this file exist?

The project bundles the Hangu duration data in `data/`, but the original source is a GitHub repository. This script exists to provide a **transparent, reproducible** way to produce that extract from the original source. A teacher or evaluator can run it to verify that the bundled data matches the claimed source.

It also exists to separate the network-dependent import step from the offline application. The dashboard never needs internet; only this script does.

#### What does it contain?

- `extract_durations()` — reads the original CSV, finds the `ServTime` column, validates each value is between 180–3600 seconds, converts to minutes, sorts ascending, and returns a list of floats.
- `main()` — downloads `Data.csv` and `LICENSE` from the pinned GitHub revision using `urllib.request`, calls `extract_durations()`, writes the three data files (`hangu_service_minutes.csv`, `hangu_provenance.json`, `HANGU_LICENSE.txt`), and prints a summary.

#### Where is it used?

- **Run manually by a developer**: `python scripts\import_hangu.py`.
- **`tests/test_models.py`** (line 15) imports `extract_durations` to unit-test the seconds-to-minutes conversion and validation logic.
- **Not imported by `app.py` or any `hospital/` module.**

#### Is it essential?

**No, for normal usage.** The data files it produces are already bundled in `data/`. Only needed if you want to regenerate the extract from source (e.g., to verify provenance).

---

### `scripts/record_walkthrough.py`

**Classification:** 🟣 **Utility — Video Production**

#### Why does this file exist?

The project deliverables include a narrated video walkthrough. Recording it manually would be error-prone and unreproducible. This script **automates the entire process**: it drives the real application through scripted interactions, records the browser, generates speech, and produces a verified MP4.

#### What does it contain?

- `perform_action()` — a dispatcher that maps action names (like "intro", "settings", "busy", "queue", "patients") to specific Playwright browser interactions (clicking buttons, filling inputs, switching tabs, scrolling to elements, verifying expected values).
- `set_caption()` — injects a styled chapter-summary overlay into the browser DOM via JavaScript.
- `main()` — orchestrates the full recording pipeline: generates speech WAVs via `narrate_video.ps1`, launches Playwright Chromium, walks through all 13 chapters (from `video_narration.json`), captures video, aligns speech to chapter start times, muxes video + audio with FFmpeg, validates the output (duration, resolution, audio volume), generates screenshots, SRT captions, transcript, and verification JSON.

#### Where is it used?

- **Run manually**: `python scripts\record_walkthrough.py --url http://127.0.0.1:8517`.
- Requires the app to be running separately and the optional `requirements-video.txt` dependencies installed.
- **Not imported by any other file.**

#### Is it essential?

**No.** The dashboard runs perfectly without it. Only needed to produce the video deliverable. The existing video in `deliverables/` was already generated by this script.

---

### `scripts/narrate_video.ps1`

**Classification:** 🟣 **Utility — Speech Synthesis**

#### Why does this file exist?

The walkthrough video needs narration. Instead of using an external speech API (which would require internet and an API key), this script uses **Windows' built-in text-to-speech** (System.Speech) with the Microsoft Zira Desktop voice. No voice cloning, no cloud, no cost.

#### What does it contain?

A PowerShell script that:
1. Loads `video_narration.json` to get the narration text for each chapter.
2. Creates a `SpeechSynthesizer` object using the `System.Speech` .NET assembly.
3. Selects the "Microsoft Zira Desktop" voice at rate 2 and volume 100.
4. Loops through each chapter and writes the spoken narration to a numbered WAV file (`speech-00.wav`, `speech-01.wav`, etc.).

#### Where is it used?

- **Called by `scripts/record_walkthrough.py`** (lines 164–170) as a subprocess during video production.
- **Not used by the application or tests.**

#### Is it essential?

**No.** Only needed for video production. Windows-only (uses .NET System.Speech).

---

### `scripts/video_narration.json`

**Classification:** 🟣 **Utility — Video Script Definition**

#### Why does this file exist?

The video walkthrough has 13 chapters. Each chapter needs a title, an on-screen caption, a UI action to perform, and narration text to speak. Defining all of this in a JSON file (rather than hard-coding it in the Python recorder) makes the script editable without touching code, and keeps the content separate from the recording logic.

#### What does it contain?

A JSON array of 13 objects, each with:
```json
{
  "title": "PatientFlow: project walkthrough",
  "caption": "Plan outpatient doctor capacity...",
  "action": "intro",
  "narration": "Welcome to Patient Flow, a local hospital..."
}
```

The `action` field maps to a specific UI interaction in `record_walkthrough.py`.

#### Where is it used?

- **`scripts/record_walkthrough.py`** (line 160) reads this file to get chapter definitions.
- **`scripts/narrate_video.ps1`** receives this file as a parameter and reads narration text from it.

#### Is it essential?

**No.** Only needed for video production.

---

## `tests/` — Automated Test Suite

The test files exist to prove that the mathematical models, data validation, simulation, and dashboard all work correctly. They are development-time tools, not runtime dependencies.

---

### `tests/test_models.py`

**Classification:** 🔵 **Testing — Core Logic Tests**

#### Why does this file exist?

The project uses mathematical formulas (Erlang C) and a simulation algorithm. If there's a bug in a formula, the dashboard would show wrong results without any visible error. This file exists to catch such bugs by comparing code output against **known correct answers** that can be verified by hand or from textbooks.

#### What does it contain?

**28 test methods across 3 test classes:**

| Test Class | What it verifies |
|---|---|
| `QueueingTests` (9 tests) | Erlang C against known M/M/1 answer (λ=2, μ=3, Wq=40 min). M/M/2 answer (P(wait)=8/15, Wq=16 min). The iterative recurrence matches a direct factorial formula for 14 × 4 = 56 combinations. Unstable queues (ρ ≥ 1) return infinity, not zero. Zero arrivals give zero wait. Staffing search finds the correct smallest feasible count. Already-met baselines aren't increased. Infeasible targets and zero targets are handled. Invalid inputs (negative rates, NaN, booleans, out-of-range integers) are rejected. |
| `DataTests` (12 tests) | Hangu `ServTime` seconds → minutes conversion and sorting. Actual bundled extract: exactly 6,637 records, mean ≈ 13.365, all within 3–60 min bounds, sorted. Hybrid mode preserves synthetic arrival times while sampling only from the source pool. Invalid sample pools (empty, 2D, zero, NaN, Inf, strings) are rejected. Missing/malformed Hangu files produce clear errors, not silent failures. Seeded generation is reproducible. Empty generation raises an error. Boundary validation for all generate_patients arguments. CSV parsing preserves string IDs ("NA" stays as "NA", not parsed as null). 14 invalid CSV examples all raise ValueError. Row-limit enforcement. validate_patients doesn't mutate its input. |
| `SimulationTests` (7 tests) | Hand-calculated 1-doctor result: starts [0,5,10], waits [0,3,6], mean 3.0, queue area 9, overtime 5 min. 2-doctor result: waits [0,0,1], mean 0.33. Doctor busy time clipped correctly at closing. Simultaneous departures and arrivals handled. Three seeded scenarios (0, 42, 100): queue always ≥ 0, ends at 0, queue-area = sum of waits, doctor busy = sum of service, utilization 0–100%, no overlapping assignments, improved waits ≤ baseline waits for every patient. Default demo scenario produces mean wait ≤ 5 min with recommendation. |

#### Where is it used?

- Run with: `python -m unittest discover -s tests -v`.
- Imports from `hospital.data`, `hospital.queueing`, `hospital.simulation`, and `scripts.import_hangu`.

#### Is it essential?

**Not for execution.** The app runs without tests. But **essential for correctness confidence** — these 28 tests are what prove the math is right.

---

### `tests/test_app.py`

**Classification:** 🔵 **Testing — Dashboard UI Tests**

#### Why does this file exist?

It's possible for the core logic to be correct but the dashboard to display it wrong (e.g., showing stale results, misconnecting widgets, silently swallowing errors). This file tests the **actual Streamlit dashboard** using Streamlit's `AppTest` framework — it simulates clicking buttons, changing inputs, and verifying what appears on screen.

#### What does it contain?

**13 test methods** covering:

| Test | What it verifies |
|---|---|
| `test_default_dashboard_and_records` | The app renders without errors on first load: 4 metrics, 4 tabs, ≥4 data frames, record switching works. |
| `test_invalid_doctor_limit_is_visible` | Setting baseline > maximum shows a visible error message, not a crash. |
| `test_infeasible_target_is_not_reported_as_success` | When the target can't be met, the app shows a warning (not a green success). |
| `test_empty_synthetic_cohort_is_visible` | Very low demand + short window shows "No patients arrived" error. |
| `test_upload_mode_requests_file` | Switching to Upload CSV shows an info prompt, not a crash. |
| `test_hybrid_dashboard_is_explicit_and_offline` | Hybrid mode runs without network (patches `urlopen`), shows warning label, shows "6,637", hides the mean-service input, and returns to synthetic correctly. |
| `test_hybrid_missing_source_error_visible` | If Hangu data is missing, shows a clear error in the dashboard. |
| `test_changes_wait_for_explicit_run` | Changing arrival rate does NOT auto-update results; shows "Settings changed" notice; clicking Run updates them. |
| `test_pending_source_does_not_relabel_saved_results` | Switching source radio to hybrid (without running) keeps "Last run: Synthetic demo" label. |
| `test_presets_and_reset_preserve_reproducible_demo` | Busy → Run → Load demo → Run reproduces the exact same 80.80 min result. |
| `test_patient_filters_do_not_change_cohort` | Searching patient IDs and filtering by wait target only change displayed rows, not the patient count or KPI metrics. |
| `test_queue_and_utilization_controls_do_not_change_results` | Toggling queue horizon and utilization period don't alter the four KPI metrics. |

#### Where is it used?

- Run with: `python -m unittest discover -s tests -v`.
- Imports `app.py` via `AppTest.from_file()`.

#### Is it essential?

**Not for execution.** But these tests catch subtle UI regressions that would be invisible to the core logic tests.

---

## `.streamlit/` — Streamlit Configuration

---

### `.streamlit/config.toml`

**Classification:** 🟡 **Configuration — UI Theme and Server Settings**

#### Why does this file exist?

Without it, Streamlit uses its default purple theme and port 8501. This file customizes three things:
1. **Visual theme** — a professional light/teal/navy color scheme instead of the default.
2. **Privacy** — disables Streamlit's usage-statistics telemetry.
3. **Server** — uses port 8517 (to avoid conflicts with other Streamlit apps on 8501) and limits uploads to 2 MB.

#### What does it contain?

```toml
[theme]
base = "light"
primaryColor = "#0d9488"          # Teal accent
backgroundColor = "#f5f7fb"       # Light grey background
secondaryBackgroundColor = "#eff3f8"
textColor = "#102a43"             # Dark navy text
font = "sans serif"

[browser]
gatherUsageStats = false          # No telemetry

[server]
maxUploadSize = 2                 # 2 MB upload limit
port = 8517                       # Custom port
address = "127.0.0.1"            # Localhost only
```

#### Where is it used?

- **Automatically read by Streamlit** when the app starts. Streamlit looks for `.streamlit/config.toml` in the project directory.
- **Not imported by any Python code.**

#### Is it essential?

**No.** The app runs without it — Streamlit falls back to defaults (different colors, port 8501, telemetry enabled). But the configured upload limit (2 MB) matches the validation in `data.py`, so removing it could allow uploads that pass Streamlit's check but fail the code's check at a different point.

---

## `deliverables/` — Generated Outputs

These files were **produced by** `scripts/record_walkthrough.py`. They are pre-built artifacts, not source code. The application never reads them.

---

### `deliverables/PatientFlow_walkthrough.mp4`

**Classification:** 🔘 **Generated Output — Video Deliverable**

#### Why does this file exist?

The project requires a narrated walkthrough video. This MP4 demonstrates the application's features with automated browser recording and computer-generated narration.

#### What does it contain?

A 4-minute 27-second (267.28s) video at 1600×900 resolution showing all 13 chapters of the application walkthrough with on-screen chapter-summary captions and Microsoft Zira Desktop narration. H.264 video codec, AAC audio.

#### Is it essential?

**No.** The dashboard runs without it. It is a presentation/submission deliverable.

---

### `deliverables/video_details.json`

**Classification:** 🔘 **Generated Output — Video Verification**

#### Why does this file exist?

To provide machine-readable proof that the video meets its specifications: correct duration (180–300s), correct resolution (1600×900), audible narration (mean volume −20.8 dB), and a complete chapter timeline with timestamps.

#### Is it essential?

**No.** A verification/audit artifact only.

---

### `deliverables/walkthrough_transcript.txt`

**Classification:** 🔘 **Generated Output — Narration Text**

#### Why does this file exist?

Provides a readable text version of everything spoken in the video, organized by chapter title. Useful for accessibility and for reviewing the narration without watching the video.

#### Is it essential?

**No.** Documentation/accessibility artifact.

---

### `deliverables/walkthrough_captions.srt`

**Classification:** 🔘 **Generated Output — Subtitle File**

#### Why does this file exist?

A standard SubRip (.srt) subtitle file that media players can display alongside the video. Contains chapter-summary captions (not word-for-word transcription) with timestamps.

#### Is it essential?

**No.** Accessibility artifact for the video.

---

### `deliverables/recommendation.png`

**Classification:** 🔘 **Generated Output — Screenshot**

#### Why does this file exist?

A screenshot of the staffing recommendation view, captured during video recording. Used in `README.md` as a visual preview of the application.

#### Is it essential?

**No.** Documentation image.

---

### `deliverables/queue.png`

**Classification:** 🔘 **Generated Output — Screenshot**

#### Why does this file exist?

A screenshot of the queue-over-time chart comparing baseline and recommended staffing. Used in `README.md`.

#### Is it essential?

**No.** Documentation image.

---

### `deliverables/hybrid.png`

**Classification:** 🔘 **Generated Output — Screenshot**

#### Why does this file exist?

A screenshot of the dashboard in Hangu hybrid mode, showing the data warning and attribution. Used in `README.md`.

#### Is it essential?

**No.** Documentation image.

---

## Summary Classification Table

This table answers at a glance: *"What kind of file is this, and do I need it?"*

| File | Category | Essential for App? | What Breaks If Removed |
|---|---|---|---|
| `app.py` | 🟢 Essential | **Yes** | Entire application cannot start. |
| `hospital/__init__.py` | 🟢 Essential | **Yes** | All `hospital` imports fail; app crashes on startup. |
| `hospital/data.py` | 🟢 Essential | **Yes** | No data loading, generation, or validation; app crashes. |
| `hospital/queueing.py` | 🟢 Essential | **Yes** | No staffing recommendation; app crashes. |
| `hospital/simulation.py` | 🟢 Essential | **Yes** | No simulation results, charts, or downloads; app crashes. |
| `data/hangu_service_minutes.csv` | 🟠 Dataset | Hybrid mode only | Hangu hybrid mode shows an error; other modes work. |
| `data/hangu_provenance.json` | 🟠 Dataset | Hybrid mode only | Hangu hybrid mode fails integrity check; other modes work. |
| `data/HANGU_LICENSE.txt` | 🟠 Dataset | No | No runtime impact; legal compliance issue. |
| `data/sample_patients.csv` | 🟠 Dataset | Partially | "Download sample input" button crashes; everything else works. |
| `.streamlit/config.toml` | 🟡 Config | No | App uses Streamlit defaults (different port, colors, telemetry on). |
| `requirements.txt` | 🟡 Config | No (if deps installed) | New developers can't know what to install. |
| `requirements-video.txt` | 🟡 Config | No | Video recording setup instructions incomplete. |
| `.gitignore` | 🟡 Config | No | Git tracks unwanted files; no runtime impact. |
| `tests/test_models.py` | 🔵 Testing | No | No mathematical correctness verification; app still runs. |
| `tests/test_app.py` | 🔵 Testing | No | No UI regression testing; app still runs. |
| `scripts/import_hangu.py` | 🟣 Utility | No | Can't regenerate Hangu data from source; bundled data still works. |
| `scripts/record_walkthrough.py` | 🟣 Utility | No | Can't re-record the video; existing video still exists. |
| `scripts/narrate_video.ps1` | 🟣 Utility | No | Can't generate narration audio; existing video still exists. |
| `scripts/video_narration.json` | 🟣 Utility | No | Can't re-record the video; existing video still exists. |
| `README.md` | ⚪ Documentation | No | No project documentation; app still runs. |
| `implementation_plan.md` | ⚪ Documentation | No | No design document; app still runs. |
| `builder.md` | ⚪ Documentation | No | No developer guide; app still runs. |
| `PROJECT_FILE_GUIDE.md` | ⚪ Documentation | No | No file structure guide; app still runs. |
| `PatientFlow.zip` | 🔘 Generated | No | No distribution archive; source files still exist. |
| `deliverables/*.mp4` | 🔘 Generated | No | No video walkthrough; app still runs. |
| `deliverables/*.json` | 🔘 Generated | No | No video verification data; app still runs. |
| `deliverables/*.txt` | 🔘 Generated | No | No transcript; app still runs. |
| `deliverables/*.srt` | 🔘 Generated | No | No captions; app still runs. |
| `deliverables/*.png` | 🔘 Generated | No | No screenshots for README; app still runs. |

---

> **The 5 files without which the application cannot function at all:**
> `app.py`, `hospital/__init__.py`, `hospital/data.py`, `hospital/queueing.py`, `hospital/simulation.py`
>
> Everything else supports the application through data, configuration, testing, documentation, or deliverables — but the core runs on these five files alone (plus the installed Python packages).

---

*This document was created by reviewing the actual implementation of every file in the project. It is intended to fully prepare you to explain any file in a presentation or viva.*

