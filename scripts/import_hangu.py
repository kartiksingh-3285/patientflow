import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import urllib.request

REVISION = "f26b66a3e3dd69d45502ff30d934e24b6476218c"
BASE_URL = f"https://raw.githubusercontent.com/fenghaolin/HanguData/{REVISION}"
DESTINATION = Path(__file__).resolve().parents[1] / "data"


def extract_durations(content: bytes) -> list[float]:
    reader = csv.DictReader(StringIO(content.decode("utf-8-sig")))
    if reader.fieldnames is None or "ServTime" not in reader.fieldnames:
        raise ValueError("Hangu source is missing ServTime.")
    durations = []
    for number, row in enumerate(reader, start=2):
        try:
            seconds = float(row["ServTime"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid Hangu ServTime on row {number}.") from error
        if not math.isfinite(seconds) or not 180 <= seconds <= 3600:
            raise ValueError(f"Hangu row {number} is outside the authors' cleaned 180..3600 second range.")
        durations.append(seconds / 60)
    if not durations:
        raise ValueError("Hangu source contains no durations.")
    return sorted(durations)


def main() -> None:
    with urllib.request.urlopen(f"{BASE_URL}/Data.csv", timeout=60) as response:
        source = response.read()
    with urllib.request.urlopen(f"{BASE_URL}/LICENSE", timeout=60) as response:
        license_text = response.read()
    durations = extract_durations(source)
    DESTINATION.mkdir(exist_ok=True)
    duration_path = DESTINATION / "hangu_service_minutes.csv"
    with duration_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["service_min"])
        writer.writerows((value,) for value in durations)
    (DESTINATION / "HANGU_LICENSE.txt").write_bytes(license_text)
    metadata = {
        "citation": "Feng, H., Jia, Y., Zhou, S., Chen, H., & Huang, T. (2023). "
                    "A Dataset of Service Time and Related Patient Characteristics from an Outpatient Clinic. Data, 8(3), 47.",
        "paper_url": "https://doi.org/10.3390/data8030047",
        "repository_url": "https://github.com/fenghaolin/HanguData",
        "archive_url": "https://doi.org/10.5281/zenodo.7484205",
        "license": "CC BY-NC-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "source_revision": REVISION,
        "source_url": f"{BASE_URL}/Data.csv",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "extract_sha256": hashlib.sha256(duration_path.read_bytes()).hexdigest(),
        "records": len(durations),
        "mean_service_min": sum(durations) / len(durations),
        "min_service_min": min(durations),
        "max_service_min": max(durations),
        "transformation": "Authors' cleaned Data.csv: ServTime seconds / 60; sorted ascending; "
                          "all other columns discarded; no additional filtering.",
        "source_cleaning": "Published Data_process_stat.ipynb retains ServTime between 180 and 3600 "
                           "seconds inclusive and nonmissing Visit.No.",
        "limitations": "Duration estimates, not stopwatch measurements. No clinic-arrival timestamps "
                       "used. Hybrid arrivals and doctor availability are synthetic assumptions. "
                       "Uniform resampling ignores session/patient heterogeneity. Not clinical validation.",
    }
    (DESTINATION / "hangu_provenance.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Imported {len(durations):,} duration estimates; mean {metadata['mean_service_min']:.3f} min.")
    print("Stored only sorted durations, attribution/provenance, and license; no patient identifiers.")


if __name__ == "__main__":
    main()
