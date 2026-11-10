from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from hospital.data import generate_patients, load_csv, load_hangu_durations
from hospital.queueing import recommend_staffing
from hospital.simulation import SimulationResult, simulate

st.set_page_config(page_title="PatientFlow | Clinic planning", page_icon="🏥", layout="wide")
COLORS = {"Current": "#64748b", "Recommended": "#0d9488"}
st.markdown(
    """
    <style>
    .stApp { background: #f5f7fb; }
    h1, h2, h3 { color: #102a43; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #dce5ef;
        padding: 1rem; border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] { color: #526477; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("PatientFlow")
st.caption("Outpatient staffing and waiting-time comparison")


def load_preset(busy: bool = False) -> None:
    values = {
        "data_source": "Synthetic demo", "hours": 8.0, "baseline_count": 2,
        "maximum_count": 6, "target": 5.0, "arrival_rate": 18.0 if busy else 12.0,
        "mean_service": 12.0, "seed": 42,
    }
    for key, value in values.items():
        st.session_state[key] = value


with st.sidebar:
    st.header("Clinic settings")
    st.caption("Change the settings, then run a comparison.")
    presets = st.columns(2)
    presets[0].button("Load demo", on_click=load_preset, width="stretch")
    presets[1].button("Busy clinic", on_click=load_preset, args=(True,), width="stretch")
    source = st.radio("Patient data", ["Synthetic demo", "Hangu hybrid", "Upload CSV"], key="data_source")
    run_clicked = st.button("Run comparison", type="primary", width="stretch", key="run_comparison")
    hours = st.number_input("Arrival window (hours)", min_value=0.25, max_value=24.0, value=8.0, step=0.25, key="hours")
    baseline_count = st.number_input("Current doctors", min_value=1, max_value=50, value=2, step=1, key="baseline_count")
    maximum_count = st.number_input("Maximum available doctors", min_value=1, max_value=50, value=6, step=1, key="maximum_count")
    target = st.number_input("Average-wait target (minutes)", min_value=0.0, max_value=120.0, value=5.0, step=1.0, key="target")
    closing = hours * 60
    upload = None
    if source in ("Synthetic demo", "Hangu hybrid"):
        arrival_rate = st.number_input("Arrivals per hour", min_value=0.1, max_value=120.0, value=12.0, step=0.5, key="arrival_rate")
        if source == "Synthetic demo":
            mean_service = st.number_input("Mean consultation (minutes)", min_value=0.5, max_value=120.0, value=12.0, step=0.5, key="mean_service")
        with st.expander("Reproducibility"):
            seed = st.number_input("Random seed", min_value=0, max_value=2**32 - 1, value=42, step=1, key="seed")
        if source == "Synthetic demo":
            st.caption("Independent exponential arrivals and consultations; illustrative, not calibrated.")
        else:
            st.caption("Assumed exponential arrivals; consultations resampled from Hangu duration estimates.")
    else:
        upload = st.file_uploader("Patient CSV (2 MB / 10,000 rows)", type=["csv"])
        st.caption("Required: patient_id, arrival_min, service_min. No names or medical information.")
        st.download_button(
            "Download sample input",
            Path(__file__).with_name("data").joinpath("sample_patients.csv").read_bytes(),
            "sample_patients.csv",
            "text/csv",
        )
    st.divider()
    st.caption("One shared queue. Doctors work until all admitted patients finish.")

if source == "Upload CSV" and upload is None:
    st.info("Upload a CSV to begin, or choose Synthetic demo. The sidebar offers a tiny example.")
    st.stop()

settings = {
    "source": source, "hours": hours, "baseline_count": baseline_count,
    "maximum_count": maximum_count, "target": target,
    "arrival_rate": arrival_rate if source != "Upload CSV" else None,
    "mean_service": mean_service if source == "Synthetic demo" else None,
    "seed": seed if source != "Upload CSV" else None,
    "upload": upload.getvalue() if upload is not None else None,
}
if run_clicked or "comparison_result" not in st.session_state:
    try:
        service_pool = None
        if source == "Synthetic demo":
            patients = generate_patients(arrival_rate, mean_service, closing, seed)
        elif source == "Hangu hybrid":
            service_pool = load_hangu_durations()
            patients = generate_patients(
                arrival_rate, float(service_pool.mean()), closing, seed,
                service_samples_min=service_pool,
            )
        else:
            if upload is None:
                raise ValueError("Select a CSV file.")
            patients = load_csv(upload.getvalue(), closing)
        recommendation = recommend_staffing(
            len(patients) / hours, float(patients["service_min"].mean()),
            baseline_count, maximum_count, target,
        )
        baseline = simulate(patients, baseline_count, closing, target)
        improved = simulate(patients, recommendation.doctors, closing, target)
    except ValueError as error:
        st.error(f"Scenario cannot run: {error}")
        st.stop()
    st.session_state.comparison_result = (
        settings, patients, recommendation, baseline, improved, service_pool,
    )

saved_settings, patients, recommendation, baseline, improved, service_pool = st.session_state.comparison_result
if settings != saved_settings:
    st.info("Settings changed. Click Run comparison to apply them. The results below are from your last run.")
source = saved_settings["source"]
hours = saved_settings["hours"]
baseline_count = saved_settings["baseline_count"]
maximum_count = saved_settings["maximum_count"]
target = saved_settings["target"]
closing = hours * 60
observed_rate = len(patients) / hours
observed_service = float(patients["service_min"].mean())
st.caption(
    f"Last run: {source} · {hours:g}-hour arrival window · {baseline_count} current doctors · "
    f"up to {maximum_count} doctors · {target:g}-minute average-wait target"
)
if source == "Synthetic demo":
    st.caption("Synthetic demo: simulated patients, not real hospital outcomes.")
elif source == "Hangu hybrid":
    st.warning(
        "Hybrid data: real-source consultation estimates with synthetic arrivals and assumed staffing. "
        "Results are simulated, not observed hospital improvements."
    )
else:
    st.caption("Uploaded data: exact input rows are simulated. Model assumptions still need checking.")

with st.expander("Data sources and assumptions"):
    st.write("One first-come-first-served queue, equal-speed doctors, no breaks or priority triage. All admitted patients finish service.")
    st.write("Queueing predictions assume Poisson arrivals and exponential consultations. Empirical hybrid or uploaded service times may not fit: treat predictions as approximations.")
    if source == "Hangu hybrid":
        if service_pool is None:
            raise ValueError("Hybrid result is missing its source duration pool.")
        st.caption(
            f"Duration pool: {len(service_pool):,} estimates · Mean: {service_pool.mean():.2f} min · "
            "Uniform resampling with replacement; clinic session structure is not preserved."
        )
        st.markdown(
            "[Feng et al. (2023)](https://doi.org/10.3390/data8030047) · "
            "[Hangu data](https://github.com/fenghaolin/HanguData) · "
            "[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)"
        )
        st.write("Source seconds are converted to minutes. Only sorted duration estimates are stored, without patient identifiers. Arrivals are synthetic, not consultation-start timestamps.")
    st.caption(
        "No clinical validation or medical advice. A five-minute average target does not promise that every patient waits five minutes or less."
    )

base_theory = recommendation.predictions[0]
selected_theory = recommendation.predictions[-1]
if not base_theory.stable:
    st.warning(
        "Current staffing cannot keep pace with estimated arrivals. "
        "No finite long-run mean wait exists at this capacity; the finite-session simulated waits are shown below."
    )
if recommendation.target_met:
    st.success(
        f"Plan for {recommendation.doctors} doctors "
        f"(add {recommendation.doctors - baseline_count}). This is the smallest allowed count "
        f"meeting the model's average-wait target: {selected_theory.mean_wait_min:.2f} minutes."
    )
else:
    st.warning(
        f"Target not reachable within the doctor limit. Comparing with {recommendation.doctors} doctors "
        "(maximum available); the model's target is not met."
    )
if improved.metrics["mean_wait_min"] > target:
    st.warning("The improved simulated mean wait still exceeds your target. Analytical expectations are not a guarantee for this finite cohort.")

base_wait = baseline.metrics["mean_wait_min"]
new_wait = improved.metrics["mean_wait_min"]
reduction = 100 * (base_wait - new_wait) / base_wait if base_wait > 0 else None
columns = st.columns(2)
columns[0].metric("Patients served · both plans", len(patients))
columns[1].metric("Current average wait", f"{base_wait:.2f} min")
columns = st.columns(2)
columns[0].metric("Recommended average wait", f"{new_wait:.2f} min", f"{new_wait - base_wait:+.2f} min", delta_color="inverse")
columns[1].metric("Waiting-time reduction", f"{reduction:.1f}%" if reduction is not None else "N/A")
st.caption(
    f"Observed demand: {observed_rate:.2f} patients/hour · Mean consultation: {observed_service:.2f} min · "
    f"Arrival window: {hours:g} hours. Staffing uses cohort estimates, not the generator's nominal rates. "
    "All patients finish service, including after closing. Zero baseline wait makes percentage reduction undefined."
)


def show_chart(fig: go.Figure) -> None:
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial", "color": "#334155"},
        margin={"l": 20, "r": 20, "t": 50, "b": 25},
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")


def comparison_table(first: SimulationResult, second: SimulationResult) -> pd.DataFrame:
    labels = {
        "mean_wait_min": "Mean wait (min)",
        "median_wait_min": "Median wait (min)",
        "p95_wait_min": "95th-percentile wait (min)",
        "within_target_pct": "Patients starting within target (%)",
        "max_queue": "Peak waiting queue (patients)",
        "mean_queue": "Time-average queue · full session",
        "window_mean_queue": "Time-average queue · arrival window",
        "utilization_pct": "Mean doctor utilization · full session (%)",
        "window_utilization_pct": "Mean doctor utilization · arrival window (%)",
        "overtime_min": "Time beyond closing (min)",
        "horizon_min": "Full-session observation duration (min)",
    }
    return pd.DataFrame(
        [
            {"Metric": label, "Current": first.metrics[key], "Recommended": second.metrics[key]}
            for key, label in labels.items()
        ]
    )


comparison, guide = st.tabs(["Waiting times", "How it works"])
with comparison:
    st.subheader("Compare the two staffing plans")
    wait_summary = pd.DataFrame(
        [
            {"Scenario": name, "Statistic": label, "Minutes": result.metrics[key]}
            for name, result in [("Current", baseline), ("Recommended", improved)]
            for label, key in [("Mean", "mean_wait_min"), ("Median", "median_wait_min"), ("95th percentile", "p95_wait_min")]
        ]
    )
    left, right = st.columns(2)
    with left:
        show_chart(px.bar(wait_summary, x="Statistic", y="Minutes", color="Scenario", barmode="group",
                          color_discrete_map=COLORS, title="Waiting-time comparison"))
    with right:
        distribution = pd.concat(
            [baseline.patients.assign(Scenario="Current"), improved.patients.assign(Scenario="Recommended")],
            ignore_index=True,
        )
        show_chart(px.box(distribution, x="Scenario", y="wait_min", color="Scenario",
                          labels={"wait_min": "Wait (minutes)"}, color_discrete_map=COLORS,
                          title="Patient waiting distribution", points=False))
    st.caption("Both plans use exactly the same patients and consultation durations. Only doctor count changes.")
    with st.expander("Detailed results"):
        st.dataframe(comparison_table(baseline, improved).round(2), hide_index=True, width="stretch")
    st.caption(
        "Mean/median/p95 wait cover the whole patient cohort. Queue and utilization are time-weighted. "
        "Full-session duration is the later of closing or final departure, separately for each scenario. "
        "Arrival-window metrics use the same fixed duration and allow a like-for-like capacity comparison."
    )

with guide:
    st.subheader("How the comparison is calculated")
    st.markdown(
        """
        **1 · M/M/c queueing theory** estimates the steady-state mean waiting time
        for a shared queue: independent Poisson arrivals, independent exponential
        consultations, and **c** equal-speed continuously available doctors.

        **2 · Discrete-event simulation** follows actual arrivals, consultation
        starts and departures. Each patient uses the earliest free doctor under
        first-come-first-served order. It tests a finite cohort starting with an
        empty clinic; no patient is dropped.
        """
    )
    st.latex(r"\mu = 60/\overline{s},\quad a=\lambda/\mu,\quad \rho=\lambda/(c\mu)")
    st.latex(r"P_0=\left[\sum_{n=0}^{c-1}\frac{a^n}{n!}+\frac{a^c}{c!(1-\rho)}\right]^{-1}")
    st.latex(r"P(\mathrm{wait})=\frac{a^cP_0}{c!(1-\rho)},\quad W_q=\frac{P(\mathrm{wait})}{c\mu-\lambda},\quad L_q=\lambda W_q")
    st.caption("Rates lambda and mu are per hour; Wq above is in hours and is converted to minutes in the dashboard. Formulas require rho < 1.")
    st.markdown(
        """
        **Decision rule:** try integer doctor counts from baseline to the allowed
        maximum. Choose the smallest stable count with predicted mean wait at or
        below the target. If none qualifies, show infeasibility and test maximum
        capacity instead. This is staffing enumeration, not an extra claimed OR technique.

        **Fair comparison:** both scenarios have identical arrival times and
        consultation requirements. Improvements come only from additional capacity.
        More doctors may be costly; staffing cost is not optimized here.

        **Why predictions differ:** theory is an infinite-horizon stationary
        expectation; simulation starts empty, runs one finite cohort, and may
        finish after closing. Uploaded data may not follow exponential assumptions.
        A mean target does not guarantee that every patient meets it.

        **Data provenance:** Synthetic demo remains fully synthetic. Hangu hybrid
        resamples the authors' cleaned consultation-duration estimates from
        [Hangu outpatient data](https://github.com/fenghaolin/HanguData), with
        **synthetic arrivals**, not consultation-start timestamps used as arrivals.
        Source ServTime is seconds, divided by 60. The authors retain durations
        from 3 to 60 minutes; only sorted durations are bundled, no identifiers
        or demographic/diagnosis fields. Attribution: Feng et al. (2023),
        DOI 10.3390/data8030047, **CC BY-NC-SA 4.0** (noncommercial, attribution,
        share-alike for adapted data). Source end times/durations are estimates,
        and resampling ignores within-session dependencies.
        Total hospital length of stay is not a substitute for doctor consultation time.

        **Scope:** one outpatient consultation stage, constant doctor availability,
        no emergencies, breaks, shifts, registration, no-shows, or clinical decisions.
        Try several seeds and realistic locally validated inputs before drawing conclusions.
        """
    )
st.caption("PatientFlow · Educational outpatient planning · Queueing theory and simulation")
