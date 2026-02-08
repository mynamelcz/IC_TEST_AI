import csv
import datetime
from pathlib import Path

import pytest


class CsvReportPlugin:
    """Pytest plugin that generates a CSV report of test results."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.results: list[dict] = []

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when != "call":
            return

        # Extract metadata stored by the test via item.user_properties
        props = dict(item.user_properties)
        self.results.append({
            "chip": props.get("chip", ""),
            "pin": props.get("pin", ""),
            "test_id": props.get("test_id", ""),
            "test_name": props.get("test_name", ""),
            "expected": props.get("expected", ""),
            "actual": props.get("actual", ""),
            "result": "PASS" if report.passed else "FAIL",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def pytest_sessionfinish(self, session, exitstatus):
        if not self.results:
            return
        fieldnames = [
            "chip", "pin", "test_id", "test_name",
            "expected", "actual", "result", "timestamp",
        ]
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)


def pytest_addoption(parser):
    parser.addoption(
        "--csv-report",
        default=None,
        help="Path to CSV report output file",
    )


def pytest_configure(config):
    csv_path = config.getoption("--csv-report")
    if csv_path:
        plugin = CsvReportPlugin(csv_path)
        config.pluginmanager.register(plugin, "csv_report")
