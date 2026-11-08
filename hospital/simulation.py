from dataclasses import dataclass
import heapq

import numpy as np
import pandas as pd

from hospital.data import require_integer, require_number, validate_patients


@dataclass(frozen=True)
class SimulationResult:
    patients: pd.DataFrame
    queue: pd.DataFrame
    doctors: pd.DataFrame
    metrics: dict[str, float]


def simulate(
    patients: pd.DataFrame, doctors: int, closing_min: float, target_min: float = 5
) -> SimulationResult:
    cohort = validate_patients(patients, closing_min)
    count = require_integer(doctors, "Doctors", 1, 50)
    closing = require_number(closing_min, "Arrival window")
    target = require_number(target_min, "Mean-wait target", allow_zero=True)
    available = [(0.0, doctor) for doctor in range(1, count + 1)]
    heapq.heapify(available)
    records: list[dict[str, object]] = []
    for patient in cohort.itertuples(index=False):
        free_at, doctor = heapq.heappop(available)
        start = max(float(patient.arrival_min), free_at)
        end = start + float(patient.service_min)
        if not np.isfinite(end):
            raise ValueError("Service durations overflowed the simulation clock. Use smaller values.")
        records.append(
            {
                "patient_id": patient.patient_id,
                "arrival_min": patient.arrival_min,
                "service_min": patient.service_min,
                "doctor": doctor,
                "start_min": start,
                "end_min": end,
                "wait_min": start - patient.arrival_min,
            }
        )
        heapq.heappush(available, (end, doctor))
    results = pd.DataFrame(records)
    horizon = max(closing, float(results["end_min"].max()))
    waiting = results.loc[results["wait_min"] > 0]
    events = pd.concat(
        [
            pd.DataFrame({"time_min": waiting["arrival_min"], "change": 1}),
            pd.DataFrame({"time_min": waiting["start_min"], "change": -1}),
            pd.DataFrame({"time_min": [0.0, closing, horizon], "change": 0}),
        ],
        ignore_index=True,
    )
    queue = events.groupby("time_min", as_index=False)["change"].sum()
    queue["queue_length"] = queue["change"].cumsum()
    queue = queue.loc[:, ["time_min", "queue_length"]]
    times = queue["time_min"].to_numpy()
    lengths = queue["queue_length"].to_numpy()[:-1]
    queue_area = float(np.dot(np.diff(times), lengths))
    window_area = float(np.dot(np.diff(np.minimum(times, closing)), lengths))

    doctor_rows = []
    for doctor in range(1, count + 1):
        assignments = results.loc[results["doctor"] == doctor]
        busy = float(assignments["service_min"].sum())
        window_busy = float(
            np.maximum(
                0,
                np.minimum(assignments["end_min"].to_numpy(), closing)
                - assignments["start_min"].to_numpy(),
            ).sum()
        )
        doctor_rows.append(
            {
                "doctor": f"Doctor {doctor}",
                "patients": len(assignments),
                "busy_min": busy,
                "window_busy_min": window_busy,
                "utilization_pct": 100 * busy / horizon,
                "window_utilization_pct": 100 * window_busy / closing,
            }
        )
    doctor_table = pd.DataFrame(doctor_rows)
    waits = results["wait_min"]
    metrics = {
        "patients": float(len(results)),
        "mean_wait_min": float(waits.mean()),
        "median_wait_min": float(waits.median()),
        "p95_wait_min": float(waits.quantile(0.95)),
        "within_target_pct": float(100 * (waits <= target).mean()),
        "max_queue": float(queue["queue_length"].max()),
        "mean_queue": queue_area / horizon,
        "window_mean_queue": window_area / closing,
        "queue_area": queue_area,
        "utilization_pct": float(doctor_table["utilization_pct"].mean()),
        "window_utilization_pct": float(doctor_table["window_utilization_pct"].mean()),
        "overtime_min": max(0.0, horizon - closing),
        "horizon_min": horizon,
    }
    return SimulationResult(results, queue, doctor_table, metrics)
