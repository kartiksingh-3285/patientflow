# Beginner-friendly implementation plan

## Project title

**Design and Develop Two Operations Research Techniques to Reduce Patient Wait Times**

Application name: **PatientFlow**

## 1. What problem are we solving?

Imagine a clinic where patients arrive throughout the day, but only two doctors
are available. If patients arrive faster than the doctors can finish consultations,
a waiting queue builds up.

Our project answers three questions:

1. How long might patients wait with the current number of doctors?
2. How many doctors should be available to meet an average-waiting-time target?
3. What happens when we test that recommendation on the same patients?

We model **one outpatient consultation queue**, not every department in a hospital.
This is an educational planning tool, not a medical decision or emergency-triage system.

## 2. What will the application do?

The user will enter:
- The number of hours during which patients can arrive.
- The current number of doctors.
- The maximum number of doctors that could be made available.
- A target for average waiting time, such as five minutes.
- Patient data, or settings for generating simulated patients.

The application will then:
1. Check that the inputs are valid.
2. Estimate patient demand and doctor service capacity.
3. Recommend a doctor count.
4. Simulate the current and recommended staffing.
5. Display waiting times, queue lengths, doctor utilization, and time beyond closing.
6. Allow the user to download the results.

**Important:** the project improves capacity by changing doctor count. It does not
optimize appointment times, build a shift roster, or reduce consultation durations.

## 3. Which two OR techniques will we use?

Operations Research, or **OR**, uses mathematics to make better decisions about
limited resources. Here, the limited resource is available doctors.

### Technique 1: M/M/c queueing theory

**In simple words:** use mathematical formulas to estimate how a waiting queue
behaves for a given arrival rate, consultation speed, and number of doctors.

The model name means:
- First **M**: arrivals follow a Poisson process. In our synthetic model, this means
  the time between arrivals is sampled from an exponential distribution.
- Second **M**: consultation durations follow an exponential distribution.
- **c**: the number of doctors serving a shared queue.

An exponential distribution allows varying durations: many are short, while some
are much longer. It is a modeling assumption, not a statement about every real clinic.

We use the **Erlang C formula** to estimate average waiting time. We then try doctor
counts one by one and select the smallest allowed count meeting the target.

**Why choose it?**
- It makes the relationship between demand and capacity easy to explain.
- It gives a clear mathematical reason for adding doctors.
- It uses standard mathematical formulas without a separate optimization solver.

### Technique 2: discrete-event simulation

**In simple words:** create a virtual clinic and follow each patient's journey:

```text
Patient arrives -> waits if necessary -> sees a doctor -> leaves
```

An **event** is something happening at a particular time, such as a patient arriving
or a consultation ending. The simulation works with these times rather than checking
every second of the day.

Patients are served **first-come-first-served (FCFS)**: the patient who arrives first
gets the next available doctor. Patients arriving together keep their input order.

**Why choose it?**
- We can calculate waiting time for each patient.
- We can draw the queue over time.
- We can test the recommendation on a finite clinic day.
- We can use uploaded or real-source consultation durations without making them exponential.

### How the two techniques work together

```text
Queueing theory recommends capacity.
Simulation tests the recommendation.
The dashboard compares the results.
```

Trying whole-number doctor counts is a simple decision rule within our queueing
approach. We do not claim it as a third technique or an integer-programming solver.

Random sampling creates the simulation inputs; the calculations use the two
mathematical techniques described above.

## 4. What data will we use?

The application supports three modes:

| Mode | Arrival times | Consultation durations |
|---|---|---|
| Synthetic demo | Randomly generated | Randomly generated |
| Hangu hybrid | Randomly generated | Resampled from real-source duration estimates |
| Upload CSV | Supplied by the user | Supplied by the user |

### A. Synthetic demo

Synthetic means **created for the experiment**, not collected from actual patients.

Default settings:

| Setting | Value |
|---|---:|
| Nominal patient arrival rate | 12 patients/hour |
| Nominal mean consultation time | 12 minutes |
| Arrival window | 8 hours |
| Baseline doctors | 2 |
| Maximum available doctors | 6 |
| Average-wait target | 5 minutes |
| Random seed | 42 |

The **random seed** makes the generated data reproducible. Using the same seed and
settings produces the same patients. A different seed produces another experiment.
These values are illustrative assumptions, not measured hospital statistics.

### B. Hangu hybrid: real-source durations with synthetic arrivals

We identified the public **Hangu outpatient dataset**:
- [Dataset repository](https://github.com/fenghaolin/HanguData)
- [Feng et al. (2023) research paper](https://doi.org/10.3390/data8030047)
- [Dataset archive](https://doi.org/10.5281/zenodo.7484205)

Our project uses **6,637 consultation-duration estimates** from the authors'
cleaned dataset. Their mean is approximately **13.365 minutes**.

Preparation:
1. Use the authors' cleaned dataset, not its larger intermediate version.
2. Read only the `ServTime` field.
3. Convert seconds to minutes: `service_min = ServTime / 60`.
4. Keep all cleaned duration estimates and sort the extracted values.
5. Discard source patient identifiers, row order, demographic, address, and diagnosis fields.
6. Save the duration-only file locally, together with attribution and license information.

The authors' cleaning retains durations between 180 and 3,600 seconds
(3 to 60 minutes), and records with a nonmissing visit count. We add no further
duration filtering. Units were checked against their published processing code.

For each new simulated patient, randomly choose one duration from this local list.
Every entry has equal chance of selection, and the same entry can be chosen again.
This is called **sampling with replacement**.

**What must we explain honestly?**
- These are real-source duration estimates, not precise stopwatch measurements.
- We do not have the clinic-arrival timestamps needed to replay a real patient queue.
- Arrival times, arrival rate, doctor staffing, and opening window remain assumptions.
- Consultation-start times must not be treated as patient-arrival times.
- Resampling does not preserve the original clinic sessions or patient differences.
- Erlang C is only a mean-based approximation here: the real-source durations are
  not assumed to follow an exponential distribution.
- The waiting-time improvements are simulated, not observed hospital improvements.

The data license is **CC BY-NC-SA 4.0**: attribution, noncommercial use, and
share-alike requirements for adapted data. Preserve the source license and citation.
The importer records the source revision and file hashes, which are fingerprints
used to check that the bundled extract has not changed.
The app runs offline after the import and uses only the extracted duration values.

### C. Upload a CSV

A CSV is a simple spreadsheet saved as comma-separated text. It must include:

| Column | Meaning | Rule |
|---|---|---|
| `patient_id` | A non-identifying patient label | Unique and nonblank |
| `arrival_min` | Minutes after opening when the patient arrives | At least 0, strictly before closing |
| `service_min` | Consultation duration in minutes | Greater than 0 |

Example:

```csv
patient_id,arrival_min,service_min
P001,0,5
P002,2,5
P003,4,5
```

`P002` arrives two minutes after opening and needs a five-minute consultation.
Do not include names, diagnoses, or other sensitive information.

Reject empty files, missing columns, duplicate headers/IDs, mismatched row field
counts, invalid numbers, missing numeric values, and arrivals outside the window.
Limit uploads to 2 MB and 10,000 patients. Errors should be visible, not silently ignored.

## 5. Our clinic assumptions

To keep the project understandable:
- There is one shared queue and one consultation stage.
- All doctors are modeled as equal-speed resources.
- All selected doctors are available from opening until the admitted patients finish.
- There are no breaks, shifts, emergencies, or priority patients.
- No new patients arrive at or after closing.
- Every patient arriving before closing is served, even if service finishes later.
- The clinic starts with an empty queue.
- Uploaded rows are simulated exactly, although queueing-theory assumptions may not fit them.

The **arrival window** is when patients can enter. The **full session** lasts until
the later of closing time or the final patient's departure.

## 6. Understanding the mathematics

### Step 1: estimate the arrival rate

```text
lambda = number of patients / arrival-window hours
```

Example: 96 patients over eight hours means `lambda = 12 patients/hour`.
Use the entire configured window, not the time of the final arrival.

### Step 2: estimate one doctor's service rate

```text
mu = 60 / average consultation minutes
```

Example: a 12-minute average consultation means one doctor can serve approximately
`60 / 12 = 5 patients/hour`.

The application uses the generated/uploaded cohort's actual sample mean, so its
estimated rate can differ from the nominal synthetic setting.

### Step 3: check whether capacity is enough

```text
total capacity = c * mu
rho = lambda / (c * mu)
```

`rho` is demand divided by service capacity.

Example: 12 arrivals/hour and two doctors serving five patients/hour each:

```text
capacity = 2 * 5 = 10 patients/hour
rho = 12 / 10 = 1.2
```

Demand exceeds capacity. In the steady-state mathematical model, no finite
average waiting time exists when `rho >= 1`.

**Do not show this as zero waiting.** A finite simulation still produces finite
waits because arrivals eventually stop.

### Step 4: calculate expected waiting with Erlang C

These formulas are evaluated only when `rho < 1`.

| Symbol | Meaning |
|---|---|
| `lambda` | Patient arrivals per hour |
| `mu` | Patients served per hour by one doctor |
| `c` | Number of doctors |
| `a` | Offered load, calculated as `lambda / mu` |
| `P0` | Probability that the system is empty |
| `P(wait)` | Probability an arriving patient must wait |
| `Wq` | Expected time waiting before consultation |
| `Lq` | Expected number of patients waiting |
| `W` | Expected total time waiting plus consultation |

```text
a = lambda / mu
rho = a / c

P0 = 1 / [sum from n=0 to c-1 of (a^n / n!)
          + a^c / (c! * (1-rho))]

P(wait) = [a^c / (c! * (1-rho))] * P0
Wq_hours = P(wait) / (c*mu - lambda)
Wq_minutes = 60 * Wq_hours
Lq = lambda * Wq_hours
W_hours = Wq_hours + 1/mu
```

Here, `n!` means factorial; for example, `3! = 3 * 2 * 1 = 6`.
The summation means add one term for each whole-number value of `n`.

You do not need to memorize the full formula for a presentation. Explain its
inputs, outputs, and stability condition, then demonstrate a checked example:

> One doctor, two arrivals/hour, and 20-minute average consultations gives a
> service rate of three patients/hour and an expected wait of 40 minutes.

In code, build successive terms using `term = term * a / n` rather than large
powers and factorials. This is the same calculation in a numerically safer form.

### Step 5: select a doctor count

```text
For each doctor count from baseline to maximum:
    Calculate the queueing-theory prediction.
    If stable and predicted average wait <= target:
        Select this count and stop.

If no count qualifies:
    Clearly report that the target is infeasible within the limit.
    Simulate the maximum count, without calling the target achieved.
```

The recommendation never reduces staffing below the baseline.
An average-wait target does **not** mean every patient waits less than that target.
With positive demand, exactly zero expected Erlang C wait cannot be achieved with
a finite doctor count.

## 7. How the simulation works

For each patient, find the doctor who will become available earliest:

```text
consultation start = later of patient arrival and doctor availability
waiting time = consultation start - arrival time
consultation end = consultation start + consultation duration
doctor becomes available again at consultation end
```

A small priority queue, implemented with Python's `heapq`, keeps track of the
earliest available doctor. It is just a convenient way to find the smallest time.

### Example you can calculate by hand

Use the three CSV rows above and one doctor:

| Patient | Arrives | Consultation starts | Leaves | Waits |
|---|---:|---:|---:|---:|
| P001 | 0 | 0 | 5 | 0 |
| P002 | 2 | 5 | 10 | 3 |
| P003 | 4 | 10 | 15 | 6 |

All times are minutes after opening.

```text
Average wait = (0 + 3 + 6) / 3 = 3 minutes
```

With two doctors, starts are `0, 2, 5` and waits are `0, 0, 1`.
Average wait becomes approximately **0.33 minutes**.

**Fair comparison:** create the patient cohort once, then use exactly the same
arrival times and consultation durations in both scenarios. Never generate new
patients or resample service times between baseline and improved staffing.

## 8. What results should we display?

| Metric | Beginner-friendly meaning |
|---|---|
| Patient count | How many admitted patients finish consultation |
| Mean wait | Total patient waiting minutes divided by patient count |
| Median wait | The middle waiting time after sorting |
| 95th-percentile wait | A value at or below which approximately 95% of waits fall |
| Within-target percentage | Percentage of patients whose individual wait is within the target |
| Peak queue | Largest number waiting, excluding patients in consultation |
| Time-average queue | Queue size averaged over elapsed time |
| Doctor utilization | Percentage of observation time each doctor is busy |
| Time beyond closing | Minutes needed after closing to finish the cohort |

Calculate time-average queue using **patient-minutes**, not the simple average
of recorded queue counts:

```text
If 3 patients wait for 10 minutes:
    queue area = 3 * 10 = 30 patient-minutes

time-average queue = total queue area / observation minutes
doctor utilization (%) = 100 * busy minutes / observation minutes
```

Report queue and utilization separately for:
1. The fixed arrival window, shared by both scenarios.
2. Each scenario's full session, including time beyond closing.

Busy time within the arrival window counts only the part of each consultation
before closing. Mean patient wait still includes the whole admitted cohort.
Group events happening at the same time and draw queue charts as horizontal steps.

Useful correctness check:

```text
Full-session queue area = sum of all patient waiting times
```

To calculate improvement:

```text
Reduction (%) = 100 * (baseline mean wait - improved mean wait)
                     / baseline mean wait
```

If baseline mean wait is zero, show percentage reduction as not applicable.
Report actual results honestly, even if there is no improvement or a target is missed.

## 9. Simple system structure

```text
User chooses settings/data in Streamlit
                 |
                 v
Load or generate patients and validate inputs
                 |
                 v
Queueing theory recommends doctor capacity
                 |
                 v
Simulate baseline and recommended doctors on the same cohort
                 |
                 v
Show comparison tables, charts, explanations, and CSV downloads
```

### Tools and file responsibilities

| Tool/file | Responsibility |
|---|---|
| Python | Core calculations and simulation |
| Streamlit | Interactive local dashboard |
| NumPy | Reproducible random sampling |
| Pandas | Read, validate, and organize tables |
| Plotly | Interactive charts |
| [app.py](app.py) | Connect controls, models, results, and downloads |
| [hospital/data.py](hospital/data.py) | Validate inputs, generate patients, load Hangu durations |
| [hospital/queueing.py](hospital/queueing.py) | Erlang C formulas and doctor-count search |
| [hospital/simulation.py](hospital/simulation.py) | Patient service events and measured metrics |
| [scripts/import_hangu.py](scripts/import_hangu.py) | Explicit one-time import of source durations |
| [tests/](tests/) | Mathematical, input, simulation, and dashboard checks |

Keep modules small and readable. No database, backend service, or separate
optimization solver is needed. See [builder.md](builder.md) for detailed construction
instructions and [README.md](README.md) for installation and usage.

## 10. Step-by-step implementation roadmap

This is a beginner's build order. The application is already implemented; use
these steps to understand, reproduce, or extend it.

### Step 1: establish the design before coding

Prepare this plan, [builder.md](builder.md), and [README.md](README.md).
Confirm the two techniques, data origins, scope, and assumptions.

**Deliverable:** a clear explanation of what the project will and will not do.

### Step 2: prepare the Python environment

Create a virtual environment, which keeps project packages separate from other
Python projects. Install the existing [requirements.txt](requirements.txt).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Deliverable:** Python can import Streamlit, NumPy, Pandas, and Plotly.

### Step 3: prepare and check input data

Implement CSV validation and reproducible synthetic generation.
For hybrid mode, import the duration-only Hangu extract with attribution, then
load it locally. Show a clear error if the source extract is missing or damaged.
If random generation produces no arrivals, ask the user to change settings or seed;
do not invent a patient.

**Deliverable:** a validated table with patient ID, arrival minute, and service minute.

### Step 4: implement queueing theory

Calculate arrival rate, mean service time, capacity, stability, and Erlang C waiting.
Check a known answer before adding staffing recommendations.

**Deliverable:** a function returning an explainable prediction for a doctor count.

### Step 5: implement the staffing decision

Try counts from baseline to maximum. Stop at the first qualifying count.
Handle an infeasible target explicitly.

**Deliverable:** selected doctor count, target-feasibility flag, and prediction table.

### Step 6: implement patient simulation

Start with the three-patient hand example. Track each doctor's availability,
then calculate patient start/end/wait times, queue events, and busy time.

**Deliverable:** per-patient results and correct time-weighted metrics.

### Step 7: connect baseline and improved scenarios

Pass the same validated cohort to both simulations. Check that patient counts,
arrival times, and service requirements are identical.

**Deliverable:** a fair before-and-after comparison.

### Step 8: build the dashboard

Add sidebar controls and four result areas:
1. Waiting times and comparison.
2. Queues and doctors.
3. Patient records and downloads.
4. Plain-language explanations of the OR techniques.

Use clear units, readable KPI cards, and consistent colors. Label synthetic,
hybrid, and uploaded data. Include data-origin labels in exported CSVs.
Add practical presets and Run comparison. Let users edit several settings before
running, clearly distinguish pending edits from the last successful results,
and keep those results' original data labels. Patient searches and chart controls
should not rerun or change the cohort.

**Deliverable:** an intuitive dashboard understandable without OR experience.

### Step 9: test the complete application

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app.py hospital scripts tests
```

Check formulas, invalid inputs, unstable queues, infeasible staffing, hand-calculated
waits, source units, reproducibility, nonoverlapping doctor assignments, and queue-area
conservation. Use Streamlit AppTest for real dashboard control changes.

**Deliverable:** passing tests and no Python compilation errors.

### Step 10: run locally and record measured results

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://127.0.0.1:8517`. Keep the server terminal open while using the
application. The project uses port 8517 to avoid other applications on 8501.
Try all data modes and test downloads.
Record actual measurements in the README rather than inventing sample results.

**Deliverable:** a working local application and reproducible presentation examples.

## 11. Verified demonstration results

Both examples below use an eight-hour arrival window, nominal demand of 12
patients/hour, seed 42, two baseline doctors, maximum six, and a five-minute mean target.

| Result | Synthetic demo | Hangu hybrid |
|---|---:|---:|
| Simulated patients served in each scenario | 102 | 102 |
| Recommended doctors | 4 | 4 |
| Baseline simulated mean wait | 80.80 min | 101.24 min |
| Improved simulated mean wait | 2.31 min | 2.32 min |
| Mean-wait reduction | 97.14% | 97.71% |

Synthetic mode additionally uses a nominal 12-minute mean consultation setting.
Hybrid mode samples the source duration pool without changing its values.
These results are for particular simulated cohorts, not real hospital benefit claims.
The full project has **41 passing automated tests**, including the interactive
UI's explicit-run behavior, presets, patient filters, and chart controls.

## 12. Expected outcomes and limitations

### What success looks like

- The project demonstrates two OR techniques working together.
- The user can identify when demand is too high for current capacity.
- The doctor recommendation has a clear mathematical explanation.
- The dashboard shows the measured effect on the same patients.
- A beginner can explain the three-patient example and the larger demonstration.

### What the project does not prove

Theory describes a **steady-state expectation**, meaning long-run behavior under
unchanging model conditions. Simulation measures **one finite cohort** that starts
with an empty clinic. Their waiting times need not match.

The project does not include emergency priorities, multiple departments, doctor
breaks/shifts, appointment no-shows, different doctor speeds, staffing costs, or
statistical confidence intervals. It is not empirically validated for deployment.

More doctors may reduce waiting but also cost more. This project selects the smallest
count meeting the analytical target; it does not minimize financial cost.

Future work could add repeated experiments with different seeds, uncertainty
intervals, locally verified arrival/service data, staffing costs, and shift availability.

## 13. A short explanation for your presentation

> "Our project uses queueing theory to estimate waiting time and recommend doctor
> capacity. We then use discrete-event simulation to test current and recommended
> staffing on identical patients. The dashboard compares waiting time, queue size,
> and utilization. We support fully synthetic data and a clearly labeled hybrid
> mode using Hangu consultation-duration estimates with synthetic arrivals.
> The project uses mathematical capacity estimates and patient-flow simulation."
