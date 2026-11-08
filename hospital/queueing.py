from dataclasses import dataclass
import math

from hospital.data import require_integer, require_number


@dataclass(frozen=True)
class QueuePrediction:
    doctors: int
    utilization: float
    stable: bool
    probability_wait: float
    mean_wait_min: float
    mean_queue: float
    mean_system_min: float


@dataclass(frozen=True)
class StaffingRecommendation:
    doctors: int
    target_met: bool
    predictions: tuple[QueuePrediction, ...]


def erlang_c(arrival_rate: float, mean_service_min: float, doctors: int) -> QueuePrediction:
    rate = require_number(arrival_rate, "Arrival rate", allow_zero=True)
    service = require_number(mean_service_min, "Mean service time")
    count = require_integer(doctors, "Doctors", 1, 50)
    mu = 60 / service
    offered_load = rate / mu
    rho = offered_load / count
    if rate == 0:
        return QueuePrediction(count, 0, True, 0, 0, 0, service)
    if rho >= 1:
        return QueuePrediction(count, rho, False, math.nan, math.inf, math.inf, math.inf)
    term = 1.0
    partial_sum = 1.0
    for n in range(1, count):
        term *= offered_load / n
        partial_sum += term
    tail = term * offered_load / count / (1 - rho)
    probability_wait = tail / (partial_sum + tail)
    wait_hours = probability_wait / (count * mu - rate)
    return QueuePrediction(
        count, rho, True, probability_wait, wait_hours * 60,
        rate * wait_hours, wait_hours * 60 + service,
    )


def recommend_staffing(
    arrival_rate: float,
    mean_service_min: float,
    baseline_doctors: int,
    max_doctors: int,
    target_min: float,
) -> StaffingRecommendation:
    baseline = require_integer(baseline_doctors, "Baseline doctors", 1, 50)
    maximum = require_integer(max_doctors, "Maximum doctors", 1, 50)
    target = require_number(target_min, "Mean-wait target", allow_zero=True)
    if maximum < baseline:
        raise ValueError("Maximum doctors cannot be below baseline doctors.")
    predictions: list[QueuePrediction] = []
    for count in range(baseline, maximum + 1):
        prediction = erlang_c(arrival_rate, mean_service_min, count)
        predictions.append(prediction)
        if prediction.stable and prediction.mean_wait_min <= target:
            return StaffingRecommendation(count, True, tuple(predictions))
    return StaffingRecommendation(maximum, False, tuple(predictions))
