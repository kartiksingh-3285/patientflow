import math
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from hospital.data import MAX_UPLOAD_BYTES, generate_patients, load_csv, load_hangu_durations, validate_patients
from hospital.queueing import erlang_c, recommend_staffing
from hospital.simulation import simulate
from scripts.import_hangu import extract_durations


def tiny_cohort() -> pd.DataFrame:
    return pd.DataFrame(
        {"patient_id": ["P001", "P002", "P003"], "arrival_min": [0, 2, 4], "service_min": [5, 5, 5]}
    )


class QueueingTests(unittest.TestCase):
    def test_mm1_known_answer(self):
        result = erlang_c(2, 20, 1)
        self.assertTrue(result.stable)
        self.assertAlmostEqual(result.utilization, 2 / 3)
        self.assertAlmostEqual(result.probability_wait, 2 / 3)
        self.assertAlmostEqual(result.mean_wait_min, 40)
        self.assertAlmostEqual(result.mean_queue, 4 / 3)
        self.assertAlmostEqual(result.mean_system_min, 60)

    def test_mm2_known_answer(self):
        result = erlang_c(4, 20, 2)
        self.assertAlmostEqual(result.probability_wait, 8 / 15)
        self.assertAlmostEqual(result.mean_wait_min, 16)

    def test_recurrence_matches_direct_formula(self):
        for doctors in range(1, 15):
            for rho in (0.01, 0.4, 0.8, 0.999):
                rate = doctors * 3 * rho
                a = rate / 3
                tail = a**doctors / math.factorial(doctors) / (1 - rho)
                p_wait = tail / (sum(a**n / math.factorial(n) for n in range(doctors)) + tail)
                expected = 60 * p_wait / (doctors * 3 - rate)
                self.assertAlmostEqual(erlang_c(rate, 20, doctors).mean_wait_min, expected, places=7)

    def test_unstable_is_not_zero(self):
        for rate in (3, 5):
            result = erlang_c(rate, 20, 1)
            self.assertFalse(result.stable)
            self.assertTrue(math.isinf(result.mean_wait_min))
            self.assertTrue(math.isnan(result.probability_wait))

    def test_zero_arrivals(self):
        result = erlang_c(0, 20, 1)
        self.assertEqual(result.mean_wait_min, 0)
        self.assertEqual(result.mean_queue, 0)
        self.assertEqual(result.mean_system_min, 20)

    def test_smallest_feasible_staffing(self):
        result = recommend_staffing(4, 20, 1, 6, 5)
        self.assertTrue(result.target_met)
        self.assertEqual(result.doctors, 3)
        self.assertTrue(all(p.mean_wait_min > 5 for p in result.predictions[:-1]))
        self.assertLessEqual(result.predictions[-1].mean_wait_min, 5)

    def test_no_added_doctors_if_baseline_meets_target(self):
        result = recommend_staffing(1, 10, 2, 6, 5)
        self.assertEqual(result.doctors, 2)
        self.assertEqual(len(result.predictions), 1)

    def test_infeasible_and_zero_target(self):
        for target in (0, 5):
            result = recommend_staffing(4, 20, 1, 2, target)
            self.assertFalse(result.target_met)
            self.assertEqual(result.doctors, 2)

    def test_invalid_inputs(self):
        for args in [(-1, 20, 1), (2, 0, 1), (2, math.nan, 1), (math.inf, 20, 1),
                     (2, 20, 0), (2, 20, 1.5), (2, 20, True), (2, 20, 51)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                erlang_c(*args)
        with self.assertRaises(ValueError):
            recommend_staffing(2, 20, 3, 2, 5)
        with self.assertRaises(ValueError):
            recommend_staffing(2, 20, 1, 6, -1)


class DataTests(unittest.TestCase):
    def test_source_conversion_and_sorting(self):
        self.assertEqual(
            extract_durations(b"ServTime,unused\n3600,discard\n180,discard\n900,discard\n"),
            [3, 15, 60],
        )
        for source in (b"other\n900\n", b"ServTime\n", b"ServTime\nNaN\n",
                       b"ServTime\n0\n", b"ServTime\n3601\n", b"ServTime\ninvalid\n"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_durations(source)

    def test_real_source_extract_and_provenance(self):
        pool = load_hangu_durations()
        self.assertEqual(len(pool), 6637)
        self.assertAlmostEqual(float(pool.mean()), 13.365, places=3)
        self.assertTrue(np.all(pool[:-1] <= pool[1:]))
        self.assertTrue(np.all((pool >= 3) & (pool <= 60)))

    def test_hybrid_preserves_arrivals_and_samples_only_source(self):
        pool = load_hangu_durations()
        hybrid = generate_patients(12, pool.mean(), 480, 42, service_samples_min=pool)
        repeat = generate_patients(12, pool.mean(), 480, 42, service_samples_min=pool)
        synthetic = generate_patients(12, 12, 480, 42)
        assert_frame_equal(hybrid, repeat)
        np.testing.assert_array_equal(hybrid["arrival_min"], synthetic["arrival_min"])
        self.assertTrue(np.isin(hybrid["service_min"], pool).all())
        self.assertEqual(len(hybrid), 102)

    def test_invalid_service_pool(self):
        for pool in (np.array([]), np.array([[5]]), np.array([0]), np.array([math.nan]),
                     np.array([math.inf]), np.array(["invalid"])):
            with self.subTest(pool=pool), self.assertRaises(ValueError):
                generate_patients(12, 12, 480, 42, service_samples_min=pool)

    def test_missing_and_invalid_local_source_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            location = Path(directory)
            with patch("hospital.data.HANGU_DATA_DIR", location):
                with self.assertRaisesRegex(ValueError, "restore"):
                    load_hangu_durations()
                (location / "hangu_service_minutes.csv").write_text("service_min\n15\n")
                (location / "hangu_provenance.json").write_text("invalid")
                with self.assertRaisesRegex(ValueError, "provenance"):
                    load_hangu_durations()
                (location / "hangu_provenance.json").write_text(json.dumps({"extract_sha256": "wrong"}))
                with self.assertRaisesRegex(ValueError, "checksum"):
                    load_hangu_durations()

    def test_reproducibility_and_boundaries(self):
        first = generate_patients(12, 12, 480, 42)
        second = generate_patients(12, 12, 480, 42)
        assert_frame_equal(first, second)
        self.assertTrue(first["arrival_min"].between(0, 480, inclusive="left").all())
        self.assertTrue((first["service_min"] > 0).all())
        self.assertFalse(first.equals(generate_patients(12, 12, 480, 43)))

    def test_empty_generation_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "No patients"):
            generate_patients(0.1, 12, 15, 42)

    def test_generation_validation(self):
        for args in [(0, 12, 480, 42), (12, 0, 480, 42), (12, 12, -1, 42),
                     (12, 12, 480, -1), (12, 12, 480, 1.2)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                generate_patients(*args)

    def test_csv_preserves_string_ids_and_ties(self):
        content = b"patient_id,arrival_min,service_min\n001,2,5\nNA,0,5\n003,2,5\n"
        patients = load_csv(content, 480)
        self.assertEqual(patients["patient_id"].tolist(), ["NA", "001", "003"])

    def test_invalid_csv(self):
        examples = [
            b"",
            b"\xff",
            b"patient_id,arrival_min\nP1,0\n",
            b"patient_id,arrival_min,service_min\n,0,5\n",
            b"patient_id,arrival_min,service_min\nP1,0,5\nP1,2,5\n",
            b"patient_id,arrival_min,service_min\nP1,abc,5\n",
            b"patient_id,arrival_min,service_min\nP1,0,NaN\n",
            b"patient_id,arrival_min,service_min\nP1,0,inf\n",
            b"patient_id,arrival_min,service_min\nP1,0,0\n",
            b"patient_id,arrival_min,service_min\nP1,480,5\n",
            b"patient_id,arrival_min,service_min\nP1,-1,5\n",
            b"patient_id,arrival_min,service_min\nP1,0\n",
            b"patient_id,arrival_min,service_min\nP1,0,5,7\n",
            b"patient_id,arrival_min,service_min\n\"P1,0,5\n",
            b"patient_id,arrival_min,service_min,service_min\nP1,0,5,7\n",
        ]
        for content in examples:
            with self.subTest(content=content), self.assertRaises(ValueError):
                load_csv(content, 480)
        with self.assertRaisesRegex(ValueError, "2 MB"):
            load_csv(b"x" * (MAX_UPLOAD_BYTES + 1), 480)

    def test_row_limit(self):
        content = "patient_id,arrival_min,service_min\n" + "".join(f"P{i},0,1\n" for i in range(10001))
        with self.assertRaisesRegex(ValueError, "patient rows"):
            load_csv(content.encode(), 480)

    def test_validation_does_not_mutate(self):
        patients = tiny_cohort()
        original = patients.copy(deep=True)
        validate_patients(patients, 480)
        assert_frame_equal(patients, original)

    def test_invalid_frame(self):
        for column, value in [("patient_id", None), ("patient_id", " "), ("arrival_min", True),
                              ("service_min", np.inf), ("arrival_min", np.nan)]:
            patients = tiny_cohort()
            patients[column] = patients[column].astype(object)
            patients.loc[0, column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                validate_patients(patients, 480)
        with self.assertRaises(ValueError):
            validate_patients(tiny_cohort().iloc[:0], 480)


class SimulationTests(unittest.TestCase):
    def test_hand_calculated_one_doctor(self):
        result = simulate(tiny_cohort(), 1, 10, 5)
        self.assertEqual(result.patients["start_min"].tolist(), [0, 5, 10])
        self.assertEqual(result.patients["wait_min"].tolist(), [0, 3, 6])
        self.assertEqual(result.metrics["mean_wait_min"], 3)
        self.assertEqual(result.metrics["queue_area"], 9)
        self.assertEqual(result.metrics["max_queue"], 2)
        self.assertEqual(result.metrics["horizon_min"], 15)
        self.assertEqual(result.metrics["overtime_min"], 5)
        self.assertAlmostEqual(result.metrics["mean_queue"], 0.6)
        self.assertAlmostEqual(result.metrics["window_mean_queue"], 0.9)
        self.assertAlmostEqual(result.metrics["within_target_pct"], 200 / 3)
        self.assertEqual(result.doctors.iloc[0]["busy_min"], 15)
        self.assertEqual(result.doctors.iloc[0]["window_busy_min"], 10)

    def test_hand_calculated_two_doctors(self):
        result = simulate(tiny_cohort(), 2, 10, 5)
        self.assertEqual(result.patients["start_min"].tolist(), [0, 2, 5])
        self.assertEqual(result.patients["wait_min"].tolist(), [0, 0, 1])
        self.assertAlmostEqual(result.metrics["mean_wait_min"], 1 / 3)
        self.assertEqual(result.metrics["queue_area"], 1)
        self.assertEqual(result.metrics["horizon_min"], 10)
        self.assertEqual(result.metrics["overtime_min"], 0)
        self.assertEqual(result.doctors["busy_min"].tolist(), [10, 5])

    def test_busy_time_clipped_at_closing(self):
        patients = pd.DataFrame({"patient_id": ["P1"], "arrival_min": [8], "service_min": [5]})
        result = simulate(patients, 2, 10)
        self.assertEqual(result.doctors["window_busy_min"].tolist(), [2, 0])
        self.assertAlmostEqual(result.metrics["window_utilization_pct"], 10)
        self.assertEqual(result.metrics["overtime_min"], 3)

    def test_simultaneous_departure_and_arrival(self):
        patients = pd.DataFrame({"patient_id": ["A", "B", "C"], "arrival_min": [0, 0, 5], "service_min": [5, 5, 5]})
        result = simulate(patients, 1, 20)
        self.assertEqual(result.patients["start_min"].tolist(), [0, 5, 10])
        self.assertEqual(result.metrics["max_queue"], 1)
        self.assertEqual(result.metrics["queue_area"], 10)
        self.assertEqual(result.queue["queue_length"].iloc[-1], 0)

    def test_seeded_invariants_and_nonoverlap(self):
        for seed in (0, 42, 100):
            patients = generate_patients(12, 12, 480, seed)
            baseline = simulate(patients, 2, 480)
            improved = simulate(patients, 4, 480)
            for result in (baseline, improved):
                self.assertEqual(len(result.patients), len(patients))
                self.assertTrue((result.queue["queue_length"] >= 0).all())
                self.assertEqual(result.queue["queue_length"].iloc[-1], 0)
                self.assertAlmostEqual(result.metrics["queue_area"], result.patients["wait_min"].sum())
                self.assertAlmostEqual(result.doctors["busy_min"].sum(), patients["service_min"].sum())
                self.assertTrue(result.doctors["utilization_pct"].between(0, 100.000000001).all())
                self.assertTrue(result.doctors["window_utilization_pct"].between(0, 100.000000001).all())
                for _, assignments in result.patients.groupby("doctor"):
                    self.assertTrue(
                        (assignments["start_min"].to_numpy()[1:] >= assignments["end_min"].to_numpy()[:-1]).all()
                    )
            self.assertTrue((improved.patients["wait_min"] <= baseline.patients["wait_min"] + 1e-9).all())
            assert_frame_equal(baseline.patients.loc[:, patients.columns], improved.patients.loc[:, patients.columns])

    def test_invalid_simulation_inputs(self):
        with self.assertRaises(ValueError):
            simulate(tiny_cohort(), 0, 480)
        with self.assertRaises(ValueError):
            simulate(tiny_cohort(), 1, 480, -1)

    def test_default_demonstrates_mean_target_and_reduction(self):
        patients = generate_patients(12, 12, 480, 42)
        recommendation = recommend_staffing(len(patients) / 8, patients["service_min"].mean(), 2, 6, 5)
        first = simulate(patients, 2, 480)
        second = simulate(patients, recommendation.doctors, 480)
        self.assertTrue(recommendation.target_met)
        self.assertLessEqual(second.metrics["mean_wait_min"], 5)
        self.assertGreater(first.metrics["mean_wait_min"], second.metrics["mean_wait_min"])
        self.assertEqual(first.metrics["patients"], second.metrics["patients"])


if __name__ == "__main__":
    unittest.main()
