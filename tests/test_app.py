from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class DashboardTests(unittest.TestCase):
    def launch(self):
        return AppTest.from_file(str(APP), default_timeout=30).run()

    def test_default_dashboard_and_records(self):
        app = self.launch()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.metric), 4)
        self.assertEqual(len(app.tabs), 4)
        self.assertGreaterEqual(len(app.dataframe), 4)
        app.radio(key="result_scenario").set_value("Recommended").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)

    def test_invalid_doctor_limit_is_visible(self):
        app = self.launch()
        app.number_input(key="baseline_count").set_value(7).run()
        app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Maximum doctors cannot be below", app.error[0].value)

    def test_infeasible_target_is_not_reported_as_success(self):
        app = self.launch()
        app.number_input(key="maximum_count").set_value(2).run()
        app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.success), 0)
        self.assertTrue(any("Target not reachable" in warning.value for warning in app.warning))

    def test_empty_synthetic_cohort_is_visible(self):
        app = self.launch()
        app.number_input(key="hours").set_value(0.25)
        app.number_input(key="arrival_rate").set_value(0.1).run()
        app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("No patients arrived", app.error[0].value)

    def test_upload_mode_requests_file(self):
        app = self.launch()
        app.radio(key="data_source").set_value("Upload CSV").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertTrue(any("Upload a CSV" in info.value for info in app.info))

    def test_hybrid_dashboard_is_explicit_and_offline(self):
        app = self.launch()
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network in dashboard")):
            app.radio(key="data_source").set_value("Hangu hybrid").run()
            app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.metric), 4)
        self.assertTrue(any("Hybrid data:" in warning.value for warning in app.warning))
        self.assertTrue(any("6,637" in caption.value for caption in app.caption))
        self.assertNotIn("Mean consultation (minutes)", [widget.label for widget in app.number_input])
        app.radio(key="data_source").set_value("Synthetic demo").run()
        app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[1].value, "80.80 min")

    def test_hybrid_missing_source_error_visible(self):
        app = self.launch()
        with patch("hospital.data.load_hangu_durations", side_effect=ValueError("Cannot read Hangu data.")):
            app.radio(key="data_source").set_value("Hangu hybrid").run()
            app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Cannot read Hangu", app.error[0].value)

    def test_changes_wait_for_explicit_run(self):
        app = self.launch()
        app.number_input(key="arrival_rate").set_value(18.0).run()
        self.assertEqual(app.metric[1].value, "80.80 min")
        self.assertTrue(any("Settings changed" in info.value for info in app.info))
        self.assertTrue(any("Synthetic demo" in caption.value and "Last run" in caption.value for caption in app.caption))
        app.button(key="run_comparison").click().run()
        self.assertEqual(len(app.error), 0)
        self.assertFalse(any("Settings changed" in info.value for info in app.info))
        self.assertNotEqual(app.metric[1].value, "80.80 min")

    def test_pending_source_does_not_relabel_saved_results(self):
        app = self.launch()
        app.radio(key="data_source").set_value("Hangu hybrid").run()
        self.assertTrue(any("Last run: Synthetic demo" in caption.value for caption in app.caption))
        self.assertFalse(any("Hybrid data:" in warning.value for warning in app.warning))

    def test_presets_and_reset_preserve_reproducible_demo(self):
        app = self.launch()
        next(button for button in app.button if button.label == "Busy clinic").click().run()
        self.assertEqual(app.number_input(key="arrival_rate").value, 18.0)
        app.button(key="run_comparison").click().run()
        self.assertNotEqual(app.metric[1].value, "80.80 min")
        next(button for button in app.button if button.label == "Load demo").click().run()
        app.button(key="run_comparison").click().run()
        self.assertEqual(app.metric[1].value, "80.80 min")

    def test_patient_filters_do_not_change_cohort(self):
        app = self.launch()
        count = app.metric[0].value
        app.text_input(key="patient_search").set_value("P0001").run()
        self.assertEqual(len(app.dataframe[-1].value), 1)
        self.assertEqual(app.dataframe[-1].value.iloc[0]["patient_id"], "P0001")
        self.assertEqual(app.metric[0].value, count)

        app.text_input(key="patient_search").set_value("not-present").run()
        self.assertEqual(len(app.dataframe[-1].value), 0)
        self.assertTrue(any("No patients match" in info.value for info in app.info))
        app.text_input(key="patient_search").set_value("").run()
        app.selectbox(key="patient_filter").set_value("Waited longer than target").run()
        self.assertTrue((app.dataframe[-1].value["wait_min"] > 5).all())
        self.assertEqual(app.metric[0].value, count)

    def test_queue_and_utilization_controls_do_not_change_results(self):
        app = self.launch()
        original_metrics = [metric.value for metric in app.metric]
        app.toggle[0].set_value(True).run()
        next(radio for radio in app.radio if radio.label == "Doctor utilization period").set_value("Full session").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([metric.value for metric in app.metric], original_metrics)


if __name__ == "__main__":
    unittest.main()
