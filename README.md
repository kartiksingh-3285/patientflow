# PatientFlow | Hospital waiting-time optimization

A beginner-friendly, local Python project demonstrating **two Operations Research
techniques** that help plan outpatient doctor capacity and reduce patient queues.
No database, cloud account, or external API is required at runtime.

## Problem and features

When arrivals exceed available doctor capacity, queues grow. PatientFlow:
- Generates synthetic patients, offers real-source Hangu hybrid mode, or accepts a CSV.
- Estimates steady-state waiting with **M/M/c queueing theory (Erlang C)**.
- Selects the smallest available doctor count meeting a mean-wait target.
- Tests baseline and recommended staffing with **discrete-event simulation**.
- Shows waiting-time distributions, overtime, utilization, and detailed comparisons.
- Explains assumptions and formulas alongside the results.
- Provides explicit Run comparison and demo/busy-clinic presets.

This is an educational consultation-queue model, not clinical triage or medical advice.

## Technology and structure

Python 3.12+, Streamlit, NumPy, Pandas, Plotly; standard-library unittest.

```text
app.py                    Dashboard
hospital/data.py          Generation and validation
hospital/queueing.py      Erlang C and staffing decision
hospital/simulation.py    FCFS discrete-event simulation
data/sample_patients.csv  Tiny synthetic upload example
data/hangu_service_minutes.csv  Real-source duration-only extract
data/hangu_provenance.json      Source revision, hashes, and attribution
data/HANGU_LICENSE.txt          Source dataset license
scripts/import_hangu.py        Optional one-time source refresh
scripts/record_walkthrough.py  Optional local video recorder
scripts/video_narration.json   Narration and chapter text
scripts/narrate_video.ps1      Offline Windows computer speech
requirements-video.txt        Optional recording dependencies
deliverables/                 Narrated video, captions, transcript, and screenshots
tests/                    Mathematical and UI tests
implementation_plan.md    Design, formulas, assumptions
builder.md                Step-by-step development guide
requirements.txt          Dependencies
.streamlit/config.toml    Local theme, upload limit, telemetry disabled
```

## Install and run (Windows PowerShell)

Extract the ZIP and open PowerShell in the project folder containing app.py.
The archive includes source, documentation, data, and video, but not installed
dependencies or a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8517 --server.address 127.0.0.1
```

Open http://127.0.0.1:8517. Using the virtual environment's executable directly
avoids PowerShell activation-policy issues.
Run the command from this project folder and keep that terminal open while using
the app. Port 8517 is configured locally to avoid another application on 8501.
If the browser says the server is unavailable, restart the command above.

## Deploy to Streamlit Community Cloud

1. Push this project folder to a GitHub repository. Keep `app.py`, `hospital/`,
   `data/`, `requirements.txt`, and `.streamlit/config.toml` at the repository root.
2. At [share.streamlit.io](https://share.streamlit.io), choose **Create app**.
3. Select the repository and branch, set the app file to `app.py`, then deploy.

Tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## How to use

1. Start with the default synthetic scenario.
2. Adjust Current doctors, Maximum available doctors, and Average-wait target.
   Click **Run comparison** to apply settings. The initial demo runs once on opening.
3. Use **Busy clinic** or **Load demo** to populate settings, then run them.
   Pending changes do not silently alter the saved results or their data-origin labels.
4. Explore Waiting times and How it works, including the detailed comparison table.
5. Upload the sample CSV or your own anonymized rows; set an arrival window containing
   all arrivals.
6. Try several random seeds; do not interpret one realization as a clinical guarantee.
7. Choose **Hangu hybrid** for source-based consultations with clearly synthetic
   arrivals. The duration pool is bundled; no network access is needed at runtime.

The dashboard compares the same patient cohort under current and recommended
staffing. Technical assumptions and detailed metrics are available on demand.

CSV format:

```csv
patient_id,arrival_min,service_min
P001,0,5
P002,2,5
P003,4,5
```

Arrival minutes are measured from opening; duration minutes must be positive.
IDs must be unique and nonblank. Arrivals must be before the configured closing
time. Maximum: 10,000 rows / 2 MB. Do not include names or medical information.

## Data provenance and assumptions

Public datasets were searched before development. The
[Hangu outpatient service-time repository](https://github.com/fenghaolin/HanguData)
and [Feng et al. (2023)](https://doi.org/10.3390/data8030047) now supply
**6,637 real-source consultation-duration estimates** for the optional hybrid mode.
The original Synthetic demo and tiny example remain fully synthetic.

### Hangu hybrid: what is real and what is assumed?

| Component | Origin |
|---|---|
| Consultation durations | Uniform resampling of real-source Hangu duration estimates |
| Arrival times and demand | Synthetic exponential arrivals; user-selected rate |
| Patient IDs | New simulation IDs, not source identifiers |
| Doctor staffing and window | User-selected scenario assumptions |
| Waiting-time improvements | Simulated outcomes, not observed hospital improvements |

The authors' **cleaned Data.csv** is used, not the 6,853-row merged intermediate
file. ServTime is in **seconds**, verified against the published
Data_process_stat.ipynb calculation using timedelta.total_seconds. The authors'
cleaning retains 180..3600 seconds inclusive and nonmissing Visit.No. We retain
all 6,637 cleaned duration estimates, divide by 60, and sort the one-column
extract, discarding IDs, source row order, demographics, addresses, and diagnoses.
Pool mean is **13.365 minutes**; range is **3..60 minutes**.

The source is one clinic physician's consultations. End times/durations are
estimates, not stopwatch measurements. Clinic-arrival timestamps are not used,
and consultation starts are never substituted as arrivals. Resampling with
replacement ignores session structure and patient heterogeneity. Empirical
services need not be exponential: **Erlang C is a mean-based approximation
in hybrid mode**, while DES uses the sampled duration values exactly.

Pinned source revision: `f26b66a3e3dd69d45502ff30d934e24b6476218c`.
Source/extract SHA-256 hashes, row count, transformations, and citation are
recorded in data/hangu_provenance.json. Dataset archive:
https://doi.org/10.5281/zenodo.7484205.

**Attribution:** Feng, Haolin; Jia, Yiwu; Zhou, Siyi; Chen, Hongyi; Huang, Teng
(2023). *A Dataset of Service Time and Related Patient Characteristics from an
Outpatient Clinic*. Data 8(3), 47. https://doi.org/10.3390/data8030047.
Source/adapted duration data are **CC BY-NC-SA 4.0**: attribution, noncommercial
use, and share-alike for adapted data. Full source license is bundled in
data/HANGU_LICENSE.txt. No endorsement by the authors is implied.
This data license is separate from the application's code.

To regenerate the extract (internet required only for this explicit command):

```powershell
.\.venv\Scripts\python.exe scripts\import_hangu.py
```

**Synthetic demo defaults** (12 arrivals/hour,
12-minute mean service, 8 hours, seed 42) are illustrative assumptions, not
measurements from that dataset. Arrivals and consultation durations are independent
exponential samples; all doctors have equal speed and are available continuously.
The model uses one FCFS queue, no breaks, priority triage, or no-shows.

Uploaded rows are simulated exactly, but analytical predictions still assume M/M/c.
The arrival rate is estimated over the configured full arrival window.
Patients arriving before closing are served to completion; overtime is shown.
Doctor counts are constant availability, not a shift roster.

## Sample results

Hand-checkable uploaded example above:

| Metric | 1 doctor | 2 doctors |
|---|---:|---:|
| Patient waits (minutes) | 0, 3, 6 | 0, 0, 1 |
| Mean wait (minutes) | 3.00 | 0.33 |
| Queue area (patient-minutes) | 9 | 1 |

Measured default synthetic scenario (seed 42, 8 hours, 12 nominal arrivals/hour,
12-minute nominal consultations, 5-minute target):

| Metric | Baseline: 2 doctors | Improved: 4 doctors |
|---|---:|---:|
| Patients served | 102 | 102 |
| Simulated mean wait (min) | 80.80 | 2.31 |
| Simulated 95th-percentile wait (min) | 153.74 | 9.44 |
| Peak waiting queue | 28 | 5 |
| Arrival-window mean queue | 13.28 | 0.49 |
| Arrival-window mean doctor utilization | 93.48% | 61.66% |
| Time beyond closing (min) | 143.42 | 0.00 |

Mean wait falls **97.14%** for this synthetic realization. Observed demand is
12.75 patients/hour and observed mean service is 11.608 minutes; these cohort
estimates drive the analytical staffing search. Four doctors are the first
allowed count meeting the analytical target (predicted mean wait 2.34 minutes).
This is a measured educational example, not an empirical hospital benefit claim.
The overloaded baseline has no finite analytical steady-state wait. DES still
returns finite values because the arrival window is finite.

Hangu hybrid with the same arrival settings and seed also generates 102 simulated
patients. Sampled consultation mean is 12.6074 minutes; the decision changes two
doctors to four. Simulated mean wait is **101.24 -> 2.32 minutes (97.71% reduction)**;
the mean-based Erlang C approximation predicts 3.66 minutes with four doctors.
These results use real-source duration estimates but **synthetic arrivals and
assumed staffing**, not an observed Hangu queue or validated clinical improvement.
The synthetic demo's 97.14% result above is unchanged.

Full-session mean queue and utilization include time through the last departure
(at least the configured arrival window); arrival-window metrics are reported
separately. Mean wait includes the whole cohort. Analytical target feasibility and
simulated target achievement are distinct.

## Screenshots

- [Staffing recommendation](deliverables/recommendation.png)
- [Patient queue](deliverables/queue.png)
- [Hybrid data and attribution](deliverables/hybrid.png)

## Narrated project video

Open [PatientFlow walkthrough](deliverables/PatientFlow_walkthrough.mp4).
Verified duration: **4 minutes 27 seconds**, resolution **1600x900**, file size
approximately **6.84 MB**. The complete MP4 decodes successfully, and narration
audio was checked for a non-silent signal.
This is an actual automated recording of the local application with chapter-summary
captions and standard **Microsoft Zira Desktop** computer narration. No voice
cloning is used; narration is produced locally with Windows System.Speech.

Additional deliverables:
- [Narration transcript](deliverables/walkthrough_transcript.txt)
- [Chapter-summary captions](deliverables/walkthrough_captions.srt) (not word-for-word subtitles)
- [Video verification details](deliverables/video_details.json)

The recording demonstrates configuration, explicit runs, presets, wait comparisons,
queue/doctor controls, patient search, CSV export, hybrid provenance, and the two OR
techniques. The requested video duration is 3–5 minutes; the recorder validates
duration, resolution, audible narration, and a complete video/audio decode.

To regenerate on Windows, install optional recording tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-video.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

Start the app in one terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8517
```

In a second terminal:

```powershell
.\.venv\Scripts\python.exe scripts\record_walkthrough.py --url http://127.0.0.1:8517
```

Windows System.Speech and the installed Microsoft Zira Desktop voice are required.
The recorder uses its own local browser session and temporary capture/audio files,
which are removed automatically. These tools are not required to use the dashboard.

## Validation

41 automated tests cover known M/M/1 and M/M/2 formulas, a direct Erlang C
reference, staffing feasibility, hand-calculated FCFS queues, CSV failures,
reproducibility, busy-time overlap, queue-area conservation, identical cohorts,
and dashboard rendering/control changes. Python compilation is also checked.
Additional coverage includes source seconds-to-minutes conversion, 6,637-row
duration bounds/checksum, empirical sample membership, identical arrivals,
missing-source errors, and offline hybrid dashboard rendering.
UI regression tests also verify explicit runs, pending-setting/source labels,
presets, patient filters, and queue/utilization controls without altering the cohort.
Streamlit AppTest may emit a harmless missing-ScriptRunContext warning.
The local server health endpoint and browser CSV-upload flow were checked;
the three-patient paired CSV endpoint returned exactly the documented waits.
Hybrid browser verification displayed the measured 102-patient KPIs, and the
paired export contained 102 rows with hybrid/service/arrival provenance on every row.

## Presentation / viva

Explain the bottleneck using rho = lambda/(c*mu). Describe Erlang C as an expected
wait under stationary assumptions, then walk through the three-row FCFS example.
The decision is the smallest permitted doctor count meeting the analytical target;
DES measures its effect on identical patients without resampling or dropping anyone.
In hybrid mode, source durations are sampled once to create the cohort, never
resampled between the baseline and improved scenarios.

## Limitations and future improvements

This is not empirical hospital validation. Future work: multi-seed confidence
intervals, locally validated consultation durations, shift/break availability,
staffing costs, appointment/no-show models, and multi-stage registration/triage.
Do not treat emergency-department total length of stay as doctor consultation time.
