# Beginner development guide

## Stack and folder structure

Python 3.12; Streamlit for the UI; NumPy for reproducible random sampling;
Pandas for tabular inputs/results; Plotly for interactive charts.
Use the standard library heapq, dataclasses, and unittest.
No optimization solver or DES package is needed.

```text
PatientFlow/
  implementation_plan.md
  builder.md
  README.md
  requirements.txt
  .streamlit/
    config.toml
  app.py
  hospital/
    __init__.py
    data.py
    queueing.py
    simulation.py
  data/
    sample_patients.csv
    hangu_service_minutes.csv
    hangu_provenance.json
    HANGU_LICENSE.txt
  scripts/
    import_hangu.py
  tests/
    test_models.py
    test_app.py
```

Responsibilities:
- app.py: scenario controls, orchestration, error display, charts, export, model explanations.
- data.py: generate synthetic arrivals; validate CSV content and model inputs.
- queueing.py: Erlang C predictions and smallest-feasible-doctor recommendation.
- simulation.py: serve exact input cohort, compute queue events and utilization.
- sample_patients.csv: small synthetic, hand-checkable example (not the random default).
- .streamlit/config.toml: consistent light/teal theme, 2 MB upload cap, telemetry disabled.
- scripts/import_hangu.py: explicit one-time import from a pinned public source;
  keeps only sorted consultation-duration estimates, source license, and provenance.
- hangu_service_minutes.csv: one service_min column without patient identifiers.
- hangu_provenance.json: source hashes, revision, extraction rules, and aggregate statistics.
- test_models.py: known mathematical answers, boundary cases, invariants.
- test_app.py: exercise real Streamlit widgets and upload logic where supported.

## Implement in order

1. Finish all three design documents. No application code precedes these.
2. Add requirements, package marker, and data validation/generation.
3. Add queueing functions, then simulation.
4. Test core functions with tiny examples before connecting the dashboard.
5. Add dashboard controls and show validation errors instead of falling back silently.
6. Add visual comparisons, CSV downloads, and model explanations.
7. Run the complete small test suite and smoke-test the local server.
8. Record measured default results and include screenshot instructions.

## Data contract and generation

Input DataFrame columns (extra columns are not needed):

| Column | Type | Constraint |
|---|---|---|
| patient_id | string | unique, nonblank |
| arrival_min | number | finite, >= 0, < session closing |
| service_min | number | finite, > 0 |

At least one row is required. Sort by arrival stably; tied arrivals retain CSV
order. Reject duplicate IDs, invalid/missing values, nonfinite numbers, and
arrivals outside the window. Uploaded data stays in memory; never require patient
names. Limit uploads to 10,000 rows and 2 MB to keep this educational app responsive.

Synthetic generator pseudocode:

```text
rng = seeded NumPy generator
time = 0
repeat:
  time += exponential(mean = 60 / arrivals_per_hour)
  if time >= closing_minute: stop
  append time
sample one exponential(mean_service_minute) duration per arrival
assign IDs P0001, P0002, ...
```

Very small demand can generate no arrivals: display an actionable error asking
for a different seed or more demand, not a fabricated patient.
Reject duplicate CSV headers and mismatched field counts before Pandas can
automatically rename columns or infer an unintended index.

## Queueing theory implementation

Validate nonnegative lambda, positive service time, and positive integer doctors.
If lambda is zero, wait/queue/utilization are zero. If rho >= 1, mark unstable.
Avoid raw factorials/powers: iteratively build t_n = t_(n-1) * a/n.

```text
a = lambda / mu
rho = a / c
if rho >= 1: return unstable with infinite waiting
term = 1; sum_terms = 1
for n = 1 .. c-1:
  term *= a/n
  sum_terms += term
tail = term * a/c / (1-rho)
p_wait = tail / (sum_terms + tail)
wq_minutes = 60 * p_wait / (c*mu - lambda)
```

Staffing recommendation:

```text
for c = baseline .. maximum:
  prediction = ErlangC(lambda, mean_service, c)
  record prediction
  if stable and predicted_wait <= target:
    return c, target_met=True, all recorded predictions
return maximum, target_met=False, recorded predictions
```

Target zero is valid, but positive demand cannot achieve exactly zero Erlang C
wait with a finite number of doctors. Show infeasibility.

## DES implementation

Keep a min-heap of (available_minute, doctor_id), initialized at (0, id).
For each validated patient in arrival order, pop the earliest doctor:

```text
start = max(arrival, doctor_available)
end = start + service
record patient_id, arrival, service, doctor, start, end, wait
push (end, doctor) into heap
```

Each waiting patient contributes +1 at arrival and -1 at start; group simultaneous
events before cumulative summation. A patient with start == arrival never enters
the waiting queue. Include zero at opening and final departure. Plot horizontal
steps, not interpolated lines.

For each interval [event_time, next_event_time):
- full queue area += queue_count * interval_length.
- window queue area += queue_count * intersection_length_with_arrival_window.

For each service interval, doctor busy time within a window is its overlap with
that window. Full-session utilization denominator is max(closing, final_departure).
The arrival-window utilization denominator is closing. Full-session doctor busy
sum must equal input service sum.

Output result:
- patients: per-patient doctor, service start/end, waiting minutes.
- queue: event time and waiting-patient count.
- doctors: full-session and arrival-window utilization percentages.
- metrics: mean/median/p95 wait, percent starting within target, max/mean queue,
  arrival-window mean queue, overtime, session duration, cohort size.

## Integrating the two techniques

Generate/load and validate one DataFrame. Estimate lambda = rows / (closing/60)
and service mean from that cohort. Run queueing-based staffing search.
Simulate baseline and chosen staffing against **the same DataFrame**. Never
resample service times between scenarios. Keep recommended count >= baseline.
Display analytical target feasibility separately from observed target performance.
The mean-wait target does not mean every patient must wait less than that target.

## UI specification

Sidebar: data source, arrival window, current/max doctors, average-wait target,
arrival rate, mean service where applicable, and seed inside Reproducibility.
Add Load demo and Busy clinic presets and an explicit Run comparison button.
The first valid example runs on opening. Subsequent edits are pending until Run.
Store settings, source pool, cohort, recommendation, and both simulations together
in session state; results and exports always use this saved snapshot.
Show a settings-changed message when edits differ from the snapshot.
Never relabel previous synthetic results as hybrid while a source change is pending.
Invalid runs show an error without replacing the previous successful snapshot.

Main screen: practical title, last-run context, concise source label, capacity
recommendation, and waiting-time KPIs. Put source details in an expander.
Tabs: Waiting times, Queues & doctors, Patient records, How it works.
Add a queue-window toggle and a utilization-period selector. They change chart
presentation only, never model inputs. Patient ID and wait-target filters change
visible rows only. Download visible patients follows filters; paired/input
downloads retain all patients and the saved source's provenance.
Always label minute/hour units and metric horizons.
Use responsive cards, a restrained navy/teal palette, and native Streamlit components.

## Testing and debugging

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q app.py hospital tests
python -m streamlit run app.py
```

Run from the project directory and open http://127.0.0.1:8517. The local config
sets port 8517 rather than Streamlit's default 8501, which may belong to another
application. Keep the server terminal open; closing it stops the dashboard.

Known M/M/1: lambda=2/hour, service mean=20 minutes => mu=3/hour,
rho=2/3, Wq=40 minutes, Lq=4/3.
Known M/M/2: lambda=4/hour, service=20 minutes => rho=2/3,
P(wait)=8/15, Wq=16 minutes.
One doctor, arrivals [0,2,4], service [5,5,5] => starts [0,5,10],
waits [0,3,6], final departure 15, queue area 9 patient-minutes.
Two doctors => starts [0,2,5], waits [0,0,1].
Tests should also cover tied arrivals, empty/invalid input, closing-time exclusion,
unstable analytical queues, infeasible staffing, queue nonnegativity, reproducibility,
CSV parse/validation errors, identical service requirements, and doctor busy overlap.

When results look unexpected, first check time units and horizon. An unstable
analytical queue can still have a finite DES wait because only a finite cohort
arrives. A capacity improvement can miss the observed target because theory is
an expectation, not a guarantee. Change seeds to investigate sensitivity.

## Verified demonstration

The default seed-42 cohort contains 102 patients. Staffing changes from two to
four doctors; measured mean wait is 80.80 -> 2.31 minutes (97.14% reduction).
The selected analytical wait is 2.34 minutes. See README for the complete
measured comparison and caveats. The small suite contains 29 passing tests.
After hybrid integration it contained 36 passing tests; after the interactive UI
update the suite contains 41. Hybrid seed 42 yields
101.24 -> 2.32 minutes mean wait with two -> four doctors. This is a simulated
hybrid outcome, not an observed hospital comparison.

## Real-source hybrid mode

Run `python scripts\import_hangu.py` once to obtain the licensed duration extract.
The app subsequently runs offline. Source: Feng et al. (2023), HanguData Data.csv,
CC BY-NC-SA 4.0. Use only the duration field, not the source's modeling notebooks.
The import validates the authors' cleaned ServTime field, in seconds and bounded
180..3600, converts it to minutes, sorts it, and persists no other source fields.
No extra filtering or synthetic augmentation of durations is performed.

Reuse the original arrival generator without changing its random sequence:
an optional service_samples_min argument selects uniform sampling with replacement
instead of exponential service sampling. Validate a nonempty finite positive
one-dimensional sample pool. Synthetic IDs represent new simulated patients,
not source patients. Same seed and pool must produce the same cohort.

Sidebar: keep Synthetic demo as the existing default; add Hangu hybrid.
Hybrid exposes arrival rate, window, seed, and staffing, but no service-mean override.
Show duration-pool count/mean and source links, with a warning that arrival rates
are assumed and Erlang C's exponential-service assumption is not established.
Include provenance columns in input, patient, and paired CSV exports so downloads
cannot reasonably be mistaken for a real-patient queue replay.
Test source extraction units, sample membership, malformed/missing source errors,
hybrid reproducibility, unchanged synthetic output, and actual dashboard mode switching.

## Producing the project walkthrough

Recording tools are optional and separate from app dependencies:
Playwright captures the actual browser, imageio-ffmpeg supplies an encoder,
and Windows System.Speech produces standard Microsoft Zira Desktop narration.
No cloned voice or external speech API is involved.

1. Install requirements-video.txt and Playwright Chromium.
2. Start Streamlit on port 8517.
3. Run scripts\record_walkthrough.py from a second terminal.
4. The recorder reads scripts\video_narration.json, generates temporary speech
   segments, and records real UI interactions with chapter-summary overlays.
5. It synchronizes those segments to their chapter start times, exports an MP4,
   a transcript, summary-caption SRT, source screenshots, and verification JSON.
6. It checks the requested 180..300 second duration, 1600x900 dimensions, audible
   narration, and full decode. Temporary browser recordings and WAVs are cleaned up.

Use browser labels rather than raw styled radio inputs for pointer interaction.
After changing presets/data sources, wait for the visible settings to update
before pressing Run comparison: Streamlit callbacks run asynchronously.
The recorder also checks reproducible results and exercises an actual CSV download.
The optional recording tools are not imported by the dashboard or model modules.
