import math
import csv
import hashlib
import json
from io import BytesIO, StringIO
from numbers import Integral, Real
from pathlib import Path

import numpy as np
import pandas as pd

MAX_PATIENTS = 10_000
MAX_UPLOAD_BYTES = 2_000_000
REQUIRED_COLUMNS = ("patient_id", "arrival_min", "service_min")
HANGU_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_hangu_durations() -> np.ndarray:
    try:
        content = (HANGU_DATA_DIR / "hangu_service_minutes.csv").read_bytes()
        metadata = json.loads((HANGU_DATA_DIR / "hangu_provenance.json").read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError("Cannot read Hangu data. Run python scripts\\import_hangu.py to restore it.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Hangu provenance is invalid. Re-run the import script.") from error
    if not isinstance(metadata, dict) or metadata.get("extract_sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError("Hangu extract checksum does not match provenance. Re-run the import script.")
    try:
        frame = pd.read_csv(BytesIO(content))
        if list(frame.columns) != ["service_min"]:
            raise ValueError("Hangu extract must contain only service_min.")
        samples = pd.to_numeric(frame["service_min"], errors="raise").to_numpy(dtype=float)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, TypeError, ValueError) as error:
        raise ValueError("Hangu duration extract is invalid. Re-run the import script.") from error
    if len(samples) != metadata.get("records") or len(samples) == 0:
        raise ValueError("Hangu duration count does not match provenance.")
    if not np.isfinite(samples).all() or ((samples < 3) | (samples > 60)).any():
        raise ValueError("Hangu durations must be finite and within the source's 3..60 minute bounds.")
    return samples


def require_number(value: Real, name: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a number.")
    number = float(value)
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        qualifier = "nonnegative" if allow_zero else "positive"
        raise ValueError(f"{name} must be finite and {qualifier}.")
    return number


def require_integer(value: Integral, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be a whole number.")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return int(value)


def validate_patients(patients: pd.DataFrame, closing_min: float) -> pd.DataFrame:
    closing = require_number(closing_min, "Arrival window")
    missing = set(REQUIRED_COLUMNS) - set(patients.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}.")
    if patients.columns.duplicated().any():
        raise ValueError("CSV column names must be unique.")
    if not 1 <= len(patients) <= MAX_PATIENTS:
        raise ValueError(f"Provide between 1 and {MAX_PATIENTS:,} patient rows.")
    clean = patients.loc[:, list(REQUIRED_COLUMNS)].copy()
    if clean["patient_id"].isna().any():
        raise ValueError("Every patient_id must be nonblank.")
    clean["patient_id"] = clean["patient_id"].astype(str).str.strip()
    if clean["patient_id"].eq("").any() or clean["patient_id"].duplicated().any():
        raise ValueError("Patient IDs must be unique and nonblank.")
    for column in ("arrival_min", "service_min"):
        if clean[column].map(lambda value: isinstance(value, (bool, np.bool_))).any():
            raise ValueError(f"{column} must contain numbers, not booleans.")
        try:
            clean[column] = pd.to_numeric(clean[column], errors="raise").astype(float)
        except (ValueError, TypeError) as error:
            raise ValueError(f"{column} must contain valid numbers.") from error
        if not np.isfinite(clean[column].to_numpy()).all():
            raise ValueError(f"{column} must contain finite numbers without missing values.")
    if ((clean["arrival_min"] < 0) | (clean["arrival_min"] >= closing)).any():
        raise ValueError("Arrival minutes must be >= 0 and strictly before closing.")
    if (clean["service_min"] <= 0).any():
        raise ValueError("Service minutes must be strictly positive.")
    return clean.sort_values("arrival_min", kind="stable").reset_index(drop=True)


def load_csv(content: bytes, closing_min: float) -> pd.DataFrame:
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("CSV exceeds the 2 MB upload limit.")
    try:
        reader = csv.reader(StringIO(content.decode("utf-8-sig")), strict=True)
        header = next(reader, [])
        if len(header) != len(set(header)):
            raise ValueError("CSV column names must be unique.")
        row_count = 0
        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f"CSV row {line_number} has a different field count than its header.")
            row_count += 1
            if row_count > MAX_PATIENTS:
                raise ValueError(f"Provide between 1 and {MAX_PATIENTS:,} patient rows.")
        patients = pd.read_csv(
            BytesIO(content),
            dtype={"patient_id": "string"},
            keep_default_na=False,
            nrows=MAX_PATIENTS + 1,
        )
    except (csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as error:
        raise ValueError("Cannot read CSV. Provide a UTF-8 comma-separated file with headers.") from error
    return validate_patients(patients, closing_min)


def generate_patients(
    arrival_rate: float, mean_service_min: float, closing_min: float, seed: int,
    *, service_samples_min: np.ndarray | None = None,
) -> pd.DataFrame:
    rate = require_number(arrival_rate, "Arrival rate")
    service = require_number(mean_service_min, "Mean service time")
    closing = require_number(closing_min, "Arrival window")
    seed = require_integer(seed, "Random seed", 0, 2**32 - 1)
    if service_samples_min is not None:
        try:
            samples = np.asarray(service_samples_min, dtype=float)
        except (ValueError, TypeError) as error:
            raise ValueError("Service sample pool must contain numbers.") from error
        if samples.ndim != 1 or samples.size == 0 or not np.isfinite(samples).all() or (samples <= 0).any():
            raise ValueError("Service sample pool must be one-dimensional, nonempty, finite, and positive.")
    rng = np.random.default_rng(seed)
    arrivals: list[float] = []
    time = 0.0
    while True:
        time += float(rng.exponential(60 / rate))
        if time >= closing:
            break
        arrivals.append(time)
        if len(arrivals) > MAX_PATIENTS:
            raise ValueError("Generated more than 10,000 patients. Reduce demand or the window.")
    if not arrivals:
        raise ValueError("No patients arrived. Increase demand/window or choose another seed.")
    patients = pd.DataFrame(
        {
            "patient_id": [f"P{i:04d}" for i in range(1, len(arrivals) + 1)],
            "arrival_min": arrivals,
            "service_min": (
                rng.exponential(service, len(arrivals))
                if service_samples_min is None
                else rng.choice(samples, size=len(arrivals), replace=True)
            ),
        }
    )
    return validate_patients(patients, closing)
